# PowerShell Startup Script for Open WebUI + Deep Research Engine
$ErrorActionPreference = "Continue"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "      OPEN WEBUI + AUTONOMOUS MULTI-AGENT DEEP RESEARCH WORKSPACE" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan

# 1. Check / Start Ollama
Write-Host "`n[1/3] Checking Local Ollama Engine (port 11434)..." -ForegroundColor Yellow
$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaPath)) {
    $ollamaPath = (Get-Command ollama -ErrorAction SilentlyContinue).Source
}

try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Ollama is active and listening!" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Ollama in background..." -ForegroundColor Yellow
    if ($ollamaPath -and (Test-Path $ollamaPath)) {
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    } else {
        Write-Warning "Ollama executable not found in default paths."
    }
}

# 2. Check / Start Research Microservice (port 8001)
Write-Host "`n[2/3] Checking Autonomous Deep Research Microservice (port 8001)..." -ForegroundColor Yellow
$pyPath = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $pyPath)) { $pyPath = "python" }
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverScript = Join-Path $scriptDir "src\research_pipeline\research_server.py"

try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Research Microservice is active and listening on port 8001!" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Research Microservice daemon on port 8001..." -ForegroundColor Yellow
    Start-Process -FilePath $pyPath -ArgumentList $serverScript -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 3. Start Open WebUI (port 3000)
Write-Host "`n[3/3] Checking Open WebUI Workspace on http://localhost:3000 ..." -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "   - Open WebUI URL:      http://localhost:3000" -ForegroundColor Green
Write-Host "   - Active Model:        autonomous-deep-research (Multi-Agent Planner+Scraper)" -ForegroundColor White
Write-Host "   - Vision Model:        llava:7b (Multimodal Diagrams & OCR)" -ForegroundColor White
Write-Host "   - Features:            Edit Prompts, Multi-turn Corrections, Flawless Scrolling," -ForegroundColor White
Write-Host "                          Clickable Citations, Side-by-Side Notes Workspace" -ForegroundColor White
Write-Host "===============================================================================`n" -ForegroundColor Cyan

$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OPENAI_API_BASE_URL = "http://127.0.0.1:8001/v1"
$env:OPENAI_API_BASE_URLS = "http://127.0.0.1:8001/v1"
$env:OPENAI_API_KEY = "local"
$env:OPENAI_API_KEYS = "local"
$env:ENABLE_OPENAI_API = "true"

try {
    $null = Invoke-RestMethod -Uri "http://localhosb t:3000" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Open WebUI is already running!" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Open WebUI server on port 3000..." -ForegroundColor Yellow
    $webuiPath = "C:\Users\user\AppData\Local\Programs\Python\Python312\Scripts\open-webui.exe"
    if (Test-Path $webuiPath) {
        Start-Process -FilePath $webuiPath -ArgumentList "serve --port 3000" -WindowStyle Normal
    } else {
        open-webui serve --port 3000
    }
}

Start-Process "http://localhost:3000"
