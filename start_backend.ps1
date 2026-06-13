$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
Write-Host "Using Python: $venvPython"
& $venvPython -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
