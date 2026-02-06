---
name: youtube-download
description: A smart YouTube video downloader with multiple strategies, auto-retry, intelligent cookie management, and subtitle support
trigger: /youtube-download
version: 1.0.0
author: lxmxhh
---

# YouTube 视频下载工具

> 一个智能的 YouTube 视频下载工具，支持多种下载策略，自动重试直到成功

## 功能特点

- 🎯 优先下载 MP4 格式（兼容性最好）
- 🔄 多种下载策略自动切换
- 🍪 智能 Cookie 管理
- 📊 实时下载进度显示
- 🎬 支持多种视频质量选择
- 📝 自动下载字幕（可选）

## 工作流程

当用户触发这个 Skill 时，按照以下流程执行：

### 阶段 1: 获取下载 URL

1. 检查用户是否提供了 YouTube URL
2. 如果没有提供，询问用户要下载的视频链接
3. 验证 URL 格式是否正确

### 阶段 2: 询问下载选项

使用 AskUserQuestion 工具询问用户：

1. **视频质量**:
   - 最高质量（推荐）
   - 1080p
   - 720p
   - 480p
   - 仅音频

2. **是否下载字幕**:
   - 是（下载所有可用字幕）
   - 否

3. **输出目录**:
   - 使用默认目录（当前工作目录）
   - 指定自定义路径

### 阶段 3: 环境检测

检查必需的工具是否已安装：

```bash
# 检查 yt-dlp
yt-dlp --version

# 检查 Python 环境
python --version
python -c "import yt_dlp; print('yt-dlp module available')"
```

如果缺少工具，提示用户安装：
- Windows: `pip install yt-dlp`
- macOS/Linux: `brew install yt-dlp` 或 `pip install yt-dlp`

### 阶段 4: 智能下载（核心功能）

使用多种策略依次尝试，直到成功：

#### 策略 1: 直接下载（无 Cookie）
- 最简单的方式
- 适用于大多数公开视频
- 失败后自动进入策略 2

```bash
yt-dlp \
  --format "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  --output "%(title)s.%(ext)s" \
  "<youtube_url>"
```

#### 策略 2: 使用 Cookies 文件
- 检查 skill 目录下的 cookies.txt
- 如果存在且未过期，使用它下载
- 失败后自动进入策略 3

```bash
yt-dlp \
  --cookies "./cookies.txt" \
  --format "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  --output "%(title)s.%(ext)s" \
  "<youtube_url>"
```

#### 策略 3: 从浏览器提取 Cookies
- 尝试从 Chrome、Firefox、Edge 等浏览器提取 cookies
- 按优先级依次尝试：Chrome -> Firefox -> Edge -> Safari

```bash
# 尝试 Chrome
yt-dlp --cookies-from-browser chrome --format "..." "<youtube_url>"

# 失败则尝试 Firefox
yt-dlp --cookies-from-browser firefox --format "..." "<youtube_url>"

# 失败则尝试 Edge
yt-dlp --cookies-from-browser edge --format "..." "<youtube_url>"
```

#### 策略 4: 使用代理（如果前面都失败）
- 询问用户是否要使用代理
- 提供代理配置选项

```bash
yt-dlp --proxy "http://proxy:port" --format "..." "<youtube_url>"
```

#### 策略 5: 降级下载（最后手段）
- 降低视频质量要求
- 尝试下载任何可用格式

```bash
yt-dlp --format "best" "<youtube_url>"
```

### 阶段 5: 进度显示

在下载过程中显示：
- 下载进度百分比
- 已下载大小 / 总大小
- 下载速度
- 预计剩余时间

示例输出：
```
🎬 正在下载: 视频标题
   策略: 使用 Chrome 浏览器 Cookies

   [████████████████░░░░░░░░] 67.8%
   已下载: 234 MB / 345 MB
   速度: 5.2 MB/s
   剩余时间: 00:21
```

### 阶段 6: 下载后处理

1. **验证文件**:
   - 检查文件是否完整
   - 验证文件大小
   - 使用 ffprobe 检查视频元数据

2. **格式转换**（如果需要）:
   - 如果下载的不是 mp4 格式，自动转换
   - 使用 FFmpeg 进行转换
   - 保持原始质量

3. **下载字幕**（如果用户选择）:
   - 下载所有可用语言的字幕
   - 优先 VTT 格式，备选 SRT 格式

4. **生成元数据文件**:
   - 创建 JSON 文件包含视频信息
   - 包括标题、时长、上传者、描述等

### 阶段 7: 输出结果

向用户展示：
- 下载成功的文件路径
- 视频信息（标题、时长、大小）
- 使用的下载策略
- 字幕文件列表（如果有）

示例输出：
```
✅ 下载成功！

📁 文件信息:
   标题: 为什么大多数人的努力都是无效的？
   路径: ./为什么大多数人的努力都是无效的？.mp4
   大小: 535 MB
   时长: 26:02
   分辨率: 1920x1080

🎯 下载策略: 使用 Chrome 浏览器 Cookies

📝 字幕文件:
   - 为什么大多数人的努力都是无效的？.zh-Hans.vtt (简体中文)
   - 为什么大多数人的努力都是无效的？.zh-Hant.vtt (繁体中文)
   - 为什么大多数人的努力都是无效的？.en.vtt (英文)

💡 快速预览:
   open "./为什么大多数人的努力都是无效的？.mp4"
```

---

## 关键技术点

### 1. Cookie 管理策略

**Cookie 文件位置**: `~/.claude/skills/youtube-download/cookies.txt`

