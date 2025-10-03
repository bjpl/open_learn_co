# Backend Installation Guide

Quick installation guide for the Colombia Intelligence & Language Learning Platform backend.

## Prerequisites

Ensure these system packages are installed:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-full
```

## Quick Install (Automated)

Run the automated installation script:

```bash
cd backend
./scripts/install_dependencies.sh
```

This script will:
1. Create a virtual environment
2. Install all Python dependencies
3. Download SpaCy language models
4. Verify installation
5. Create .env configuration file

## Manual Installation

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Download SpaCy Model

```bash
python -m spacy download es_core_news_lg
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit configuration
```

## Required Services

The backend requires these services to be running:

- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **Elasticsearch** (port 9200) - Optional

## Verification

Test the installation:

```bash
source venv/bin/activate
python -c "from app.main import app; print('✓ Backend OK')"
```

## Running the Application

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at: http://localhost:8000/docs

## Dependency Summary

**Total: 44 packages**

- FastAPI & Uvicorn (web framework)
- SQLAlchemy & Alembic (database)
- Spacy & Transformers (NLP)
- Celery & APScheduler (task queue)
- Prometheus & OpenTelemetry (monitoring)
- And more...

See `/mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/docs/backend-dependency-setup.md` for detailed dependency analysis.

## Troubleshooting

**Error: "No module named venv"**
```bash
sudo apt-get install python3-venv
```

**Error: "No module named pip"**
```bash
sudo apt-get install python3-pip
```

**Error: "externally-managed-environment"**
- Always use virtual environment (never install globally)

**Large download for torch (~2GB)**
- CPU-only version: `pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu`

## Support

- Full setup guide: `/mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/docs/backend-dependency-setup.md`
- API documentation: http://localhost:8000/docs (after starting)
