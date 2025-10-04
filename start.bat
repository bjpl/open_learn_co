@echo off
REM OpenLearn Colombia - Windows Start Script

echo.
echo 🚀 Starting OpenLearn Colombia...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Step 1: Start infrastructure
echo 1️⃣  Starting infrastructure (PostgreSQL + Redis)...
docker-compose up -d postgres redis

timeout /t 5 /nobreak >nul

REM Step 2: Check if backend venv exists
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM Install dependencies if needed
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python packages...
    pip install -r requirements.txt --quiet
) else (
    echo ✓ Backend dependencies already installed
)

cd ..

REM Step 3: Run migrations
echo.
echo 3️⃣  Running database migrations...
cd backend
call venv\Scripts\activate.bat
python -m alembic upgrade head
cd ..

REM Step 4: Install frontend dependencies
echo.
echo 4️⃣  Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    echo Installing npm packages...
    call npm install
) else (
    echo ✓ Frontend dependencies already installed
)
cd ..

REM Step 5: Start services
echo.
echo 5️⃣  Starting application services...
echo.

REM Create logs directory
if not exist "logs" mkdir logs

REM Start backend
echo Starting backend...
cd backend
call venv\Scripts\activate.bat
start /B uvicorn app.main:app --reload --port 8000 > ..\logs\backend.log 2>&1
cd ..

timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend...
cd frontend
start /B npm run dev > ..\logs\frontend.log 2>&1
cd ..

timeout /t 5 /nobreak >nul

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✅ OpenLearn Colombia is running!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📱 Access your application:
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo 📊 View logs:
echo.
echo   Backend:  type logs\backend.log
echo   Frontend: type logs\frontend.log
echo.
echo 🛑 To stop: Press Ctrl+C in this window or run stop.bat
echo.
echo Happy researching! 🇨🇴
echo.

pause
