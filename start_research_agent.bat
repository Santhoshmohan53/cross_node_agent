@echo off
TITLE Multimodal Deep Research Agent - Local Web UI
cd /d "%~dp0"

echo ===============================================================================
echo          MULTIMODAL DEEP RESEARCH AGENT ^& OPEN WEBUI LAUNCHER
echo ===============================================================================
echo.

REM 1. Verify Ollama is running
echo [1/3] Checking Ollama Local Model Engine...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Ollama server in background...
    start "" /b "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Ollama server is running!
)

REM 2. Verify Models
echo.
echo [2/3] Verifying Models (qwen2.5-vl:7b ^& deepseek-r1:7b)...
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" list

REM 3. Start Open WebUI
echo.
echo [3/3] Launching Open WebUI on http://localhost:8080 ...
echo.
echo ===============================================================================
echo   Workspace URL: http://localhost:8080
echo   Models Loaded: qwen2.5-vl:7b (Multimodal/Vision), deepseek-r1:7b (Reasoning)
echo   Research Pipe: Autonomous Multi-Agent Loop (Planner + Scraper + Synthesizer)
echo ===============================================================================
echo.

if exist ".venv_research\Scripts\activate.bat" (
    call .venv_research\Scripts\activate.bat
    start http://localhost:8080
    open-webui serve --port 8080
) else (
    python -m open_webui serve --port 8080
)

pause
