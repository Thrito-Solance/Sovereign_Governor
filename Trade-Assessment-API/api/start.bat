@echo off
REM Startup script for Trade Assessment API (Windows)

echo ==================================================
echo Trade Assessment API - Startup
echo ==================================================

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Creating from template...
    copy api\.env.example .env
    echo .
    echo .env created - Please update with your configuration
    echo Especially: AUTHORIZED_API_KEYS
    echo.
    exit /b 1
)

echo.
echo .env configuration found
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed!
    echo Install Docker from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Build and start container
echo.
echo Building Docker image...
docker-compose -f api\docker-compose.yml build

echo.
echo Starting Trade Assessment API...
docker-compose -f api\docker-compose.yml up -d

timeout /t 2 /nobreak

REM Check if API is running
docker ps | find "trade-assessment-api" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: API is running!
    echo.
    echo Access the API at: http://localhost:8000
    echo Interactive docs: http://localhost:8000/docs
    echo Alternative docs: http://localhost:8000/redoc
    echo.
    echo View logs: docker-compose -f api\docker-compose.yml logs -f
    echo Stop API: docker-compose -f api\docker-compose.yml down
) else (
    echo.
    echo ERROR: Failed to start API
    docker-compose -f api\docker-compose.yml logs
    exit /b 1
)
