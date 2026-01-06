# Setup script for Windows PowerShell
# This script sets up the development environment for all project components

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Starting MS Neuroplatform Development Environment Setup" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# Check Python
function Check-Python {
    Write-Host "Checking Python..." -ForegroundColor Yellow
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonVersion = python --version
        Write-Host "[OK] $pythonVersion is installed" -ForegroundColor Green
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonVersion = python3 --version
        Write-Host "[OK] $pythonVersion is installed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Python 3 not found. Please install Python 3.9+" -ForegroundColor Red
        exit 1
    }
}

# Setup Gateway Service
function Setup-Gateway {
    Write-Host ""
    Write-Host "Setting up Gateway Service..." -ForegroundColor Yellow
    Push-Location gateway\gateway-service
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    }
    
    & .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "[OK] Gateway dependencies installed" -ForegroundColor Green
    
    deactivate
    Pop-Location
}

# Setup Cloud Backend
function Setup-Backend {
    Write-Host ""
    Write-Host "Setting up Cloud Backend..." -ForegroundColor Yellow
    Push-Location cloud\backend
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    }
    
    & .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "[OK] Backend dependencies installed" -ForegroundColor Green
    
    deactivate
    Pop-Location
}

# Setup ML Environment
function Setup-ML {
    Write-Host ""
    Write-Host "Setting up ML Environment..." -ForegroundColor Yellow
    Push-Location ml
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    }
    
    & .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "[OK] ML dependencies installed" -ForegroundColor Green
    
    deactivate
    Pop-Location
}

# Check Firmware Tools
function Check-FirmwareTools {
    Write-Host ""
    Write-Host "Checking Firmware Tools..." -ForegroundColor Yellow
    
    # Check CMake
    if (Get-Command cmake -ErrorAction SilentlyContinue) {
        $cmakeVersion = cmake --version | Select-Object -First 1
        Write-Host "[OK] $cmakeVersion is installed" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] CMake not found. Required for Firmware compilation." -ForegroundColor Yellow
    }
    
    # Check ARM GCC
    if (Get-Command arm-none-eabi-gcc -ErrorAction SilentlyContinue) {
        $gccVersion = arm-none-eabi-gcc --version | Select-Object -First 1
        Write-Host "[OK] ARM GCC is installed: $gccVersion" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] ARM GCC Toolchain not found. Required for Firmware compilation." -ForegroundColor Yellow
        Write-Host "   Download from: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain" -ForegroundColor Yellow
    }
}

# Create .env example files
function Create-EnvFiles {
    Write-Host ""
    Write-Host "Creating .env example files..." -ForegroundColor Yellow
    
    # Gateway .env
    if (-not (Test-Path "gateway\gateway-service\.env.example")) {
        $gatewayEnv = @"
# Gateway Service Configuration
BLE_SCAN_INTERVAL=5
CLOUD_API_URL=https://api.example.com
API_KEY=your_api_key_here
LOG_LEVEL=INFO
"@
        $gatewayEnv | Out-File -FilePath "gateway\gateway-service\.env.example" -Encoding UTF8
        Write-Host "[OK] .env.example created for Gateway" -ForegroundColor Green
    }
    
    # Backend .env
    if (-not (Test-Path "cloud\backend\.env.example")) {
        $backendEnv = @"
# Backend Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/ms_platform
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
"@
        $backendEnv | Out-File -FilePath "cloud\backend\.env.example" -Encoding UTF8
        Write-Host "[OK] .env.example created for Backend" -ForegroundColor Green
    }
}

# Main execution
function Main {
    Check-Python
    Setup-Gateway
    Setup-Backend
    Setup-ML
    Check-FirmwareTools
    Create-EnvFiles
    
    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "[OK] Development environment setup completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Copy .env.example files to .env and fill in the settings"
    Write-Host "2. For Gateway: cd gateway\gateway-service && .\venv\Scripts\Activate.ps1"
    Write-Host "3. For Backend: cd cloud\backend && .\venv\Scripts\Activate.ps1"
    Write-Host "4. For ML: cd ml && .\venv\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "For more information, see DEVELOPMENT.md" -ForegroundColor Cyan
}

Main

