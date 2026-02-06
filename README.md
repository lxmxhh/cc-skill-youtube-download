# YouTube Download Skill

一个智能的 YouTube 视频下载工具，支持多种下载策略，自动重试直到成功。

## 功能特点

- 🎯 **优先下载 MP4 格式** - 兼容性最好
- 🔄 **多种下载策略** - 自动切换直到成功
- 🍪 **智能 Cookie 管理** - 自动从浏览器提取
- 📊 **实时进度显示** - 下载速度、进度、ETA
- 🎬 **多种质量选择** - 最高质量/1080p/720p/480p/仅音频
- 📝 **自动下载字幕** - 支持多语言字幕

## 安装

### 方法 1: 使用 Claude Code CLI (推荐)

```bash
npx skills add https://github.com/lxmxhh/cc-skill-youtube-download.git
```

### 方法 2: 手动安装

1. 将此目录复制到 `~/.claude/skills/youtube-download`
2. 安装依赖:

```bash
pip install yt-dlp
```

## 使用方法

### 在 Claude Code 中使用

触发 skill:
```
/youtube-download https://youtube.com/watch?v=xxxxx
```

或者:
```
下载这个 YouTube 视频: https://youtube.com/watch?v=xxxxx
```

### 直接使用 Python 脚本

```bash
# 基本用法
python scripts/download_video.py <youtube_url>

# 指定质量
python scripts/download_video.py <youtube_url> 1080p

# 指定输出目录
python scripts/download_video.py <youtube_url> 720p ./downloads

# 下载字幕
python scripts/download_video.py <youtube_url> best ./downloads true
```

## 下载策略

工具会按以下顺序自动尝试不同的策略：

1. **直接下载** - 无需 Cookie，适用于公开视频
2. **使用 Cookies 文件** - 使用 `cookies.txt` 文件
3. **Chrome 浏览器** - 从 Chrome 提取 Cookies
4. **Firefox 浏览器** - 从 Firefox 提取 Cookies
5. **Edge 浏览器** - 从 Edge 提取 Cookies
6. **降级下载** - 接受任何可用格式

## Cookie 配置

如果视频需要登录才能观看，你需要提供 YouTube Cookies：

### 方法 1: 手动导出 (推荐)

1. 安装浏览器扩展 "Get cookies.txt LOCALLY"
   - [Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. 在 YouTube 网站上登录你的账号

3. 点击扩展图标，导出 cookies

4. 将导出的 `cookies.txt` 保存到 `~/.claude/skills/youtube-download/cookies.txt`

### 方法 2: 自动提取

工具会自动尝试从你的浏览器（Chrome/Firefox/Edge）提取 Cookies，无需手动配置。

## 质量选项

- `best` - 最高质量（默认）
- `1080p` - 1080p 分辨率
- `720p` - 720p 分辨率
- `480p` - 480p 分辨率
- `audio` - 仅音频

## 常见问题

### Q: 下载失败，提示 "Sign in to confirm you're not a bot"

**A:** 这意味着 YouTube 需要身份验证。工具会自动尝试从浏览器提取 Cookies。如果仍然失败，请手动导出 cookies.txt。

### Q: 下载的是 webm 格式，不是 mp4

**A:** 工具会优先尝试下载 mp4 格式。如果只有 webm 可用，可以使用 FFmpeg 转换：

```bash
ffmpeg -i video.webm -c:v libx264 -c:a aac video.mp4
```

### Q: 如何下载播放列表？

**A:** 直接传入播放列表 URL，工具会自动检测并下载所有视频。

### Q: 下载速度很慢

**A:** 这取决于你的网络连接和 YouTube 服务器。可以尝试：
- 降低视频质量
- 更换网络环境
- 使用代理

## 技术细节

### 依赖

- **yt-dlp** - YouTube 下载核心
- **Python 3.7+** - 运行环境
- **FFmpeg** (可选) - 用于格式转换和合并

### 输出格式

下载成功后，脚本会输出 JSON 格式的结果：

```json
{
  "success": true,
  "strategy": "browser_chrome",
  "video_path": "/path/to/video.mp4",
  "title": "视频标题",
  "duration": 1562,
  "file_size": 561234567,
  "subtitle_files": [
    "/path/to/video.zh-Hans.vtt",
    "/path/to/video.en.vtt"
  ],
  "resolution": "1920x1080",
  "uploader": "频道名称"
}
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 相关链接

- [yt-dlp 文档](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg 文档](https://ffmpeg.org/documentation.html)
- [Claude Code 文档](https://docs.anthropic.com/claude/docs)
