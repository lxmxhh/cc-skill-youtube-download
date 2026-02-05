#!/usr/bin/env python3
"""
YouTube 视频智能下载工具
支持多种下载策略，自动重试直到成功
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import yt_dlp
except ImportError:
    print("❌ 错误: yt-dlp 未安装")
    print("请安装: pip install yt-dlp")
    sys.exit(1)


class DownloadStrategy:
    """下载策略基类"""

    def __init__(self, url: str, quality: str, output_dir: str, download_subs: bool = False):
        self.url = url
        self.quality = quality
        self.output_dir = Path(output_dir)
        self.download_subs = download_subs

    def get_format_string(self) -> str:
        """根据质量设置获取格式字符串"""
        quality_map = {
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '1080p': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best[height<=1080]',
            '720p': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best[height<=720]',
            '480p': 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best[height<=480]',
            'audio': 'bestaudio[ext=m4a]/bestaudio/best'
        }
        return quality_map.get(self.quality, quality_map['best'])

    def get_base_options(self) -> dict:
        """获取基础 yt-dlp 选项"""
        return {
            'format': self.get_format_string(),
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'writesubtitles': self.download_subs,
            'writeautomaticsub': self.download_subs,
            'subtitleslangs': ['zh-Hans', 'zh-Hant', 'en', 'ja', 'ko'],
            'subtitlesformat': 'vtt/srt',
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
        }

    def _progress_hook(self, d):
        """下载进度回调"""
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                downloaded = self._format_bytes(d['downloaded_bytes'])
                total = self._format_bytes(d['total_bytes'])
                speed = d.get('speed', 0)
                speed_str = self._format_bytes(speed) + '/s' if speed else 'N/A'

                bar_length = 30
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)

                print(f"\r   [{bar}] {percent:.1f}% - {downloaded}/{total} - {speed_str}", end='', flush=True)
            elif 'downloaded_bytes' in d:
                downloaded = self._format_bytes(d['downloaded_bytes'])
                speed = d.get('speed', 0)
                speed_str = self._format_bytes(speed) + '/s' if speed else 'N/A'
                print(f"\r   下载中... {downloaded} - {speed_str}", end='', flush=True)
        elif d['status'] == 'finished':
            print()  # 换行

    def _format_bytes(self, bytes_num: float) -> str:
        """格式化字节数"""
        if bytes_num is None:
            return 'N/A'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} TB"

    def download(self) -> Dict:
        """执行下载，由子类实现"""
        raise NotImplementedError


class DirectDownloadStrategy(DownloadStrategy):
    """策略1: 直接下载（无 Cookie）"""

    def download(self) -> Dict:
        print("🎯 策略 1: 直接下载（无 Cookie）")

        ydl_opts = self.get_base_options()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频信息
            info = ydl.extract_info(self.url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            print(f"   标题: {title}")
            print(f"   时长: {self._format_duration(duration)}")
            print(f"\n📥 开始下载...")

            # 下载
            info = ydl.extract_info(self.url, download=True)

            return self._prepare_result(ydl, info)

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _prepare_result(self, ydl, info) -> Dict:
        """准备返回结果"""
        video_filename = ydl.prepare_filename(info)
        video_path = Path(video_filename)

        # 如果是 webm 或其他格式，检查是否有 mp4
        if video_path.suffix != '.mp4':
            mp4_path = video_path.with_suffix('.mp4')
            if mp4_path.exists():
                video_path = mp4_path

        file_size = video_path.stat().st_size if video_path.exists() else 0

        # 查找字幕文件
        subtitle_files = []
        if self.download_subs:
            subtitle_pattern = f"{video_path.stem}.*"
            for sub_file in video_path.parent.glob(subtitle_pattern):
                if sub_file.suffix in ['.vtt', '.srt']:
                    subtitle_files.append(str(sub_file))

        return {
            'video_path': str(video_path),
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'file_size': file_size,
            'subtitle_files': subtitle_files,
            'resolution': f"{info.get('width', 0)}x{info.get('height', 0)}",
            'uploader': info.get('uploader', 'Unknown')
        }


class CookiesFileStrategy(DownloadStrategy):
    """策略2: 使用 Cookies 文件"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookies_path = Path(__file__).parent.parent / 'cookies.txt'

    def download(self) -> Dict:
        if not self.cookies_path.exists():
            raise FileNotFoundError(f"Cookies 文件不存在: {self.cookies_path}")

        print(f"🎯 策略 2: 使用 Cookies 文件")
        print(f"   Cookies 路径: {self.cookies_path}")

        ydl_opts = self.get_base_options()
        ydl_opts['cookiefile'] = str(self.cookies_path)

        strategy = DirectDownloadStrategy(self.url, self.quality, str(self.output_dir), self.download_subs)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            print(f"   标题: {title}")
            print(f"   时长: {strategy._format_duration(duration)}")
            print(f"\n📥 开始下载...")

            info = ydl.extract_info(self.url, download=True)
            return strategy._prepare_result(ydl, info)