**Cookie 优先级**:
1. 用户提供的 cookies.txt（skill 目录下）
2. 从浏览器自动提取（Chrome > Firefox > Edge > Safari）
3. 无 Cookie 直接下载

**Cookie 过期检测**:
- 捕获 "Sign in to confirm you're not a bot" 错误
- 自动切换到下一个策略

### 2. 格式优先级

**MP4 优先策略**:
```bash
# 第一优先：MP4 视频 + M4A 音频
bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]

# 第二优先：最佳 MP4
best[ext=mp4][height<=1080]

# 第三优先：任何最佳格式
best[height<=1080]

# 最后：任何格式
best
```

### 3. 错误处理

**常见错误和解决方案**:

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| "Sign in to confirm you're not a bot" | Cookie 无效/缺失 | 切换到浏览器 Cookie 提取 |
| "Video unavailable" | 视频被删除或私有 | 提示用户检查 URL |
| "This video is age restricted" | 年龄限制 | 必须使用有效 Cookie |
| "HTTP Error 429: Too Many Requests" | 请求过多 | 等待或使用代理 |
| "No video formats found" | 地区限制 | 使用代理 |

### 4. 进度显示

使用 yt-dlp 的进度钩子实时更新：
- 下载百分比
- 下载速度
- ETA（预计完成时间）
- 已下载/总大小

### 5. 并发下载

如果用户提供多个 URL：
- 询问是否并发下载
- 限制并发数（建议 3 个）
- 显示整体进度

---

## Python 脚本说明

### download_video.py

核心下载脚本，实现智能重试机制：

```python
def download_with_strategies(url, quality, output_dir):
    """
    使用多种策略依次尝试下载
    返回：成功使用的策略和文件路径
    """
    strategies = [
        ('direct', download_direct),
        ('cookies_file', download_with_cookies_file),
        ('browser_chrome', download_from_browser_chrome),
        ('browser_firefox', download_from_browser_firefox),
        ('browser_edge', download_from_browser_edge),
        ('fallback', download_fallback)
    ]

    for strategy_name, strategy_func in strategies:
        try:
            result = strategy_func(url, quality, output_dir)
            return strategy_name, result
        except Exception as e:
            print(f"❌ 策略 {strategy_name} 失败: {e}")
            continue

    raise Exception("所有下载策略都失败了")
```

### check_cookies.py

检查和管理 Cookies：

```python
def check_cookies_validity(cookies_path):
    """检查 cookies 文件是否有效"""
    # 尝试使用 cookies 获取视频信息
    # 如果失败，返回 False

def export_cookies_from_browser(browser_name):
    """从浏览器导出 cookies"""
    # 使用 yt-dlp 的内置功能
    # 保存到 cookies.txt
```

### convert_format.py

格式转换工具：

```python
def convert_to_mp4(input_path, output_path):
    """
    将任何视频格式转换为 MP4
    使用 FFmpeg
    """
```

---

## 用户体验优化

### 1. 智能建议

根据视频信息给出建议：
- 如果视频很大（>1GB），建议降低质量
- 如果是音乐视频，建议"仅音频"选项
- 如果是教程视频，建议下载字幕

### 2. 批量下载

支持播放列表和多个 URL：
```bash
# 播放列表
yt-dlp --yes-playlist "<playlist_url>"

# 多个 URL
# 从文件读取 URLs
```

### 3. 断点续传

如果下载中断：
- 自动检测未完成的下载
- 询问是否继续
- 使用 `--continue` 参数

### 4. 下载历史

记录下载历史：
- 保存在 `~/.claude/skills/youtube-download/history.json`
- 避免重复下载
- 提供历史查询功能

---

## 配置文件

### config.json

```json
{
  "default_quality": "1080p",
  "default_output_dir": "~/Downloads/YouTube",
  "auto_download_subtitles": false,
  "preferred_subtitle_languages": ["zh-Hans", "zh-Hant", "en"],
  "cookies_path": "./cookies.txt",
  "max_concurrent_downloads": 3,
  "enable_download_history": true,
  "auto_convert_to_mp4": true
}
```

---

## 使用示例

### 示例 1: 基本下载
```
用户: /youtube-download https://youtube.com/watch?v=xxxxx
助手:
  - 询问质量选项（选择：最高质量）
  - 询问是否下载字幕（选择：是）
  - 开始下载（策略1失败 -> 策略2成功）
  - 显示结果
```

### 示例 2: 批量下载
```
用户: /youtube-download 下载这个播放列表 <playlist_url>
助手:
  - 检测到播放列表
  - 显示播放列表信息（23个视频）
  - 询问是否全部下载
  - 并发下载（3个同时）
```

### 示例 3: 错误恢复
```
用户: /youtube-download <url>
助手:
  - 策略1失败（需要登录）
  - 策略2失败（cookies过期）
  - 策略3成功（从Chrome提取新cookies）
  - 自动保存新cookies供下次使用
```

---

## 开始执行

当用户触发此 Skill 时：

1. **立即获取 URL**（从参数或询问用户）
2. **询问下载选项**（质量、字幕、输出目录）
3. **检查环境**（yt-dlp、Python、FFmpeg）
4. **开始智能下载**（自动尝试多种策略）
5. **显示实时进度**
6. **验证和后处理**
7. **展示结果**

**核心价值**:
- 🎯 **智能重试**: 自动尝试多种方式，不需要用户干预
- 🍪 **Cookie 管理**: 智能处理 YouTube 的身份验证
- 📦 **开箱即用**: 一次配置，永久使用
- 🔄 **容错性强**: 遇到问题自动切换策略

让我们开始吧！
