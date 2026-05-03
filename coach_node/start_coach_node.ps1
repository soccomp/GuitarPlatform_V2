$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

if (-not (Test-Path ".venv\Scripts\uvicorn.exe")) {
  .\.venv\Scripts\pip install -r requirements.txt
}

if (-not $env:OLLAMA_BASE_URL) {
  $env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
}

if (-not $env:COACH_OLLAMA_MODEL) {
  $env:COACH_OLLAMA_MODEL = "qwen3:8b"
}

Write-Host "Starting coach_node with auto reload..." -ForegroundColor Cyan
Write-Host "OLLAMA_BASE_URL=$env:OLLAMA_BASE_URL" -ForegroundColor DarkGray
Write-Host "COACH_OLLAMA_MODEL=$env:COACH_OLLAMA_MODEL" -ForegroundColor DarkGray

.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
