param(
    [string]$UpxDir = ""
)

$ErrorActionPreference = "Stop"

function Get-TomlValue {
    param(
        [Parameter(Mandatory = $true)][string]$TomlPath,
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $lines = Get-Content -Path $TomlPath
    $inTargetSection = $false

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^\[(.+)\]$') {
            $inTargetSection = ($matches[1] -eq $Section)
            continue
        }
        if (-not $inTargetSection) {
            continue
        }
        if ($trimmed -match ('^{0}\s*=\s*"(.*)"$' -f [Regex]::Escape($Key))) {
            return $matches[1]
        }
    }

    throw "Key not found in [$Section]: $Key"
}

# NOTE: 构建配置统一从 pyproject.toml 读取，避免版本号与命名规则多处维护
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyprojectPath = Join-Path $projectRoot "pyproject.toml"
$section = "tool.windows_update_manager"

$versionId = Get-TomlValue -TomlPath $pyprojectPath -Section $section -Key "version-id"
$nameTemplate = Get-TomlValue -TomlPath $pyprojectPath -Section $section -Key "exe-name-template"
$entryScript = Get-TomlValue -TomlPath $pyprojectPath -Section $section -Key "entry-script"
$iconPath = Get-TomlValue -TomlPath $pyprojectPath -Section $section -Key "icon-path"

$exeName = $nameTemplate.Replace("<VersionID>", $versionId)
if ($exeName.ToLower().EndsWith(".exe")) {
    $exeName = $exeName.Substring(0, $exeName.Length - 4)
}

$entryAbs = Join-Path $projectRoot $entryScript
$iconAbs = Join-Path $projectRoot $iconPath

if (-not (Test-Path -Path $entryAbs)) {
    throw "Entry script not found: $entryAbs"
}
if (-not (Test-Path -Path $iconAbs)) {
    throw "Icon file not found: $iconAbs"
}

Write-Host "Build started..."
Write-Host "Version ID: $versionId"
Write-Host "Target EXE: $exeName.exe"
Write-Host "Entry script: $entryScript"
Write-Host "Icon file: $iconPath"
if ([string]::IsNullOrWhiteSpace($UpxDir)) {
    Write-Host "UPX dir: not provided (UPX compression disabled)"
}
else {
    if (-not (Test-Path -Path $UpxDir)) {
        throw "UPX dir not found: $UpxDir"
    }
    Write-Host "UPX dir: $UpxDir"
}

Push-Location $projectRoot
try {
    # NOTE: 忽略外部激活虚拟环境，避免 uv 提示环境不匹配并干扰项目环境解析
    $oldVirtualEnv = $env:VIRTUAL_ENV
    if ($env:VIRTUAL_ENV) {
        Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
    }

    $pyiArgs = @(
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--icon", $iconPath,
        "-n", $exeName
    )
    if (-not [string]::IsNullOrWhiteSpace($UpxDir)) {
        $pyiArgs += @("--upx-dir", $UpxDir)
    }
    # NOTE: 传入入口文件绝对路径，避免不同 Shell/工作目录下的路径规范化问题
    $pyiArgs += $entryAbs
    uv run -- python -m PyInstaller @pyiArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed: uv run python -m PyInstaller exited with code $LASTEXITCODE"
    }

    if ($oldVirtualEnv) {
        $env:VIRTUAL_ENV = $oldVirtualEnv
    }
}
finally {
    if ($oldVirtualEnv) {
        $env:VIRTUAL_ENV = $oldVirtualEnv
    }
    Pop-Location
}

Write-Host "Build completed: dist\$exeName.exe"
