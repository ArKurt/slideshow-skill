# Windows 客户部署说明

本分支只用于在客户的 Windows x64 电脑上部署 `slideshow-skill` 与 Open Design 桌面版。

## 给 Codex 的执行规则

1. 如果本分支尚未在本机，优先克隆到用户的 `Documents\slideshow-skill`：

   ```powershell
   git clone --branch client-windows --single-branch --depth 1 `
     https://github.com/ArKurt/slideshow-skill.git `
     "$HOME\Documents\slideshow-skill"
   ```

   如果没有 Git，可以从
   `https://github.com/ArKurt/slideshow-skill/archive/refs/heads/client-windows.zip` 下载并解压。
   不要把项目或运行输出放在 `C:\` 根目录。
2. 先读根目录 `README.md`，再运行 `windows-check.ps1`。脚本只检查环境；除非用户明确加上
   `-PrepareExample`，不要生成示例。
3. Open Design 使用官方 Windows x64 桌面安装包。当前固定版本为 `0.14.1`。只允许从
   `https://github.com/nexu-io/open-design/releases/tag/open-design-v0.14.1` 下载，不从镜像、网盘或
   第三方页面下载，不把安装包提交进本仓库。
4. 安装软件、改变 PowerShell 设置、修改 PATH 或处理 SmartScreen 提示前，先向用户说明并取得
   同意。若用户提供了已下载的安装包，用 `windows-check.ps1 -InstallerPath <path>` 核对 SHA-256。
5. 使用 Windows 原生 Open Design 与 Windows 原生 Codex。不要改用 WSL，不要克隆或编译 Open
   Design 源码，不要求安装 Node、pnpm、VS Code 或 Visual Studio Build Tools。
6. 将 `.agents\skills\slideshow-skill` 作为本地插件安装。首选界面中的
   `插件 → 导入 → 上传文件夹`；若使用 Open Design CLI，则运行
   `od plugin install .\.agents\skills\slideshow-skill`。若界面找不到 Codex，先确认
   `codex --version` 和登录状态，再在 Open Design 设置中重新检查。
7. 第一次只用 skill 自带的公开 brief 与 SVG 生成示例。确认九页预览、翻页、编辑保存和 renderer
   生成的 `deck.pdf`，再接触客户资料。
8. Open Design 顶部 PDF 导出与系统打印只算备用路径。正式 PDF 使用
   `scripts\render_deck.py` 生成的 `deck.pdf`。OD 文件页若只显示文字，下载实际 PDF 再检查。
9. 不修改 Open Design 安装目录或源码。遇到失败，记录版本、完整提示和发生步骤，不用临时补丁
   掩盖问题。

## 内容与隐私

- `inputs\` 只放客户本地资料，`outputs\` 只放生成结果；两者都不得提交或上传。
- 只使用公开素材或用户明确提供的素材，保留来源、授权状态和人工审核记录。
- 不保存账号、密码、token、cookie、浏览器 profile 或其他登录资料。
- PDF 是主要交付；HTML 与 JSON brief 是可修改的生成源；当前不生成 PPTX 真源。
- 修改已人工精修的 deck 时，只改用户指定页面，或另存新版本；不要静默整稿重生成。

## 验证命令

在 Windows PowerShell 中：

```powershell
.\windows-check.ps1
.\windows-check.ps1 -PrepareExample
```

skill 结构校验和 Open Design 插件安装由 Codex 完成。完成时用简单中文报告：Open Design 版本、
Codex 是否识别、示例 HTML/PDF 路径、九页是否正常，以及仍未通过的功能。
