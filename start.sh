#!/bin/bash

# OpenLearn Colombia - Quick Start Script
# This script starts all services for local development

set -e

echo "🚀 Starting OpenLearn Colombia..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1

    echo -n "⏳ Waiting for $service to be ready..."

    while ! nc -z $host $port >/dev/null 2>&1; do
        if [ $attempt -eq $max_attempts ]; then
            echo -e " ${RED}✗ Failed${NC}"
            return 1
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo -e " ${GREEN}✓${NC}"
    return 0
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

if ! command_exists python; then
    echo -e "${RED}✗ Python not found. Please install Python 3.9+ first.${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}✗ npm not found. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 1: Start infrastructure
echo "1️⃣  Starting infrastructure (PostgreSQL + Redis)..."
docker-compose up -d postgres redis

# Wait for PostgreSQL
wait_for_service localhost 5432 "PostgreSQL" || {
    echo -e "${RED}Failed to start PostgreSQL${NC}"
    docker-compose logs postgres
    exit 1
}

# Wait for Redis
wait_for_service localhost 6379 "Redis" || {
    echo -e "${RED}Failed to start Redis${NC}"
    docker-compose logs redis
    exit 1
}

echo ""

# Step 2: Install backend dependencies
echo "2️⃣  Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

if ! pip show fastapi >/dev/null 2>&1; then
    echo "Installing Python packages..."
    pip install -r requirements.txt --quiet
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

cd ..
echo ""

# Step 3: Run database migrations
echo "3️⃣  Running database migrations..."
cd backend
python -m alembic upgrade head
cd ..
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Step 4: Install frontend dependencies
echo "4️⃣  Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install --silent
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
cd ..
echo ""

# Step 5: Start services
echo "5️⃣  Starting application services..."
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Starting Backend and Frontend in background...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start backend in background
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
nohup uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "Backend PID: ${GREEN}$BACKEND_PID${NC}"
cd ..

# Wait for backend to start
sleep 3
wait_for_service localhost 8000 "Backend API" || {
    echo -e "${RED}Failed to start backend${NC}"
    cat logs/backend.log
    exit 1
}

# Start frontend in background
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "Frontend PID: ${GREEN}$FRONTEND_PID${NC}"
cd ..

# Wait for frontend to start
sleep 5
wait_for_service localhost 3000 "Frontend" || {
    echo -e "${RED}Failed to start frontend${NC}"
    cat logs/frontend.log
    exit 1
}

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ OpenLearn Colombia is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📱 Access your application:"
echo ""
echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "📊 Monitor services:"
echo ""
echo -e "  Backend logs:  ${YELLOW}tail -f logs/backend.log${NC}"
echo -e "  Frontend logs: ${YELLOW}tail -f logs/frontend.log${NC}"
echo -e "  Docker logs:   ${YELLOW}docker-compose logs -f${NC}"
echo ""
echo "🛑 To stop all services:"
echo ""
echo -e "  ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${GREEN}Happy researching! 🇨🇴${NC}"
echo ""

# Save PIDs for cleanup
mkdir -p .pids
echo $BACKEND_PID > .pids/backend.pid
echo $FRONTEND_PID > .pids/frontend.pid
