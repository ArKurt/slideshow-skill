[CmdletBinding()]
param(
    [switch]$PrepareExample,
    [string]$InstallerPath
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillRoot = Join-Path $RepoRoot ".agents\skills\slideshow-skill"
$Renderer = Join-Path $SkillRoot "scripts\render_deck.py"
$ExampleBrief = Join-Path $SkillRoot "assets\example-brief.json"
$OpenDesignVersion = "0.14.1"
$OpenDesignUrl = "https://github.com/nexu-io/open-design/releases/tag/open-design-v0.14.1"
$OpenDesignInstallerSha256 = "18d7f5243bbacc48db9ff13ea1298feb15142ee55c6296df555a036b7b8c2ec2"

$Problems = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

function Show-Result {
    param([string]$Label, [bool]$Ok, [string]$Detail)
    $Mark = if ($Ok) { "[OK]" } else { "[--]" }
    Write-Host ("{0} {1}: {2}" -f $Mark, $Label, $Detail)
}

function Find-Python {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        return @{ Exe = $PyLauncher.Source; Prefix = @("-3") }
    }
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $Python) {
        return @{ Exe = $Python.Source; Prefix = @() }
    }
    return $null
}

function Run-Python {
    param(
        [hashtable]$PythonCommand,
        [string[]]$Arguments
    )
    $AllArguments = @($PythonCommand.Prefix) + $Arguments
    & $PythonCommand.Exe @AllArguments
}

function Join-OptionalPath {
    param([string]$Root, [string]$Child)
    if ([string]::IsNullOrWhiteSpace($Root)) { return $null }
    return Join-Path $Root $Child
}

function Find-Browser {
    $Candidates = @(
        (Join-OptionalPath ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
        (Join-OptionalPath $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
        (Join-OptionalPath ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
        (Join-OptionalPath $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
        (Join-OptionalPath $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
    )
    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            return $Candidate
        }
    }
    return $null
}

function Find-OpenDesign {
    $Candidates = @(
        (Join-OptionalPath $env:LOCALAPPDATA "Programs\Open Design\Open Design.exe"),
        (Join-OptionalPath $env:ProgramFiles "Open Design\Open Design.exe"),
        (Join-OptionalPath ${env:ProgramFiles(x86)} "Open Design\Open Design.exe")
    )
    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            return $Candidate
        }
    }
    return $null
}

Write-Host ""
Write-Host "Slideshow Skill - Windows check"
Write-Host "================================"

$RunningOnWindows = $env:OS -eq "Windows_NT"
Show-Result "Windows" $RunningOnWindows $(if ($RunningOnWindows) { [Environment]::OSVersion.VersionString } else { "not Windows" })
if (-not $RunningOnWindows) { $Problems.Add("Run this branch in native Windows.") }

$Architecture = $env:PROCESSOR_ARCHITEW6432
if (-not $Architecture) { $Architecture = $env:PROCESSOR_ARCHITECTURE }
$IsX64 = $Architecture -eq "AMD64"
Show-Result "Architecture" $IsX64 $Architecture
if (-not $IsX64) { $Problems.Add("The pinned Open Design installer requires Windows x64.") }

$Codex = Get-Command codex -ErrorAction SilentlyContinue
Show-Result "Codex" ($null -ne $Codex) $(if ($null -ne $Codex) { $Codex.Source } else { "codex command not found" })
if ($null -eq $Codex) { $Problems.Add("Install and sign in to native Windows Codex CLI.") }

$PythonOk = $false
$PythonCommand = Find-Python
if ($null -ne $PythonCommand) {
    $PythonVersion = (Run-Python $PythonCommand @("--version") 2>&1 | Out-String).Trim()
    if ($PythonVersion -match "Python\s+(\d+)\.(\d+)") {
        $PythonMajor = [int]$Matches[1]
        $PythonMinor = [int]$Matches[2]
        $PythonOk = ($PythonMajor -gt 3) -or (($PythonMajor -eq 3) -and ($PythonMinor -ge 10))
    }
    Show-Result "Python" $PythonOk $PythonVersion
    if (-not $PythonOk) { $Problems.Add("Python 3.10 or newer is required.") }
} else {
    Show-Result "Python" $false "Python 3 not found"
    $Problems.Add("Python 3.10 or newer is required.")
}

$Browser = Find-Browser
Show-Result "PDF browser" ($null -ne $Browser) $(if ($null -ne $Browser) { $Browser } else { "Edge or Chrome not found" })
if ($null -eq $Browser) { $Problems.Add("Edge or Chrome is required to render the final PDF.") }

$OpenDesign = Find-OpenDesign
if ($null -ne $OpenDesign) {
    $InstalledOpenDesignVersion = (Get-Item -LiteralPath $OpenDesign).VersionInfo.ProductVersion
    $OpenDesignVersionOk = $InstalledOpenDesignVersion -like "$OpenDesignVersion*"
    Show-Result "Open Design" $OpenDesignVersionOk "$InstalledOpenDesignVersion - $OpenDesign"
    if (-not $OpenDesignVersionOk) { $Problems.Add("Use the pinned Open Design $OpenDesignVersion build for this pilot.") }
} else {
    Show-Result "Open Design" $false "not installed; pinned version $OpenDesignVersion"
    $Problems.Add("Install Open Design $OpenDesignVersion for Windows x64.")
}

$SkillReady = (Test-Path -LiteralPath (Join-Path $SkillRoot "SKILL.md") -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $SkillRoot "open-design.json") -PathType Leaf) -and
    (Test-Path -LiteralPath $Renderer -PathType Leaf) -and
    (Test-Path -LiteralPath $ExampleBrief -PathType Leaf)
