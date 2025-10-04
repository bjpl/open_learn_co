#!/bin/bash

# OpenLearn Colombia - Stop Script
# This script stops all running services

set -e

echo "🛑 Stopping OpenLearn Colombia..."
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop backend
if [ -f .pids/backend.pid ]; then
    BACKEND_PID=$(cat .pids/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -n "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        echo -e " ${GREEN}✓${NC}"
    fi
    rm -f .pids/backend.pid
fi

# Stop frontend
if [ -f .pids/frontend.pid ]; then
    FRONTEND_PID=$(cat .pids/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -n "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e " ${GREEN}✓${NC}"
    fi
    rm -f .pids/frontend.pid
fi

# Stop Docker services
echo -n "Stopping Docker services..."
docker-compose down > /dev/null 2>&1
echo -e " ${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo -e "To start again, run: ${YELLOW}./start.sh${NC}"
echo ""
