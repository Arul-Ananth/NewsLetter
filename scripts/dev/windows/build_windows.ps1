# AeroBrief Build Script for Windows
Write-Host "Starting Build Process..."

# Activate Venv
$d = ".\venv_win\Scripts\activate.ps1"
if (Test-Path $d) {
    . $d
}
else {
    Write-Host "Error: venv_win not found."
    exit 1
}

# Run PyInstaller
# We need to handle hidden imports for dynamic libraries like CrewAI and Qdrant
# --collect-all might be needed for some packages, but start with --hidden-import
$imports = "--hidden-import=crewai --hidden-import=qdrant_client --hidden-import=keyring --hidden-import=PySide6 --hidden-import=litellm"
$paths = "--paths=core --paths=desktop"

Write-Host "Running PyInstaller..."
pyinstaller --noconfirm --onedir --windowed --name "AeroBrief" $imports $paths desktop/main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build Successful! Executable in dist\AeroBrief\AeroBrief.exe"
}
else {
    Write-Host "Build Failed."
    exit $LASTEXITCODE
}
