@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

if not exist ".venv\Scripts\uvicorn.exe" (
  .\.venv\Scripts\pip install -r requirements.txt
)

if "%OLLAMA_BASE_URL%"=="" set OLLAMA_BASE_URL=http://127.0.0.1:11434
if "%COACH_OLLAMA_MODEL%"=="" set COACH_OLLAMA_MODEL=qwen3:8b

echo Starting coach_node with auto reload...
echo OLLAMA_BASE_URL=%OLLAMA_BASE_URL%
echo COACH_OLLAMA_MODEL=%COACH_OLLAMA_MODEL%

.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
