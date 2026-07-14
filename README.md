# AI 演示文稿 · Windows 客户版

这个项目可以把文案和图片整理成一份统一风格的演示文稿。

你不需要学习代码。把下面这段话发给这台电脑上的 Codex，它会检查环境、安装制作规则，并带你完成公开示例。

```text
请帮我在这台 Windows 电脑上安装并测试下面这个项目：
https://github.com/ArKurt/slideshow-skill/tree/client-windows

请先阅读 README.md 和 AGENTS.md。使用 client-windows 分支，只从 Open Design 官方发布页
下载 Windows x64 版本。先运行 windows-check.ps1 检查电脑；安装或修改系统设置前先征得我同意。
然后把 .agents\skills\slideshow-skill 安装到 Open Design，用项目自带的公开示例生成一份
deck.html 和 deck.pdf，打开预览，并用简单中文告诉我以后怎样提供文案和图片。
```

## 第一次安装时，你需要做什么

Codex 会处理大部分步骤。你通常只需要：

1. 同意从 [Open Design 官方发布页](https://github.com/nexu-io/open-design/releases/tag/open-design-v0.14.1) 下载 Windows 安装包；
2. 完成 Open Design 安装；
3. 第一次打开时，选择使用这台电脑上的 Codex；
4. 按 Codex 的引导，在 Open Design 中选择“插件 → 导入 → 上传文件夹”，选中 `.agents\skills\slideshow-skill`；
5. 查看公开示例，确认翻页、编辑和 PDF 都能打开。

本次固定使用的安装包是：

```text
open-design-0.14.1-win-x64-setup.exe
SHA-256: 18d7f5243bbacc48db9ff13ea1298feb15142ee55c6296df555a036b7b8c2ec2
```

这个校验值由本项目从上述官方发布文件记录。Windows 可能提示“已保护你的电脑”或“未知发布者”。先让 Codex 核对下载地址和文件校验值；两者都正确后，再决定是否点击“更多信息 → 仍要运行”。

## 以后怎样制作演示文稿

文案和图片不必放进固定文件夹。你可以直接粘贴文字、发送文件，或告诉 Codex 文件在哪里。

可以这样开始：

```text
使用 slideshow-skill，根据我刚才提供的文案和图片制作一份演示文稿。
先按内容安排页面，再生成可预览的 HTML 和正式 PDF。
如果没有新的风格参考，使用默认的暖色编辑风格。
完成后检查文字边界、字体、图片裁切和图片来源，并告诉我先看哪几页。
```

修改时尽量说清页码和保留内容：

```text
只修改第 4 页：保留标题和图片，把正文缩短三分之一。其他页面不要改。
重新生成一个新版本，不要覆盖我已经手工修改的版本。
```

## 会得到哪些文件

```text
deck.html    可以预览和继续修改的演示文稿
deck.pdf     发给客户查看的正式 PDF
brief.json   本次文案、页面和图片记录
```

正式查看请以 `deck.pdf` 为准。如果 Open Design 里打开 PDF 时只看到文字，请下载后用电脑的 PDF 阅读器打开。顶部“导出 PDF”若进入系统打印窗口，可能出现版面变化；已有 `deck.pdf` 时不必再打印一次。

## 默认风格

没有提供新参考时，会使用当前内置的暖色编辑风格：暖白纸色、深色文字、少量酒红和黄铜色、较多留白，以及清楚的图文关系。

如果你提供新的参考，只借鉴它的色彩、字体层次、留白和图片安排；每次演示文稿的内容顺序仍根据本次文案决定。

## 文件与隐私

- 只使用你提供或确认可以使用的图片；
- 客户文案、原图和生成结果不要上传到公开仓库；
- `inputs` 和 `outputs` 文件夹不会被 Git 提交；
- 不要把账号、密码、浏览器资料或登录信息放进项目目录。

公开示例：[PDF](examples/example-output.pdf) · [九页缩略图](examples/example-contact-sheet.jpg)
