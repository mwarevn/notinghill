# NotingHill - run_app.ps1
# Production mode: builds frontend into backend/static, then serves via FastAPI
# Usage: .\run_app.ps1

$ErrorActionPreference = "Stop"

$ROOT     = $PSScriptRoot
$BACKEND  = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$VENV     = Join-Path $ROOT ".venv"
$PYTHON   = if ($env:PYTHON) { $env:PYTHON } else { "python" }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "             N O T I N G H I L L          " -ForegroundColor Cyan
Write-Host "             Production Mode              " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# venv
$venvPython = Join-Path $VENV "Scripts\python.exe"
$venvPip    = Join-Path $VENV "Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[1/4] Creating venv..." -ForegroundColor Yellow
    & $PYTHON -m venv $VENV
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

$VENV_PYTHON = $venvPython
$VENV_PIP    = $venvPip

# pip install
Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Yellow
& $VENV_PIP install -r (Join-Path $BACKEND "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed." -ForegroundColor Red
    exit 1
}

# Build frontend
Write-Host "[3/4] Building React frontend..." -ForegroundColor Yellow
Push-Location $FRONTEND
try {
    if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
        npm install --silent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: npm install failed." -ForegroundColor Red
            exit 1
        }
    }

    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed." -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

Write-Host "      Frontend built -> backend/static OK" -ForegroundColor Green

# Start backend
Write-Host "[4/4] Starting NotingHill..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  App   -> http://127.0.0.1:7878" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

Set-Location $BACKEND
& $VENV_PYTHON main.py