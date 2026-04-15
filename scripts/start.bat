@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."

docker stop pm-app 2>nul

echo Building...
docker build -t pm-app "%PROJECT_ROOT%"
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

if not exist "%PROJECT_ROOT%\data" mkdir "%PROJECT_ROOT%\data"

set "ENV_ARG="
if exist "%PROJECT_ROOT%\.env" (
    set "ENV_ARG=--env-file %PROJECT_ROOT%\.env"
) else (
    echo Warning: .env not found at %PROJECT_ROOT%\.env -- OPENROUTER_API_KEY will not be set
)

echo Starting...
docker run -d --rm --name pm-app -p 8000:8000 -v "%PROJECT_ROOT%\data:/app/data" %ENV_ARG% pm-app

echo Running at http://localhost:8000
