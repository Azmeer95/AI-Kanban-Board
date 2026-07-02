$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv")) {
  py -m venv .venv
}

. ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
python -m pip install -r backend/requirements.txt | Out-Null

if (-not (Test-Path "frontend/node_modules")) {
  npm --prefix frontend install | Out-Null
}

npm --prefix frontend run build | Out-Null

Start-Process -FilePath python -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $root -PassThru | Out-Null
Write-Host "Backend started on http://localhost:8000"
