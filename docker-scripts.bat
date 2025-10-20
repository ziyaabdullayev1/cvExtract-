@echo off
REM Docker management scripts for CVExtract Pro

setlocal enabledelayedexpansion

if "%1"=="dev" goto dev
if "%1"=="prod" goto prod
if "%1"=="stop" goto stop
if "%1"=="clean" goto clean
if "%1"=="logs" goto logs
if "%1"=="health" goto health
if "%1"=="build" goto build
if "%1"=="help" goto help
if "%1"=="" goto help
goto help

:dev
echo [INFO] Starting CVExtract Pro in development mode...
docker-compose up --build
goto end

:prod
echo [INFO] Starting CVExtract Pro in production mode...
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
echo [SUCCESS] Application started in production mode at http://localhost:5000
goto end

:stop
echo [INFO] Stopping CVExtract Pro...
docker-compose down
echo [SUCCESS] Application stopped
goto end

:clean
echo [INFO] Cleaning up Docker resources...
docker-compose down -v
docker system prune -f
echo [SUCCESS] Cleanup completed
goto end

:logs
echo [INFO] Showing application logs...
docker-compose logs -f
goto end

:health
echo [INFO] Checking application health...
curl -f http://localhost:5000/ >nul 2>&1
if %errorlevel%==0 (
    echo [SUCCESS] Application is healthy
) else (
    echo [ERROR] Application is not responding
    exit /b 1
)
goto end

:build
echo [INFO] Building Docker image...
docker-compose build
echo [SUCCESS] Docker image built successfully
goto end

:help
echo CVExtract Pro Docker Management Script
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   dev     Start in development mode (with hot reloading)
echo   prod    Start in production mode
echo   stop    Stop the application
echo   clean   Stop and clean up all resources
echo   logs    Show application logs
echo   health  Check application health
echo   build   Build Docker image only
echo   help    Show this help message
echo.
echo Examples:
echo   %0 dev     # Start development server
echo   %0 prod    # Start production server
echo   %0 logs    # View logs
goto end

:end