Show-Result "Skill files" $SkillReady $(if ($SkillReady) { $SkillRoot } else { "required files are missing" })
if (-not $SkillReady) { $Problems.Add("Get a fresh copy of the client-windows branch.") }

if ($InstallerPath) {
    if (Test-Path -LiteralPath $InstallerPath -PathType Leaf) {
        $ActualHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $HashOk = $ActualHash -eq $OpenDesignInstallerSha256
        Show-Result "Installer hash" $HashOk $ActualHash
        if (-not $HashOk) { $Problems.Add("Installer hash mismatch. Do not run this file.") }
    } else {
        Show-Result "Installer hash" $false "file not found: $InstallerPath"
        $Problems.Add("The selected Open Design installer does not exist.")
    }
}

if ($PrepareExample) {
    Write-Host ""
    Write-Host "Preparing public example"
    Write-Host "------------------------"
    if (($null -eq $PythonCommand) -or (-not $PythonOk) -or (-not $SkillReady)) {
        $Problems.Add("The public example cannot run until Python and the skill files are ready.")
    } else {
        $OutputDir = Join-Path $RepoRoot "outputs\windows-check"
        New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
        $HtmlPath = Join-Path $OutputDir "deck.html"
        $PdfPath = Join-Path $OutputDir "deck.pdf"
        $RenderArguments = @($Renderer, $ExampleBrief, "--output", $HtmlPath)
        if ($null -ne $Browser) {
            $RenderArguments += @("--pdf", $PdfPath, "--preflight", "--strict")
        }
        Run-Python $PythonCommand $RenderArguments
        if ($LASTEXITCODE -ne 0) {
            $Problems.Add("Public example failed. Keep the complete error above.")
        } else {
            Show-Result "Example HTML" (Test-Path -LiteralPath $HtmlPath) $HtmlPath
            if ($null -ne $Browser) {
                Show-Result "Example PDF" (Test-Path -LiteralPath $PdfPath) $PdfPath
            }
        }
    }
}

Write-Host ""
Write-Host "Official Open Design release: $OpenDesignUrl"
Write-Host ""

if ($Warnings.Count -gt 0) {
    Write-Host "Warnings:"
    foreach ($Warning in $Warnings) { Write-Host "- $Warning" }
    Write-Host ""
}

if ($Problems.Count -gt 0) {
    Write-Host "Action needed:"
    foreach ($Problem in $Problems) { Write-Host "- $Problem" }
    exit 1
}

Write-Host "Check passed. Install .agents\skills\slideshow-skill in Open Design."
exit 0
