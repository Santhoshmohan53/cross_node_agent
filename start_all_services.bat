@echo off
TITLE Open WebUI + Autonomous Deep Research Workspace
cd /d "%~dp0"

echo ===============================================================================
echo        OPEN WEBUI + AUTONOMOUS MULTI-AGENT DEEP RESEARCH WORKSPACE
echo ===============================================================================
echo.

REM 1. Verify Ollama Engine
echo [1/3] Checking Local Ollama Model Engine (port 11434)...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Ollama server in background...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start /min "Ollama-Service" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start /min "Ollama-Service" ollama serve
    )
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Ollama is active and listening!
)

REM 2. Verify Research Microservice
echo.
echo [2/3] Checking Autonomous Deep Research Microservice (port 8001)...
curl -s http://127.0.0.1:8001/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Research Microservice daemon on port 8001...
    start /min "Research-Server" "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" "src\research_pipeline\research_server.py"
    timeout /t 2 /nobreak >nul
) else (
    echo [OK] Research Microservice is active and listening!
)

REM 3. Start Open WebUI
echo.
echo [3/3] Starting Open WebUI Workspace (port 3000)...
echo.
echo ===============================================================================
echo   - Open WebUI URL:      http://localhost:3000
echo   - Active Model:        autonomous-deep-research (Multi-Agent Planner+Scraper)
echo   - Vision Model:        llava:7b (Multimodal Diagrams & OCR)
echo   - Features:            Edit Prompts, Multi-turn Corrections, Flawless Scrolling,
echo                          Clickable Citations, Side-by-Side Notes Workspace
echo ===============================================================================
echo.

set OLLAMA_BASE_URL=http://127.0.0.1:11434
set OPENAI_API_BASE_URL=http://127.0.0.1:8001/v1
set OPENAI_API_BASE_URLS=http://127.0.0.1:8001/v1
set OPENAI_API_KEY=local
set OPENAI_API_KEYS=local
set ENABLE_OPENAI_API=true

start http://localhost:3000

curl -s http://localhost:3000 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    "C:\Users\user\AppData\Local\Programs\Python\Python312\Scripts\open-webui.exe" serve --port 3000
) else (
    echo [OK] Open WebUI is already running and serving http://localhost:3000!
    pause
)
