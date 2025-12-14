# start_dev.ps1

Write-Host "Starting Development Environment..." -ForegroundColor Green

# --- Configuration ---
$BackendPath = "/mnt/c/Dev/NewsLetter/backend"  # Path inside WSL
$FrontendPath = "C:\Dev\NewsLetter\frontend"    # Path in Windows
$WslDistro = "Ubuntu"                           # Change if using 'Ubuntu-20.04' etc.

# --- 1. Start Backend (WSL) ---
Write-Host "Launching Backend (FastAPI) in WSL..." -ForegroundColor Cyan
# This command: 1. Enters WSL -> 2. Goes to folder -> 3. Activates venv -> 4. Runs Server
$BackendCommand = "wsl -d $WslDistro bash -c 'cd $BackendPath && source ~/.virtualenvs/backend/bin/activate && uvicorn app.main:app --reload'"

# Open in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$BackendCommand"

# --- 2. Start Frontend (Windows) ---
Write-Host "Launching Frontend (React) in Windows..." -ForegroundColor Magenta

if (Test-Path $FrontendPath) {
    # Open in a new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $FrontendPath; npm run dev"
} else {
    Write-Warning "Frontend folder not found at: $FrontendPath"
    Write-Warning "Please check the path variable at the top of this script."
}

Write-Host "Done! Servers are spinning up." -ForegroundColor Green
Write-Host "Reminder: Please fix the Qdrant DB issue as planned." -ForegroundColor Yellow