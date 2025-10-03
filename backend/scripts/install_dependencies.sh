#!/bin/bash
# Backend Dependency Installation Script
# Colombia Intelligence & Language Learning Platform
# Generated: 2025-10-03

set -e  # Exit on error

echo "================================================"
echo "Backend Dependency Installation"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "Backend Directory: $BACKEND_DIR"
echo ""

# Step 1: Check for virtual environment
echo -e "${YELLOW}[1/7] Checking for virtual environment...${NC}"
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd "$BACKEND_DIR"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi
echo ""

# Step 2: Activate virtual environment
echo -e "${YELLOW}[2/7] Activating virtual environment...${NC}"
source "$BACKEND_DIR/venv/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 3: Upgrade pip
echo -e "${YELLOW}[3/7] Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ Package managers updated${NC}"
echo ""

# Step 4: Install dependencies
echo -e "${YELLOW}[4/7] Installing dependencies from requirements.txt...${NC}"
cd "$BACKEND_DIR"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Download SpaCy model
echo -e "${YELLOW}[5/7] Downloading SpaCy Spanish language model...${NC}"
python -m spacy download es_core_news_lg || {
    echo -e "${YELLOW}⚠ Large model failed, trying medium model...${NC}"
    python -m spacy download es_core_news_md || {
        echo -e "${YELLOW}⚠ Medium model failed, trying small model...${NC}"
        python -m spacy download es_core_news_sm
    }
}
echo -e "${GREEN}✓ SpaCy model downloaded${NC}"
echo ""

# Step 6: Verify installation
echo -e "${YELLOW}[6/7] Verifying installation...${NC}"
python3 << EOF
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import spacy
    import transformers
    import apscheduler
    import celery
    import prometheus_client
    import structlog
    import pydantic_settings
    print("✓ All core dependencies imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
EOF
echo -e "${GREEN}✓ Verification complete${NC}"
echo ""

# Step 7: Create .env if not exists
echo -e "${YELLOW}[7/7] Checking environment configuration...${NC}"
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and configure:${NC}"
    echo "  - DATABASE_URL"
    echo "  - REDIS_URL"
    echo "  - SECRET_KEY (generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Summary
echo "================================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "================================================"
echo ""
echo "Installed packages:"
pip list | grep -E "fastapi|uvicorn|spacy|celery|sqlalchemy|redis|prometheus" || true
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Configure .env file with your settings"
echo "3. Start PostgreSQL and Redis services"
echo "4. Run migrations: alembic upgrade head"
echo "5. Start application: uvicorn app.main:app --reload"
echo ""
echo "Virtual environment location: $BACKEND_DIR/venv"
echo "To activate: source $BACKEND_DIR/venv/bin/activate"
echo ""
