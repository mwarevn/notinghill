# NotingHill — build_exe.ps1
# Full build pipeline -> produces standalone exe (Windows) or .app (macOS)
#
# Requirements:
#   - Python 3.11+
#   - Node.js 18+
#   - npm
#   - PyInstaller (installed automatically into venv)
#
# Usage (Windows PowerShell):
#   .\build_exe.ps1
#
# Output:
#   Windows -> backend\dist\NotingHill\notinghill.exe
#   macOS   -> backend\dist\NotingHill.app

$ErrorActionPreference = "Stop"

$ROOT     = $PSScriptRoot
$BACKEND  = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$VENV     = Join-Path $ROOT ".venv"
$BUILD    = Join-Path $BACKEND "build"
$DIST     = Join-Path $BACKEND "dist"
$PYTHON   = if ($env:PYTHON) { $env:PYTHON } else { "python" }

# Detect platform
$IS_WINDOWS = $IsWindows -or ($env:OS -eq "Windows_NT")

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "               N O T I N G H I L L               " -ForegroundColor Cyan
Write-Host "                 Build Pipeline                  " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# Step 1: Python venv
Write-Host "[1/6] Python virtual environment" -ForegroundColor DarkCyan

$venvPythonWin = Join-Path $VENV "Scripts\python.exe"
$venvPythonMac = Join-Path $VENV "bin/python"

if (-not (Test-Path $venvPythonWin) -and -not (Test-Path $venvPythonMac)) {
    Write-Host "  Creating .venv..." -ForegroundColor Yellow
    & $PYTHON -m venv $VENV
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Cannot create venv. Is Python 3.11+ installed?" -ForegroundColor Red
        exit 1
    }
}

if ($IS_WINDOWS) {
    $VENV_PYTHON = Join-Path $VENV "Scripts\python.exe"
    $VENV_PIP    = Join-Path $VENV "Scripts\pip.exe"
} else {
    $VENV_PYTHON = Join-Path $VENV "bin/python"
    $VENV_PIP    = Join-Path $VENV "bin/pip"
}

Write-Host "  OK venv ready: $VENV_PYTHON" -ForegroundColor Green

# Step 2: Install Python deps + PyInstaller
Write-Host ""
Write-Host "[2/6] Installing Python dependencies" -ForegroundColor DarkCyan

Write-Host "  Installing requirements.txt..." -ForegroundColor Yellow
& $VENV_PIP install -r (Join-Path $BACKEND "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: pip install failed." -ForegroundColor Red
    exit 1
}

Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
& $VENV_PIP install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: PyInstaller install failed." -ForegroundColor Red
    exit 1
}

Write-Host "  OK Python dependencies ready" -ForegroundColor Green

# Step 3: Node deps
Write-Host ""
Write-Host "[3/6] Node.js dependencies" -ForegroundColor DarkCyan

Push-Location $FRONTEND
try {
    if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
        Write-Host "  Running npm install..." -ForegroundColor Yellow
        npm install --silent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR: npm install failed." -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "  OK Node modules ready" -ForegroundColor Green
}
finally {
    Pop-Location
}

# Step 4: Build React frontend
Write-Host ""
Write-Host "[4/6] Building React frontend" -ForegroundColor DarkCyan

Push-Location $FRONTEND
try {
    Write-Host "  Running vite build..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Frontend build failed." -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

$staticDir = Join-Path $BACKEND "static"
if (Test-Path $staticDir) {
    $fileCount = (Get-ChildItem $staticDir -Recurse -File | Measure-Object).Count
    Write-Host "  OK Frontend built -> $fileCount files in backend\static" -ForegroundColor Green
} else {
    Write-Host "  ERROR: backend\static not found after build!" -ForegroundColor Red
    exit 1
}

# Step 5: PyInstaller
Write-Host ""
Write-Host "[5/6] Running PyInstaller" -ForegroundColor DarkCyan
Write-Host "  This may take 2-5 minutes..." -ForegroundColor Yellow

if (Test-Path $DIST) {
    Write-Host "  Cleaning previous dist..." -ForegroundColor Gray
    Remove-Item -Path $DIST -Recurse -Force
}

if ($IS_WINDOWS) {
    $PYINSTALLER = Join-Path $VENV "Scripts\pyinstaller.exe"
} else {
    $PYINSTALLER = Join-Path $VENV "bin/pyinstaller"
}

Push-Location $BACKEND
try {
    & $PYINSTALLER `
        (Join-Path $BUILD "notinghill.spec") `
        --distpath $DIST `
        --workpath (Join-Path $BUILD "work") `
        --noconfirm `
        --clean

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: PyInstaller build failed." -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

Write-Host "  OK PyInstaller build complete" -ForegroundColor Green

# Step 6: Package output
Write-Host ""
Write-Host "[6/6] Packaging output" -ForegroundColor DarkCyan

if ($IS_WINDOWS) {
    $exePath = Join-Path $DIST "NotingHill\notinghill.exe"
    $zipName = "NotingHill-windows-x64.zip"
    $zipPath = Join-Path $ROOT $zipName

    if (Test-Path $exePath) {
        Write-Host "  Creating zip archive..." -ForegroundColor Yellow
        Compress-Archive -Path (Join-Path $DIST "NotingHill\*") -DestinationPath $zipPath -Force
        $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)

        Write-Host "  OK $zipName ($zipSize MB)" -ForegroundColor Green
        Write-Host "  EXE: $exePath" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: EXE not found at expected path." -ForegroundColor Yellow
    }
} else {
    $appPath = Join-Path $DIST "NotingHill.app"

    if (Test-Path $appPath) {
        Write-Host "  OK macOS app: $appPath" -ForegroundColor Green
        Write-Host "  To create a DMG, use: hdiutil create ..." -ForegroundColor Gray
    }
}

# Summary
$elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "BUILD COMPLETE - ${elapsed}s" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

if ($IS_WINDOWS) {
    Write-Host "EXE -> backend\dist\NotingHill\notinghill.exe" -ForegroundColor Green
    Write-Host "ZIP -> NotingHill-windows-x64.zip" -ForegroundColor Green
} else {
    Write-Host "APP -> backend\dist\NotingHill.app" -ForegroundColor Green
}

Write-Host ""
Write-Host "Double-click notinghill.exe to run." -ForegroundColor Cyan
Write-Host "The app will open http://127.0.0.1:7878 in your browser." -ForegroundColor Gray
Write-Host ""