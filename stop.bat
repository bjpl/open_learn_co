@echo off
REM OpenLearn Colombia - Windows Stop Script

echo.
echo 🛑 Stopping OpenLearn Colombia...
echo.

REM Stop Docker services
echo Stopping Docker services...
docker-compose down >nul 2>&1

REM Kill Python processes (backend)
echo Stopping backend...
taskkill /F /IM python.exe /T >nul 2>&1

REM Kill Node processes (frontend)
echo Stopping frontend...
taskkill /F /IM node.exe /T >nul 2>&1

echo.
echo ✅ All services stopped
echo.
echo To start again, run: start.bat
echo.

pause
