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

echo Starting...
docker run -d --rm --name pm-app -p 8000:8000 pm-app

echo Running at http://localhost:8000
