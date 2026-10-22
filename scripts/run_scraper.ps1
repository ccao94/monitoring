# One scraping cycle, run by the Windows scheduled task
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force logs | Out-Null
"--- $(Get-Date -Format s) ---" | Out-File -Append logs\scraper.log
& .\venv\Scripts\python.exe main.py *>> logs\scraper.log