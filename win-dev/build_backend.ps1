# win_dev/build_backend.ps1

Write-Host "[INFO] Starting Backend Build Process..." -ForegroundColor Cyan

# 1. Define Relative Paths
$ScriptDir = $PSScriptRoot
$RootDir = Join-Path $ScriptDir ".."
$BackendDir = Join-Path $RootDir "backend"
$FrontendBinDir = Join-Path $RootDir "src-tauri\binaries"
$VenvPyInstaller = Join-Path $BackendDir "venv_win\Scripts\pyinstaller.exe"
$TargetTriple = "x86_64-pc-windows-msvc"

# 2. Locate PyInstaller (Auto-detect venv or global)
if (Test-Path $VenvPyInstaller) {
    Write-Host "[INFO] Using PyInstaller from venv_win..." -ForegroundColor Green
    $PyInstallerCmd = $VenvPyInstaller
}
elseif (Get-Command pyinstaller -ErrorAction SilentlyContinue) {
    Write-Host "[INFO] Using global PyInstaller..." -ForegroundColor Green
    $PyInstallerCmd = "pyinstaller"
}
else {
    Write-Error "[ERROR] PyInstaller not found! Please run: pip install pyinstaller"
    exit 1
}

# 3. Clean previous builds
Write-Host "[INFO] Cleaning old builds..." -ForegroundColor Yellow
if (Test-Path "$BackendDir\dist") { Remove-Item -Recurse -Force "$BackendDir\dist" }
if (Test-Path "$BackendDir\build") { Remove-Item -Recurse -Force "$BackendDir\build" }

# 4. Run PyInstaller
Write-Host "[INFO] Building Python Backend..." -ForegroundColor Green
Push-Location $BackendDir

# Find the CrewAI package location inside the venv
$CrewAIPath = Join-Path $ScriptDir "..\backend\venv_win\Lib\site-packages\crewai"

# Execute via the detected command path using '&' operator
# FIX: Added --add-data to include the missing 'translations' folder from CrewAI
$LiteLLMPath = Join-Path $BackendDir "venv_win\Lib\site-packages\litellm"

& $PyInstallerCmd --name newsletter-backend --onefile app/main.py --clean --log-level WARN `
    --hidden-import="passlib.handlers.pbkdf2" `
    --hidden-import="passlib.handlers.bcrypt" `
    --collect-all="litellm" `
    --add-data "$LiteLLMPath\litellm_core_utils\tokenizers;litellm\litellm_core_utils\tokenizers" `
    --hidden-import="tiktoken_ext.openai_public" `
    --collect-all="tiktoken" `
    --add-data "$CrewAIPath\translations;crewai\translations"

if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] PyInstaller failed!"
    Pop-Location
    exit 1
}
Pop-Location

# 5. Create Tauri binaries folder if it doesn't exist
if (-not (Test-Path $FrontendBinDir)) {
    Write-Host "[INFO] Creating binaries folder..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $FrontendBinDir | Out-Null
}

# 6. Move and Rename the Executable
$SourceExe = Join-Path $BackendDir "dist\newsletter-backend.exe"
$DestExe = Join-Path $FrontendBinDir "newsletter-backend-$TargetTriple.exe"

if (Test-Path $SourceExe) {
    Write-Host "[INFO] Moving binary to Tauri folder..." -ForegroundColor Green
    Copy-Item -Path $SourceExe -Destination $DestExe -Force
    Write-Host "[SUCCESS] Backend built and moved to:" -ForegroundColor Cyan
    Write-Host "   $DestExe"
}
else {
    Write-Error "[ERROR] Build artifact not found at $SourceExe"
    exit 1
}