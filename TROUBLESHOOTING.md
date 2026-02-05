# 故障排除指南

## 问题：所有下载策略都失败

### 症状
```
❌ 下载失败: 所有下载策略都失败了
ERROR: Sign in to confirm you're not a bot
```

### 原因
YouTube 需要身份验证，但无法获取有效的 cookies。

---

## 解决方案

### 方案 1: 手动导出 Cookies（最可靠）

#### 步骤：

1. **安装浏览器扩展**
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

2. **登录 YouTube**
   - 在浏览器中打开 youtube.com
   - 确保已登录你的 Google 账号

3. **导出 Cookies**
   - 点击扩展图标
   - 选择 "Export" 或 "Get cookies.txt"
   - 保存文件

4. **放置文件**
   ```bash
   # 将导出的 cookies.txt 复制到：
   .claude/skills/youtube-download/cookies.txt
   ```

5. **重新尝试下载**

---

### 方案 2: 关闭浏览器后自动提取

#### 问题
```
ERROR: Could not copy Chrome cookie database
```

这是因为 Chrome/Edge 正在运行，数据库被锁定。

#### 解决方案：

1. **完全关闭 Chrome/Edge**
   - Windows: 在任务管理器中结束所有 Chrome/Edge 进程
   - macOS: `Command + Q` 完全退出
   - Linux: `killall chrome` 或 `killall microsoft-edge`

2. **立即运行下载脚本**
   ```bash
   python scripts/download_video.py <url>
   ```

3. **脚本会自动从浏览器提取 cookies**

---

### 方案 3: 使用 yt-dlp 命令行直接提取

```bash
# 先关闭 Chrome
# 然后运行：
yt-dlp --cookies-from-browser chrome --cookies cookies.txt --skip-download <youtube_url>

# 生成的 cookies.txt 可以重复使用
```

---

### 方案 4: 尝试不同的浏览器

如果 Chrome 不行，尝试其他浏览器：

```bash
# Firefox (需要先关闭 Firefox)
python scripts/download_video.py <url>

# Edge (需要先关闭 Edge)
python scripts/download_video.py <url>

# Safari (macOS)
python scripts/download_video.py <url>
```

---

## 其他常见问题

### Q: Cookies 多久过期？

**A:** 通常 YouTube cookies 可以使用几周到几个月。当看到 "Sign in to confirm" 错误时，说明已过期。

### Q: 为什么不能一直使用同一个 cookies.txt？

**A:** YouTube 会定期轮换 cookies 作为安全措施。建议：
- 每月更新一次 cookies
- 或者在下载失败时更新

### Q: 可以用无痕模式的 cookies 吗？

**A:** 不可以。无痕模式的 cookies 在关闭窗口后就失效了。必须使用正常模式登录的 cookies。

### Q: 是否需要 YouTube Premium？

**A:** 不需要。普通的 Google 账号即可。但如果要下载 Premium 专属内容，则需要 Premium 账号的 cookies。

---

## 快速测试 Cookies 是否有效

```bash
# 测试命令
yt-dlp --cookies cookies.txt --skip-download --print "%(title)s" <youtube_url>

# 如果显示视频标题，说明 cookies 有效
# 如果提示 "Sign in to confirm"，说明 cookies 无效
```

---

## Windows 特殊说明

### Chrome 数据库锁定问题

Windows 上 Chrome 经常后台运行，即使关闭窗口。

**解决方法：**

1. **打开任务管理器** (`Ctrl + Shift + Esc`)
2. **查找所有 Chrome 进程**
   - Google Chrome
   - Google Chrome Helper
   - 后台进程
3. **全部结束进程**
4. **立即运行下载脚本**

或者使用命令行：
```bash
# PowerShell
Get-Process chrome | Stop-Process -Force

# 然后立即运行
python scripts/download_video.py <url>
```

---

## 推荐工作流

1. **首次使用：手动导出 cookies** (方案 1)
   - 最可靠
   - 可以随时导出
   - 不受浏览器运行状态影响

2. **日常使用：重复使用 cookies.txt**
   - cookies.txt 可以用很长时间
   - 只在失效时更新

3. **Cookies 失效：重新导出**
   - 看到 "Sign in to confirm" 错误时
   - 重复方案 1 的步骤

---

## 成功示例

```bash
$ python scripts/download_video.py "https://youtube.com/watch?v=xxxxx" 720p

============================================================
🎬 YouTube 视频智能下载
============================================================

尝试策略: cookies_file
------------------------------------------------------------
🎯 策略 2: 使用 Cookies 文件
   标题: 示例视频标题
   时长: 10:25

📥 开始下载...
   [███████████████████████████] 100.0% - 145.2 MB/145.2 MB - 5.2 MB/s

✅ 策略 cookies_file 成功！

============================================================
✅ 下载成功！
============================================================
```

---

## 需要更多帮助？

如果以上方案都不行，请检查：

1. **网络连接** - 确保能访问 youtube.com
2. **视频可用性** - 视频是否被删除或设为私有
3. **地区限制** - 视频是否在你的地区不可用
4. **yt-dlp 版本** - 更新到最新版 `pip install -U yt-dlp`

更多信息：
- [yt-dlp 官方文档](https://github.com/yt-dlp/yt-dlp)
- [YouTube Cookies 导出指南](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)