class BrowserCookiesStrategy(DownloadStrategy):
    """策略3: 从浏览器提取 Cookies"""

    def __init__(self, browser_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.browser_name = browser_name

    def download(self) -> Dict:
        print(f"🎯 策略 3: 从 {self.browser_name} 浏览器提取 Cookies")

        ydl_opts = self.get_base_options()
        ydl_opts['cookiesfrombrowser'] = (self.browser_name,)

        strategy = DirectDownloadStrategy(self.url, self.quality, str(self.output_dir), self.download_subs)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            print(f"   标题: {title}")
            print(f"   时长: {strategy._format_duration(duration)}")
            print(f"\n📥 开始下载...")

            info = ydl.extract_info(self.url, download=True)
            return strategy._prepare_result(ydl, info)


class FallbackStrategy(DownloadStrategy):
    """策略4: 降级下载（最后手段）"""

    def download(self) -> Dict:
        print("🎯 策略 4: 降级下载（任何可用格式）")

        ydl_opts = self.get_base_options()
        ydl_opts['format'] = 'best'  # 接受任何格式

        strategy = DirectDownloadStrategy(self.url, self.quality, str(self.output_dir), self.download_subs)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            print(f"   标题: {title}")
            print(f"   时长: {strategy._format_duration(duration)}")
            print(f"\n📥 开始下载...")

            info = ydl.extract_info(self.url, download=True)
            return strategy._prepare_result(ydl, info)


def download_with_strategies(url: str, quality: str = 'best',
                            output_dir: str = None,
                            download_subs: bool = False) -> Tuple[str, Dict]:
    """
    使用多种策略依次尝试下载

    Returns:
        Tuple[str, Dict]: (成功的策略名称, 下载结果)
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"🎬 YouTube 视频智能下载")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"质量: {quality}")
    print(f"输出目录: {output_dir}")
    print(f"下载字幕: {'是' if download_subs else '否'}")
    print(f"{'='*60}\n")

    # 定义策略列表
    strategies = [
        ('direct', lambda: DirectDownloadStrategy(url, quality, str(output_dir), download_subs).download()),
        ('cookies_file', lambda: CookiesFileStrategy(url, quality, str(output_dir), download_subs).download()),
        ('browser_chrome', lambda: BrowserCookiesStrategy('chrome', url, quality, str(output_dir), download_subs).download()),
        ('browser_firefox', lambda: BrowserCookiesStrategy('firefox', url, quality, str(output_dir), download_subs).download()),
        ('browser_edge', lambda: BrowserCookiesStrategy('edge', url, quality, str(output_dir), download_subs).download()),
        ('fallback', lambda: FallbackStrategy(url, quality, str(output_dir), download_subs).download()),
    ]

    last_error = None
    for strategy_name, strategy_func in strategies:
        try:
            print(f"\n尝试策略: {strategy_name}")
            print("-" * 60)
            result = strategy_func()
            print(f"\n✅ 策略 {strategy_name} 成功！\n")
            return strategy_name, result
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ 策略 {strategy_name} 失败: {error_msg}\n")
            last_error = error_msg

            # 检查是否是需要身份验证的错误
            if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                print("   提示: 需要身份验证，尝试下一个策略...\n")
                continue
            elif "Video unavailable" in error_msg:
                print("   提示: 视频不可用，请检查 URL\n")
                break
            else:
                continue

    # 所有策略都失败
    raise Exception(f"所有下载策略都失败了。最后一个错误: {last_error}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python download_video.py <youtube_url> [quality] [output_dir] [download_subs]")
        print("\n质量选项:")
        print("  best    - 最高质量（默认）")
        print("  1080p   - 1080p")
        print("  720p    - 720p")
        print("  480p    - 480p")
        print("  audio   - 仅音频")
        print("\n示例:")
        print("  python download_video.py https://youtube.com/watch?v=xxxxx")
        print("  python download_video.py https://youtube.com/watch?v=xxxxx 1080p")
        print("  python download_video.py https://youtube.com/watch?v=xxxxx 720p ./downloads true")
        sys.exit(1)

    url = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else 'best'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    download_subs = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False

    try:
        strategy_name, result = download_with_strategies(url, quality, output_dir, download_subs)

        # 输出结果
        print("\n" + "="*60)
        print("✅ 下载成功！")
        print("="*60)
        print(f"\n🎯 使用策略: {strategy_name}")
        print(f"\n📁 文件信息:")
        print(f"   标题: {result['title']}")
        print(f"   路径: {result['video_path']}")

        # 格式化文件大小
        size_mb = result['file_size'] / (1024 * 1024)
        print(f"   大小: {size_mb:.1f} MB")

        # 格式化时长
        duration = result['duration']
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours > 0:
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes:02d}:{seconds:02d}"
        print(f"   时长: {duration_str}")
        print(f"   分辨率: {result['resolution']}")
        print(f"   上传者: {result['uploader']}")

        # 字幕文件
        if result['subtitle_files']:
            print(f"\n📝 字幕文件:")
            for sub_file in result['subtitle_files']:
                sub_path = Path(sub_file)
                print(f"   - {sub_path.name}")

        # 输出 JSON（供程序使用）
        print("\n" + "="*60)
        print("下载结果 (JSON):")
        print(json.dumps({
            'success': True,
            'strategy': strategy_name,
            **result
        }, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        print("\n💡 建议:")
        print("   1. 检查 URL 是否正确")
        print("   2. 确保视频是公开的")
        print("   3. 尝试在浏览器中登录 YouTube")
        print("   4. 检查网络连接")
        sys.exit(1)


if __name__ == "__main__":
    main()
