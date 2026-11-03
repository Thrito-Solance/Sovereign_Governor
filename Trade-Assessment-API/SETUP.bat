@echo off
REM Quick setup script for Trade Assessment API
REM Run this FIRST to set up the API

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo Trade Assessment API - Quick Setup
echo ============================================================
echo.

REM Check if Docker is installed
echo Checking for Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is installed

REM Check if Lean4.exe exists
echo.
echo Checking for Lean4.exe...
if not exist "Lean4.exe" (
    echo.
    echo WARNING: Lean4.exe not found in current directory
    echo.
    echo Please ensure your compiled Lean kernel (Lean4.exe) is in:
    echo   %cd%\Lean4.exe
    echo.
    pause
    exit /b 1
)
echo [OK] Lean4.exe found

REM Check if API files exist
echo.
echo Checking for API files...
if not exist "api\main.py" (
    echo.
    echo ERROR: API files not found. Ensure you have the api\ directory.
    echo.
    pause
    exit /b 1
)
echo [OK] API files found

REM Generate initial API key if needed
echo.
echo Setting up configuration...
if not exist ".env" (
    echo Creating .env from template...
    if exist "api\.env.example" (
        copy api\.env.example .env >nul
        echo [OK] .env created
    )
) else (
    echo [OK] .env already exists
)

REM Check if AUTHORIZED_API_KEYS is set
for /f "tokens=*" %%A in ('type .env ^| find "AUTHORIZED_API_KEYS"') do set "LINE=%%A"
if "!LINE!"=="" (
    echo.
    echo WARNING: AUTHORIZED_API_KEYS not set in .env
    goto :need_keys
)
if "!LINE:key1=!"=="!LINE!" (
    echo [OK] API keys configured
    goto :ready
)

:need_keys
echo.
echo ============================================================
echo API KEYS SETUP REQUIRED
echo ============================================================
echo.
echo No valid API keys found in .env
echo.
echo OPTION 1: Generate new keys (Recommended)
echo   python api\generate_keys.py --count 1
echo   Then copy the key into .env AUTHORIZED_API_KEYS setting
echo.
echo OPTION 2: Set a temporary test key
echo   Edit .env and change AUTHORIZED_API_KEYS to a value like:
echo   AUTHORIZED_API_KEYS=test-key-12345
echo.
pause
exit /b 1

:ready
echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Next steps:
echo   1. Start the API by running: api\start.bat
echo   2. Access the API at: http://localhost:8000
echo   3. View docs at: http://localhost:8000/docs
echo   4. Use api\example_client.py to test
echo.
echo For production deployment, see: DEPLOYMENT_CHECKLIST.md
echo.
echo.
pause
exit /b 0
