# Set Environment Variables for Backend
$env:PYTHONIOENCODING = "utf-8"

#Start BackendServer (Tauri manages frontend via beforeDevCommand)

#==================

#Start BackendServer
Start-Process powershell `
  -ArgumentList "-NoExit", "-Command", "cd C:\Dev\NewsLetter; & '.\frontend\node_modules\.bin\tauri' dev"
