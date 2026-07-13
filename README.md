# Slideshow Skill

把策展文案、项目图片和视觉参考整理成一份完整、统一的图文演示文稿。

它不是固定套用某一种内容框架：每个项目先根据文案建立叙事，再从页面组件中选择合适的图文关系。当前主交付是 **PDF**，同时保留结构化 brief 和 HTML 作为可修改的生成源。

![9 页示例缩略图](examples/example-contact-sheet.jpg)

## 五分钟开始

### 1. 下载并打开仓库

可以使用 Git：

```bash
git clone https://github.com/ArKurt/slideshow-skill.git
```

也可以在 GitHub 页面点击 **Code → Download ZIP**，解压后用 Codex 打开整个 `slideshow-skill` 文件夹。

仓库已经把 skill 放在 `.agents/skills/slideshow-skill/`。Codex 从仓库根目录启动时会自动发现它；如果没有立即出现，关闭并重新打开这个项目，或新建一个 Codex 会话。

### 2. 放入项目资料

在仓库根目录新建：

```text
inputs/项目名称/
```

建议放入：

- 客户确认过的文案，推荐 Markdown、Word 导出的文本或 TXT；
- 已筛选的 JPG、PNG、SVG 图片；
- 图片说明、来源和授权备注；
- 可选的参考 PDF；
- 对页数、语气、受众和交付时间的说明。

`inputs/` 已被 Git 忽略，不会因为普通提交意外上传到仓库。仍请只放入你有权处理的资料。

### 3. 在 Codex 中发出指令

第一版可以直接使用：

```text
使用 $slideshow-skill。
读取 inputs/项目名称 中的文案和图片，先根据内容设计一份策展演示文稿结构，
再生成统一的 HTML 和 PDF。每页只表达一个主要判断，完成后检查文字溢出、
字体替换、图片裁切和素材来源。把结果放到 outputs/项目名称/。
```

如果有视觉参考：

```text
使用 $slideshow-skill。
参考 inputs/项目名称/reference.pdf 的色彩、字体层级、留白和图文关系，
但不要照搬它的内容章节。根据本项目文案重新组织页面。
```

修改时尽量指出页码和保留项：

```text
继续使用 $slideshow-skill 修改第 4 页：保留图片和标题，正文缩短三分之一，
修正右侧文字溢出；其他页面不要改。重新导出 PDF。
```

### 4. 查看结果

通常会在 `outputs/项目名称/` 得到：

```text
brief.json       结构化内容与素材记录
deck.html        可在浏览器打开的生成稿
deck.pdf         供客户查看和交付的 PDF
```

`outputs/` 同样不进入 Git。

## 运行示例

如果想先确认本机环境，可以让 Codex 执行下面的示例，也可以自己运行。

Windows PowerShell：

```powershell
py .agents/skills/slideshow-skill/scripts/render_deck.py `
  .agents/skills/slideshow-skill/assets/example-brief.json `
  --output outputs/example/deck.html `
  --pdf outputs/example/deck.pdf `
  --preflight
```

macOS / Linux：

```bash
python .agents/skills/slideshow-skill/scripts/render_deck.py \
  .agents/skills/slideshow-skill/assets/example-brief.json \
  --output outputs/example/deck.html \
  --pdf outputs/example/deck.pdf \
  --preflight
```

示例结果也可以直接查看：[example-output.pdf](examples/example-output.pdf)。

## 环境要求

- Codex：用于读取资料、组织内容、编写 brief、调用 skill 和修订页面；
- Python 3.10 或更新版本：HTML renderer 只使用标准库，不需要 `pip install`；
- Edge、Chrome 或 Chromium：只在导出 PDF 和运行边界检查时需要；
- 推荐安装 Noto Serif CJK SC 与 Noto Sans CJK SC；缺少时系统会使用后备字体，版面可能变化。

如果不熟悉命令行，可以直接告诉 Codex：

```text
请先检查运行 slideshow-skill 所需的 Python、浏览器和字体；缺少时告诉我最简单的处理方法，然后运行示例。
```

## 这个 skill 会做什么

- 从文案推导页面顺序，而不是强套固定章节；
- 使用封面、中心宣言、章节页、大图文字页、对照页、卡片网格、时间线、素材清单和结尾页等组件；
- 把本地图片嵌入单文件 HTML，方便传阅；
- 保留图片来源、授权状态和人工审核记录；
- 在浏览器中检查页面边界，再导出 A4 横版 PDF；
- 支持根据新的参考 PDF 调整视觉语言。

## 当前边界

- PDF 是主交付，HTML 和 JSON brief 是生成源；
- 当前版本不生成 PPTX；如确有可编辑办公文稿需求，需要单独验证；
- 不会自动下载远程图片，也不会绕过登录、付费、验证码、DRM 或反爬措施；
- 参考 PDF 只用于提取视觉语言，除非明确要求，不复用其内容框架；
- 图片授权为 `unknown`、`rights_reserved` 或待审核时，不应直接用于外部发布。

## 常见问题

**Codex 没找到 `$slideshow-skill`**

确认打开的是仓库根目录，而不是其中某个文件；然后新建会话或重启 Codex。

**图片显示为占位框**

检查 `brief.json` 中的图片路径。相对路径以 brief 文件所在目录为基准。

**PDF 文字或边界有问题**

让 Codex 使用 `--preflight` 找出溢出页，并把 PDF 渲染成缩略图进行一次检查—修正—重导。字体不同也会改变换行。

**无法导出 PDF**

先打开生成的 HTML 确认内容；再检查 Edge、Chrome 或 Chromium 是否安装。HTML 生成不依赖浏览器。

## 仓库结构

```text
.agents/skills/slideshow-skill/
├── SKILL.md
├── agents/openai.yaml
├── scripts/render_deck.py
├── references/brief-schema.md
└── assets/
    ├── example-brief.json
    └── example-scene-*.svg

examples/     可公开示例
inputs/       本地项目提资，不进 Git
outputs/      本地生成物，不进 Git
```

这个仓库仍处于客户试用阶段。最有价值的反馈是：输入资料通常长什么样、哪类页面最常修改、PDF 是否满足沟通习惯，以及是否确实需要 PPTX。
