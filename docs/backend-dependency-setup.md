# Backend Dependency Installation Guide

## Current Status: BLOCKED - System Setup Required

**Date**: 2025-10-03
**Environment**: WSL2 Ubuntu (Python 3.12.3)
**Issue**: Missing system packages for Python virtual environment and pip

---

## Issues Identified

### 1. Missing System Packages
The WSL2 environment is missing required Python packages:
- `python3-pip` - Python package installer
- `python3-venv` - Virtual environment support
- `python3-full` - Full Python installation (recommended)

### 2. Externally Managed Environment
Python 3.12+ uses PEP 668 to prevent system-wide package installations.
Virtual environments are **REQUIRED** for package management.

---

## Required System Setup (Run Once)

### Option 1: Install Required System Packages (Recommended)
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-full
```

### Option 2: Install pipx for Isolated Environments
```bash
sudo apt-get update
sudo apt-get install -y pipx
pipx ensurepath
```

---

## Backend Dependency Installation Steps

Once system packages are installed, run these commands:

### Step 1: Create Virtual Environment
```bash
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/backend
python3 -m venv venv
```

### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
```

### Step 3: Upgrade pip and Install Build Tools
```bash
pip install --upgrade pip setuptools wheel
```

### Step 4: Install All Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Download SpaCy Language Model
```bash
python -m spacy download es_core_news_lg
```

### Step 6: Verify Installation
```bash
pip list
python -c "import fastapi; import spacy; print('Dependencies OK')"
```

---

## Dependencies Analysis

### Core Framework (3 packages)
- ✅ fastapi==0.104.1
- ✅ uvicorn[standard]==0.24.0
- ✅ python-dotenv==1.0.0

### Web Scraping (6 packages)
- ✅ beautifulsoup4==4.12.2
- ✅ scrapy==2.11.0
- ✅ selenium==4.15.2
- ✅ aiohttp==3.9.1
- ✅ requests==2.31.0
- ✅ lxml==4.9.3

### NLP & Text Processing (4 packages)
- ✅ spacy==3.7.2
- ✅ transformers==4.35.2
- ✅ nltk==3.8.1
- ✅ textblob==0.17.1

### Database (6 packages)
- ✅ sqlalchemy==2.0.23
- ✅ psycopg2-binary==2.9.9
- ✅ aiosqlite==0.19.0
- ✅ alembic==1.12.1
- ✅ elasticsearch==8.11.0
- ✅ redis==5.0.1

### Data Processing (3 packages)
- ✅ pandas==2.1.3
- ✅ numpy==1.26.2
- ✅ pydantic==2.5.2

### ML & Analytics (2 packages)
- ✅ scikit-learn==1.3.2
- ✅ torch==2.1.1

### Monitoring & Logging (8 packages)
- ✅ loguru==0.7.2
- ✅ sentry-sdk[fastapi]==1.38.0
- ✅ structlog==23.2.0
- ✅ prometheus-client==0.19.0
- ✅ python-json-logger==2.0.7
- ✅ opentelemetry-api==1.21.0
- ✅ opentelemetry-sdk==1.21.0
- ✅ opentelemetry-instrumentation-fastapi==0.42b0

### Testing (3 packages)
- ✅ pytest==7.4.3
- ✅ pytest-asyncio==0.21.1
- ✅ httpx==0.25.2

### Task Queue & Scheduling (4 packages)
- ✅ celery==5.3.4
- ✅ flower==2.0.1
- ✅ apscheduler==3.10.4
- ✅ pytz==2023.3

### Security (3 packages)
- ✅ python-jose[cryptography]==3.3.0
- ✅ passlib[bcrypt]==1.7.4
- ✅ python-multipart==0.0.6

**Total: 42 packages** (excluding dependencies)

---

## Missing Dependencies Detected

After analyzing imports in the codebase, the following packages are **IMPLICITLY REQUIRED** but may not be in requirements.txt:

### Standard Library (Already Available)
- ✅ jwt (provided by python-jose)
- ✅ email, smtplib (Python standard library)
- ✅ secrets, uuid, time, sys, os (Python standard library)
- ✅ logging, asyncio, random (Python standard library)
- ✅ typing, functools, contextlib, enum (Python standard library)
- ✅ datetime, contextvars (Python standard library)

### Additional Package Needed
- ⚠️ **pydantic-settings** - Required for settings.py configuration
  - Used: `from pydantic_settings import BaseSettings`
  - Add to requirements.txt: `pydantic-settings==2.1.0`

### NLP Model Download Required
- ⚠️ **SpaCy Spanish Model** - Must be downloaded separately
  - Command: `python -m spacy download es_core_news_lg`
  - Alternative: `python -m spacy download es_core_news_sm`

---

## Updated requirements.txt (Recommended)

Add the following to requirements.txt:

```txt
# Settings Management (MISSING - CRITICAL)
pydantic-settings==2.1.0
```

---

## Import Analysis Summary

### External Packages Used
All imports have been verified against requirements.txt:
- ✅ FastAPI ecosystem (fastapi, starlette)
- ✅ Database (sqlalchemy, psycopg2)
- ✅ Web scraping (aiohttp, requests, beautifulsoup4, scrapy, selenium)
- ✅ NLP (spacy, transformers, nltk, textblob)
- ✅ Scheduling (apscheduler, celery)
- ✅ Security (jwt via python-jose, passlib)
- ✅ Logging (structlog, logging, pythonjsonlogger)
- ✅ Monitoring (prometheus, opentelemetry, sentry)
- ✅ Data processing (pandas, numpy, pydantic)

### Potential Issues
1. **pydantic-settings** is used but not in requirements.txt
2. **SpaCy model** requires manual download after pip install
3. **Local imports** from scrapers/ directory (outside backend/app)

---

## Post-Installation Verification

### Test 1: Import Core Dependencies
```bash
python3 << EOF
import fastapi
import uvicorn
import sqlalchemy
import spacy
import transformers
import apscheduler
import celery
import prometheus_client
import structlog
print("✅ All core dependencies imported successfully")
EOF
```

### Test 2: Check SpaCy Model
```bash
python3 -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('✅ SpaCy model loaded')"
```

### Test 3: Run Application Imports
```bash
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/backend
python3 -c "from app.main import app; print('✅ Application imports successful')"
```

---

## Environment Variables Setup

After installing dependencies, configure environment variables:

```bash
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/backend
cp .env.example .env
# Edit .env with your configuration
nano .env
```

**Critical Variables**:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `SECRET_KEY` - JWT secret (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

---

## Troubleshooting

### Issue: "externally-managed-environment"
**Solution**: Always use virtual environment (venv) - never install globally

### Issue: "No module named pip"
**Solution**: Install system package `sudo apt-get install python3-pip`

### Issue: "No module named ensurepip"
**Solution**: Install system package `sudo apt-get install python3-venv`

### Issue: torch installation fails (large package ~2GB)
**Solution**: Install CPU-only version:
```bash
pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu
```

### Issue: SpaCy model not found
**Solution**: Download after pip install:
```bash
python -m spacy download es_core_news_lg
```

---

## Next Steps

1. ✅ **System Setup**: Install python3-pip, python3-venv, python3-full
2. ✅ **Virtual Environment**: Create and activate venv
3. ✅ **Update Requirements**: Add pydantic-settings==2.1.0
4. ✅ **Install Dependencies**: Run pip install -r requirements.txt
5. ✅ **Download SpaCy Model**: python -m spacy download es_core_news_lg
6. ✅ **Configure Environment**: Copy and edit .env file
7. ✅ **Verify Installation**: Run verification tests
8. ✅ **Start Application**: uvicorn app.main:app --reload

---

## Status Report

**Installation Status**: ⚠️ BLOCKED
**Blocking Issue**: System packages not installed (python3-venv, python3-pip)
**Action Required**: Run system package installation commands
**ETA**: 5-10 minutes after system packages installed

**Reviewed By**: DevOps Engineer Agent
**Swarm ID**: swarm-1759472272810
**Task ID**: deps-install
