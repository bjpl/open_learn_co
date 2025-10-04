# OpenLearn Colombia - Complete Deployment Walkthrough

**Generated:** December 3, 2025
**Target:** Production Deployment in 1.5-2 weeks
**Current Status:** 92% Ready

---

## Overview

This guide provides a **step-by-step walkthrough** to take OpenLearn Colombia from 92% ready to fully deployed in production. Tasks are divided into:

- 🤖 **AUTOMATED** - Claude Code will handle programmatically
- 👤 **MANUAL** - You must complete personally
- 🔄 **COLLABORATIVE** - Requires both automation and manual steps

**Estimated Total Time:** 12-16 hours of active work over 1.5-2 weeks

---

## Phase 1: Critical Fixes (Day 1 - 4 hours)

### Task 1.1: Fix Redis Dependency Conflict 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes (automated)
**You do:** Nothing - approve the fix
**Claude does:** Edit requirements.txt to remove duplicates

**What will be fixed:**
```python
# BEFORE (requirements.txt):
redis==5.0.1
aioredis==2.0.1  # ❌ Deprecated
redis[hiredis]==5.0.1  # ❌ Duplicate

# AFTER:
redis[hiredis]==5.0.1  # ✅ Includes async support natively
```

**Approval Required:** Review the change and confirm

---

### Task 1.2: Generate Production SECRET_KEY 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 15 minutes
**Why manual:** You need to securely store the secret key

**Steps:**

```bash
# 1. Navigate to backend directory
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/backend

# 2. Generate 64-byte secret key
python scripts/generate_secret_key.py --bytes 64 --format raw

# Example output (yours will be different):
# kJ8mN2pQ5tR7wY0zX3vB6nM9lK4jH8gF5dS2aP0oI9uY7tR6eW4qZ1xC3vB5nM8k

# 3. COPY the output and save it securely
# - Use a password manager (1Password, Bitwarden, etc.)
# - Store as "OpenLearn Production SECRET_KEY"
# - NEVER commit this to git
```

**Important Security Notes:**
- ⚠️ This key signs JWT tokens - keep it absolutely secret
- ⚠️ If compromised, all user sessions will need to be invalidated
- ⚠️ Minimum 64 bytes for production (script enforces this)
- ⚠️ Rotate every 90 days (set calendar reminder)

**Verification:**
```bash
# Verify key length (should be 88 characters base64-encoded)
echo "YOUR_GENERATED_KEY" | wc -c
# Should output: 88 or 89 (with newline)
```

---

### Task 1.3: Generate Database & Redis Passwords 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 10 minutes

**Steps:**

```bash
# 1. Generate PostgreSQL password (32 bytes minimum)
python scripts/generate_secret_key.py --bytes 32 --format raw

# Example output:
# tR6eW4qZ1xC3vB5nM8kJ9mN2pQ

# 2. Generate Redis password (32 bytes minimum)
python scripts/generate_secret_key.py --bytes 32 --format raw

# Example output:
# xC3vB5nM8kJ9mN2pQ5tR7wY0z

# 3. Save both passwords securely in password manager:
# - "OpenLearn Production PostgreSQL Password"
# - "OpenLearn Production Redis Password"
```

**Security Checklist:**
- [ ] Passwords are 32+ characters
- [ ] Passwords contain mix of alphanumeric characters
- [ ] Passwords stored in password manager
- [ ] Passwords NOT committed to git
- [ ] Different passwords for PostgreSQL and Redis

---

### Task 1.4: Create Production .env File 🔄 **COLLABORATIVE**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 20 minutes
**You do:** Provide secrets and API keys
**Claude does:** Generate .env template with placeholders

**Claude will create:**
```bash
backend/.env.production.local
```

**You must fill in:**

1. **Secrets (from Tasks 1.2 & 1.3):**
   ```env
   SECRET_KEY=<paste from Task 1.2>
   POSTGRES_PASSWORD=<paste from Task 1.3>
   REDIS_PASSWORD=<paste from Task 1.3>
   ```

2. **Colombian API Keys (if you have them):**
   ```env
   DANE_API_KEY=<your key or leave empty>
   SECOP_API_TOKEN=<your key or leave empty>
   IDEAM_API_KEY=<your key or leave empty>
   ```

3. **Monitoring (optional for initial deployment):**
   ```env
   SENTRY_DSN=<your Sentry DSN or leave empty>
   ```

4. **Email/Alerting (optional for initial deployment):**
   ```env
   SMTP_HOST=<your SMTP server or leave empty>
   SMTP_USER=<your email or leave empty>
   SMTP_PASSWORD=<your email password or leave empty>
   ```

**Important:**
- ⚠️ Never commit `.env.production.local` to git
- ⚠️ Claude will add it to `.gitignore` automatically
- ✅ You can leave API keys empty for initial deployment
- ✅ Monitoring can be configured post-deployment

---

### Task 1.5: Validate Production Configuration 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes (automated)
**You do:** Review validation results
**Claude does:** Run validation script

**What Claude will run:**
```bash
cd backend
python scripts/validate_config.py --env production --strict
```

**Expected output:**
```
✅ VALIDATION PASSED: 0 error(s), 2 warning(s)

WARNINGS:
⚠️  Colombian API keys not configured (non-blocking)
⚠️  Sentry DSN not configured (optional)

PASSED CHECKS:
✅ SECRET_KEY length: 64 bytes (exceeds 32-byte minimum)
✅ POSTGRES_PASSWORD strength: Strong (32+ characters)
✅ REDIS_PASSWORD configured
✅ DEBUG mode: False (production)
✅ CORS origins: No wildcards (production-safe)
✅ Database URL format: Valid PostgreSQL connection string
```

**If validation fails:**
- Claude will identify which values are missing/invalid
- You'll need to correct the `.env.production.local` file
- Re-run validation until it passes

---

## Phase 2: Code Fixes (Day 1 - 2 hours)

### Task 2.1: Consolidate Stop Words 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 5 minutes (automated)
**You do:** Approve changes
**Claude does:** Refactor duplicated code

**What will be fixed:**
1. Create `backend/nlp/common/stop_words.py`
2. Move Colombian Spanish stop words list there
3. Update imports in `difficulty_scorer.py` and `topic_modeler.py`
4. Remove duplicated lists

**Result:**
- 30-40 lines of duplicate code removed
- Single source of truth for stop words
- Easier maintenance going forward

---

### Task 2.2: Document Incomplete TODOs 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 10 minutes (automated)
**You do:** Review and prioritize
**Claude does:** Create tracking document

**What Claude will create:**
```
backend/docs/INCOMPLETE_FEATURES.md
```

**Content:**
- List of 10 incomplete TODO items found
- File locations and line numbers
- Impact assessment (High/Medium/Low)
- Recommended timeline for completion
- Workarounds for production deployment

**Example entries:**
```markdown
### Email Password Reset (HIGH PRIORITY)
**File:** `/app/api/auth.py:426`
**Current:** TODO comment, no implementation
**Impact:** Users cannot reset passwords via email
**Workaround:** Admin manual password reset
**Recommended Fix:** Week 2 post-deployment

### User Timezone Handling (MEDIUM PRIORITY)
**File:** `/app/services/notification_scheduler_jobs.py:52`
**Current:** TODO comment, sends at server time
**Impact:** Notifications sent at wrong time for users
**Workaround:** Document server timezone (UTC)
**Recommended Fix:** Month 2
```

**You decide:**
- Which TODOs to fix before deployment (if any)
- Which can wait until post-deployment
- Which can be documented as known limitations

---

### Task 2.3: Add Missing LICENSE File 🤖 **AUTOMATED**

**Status:** MEDIUM PRIORITY (required for open source)
**Estimated Time:** 2 minutes (automated)
**You do:** Confirm license choice
**Claude does:** Create LICENSE file

**Options:**
1. **MIT License** (permissive, recommended based on README)
2. **Apache 2.0** (permissive with patent grant)
3. **GPL v3** (copyleft)

**Default:** MIT (as mentioned in README.md:238)

**Claude will create:**
```
LICENSE
```

**You must provide:**
- Copyright year (default: 2025)
- Copyright holder name (default: "OpenLearn Colombia Contributors")

---

## Phase 3: Dependency Installation (Day 2 - 2 hours)

### Task 3.1: Verify Python Version 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes

**Steps:**
```bash
# Check Python version
python --version
# OR
python3 --version

# Required: Python 3.9, 3.10, 3.11, or 3.12
# Recommended: Python 3.11 or 3.12
```

**If Python version is wrong:**

**Option A: Install Python 3.12 (Recommended)**
```bash
# Windows (using winget):
winget install Python.Python.3.12

# OR using Chocolatey:
choco install python312

# Verify installation:
python3.12 --version
```

**Option B: Use pyenv (Advanced)**
```bash
# Install pyenv (if not installed)
curl https://pyenv.run | bash

# Install Python 3.12
pyenv install 3.12.1
pyenv local 3.12.1
```

---

### Task 3.2: Create Python Virtual Environment 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes

**Steps:**
```bash
# Navigate to backend directory
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (CMD):
.\venv\Scripts\activate.bat

# On WSL/Linux/Mac:
source venv/bin/activate

# Verify activation (you should see (venv) in prompt):
# (venv) PS C:\...\backend>
```

**Troubleshooting:**
- If PowerShell execution policy error:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

### Task 3.3: Install Python Dependencies 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 15-30 minutes (download time varies)

**Steps:**
```bash
# Ensure virtual environment is activated (see Task 3.2)
# You should see (venv) in your prompt

# Upgrade pip first
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Expected output:
# Successfully installed 50+ packages
# Including: fastapi, sqlalchemy, uvicorn, spacy, etc.
```

**Watch for errors:**
- ⚠️ If `psycopg2-binary` fails on Windows, it may need Visual C++ Build Tools
- ⚠️ If `torch` is slow, it's downloading ~2GB (be patient)
- ⚠️ If network issues, try again with `--retries 3`

**Verify installation:**
```bash
# Check key packages installed
pip show fastapi sqlalchemy uvicorn spacy redis

# All should show version numbers
```

---

### Task 3.4: Install Development Dependencies 👤 **MANUAL**

**Status:** HIGH PRIORITY (for testing)
**Estimated Time:** 5-10 minutes

**Steps:**
```bash
# Ensure virtual environment is activated

# Install dev dependencies
pip install -r requirements-dev.txt

# Verify pytest installed
pytest --version
# Should show: pytest 7.4.3
```

---

### Task 3.5: Download spaCy NLP Model 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 10-20 minutes (large download ~500MB)

**Steps:**
```bash
# Ensure virtual environment is activated

# Download Spanish NLP model (LARGE version for production)
python -m spacy download es_core_news_lg

# Expected output:
# Downloading model 'es_core_news_lg'...
# Successfully installed es_core_news_lg-3.7.0
```

**Verify installation:**
```bash
# Test model loads correctly
python -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('✅ NLP model loaded successfully')"

# Should output:
# ✅ NLP model loaded successfully
```

**Troubleshooting:**
- If download fails, try direct download:
  ```bash
  pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_lg-3.7.0/es_core_news_lg-3.7.0-py3-none-any.whl
  ```

---

### Task 3.6: Verify All Dependencies Installed 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes (automated)
**You do:** Review results
**Claude does:** Run import verification script

**What Claude will run:**
```python
# Test all critical imports
import fastapi
import sqlalchemy
import uvicorn
import redis
import spacy
import apscheduler
import prometheus_client
import sentry_sdk
import pytest
# ... etc.

# Verify NLP model
nlp = spacy.load('es_core_news_lg')

# Print success summary
```

**Expected output:**
```
✅ All critical dependencies installed successfully
✅ spaCy model 'es_core_news_lg' loaded
✅ Redis client available
✅ Database drivers available
✅ Monitoring tools available
✅ Testing framework available
```

---

## Phase 4: Database Setup (Day 2 - 1 hour)

### Task 4.1: Start PostgreSQL via Docker 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 10 minutes

**Steps:**
```bash
# Navigate to project root
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn

# Start only PostgreSQL and Redis (for testing)
docker-compose -f docker-compose.production.yml up -d postgres redis

# Expected output:
# Creating network "open_learn_colombian_network" ... done
# Creating colombian_platform_db ... done
# Creating colombian_platform_redis ... done
```

**Verify services started:**
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Should show:
# NAME                        STATUS
# colombian_platform_db       Up (healthy)
# colombian_platform_redis    Up (healthy)
```

**Wait for health checks:**
```bash
# Wait 30 seconds for services to become healthy
# You can monitor with:
watch docker-compose -f docker-compose.production.yml ps
```

---

### Task 4.2: Initialize Database Schema 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes (automated)
**You do:** Verify no errors
**Claude does:** Run Alembic migrations

**What Claude will run:**
```bash
cd backend

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://colombian_user:${POSTGRES_PASSWORD}@localhost:5432/colombian_platform"

# Run migrations
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_add_performance_indexes
```

**Verification:**
```bash
# Check tables were created
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform -c "\dt"

# Should show tables:
# - users
# - articles
# - scrapers
# - vocabulary
# - etc.
```

---

### Task 4.3: Initialize APScheduler Tables 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 2 minutes (automated)
**You do:** Verify no errors
**Claude does:** Run initialization script

**What Claude will run:**
```bash
cd backend
python scripts/init_scheduler_db.py
```

**Expected output:**
```
Connecting to database...
Checking if APScheduler tables exist...
Creating apscheduler_jobs table...
✅ APScheduler tables initialized successfully
```

**Verification:**
```bash
# Check APScheduler table was created
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform -c "SELECT COUNT(*) FROM apscheduler_jobs;"

# Should show:
# count
# -------
#     0
# (1 row)
```

---

## Phase 5: Testing & Validation (Day 3 - 3 hours)

### Task 5.1: Run Test Suite 👤 **MANUAL**

**Status:** HIGH PRIORITY
**Estimated Time:** 10-15 minutes

**Steps:**
```bash
# Ensure virtual environment is activated
# Ensure PostgreSQL is running (Task 4.1)

cd backend

# Run all tests with coverage
pytest -v --cov=app --cov=nlp --cov-report=term --cov-report=html

# Expected output:
# ===== test session starts =====
# collected 811 items
#
# tests/api/test_auth.py::test_login PASSED
# tests/api/test_scraping_endpoints.py::test_scrape PASSED
# ... (many more tests)
#
# ===== 811 passed in 45.23s =====
#
# Coverage summary:
# app/api/auth.py      95%
# app/api/scraping.py  88%
# ... (coverage report)
#
# Total coverage: 45%
```

**Review coverage report:**
```bash
# Open HTML coverage report
# On Windows:
start htmlcov/index.html

# On WSL:
explorer.exe htmlcov/index.html

# On Linux:
xdg-open htmlcov/index.html
```

**Acceptable results:**
- ✅ All tests pass (or document failing tests)
- ✅ Coverage ≥ 40% (target 85% long-term)
- ⚠️ Some tests may be skipped (documented in report)

**If tests fail:**
- Review test output for errors
- Common issues:
  - Database connection errors (check PostgreSQL is running)
  - Redis connection errors (check Redis is running)
  - Import errors (check dependencies installed)
- Document failing tests in deployment notes

---

### Task 5.2: Test Health Check Endpoints 👤 **MANUAL**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 10 minutes

**Steps:**
```bash
# Start backend server (in separate terminal)
cd backend
uvicorn app.main:app --reload --port 8000

# In another terminal, test health endpoints:

# 1. Liveness check (should always return 200)
curl http://localhost:8000/health/live
# Expected: {"status": "healthy", "timestamp": "..."}

# 2. Readiness check (checks dependencies)
curl http://localhost:8000/health/ready
# Expected: {"status": "healthy", "checks": {...}}

# 3. Startup check
curl http://localhost:8000/health/startup
# Expected: {"status": "healthy", "initialized": true}

# 4. Detailed health check
curl http://localhost:8000/health
# Expected: {
#   "status": "healthy",
#   "database": {"healthy": true, ...},
#   "redis": {"healthy": true, ...},
#   "disk_space": {"healthy": true, ...},
#   ...
# }

# 5. Metrics endpoint
curl http://localhost:8000/metrics
# Expected: Prometheus metrics in text format
```

**Expected results:**
- ✅ `/health/live` returns 200 with `{"status": "healthy"}`
- ✅ `/health/ready` returns 200 with all checks healthy
- ✅ `/health` returns detailed status for all dependencies
- ✅ `/metrics` returns Prometheus-format metrics

**If health checks fail:**
- Check database connection (PostgreSQL running?)
- Check Redis connection (Redis running?)
- Review error messages in server logs
- Common issues documented in TROUBLESHOOTING.md (Claude will create)

---

### Task 5.3: Test Manual Scraper Run 👤 **MANUAL**

**Status:** HIGH PRIORITY
**Estimated Time:** 15 minutes

**Steps:**
```bash
# Ensure backend server is running (Task 5.2)

# Test scraping a single article (using API)
curl -X POST http://localhost:8000/api/v1/scrape/manual \
  -H "Content-Type: application/json" \
  -d '{
    "source": "semana",
    "limit": 5
  }'

# Expected response:
# {
#   "status": "success",
#   "articles_scraped": 5,
#   "source": "semana",
#   "processing_time_seconds": 12.34
# }

# Check database for scraped articles
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT COUNT(*) FROM articles WHERE source = 'semana';"

# Should show:
# count
# -------
#     5
```

**Test NLP processing:**
```bash
# Trigger NLP analysis on scraped articles
curl -X POST http://localhost:8000/api/v1/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "source": "semana",
    "limit": 5
  }'

# Expected:
# {
#   "status": "success",
#   "articles_analyzed": 5,
#   "entities_extracted": 47,
#   "sentiment_scores": [...],
#   "processing_time_seconds": 3.21
# }
```

**Verify results:**
```bash
# Check NLP results in database
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT title, sentiment_score, difficulty_score FROM articles WHERE source = 'semana' LIMIT 3;"
```

**Acceptable results:**
- ✅ Articles scraped successfully
- ✅ NLP processing completes without errors
- ✅ Results stored in database
- ⚠️ Some scrapers may fail (document which ones)

---

### Task 5.4: Create Troubleshooting Guide 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 5 minutes (automated)
**You do:** Review and add your observations
**Claude does:** Create template

**What Claude will create:**
```
backend/docs/TROUBLESHOOTING.md
```

**Content:**
- Common errors encountered during testing
- Solutions for each error
- Debug commands
- How to check logs
- How to reset state

**You add:**
- Any specific errors you encountered
- Your solutions that worked
- Environment-specific notes

---

## Phase 6: SSL/TLS Setup (Day 4 - 2-3 hours)

### Task 6.1: Acquire Domain Name 👤 **MANUAL**

**Status:** CRITICAL for public deployment
**Estimated Time:** 30 minutes - 24 hours (domain registration)

**Options:**

**Option A: Use existing domain**
- If you already have a domain, skip to Task 6.2

**Option B: Register new domain**
- Recommended registrars:
  - Namecheap (affordable, good UI)
  - Google Domains / Squarespace (premium)
  - Cloudflare (includes DDoS protection)

**Recommended domain structure:**
```
Primary: openlearn.co (or similar)
API subdomain: api.openlearn.co
Admin subdomain: admin.openlearn.co (optional)
```

**DNS Setup (after registration):**
```
A record:     openlearn.co          → <your-server-ip>
A record:     api.openlearn.co      → <your-server-ip>
CNAME record: www.openlearn.co      → openlearn.co
```

---

### Task 6.2: Point Domain to Server 👤 **MANUAL**

**Status:** CRITICAL for public deployment
**Estimated Time:** 5 minutes (plus DNS propagation 5 min - 24 hours)

**Steps:**

1. **Get your server IP:**
   ```bash
   # If deploying locally for testing:
   curl ifconfig.me
   # Output: 203.0.113.42 (example)

   # If using cloud provider (AWS, DigitalOcean, etc.):
   # Get IP from cloud console
   ```

2. **Configure DNS records:**
   - Log into your domain registrar
   - Navigate to DNS settings
   - Add A records:
     ```
     Type: A
     Name: @
     Value: <your-server-ip>
     TTL: 300 (5 minutes)

     Type: A
     Name: api
     Value: <your-server-ip>
     TTL: 300
     ```

3. **Verify DNS propagation:**
   ```bash
   # Wait 5-10 minutes, then test:
   nslookup api.openlearn.co

   # Should show:
   # Server: ...
   # Address: ...
   #
   # Name:    api.openlearn.co
   # Address: <your-server-ip>
   ```

**Note:** DNS propagation can take up to 24-48 hours, but usually 5-15 minutes.

---

### Task 6.3: Install Certbot 👤 **MANUAL**

**Status:** CRITICAL for public deployment
**Estimated Time:** 10 minutes

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

**On Windows (WSL):**
```bash
# Use Ubuntu WSL terminal
sudo apt update
sudo apt install certbot
```

**On macOS:**
```bash
brew install certbot
```

**Verify installation:**
```bash
certbot --version
# Should show: certbot 2.x.x
```

---

### Task 6.4: Stop Nginx Temporarily 👤 **MANUAL**

**Status:** Required for Let's Encrypt
**Estimated Time:** 1 minute

**Why:** Certbot needs port 80 free for domain validation

```bash
# If Nginx is running via Docker:
docker-compose -f docker-compose.production.yml stop nginx

# If Nginx is running as system service:
sudo systemctl stop nginx

# Verify port 80 is free:
sudo netstat -tulpn | grep :80
# Should show nothing
```

---

### Task 6.5: Acquire SSL Certificate 👤 **MANUAL**

**Status:** CRITICAL for public deployment
**Estimated Time:** 5-10 minutes

**Steps:**

```bash
# Option 1: Standalone mode (recommended for first time)
sudo certbot certonly --standalone -d api.openlearn.co -d openlearn.co

# Follow prompts:
# Enter email address: your-email@example.com
# Agree to terms: Y
# Share email with EFF: Y/N (your choice)

# Expected output:
# Congratulations! Your certificate and chain have been saved at:
# /etc/letsencrypt/live/api.openlearn.co/fullchain.pem
# Your key file has been saved at:
# /etc/letsencrypt/live/api.openlearn.co/privkey.pem
```

**Certificate files created:**
```
/etc/letsencrypt/live/api.openlearn.co/
├── fullchain.pem  (certificate + chain)
├── privkey.pem    (private key)
├── cert.pem       (certificate only)
└── chain.pem      (chain only)
```

**Verify certificates:**
```bash
sudo ls -la /etc/letsencrypt/live/api.openlearn.co/
# Should show 4 .pem files created today
```

---

### Task 6.6: Update Nginx Configuration for SSL 🔄 **COLLABORATIVE**

**Status:** CRITICAL for public deployment
**Estimated Time:** 15 minutes
**You do:** Review configuration
**Claude does:** Generate SSL-enabled nginx.conf

**What Claude will create:**
```
infrastructure/nginx/nginx-ssl.conf
```

**Configuration will include:**
- HTTPS listener on port 443
- HTTP to HTTPS redirect (port 80 → 443)
- SSL certificate paths
- Modern SSL configuration (TLS 1.2+, strong ciphers)
- Security headers (HSTS, CSP, etc.)
- Rate limiting
- Gzip/Brotli compression

**You must verify:**
- Certificate paths match your Let's Encrypt paths
- Domain names match your actual domains
- Backend upstream points to correct container

**Sample configuration:**
```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.openlearn.co openlearn.co;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.openlearn.co;

    ssl_certificate /etc/letsencrypt/live/api.openlearn.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.openlearn.co/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Backend proxy
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### Task 6.7: Update Docker Compose for SSL 🤖 **AUTOMATED**

**Status:** CRITICAL for public deployment
**Estimated Time:** 5 minutes (automated)
**You do:** Approve changes
**Claude does:** Update docker-compose.production.yml

**What will be updated:**
```yaml
nginx:
  image: nginx:alpine
  volumes:
    - ./infrastructure/nginx/nginx-ssl.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro  # ← SSL certificates
  ports:
    - "80:80"
    - "443:443"  # ← HTTPS port
```

---

### Task 6.8: Test SSL Configuration 👤 **MANUAL**

**Status:** CRITICAL for public deployment
**Estimated Time:** 10 minutes

**Steps:**

```bash
# 1. Restart Nginx with SSL config
docker-compose -f docker-compose.production.yml up -d nginx

# 2. Test HTTP to HTTPS redirect
curl -I http://api.openlearn.co/health
# Should show:
# HTTP/1.1 301 Moved Permanently
# Location: https://api.openlearn.co/health

# 3. Test HTTPS endpoint
curl https://api.openlearn.co/health
# Should show:
# {"status": "healthy", ...}

# 4. Test SSL certificate
openssl s_client -connect api.openlearn.co:443 -servername api.openlearn.co < /dev/null
# Should show:
# Certificate chain
# Server certificate
# subject=CN = api.openlearn.co
# issuer=C = US, O = Let's Encrypt, CN = R3
```

**Test in browser:**
```
1. Open: https://api.openlearn.co/health
2. Check for green padlock icon
3. Click padlock → View certificate
4. Verify:
   - Issued to: api.openlearn.co
   - Issued by: Let's Encrypt
   - Valid until: ~90 days from now
```

**SSL testing tools:**
```bash
# Use SSL Labs to test configuration:
# https://www.ssllabs.com/ssltest/analyze.html?d=api.openlearn.co

# Expected rating: A or A+
```

---

### Task 6.9: Setup SSL Certificate Auto-Renewal 👤 **MANUAL**

**Status:** HIGH PRIORITY
**Estimated Time:** 10 minutes

**Why:** Let's Encrypt certificates expire every 90 days

**Steps:**

```bash
# 1. Test renewal process (dry-run)
sudo certbot renew --dry-run

# Expected output:
# Congratulations, all simulated renewals succeeded:
#   /etc/letsencrypt/live/api.openlearn.co/fullchain.pem (success)

# 2. Setup automatic renewal (cron job)
sudo crontab -e

# Add this line (runs twice daily at 3:30am and 3:30pm):
30 3,15 * * * certbot renew --quiet --deploy-hook "docker-compose -f /path/to/docker-compose.production.yml restart nginx"

# Save and exit
```

**Verify cron job:**
```bash
sudo crontab -l
# Should show the certbot renew line
```

**Set calendar reminder:**
- Reminder in 80 days to verify auto-renewal worked
- Check certificate expiry date periodically

---

## Phase 7: Monitoring Setup (Day 5 - 4 hours)

### Task 7.1: Create Grafana Dashboards 🔄 **COLLABORATIVE**

**Status:** HIGH PRIORITY
**Estimated Time:** 2 hours
**You do:** Customize and test
**Claude does:** Generate dashboard JSON templates

**What Claude will create:**

1. **System Overview Dashboard**
   ```
   monitoring/grafana/dashboards/system-overview.json
   ```
   - HTTP request rate, latency, errors
   - Database connection pool status
   - Redis cache hit ratio
   - CPU, memory, disk usage

2. **Scraper Performance Dashboard**
   ```
   monitoring/grafana/dashboards/scraper-performance.json
   ```
   - Articles scraped per source
   - Scraper success/failure rates
   - Scraping duration by source
   - Error types and frequencies

3. **NLP Processing Dashboard**
   ```
   monitoring/grafana/dashboards/nlp-processing.json
   ```
   - Processing queue length
   - Documents processed per hour
   - Average processing time
   - Entity extraction counts

4. **Database Performance Dashboard**
   ```
   monitoring/grafana/dashboards/database-performance.json
   ```
   - Query duration percentiles (p50, p95, p99)
   - Slow query log
   - Connection pool saturation
   - Table sizes and growth

**You customize:**
- Alert thresholds (when to notify)
- Refresh intervals (5s, 10s, 1m, etc.)
- Time ranges (last 15m, 1h, 6h, 24h)
- Graph colors and layout

**Test dashboards:**
```bash
# 1. Access Grafana
# Open browser: http://localhost:3001
# Login: admin / <GRAFANA_PASSWORD from .env>

# 2. Navigate to Dashboards → Browse
# Should see 4 new dashboards

# 3. Open each dashboard and verify:
#    - Data is loading
#    - Graphs are rendering
#    - No "No data" errors
```

---

### Task 7.2: Configure Prometheus Alert Rules 🔄 **COLLABORATIVE**

**Status:** HIGH PRIORITY
**Estimated Time:** 1 hour
**You do:** Set thresholds
**Claude does:** Generate alert rules

**What Claude will create:**
```
monitoring/prometheus/alerts.yml
```

**Alert categories:**

1. **System Alerts:**
   - High CPU usage (>80% for 5 minutes)
   - High memory usage (>85% for 5 minutes)
   - Low disk space (<15% free)
   - Service down (health check failing)

2. **Application Alerts:**
   - High error rate (>5% for 5 minutes)
   - Slow response time (p95 >1s for 5 minutes)
   - Database connection pool exhausted
   - Redis connection failures

3. **Scraper Alerts:**
   - Scraper failure rate >20% for 1 hour
   - No articles scraped in 2 hours
   - Scraper timeout increase (>2x baseline)

4. **Data Quality Alerts:**
   - NLP processing queue backed up (>1000 items)
   - Duplicate article detection rate >10%

**Sample alert rule:**
```yaml
groups:
  - name: application_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"
```

**You configure:**
- Alert thresholds (when is it critical?)
- Alert duration (how long before firing?)
- Notification channels (email, Slack, PagerDuty)

---

### Task 7.3: Setup Sentry Error Tracking 👤 **MANUAL** (Optional)

**Status:** OPTIONAL (but highly recommended)
**Estimated Time:** 30 minutes

**Steps:**

1. **Create Sentry account:**
   - Go to: https://sentry.io/signup/
   - Choose free tier (5,000 errors/month)
   - Create organization and project

2. **Get DSN:**
   - After project creation, copy DSN
   - Format: `https://abc123@o123456.ingest.sentry.io/789012`

3. **Add to .env:**
   ```env
   SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/789012
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of requests
   ```

4. **Restart backend:**
   ```bash
   docker-compose -f docker-compose.production.yml restart api
   ```

5. **Test error tracking:**
   ```bash
   # Trigger a test error
   curl http://localhost:8000/api/v1/test-error

   # Check Sentry dashboard for captured error
   ```

**Benefits:**
- Real-time error alerts
- Stack traces with source code
- Error grouping and trends
- User impact analysis

**Alternative:** Can skip for initial deployment, add later

---

### Task 7.4: Configure Email/Slack Alerting 👤 **MANUAL** (Optional)

**Status:** OPTIONAL
**Estimated Time:** 30 minutes

**Option A: Email Alerts**

1. **Get SMTP credentials:**
   - Gmail: https://support.google.com/mail/answer/185833
   - SendGrid: https://sendgrid.com/free/
   - AWS SES: https://aws.amazon.com/ses/

2. **Add to .env:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_USE_TLS=true
   ALERT_EMAIL_FROM=alerts@openlearn.co
   ALERT_EMAIL_TO=your-email@gmail.com
   ```

**Option B: Slack Alerts**

1. **Create Slack webhook:**
   - Go to: https://api.slack.com/messaging/webhooks
   - Create webhook for your channel
   - Copy webhook URL

2. **Add to .env:**
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX
   SLACK_CHANNEL=#alerts
   ```

**Test alerting:**
```bash
# Restart services with new config
docker-compose -f docker-compose.production.yml restart api

# Trigger test alert
curl -X POST http://localhost:8000/api/v1/admin/test-alert

# Check email or Slack for test message
```

---

## Phase 8: Final Pre-Deployment (Day 6 - 2 hours)

### Task 8.1: Run Final Configuration Validation 🤖 **AUTOMATED**

**Status:** CRITICAL BLOCKER
**Estimated Time:** 5 minutes (automated)
**You do:** Review and fix any errors
**Claude does:** Run comprehensive validation

**What Claude will validate:**
```bash
# 1. Environment configuration
python scripts/validate_config.py --env production --strict

# 2. Database connectivity
python scripts/validate_database.py

# 3. Redis connectivity
python scripts/validate_redis.py

# 4. SSL certificate validity
python scripts/validate_ssl.py --domain api.openlearn.co

# 5. All services health
curl https://api.openlearn.co/health/ready
```

**Expected output:**
```
✅ Configuration validation: PASSED
✅ Database connectivity: PASSED
✅ Redis connectivity: PASSED
✅ SSL certificate: VALID (expires in 89 days)
✅ All health checks: HEALTHY

🎉 System ready for production deployment!
```

**If any validation fails:**
- Claude will provide specific fix instructions
- Must resolve before proceeding

---

### Task 8.2: Create Deployment Checklist 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 5 minutes (automated)
**You do:** Use for go/no-go decision
**Claude does:** Generate comprehensive checklist

**What Claude will create:**
```
backend/docs/DEPLOYMENT_CHECKLIST.md
```

**Checklist includes:**
- [ ] All environment variables configured
- [ ] SECRET_KEY is production-grade (64+ bytes)
- [ ] Database passwords are strong (32+ chars)
- [ ] SSL/TLS certificates installed and valid
- [ ] Health checks all return healthy
- [ ] Test suite passes with ≥85% coverage
- [ ] Monitoring dashboards configured
- [ ] Alert rules configured
- [ ] Backup strategy documented
- [ ] Rollback procedure documented
- [ ] All Docker services start successfully
- [ ] DNS points to correct server
- [ ] CORS origins configured for production
- [ ] DEBUG mode is False
- [ ] Sentry or error tracking configured
- [ ] Email/Slack alerting configured (optional)

**Usage:**
```bash
# Go through checklist item by item
# Mark each as complete
# Only deploy when ALL items checked
```

---

### Task 8.3: Create Backup & Rollback Procedures 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 10 minutes (automated)
**You do:** Review and test
**Claude does:** Generate procedures

**What Claude will create:**

1. **Backup Procedure:**
   ```
   backend/docs/BACKUP_PROCEDURE.md
   ```
   - Database backup commands
   - Redis persistence settings
   - Elasticsearch snapshot configuration
   - Backup schedule recommendations
   - Backup verification steps

2. **Rollback Procedure:**
   ```
   backend/docs/ROLLBACK_PROCEDURE.md
   ```
   - When to rollback (error rate, downtime, etc.)
   - Step-by-step rollback commands
   - How to restore from backup
   - Communication template
   - Post-rollback verification

**Example backup script:**
```bash
#!/bin/bash
# Automated daily backup

# Backup PostgreSQL
docker exec colombian_platform_db pg_dump -U colombian_user colombian_platform | \
  gzip > backup_$(date +%Y%m%d).sql.gz

# Backup Redis (already persists to disk)
docker exec colombian_platform_redis redis-cli SAVE

# Upload to S3 (optional)
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://openlearn-backups/

# Keep last 30 days
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

**You test:**
```bash
# Test backup
./scripts/backup.sh

# Test restore
./scripts/restore.sh backup_20251203.sql.gz
```

---

### Task 8.4: Document Known Issues & Limitations 🤖 **AUTOMATED**

**Status:** MEDIUM PRIORITY
**Estimated Time:** 10 minutes (automated)
**You do:** Add your observations
**Claude does:** Generate template

**What Claude will create:**
```
backend/docs/KNOWN_ISSUES.md
```

**Will document:**
1. **Incomplete Features (from Task 2.2):**
   - Email password reset not implemented
   - User timezone handling missing
   - Notification streak calculation placeholder
   - etc.

2. **Performance Limitations:**
   - Max concurrent scrapers: 13
   - Target: 10,000 articles/day (not load tested)
   - NLP processing: ~2s per article

3. **Testing Gaps:**
   - Exporter modules: 0% coverage
   - Notifier modules: 0% coverage
   - Security testing suite missing

4. **Infrastructure Notes:**
   - Single server deployment (no HA)
   - No automatic failover
   - Manual certificate renewal if cron fails

5. **Workarounds:**
   - For each issue, document temporary workaround
   - Link to GitHub issues (if using)

**You add:**
- Any issues you discovered during testing
- Browser compatibility notes
- Mobile app limitations (if applicable)

---

## Phase 9: Production Deployment (Day 7 - 1 hour)

### Task 9.1: Deploy Full Stack 👤 **MANUAL**

**Status:** CRITICAL - GO/NO-GO DECISION
**Estimated Time:** 10 minutes

**Pre-deployment checklist:**
```bash
# Review deployment checklist (Task 8.2)
cat backend/docs/DEPLOYMENT_CHECKLIST.md

# All items must be checked before proceeding
```

**If checklist complete, deploy:**

```bash
# Navigate to project root
cd /mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn

# Stop any running services
docker-compose -f docker-compose.production.yml down

# Pull latest images (if using registry)
docker-compose -f docker-compose.production.yml pull

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Expected output:
# Creating network "open_learn_colombian_network" ... done
# Creating volume "open_learn_postgres_data" ... done
# Creating volume "open_learn_redis_data" ... done
# Creating colombian_platform_db ... done
# Creating colombian_platform_redis ... done
# Creating colombian_platform_elasticsearch ... done
# Creating colombian_platform_api ... done
# Creating colombian_platform_worker ... done
# Creating colombian_platform_scheduler ... done
# Creating colombian_platform_nginx ... done
# Creating colombian_platform_prometheus ... done
# Creating colombian_platform_grafana ... done
```

**Monitor startup:**
```bash
# Watch service status
watch -n 2 docker-compose -f docker-compose.production.yml ps

# Wait for all services to show "Up (healthy)"
# This may take 1-3 minutes
```

---

### Task 9.2: Verify All Services Healthy 👤 **MANUAL**

**Status:** CRITICAL
**Estimated Time:** 10 minutes

**Check each service:**

```bash
# 1. PostgreSQL
docker exec colombian_platform_db pg_isready -U colombian_user
# Expected: /var/run/postgresql:5432 - accepting connections

# 2. Redis
docker exec colombian_platform_redis redis-cli ping
# Expected: PONG

# 3. Elasticsearch
curl http://localhost:9200/_cluster/health
# Expected: {"status":"green",...}

# 4. Backend API
curl https://api.openlearn.co/health
# Expected: {"status":"healthy",...}

# 5. Nginx
curl -I https://api.openlearn.co
# Expected: HTTP/2 200

# 6. Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# 7. Grafana
curl http://localhost:3001/api/health
# Expected: {"commit":"...","database":"ok",...}
```

**Check Docker logs for errors:**
```bash
# View logs for all services
docker-compose -f docker-compose.production.yml logs --tail=100

# View specific service logs
docker-compose -f docker-compose.production.yml logs api
docker-compose -f docker-compose.production.yml logs worker
docker-compose -f docker-compose.production.yml logs scheduler
```

**Acceptable:** No ERROR level messages, warnings are OK

---

### Task 9.3: Run Smoke Tests 👤 **MANUAL**

**Status:** CRITICAL
**Estimated Time:** 15 minutes

**Test core functionality:**

```bash
# 1. Test authentication (if implemented)
curl -X POST https://api.openlearn.co/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}'

# 2. Test manual scrape
curl -X POST https://api.openlearn.co/api/v1/scrape/manual \
  -H "Content-Type: application/json" \
  -d '{"source":"semana","limit":3}'

# 3. Test NLP analysis
curl -X POST https://api.openlearn.co/api/v1/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"source":"semana","limit":3}'

# 4. Test data retrieval
curl https://api.openlearn.co/api/v1/articles?limit=10

# 5. Test export (if implemented)
curl https://api.openlearn.co/api/v1/export/csv?source=semana

# 6. Test search (if Elasticsearch enabled)
curl https://api.openlearn.co/api/v1/search?q=colombia
```

**Expected:** All endpoints return 200 or 201, no 500 errors

---

### Task 9.4: Enable Scrapers One-by-One 👤 **MANUAL**

**Status:** HIGH PRIORITY
**Estimated Time:** 20 minutes

**Why:** Gradual rollout to monitor for issues

**Phase 1: Enable 3 high-priority scrapers (Day 1)**

```bash
# Access Django admin or API to enable scrapers
# OR manually trigger via API:

curl -X POST https://api.openlearn.co/api/v1/admin/scrapers/enable \
  -H "Content-Type: application/json" \
  -d '{
    "scrapers": ["semana", "eltiempo", "elespectador"]
  }'
```

**Monitor for 2-4 hours:**
```bash
# Watch Grafana scraper dashboard
# Check logs for errors:
docker-compose -f docker-compose.production.yml logs -f worker

# Check database for articles:
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT source, COUNT(*) FROM articles GROUP BY source;"
```

**Phase 2: Enable 5 more scrapers (Day 2)**

```bash
curl -X POST https://api.openlearn.co/api/v1/admin/scrapers/enable \
  -H "Content-Type: application/json" \
  -d '{
    "scrapers": ["portafolio", "elcolombiano", "elpais", "wradio", "bluradio"]
  }'
```

**Monitor for 4-8 hours:**
- Check scraper success rates
- Monitor error rates
- Review server resources (CPU, memory)

**Phase 3: Enable remaining scrapers (Day 3)**

```bash
# Enable all remaining scrapers
curl -X POST https://api.openlearn.co/api/v1/admin/scrapers/enable \
  -H "Content-Type: application/json" \
  -d '{
    "scrapers": ["elheraldo", "eluniversal", "vanguardia", "pulzo", "laopinion"]
  }'
```

**Final monitoring (24 hours):**
- All scrapers operational
- Articles being scraped continuously
- NLP processing keeping up
- No persistent errors

---

### Task 9.5: Configure Scheduler Jobs 👤 **MANUAL**

**Status:** HIGH PRIORITY
**Estimated Time:** 10 minutes

**Set up recurring jobs:**

```bash
# Access backend container
docker exec -it colombian_platform_api bash

# Configure scheduler (Python script or Django admin)
python manage.py shell

# In Python shell:
from app.services.scheduler import SchedulerService
scheduler = SchedulerService()

# Add scraping jobs for each source
scheduler.add_job(
    func='app.tasks.scrape_articles',
    args=['semana'],
    trigger='interval',
    minutes=15,  # High-priority: every 15 minutes
    id='scrape_semana',
    replace_existing=True
)

scheduler.add_job(
    func='app.tasks.scrape_articles',
    args=['eltiempo'],
    trigger='interval',
    minutes=15,
    id='scrape_eltiempo',
    replace_existing=True
)

# Medium-priority sources: every 30 minutes
scheduler.add_job(
    func='app.tasks.scrape_articles',
    args=['portafolio'],
    trigger='interval',
    minutes=30,
    id='scrape_portafolio',
    replace_existing=True
)

# Low-priority sources: every 60 minutes
scheduler.add_job(
    func='app.tasks.scrape_articles',
    args=['pulzo'],
    trigger='interval',
    minutes=60,
    id='scrape_pulzo',
    replace_existing=True
)

# Add NLP processing job
scheduler.add_job(
    func='app.tasks.process_nlp',
    trigger='interval',
    minutes=5,  # Process queue every 5 minutes
    id='nlp_processing',
    replace_existing=True
)

# Add cleanup job
scheduler.add_job(
    func='app.tasks.cleanup_old_data',
    trigger='cron',
    hour=3,  # 3 AM daily
    id='daily_cleanup',
    replace_existing=True
)

# Exit shell
exit()
```

**Verify jobs scheduled:**
```bash
# Check APScheduler jobs table
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT id, func, trigger FROM apscheduler_jobs ORDER BY id;"

# Should show all configured jobs
```

---

## Phase 10: Post-Deployment Monitoring (Day 8-14)

### Task 10.1: 24-Hour Monitoring 👤 **MANUAL**

**Status:** CRITICAL
**Estimated Time:** Periodic checks over 24 hours

**Monitoring checklist (every 2-4 hours):**

```bash
# 1. Check service status
docker-compose -f docker-compose.production.yml ps

# 2. Check health endpoints
curl https://api.openlearn.co/health

# 3. Review Grafana dashboards
# Open: http://localhost:3001
# Check:
# - System Overview: CPU, memory, requests/sec
# - Scraper Performance: Success rates, errors
# - Database Performance: Query times, connections
# - NLP Processing: Queue length, processing times

# 4. Check logs for errors
docker-compose -f docker-compose.production.yml logs --tail=100 | grep ERROR

# 5. Verify articles being scraped
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT COUNT(*), MAX(created_at) FROM articles;"

# 6. Check disk space
df -h
# Ensure database volume has >20% free

# 7. Check memory usage
free -h
# Ensure <85% used

# 8. Check certificate expiry
openssl s_client -connect api.openlearn.co:443 -servername api.openlearn.co < /dev/null 2>/dev/null | \
  openssl x509 -noout -dates
```

**Set alerts on phone:**
- Every 4 hours: Check Grafana
- If Sentry configured: Email/Slack alerts automatically

**Red flags (investigate immediately):**
- ❌ Any service showing "unhealthy"
- ❌ Error rate >5%
- ❌ Response time p95 >2s
- ❌ Disk space <15%
- ❌ Memory usage >90%
- ❌ No articles scraped in 2+ hours

---

### Task 10.2: Create Incident Response Runbook 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 10 minutes (automated)
**You do:** Add contact info
**Claude does:** Generate runbook template

**What Claude will create:**
```
backend/docs/INCIDENT_RESPONSE.md
```

**Will include:**

1. **Incident Severity Levels:**
   - P0: Complete outage (resolve in 1 hour)
   - P1: Partial outage (resolve in 4 hours)
   - P2: Degraded performance (resolve in 24 hours)
   - P3: Minor issues (resolve in 1 week)

2. **Common Incidents & Solutions:**
   - Database connection pool exhausted
   - Redis out of memory
   - Scraper repeatedly failing
   - Disk space full
   - SSL certificate expired
   - High response times
   - Memory leak

3. **Escalation Process:**
   - Who to contact
   - When to escalate
   - Communication templates

4. **Recovery Procedures:**
   - Restart services
   - Rollback deployment
   - Restore from backup
   - Scale resources

**You add:**
- Contact information (phone, email, Slack)
- On-call rotation (if applicable)
- Stakeholder notification list

---

### Task 10.3: Performance Tuning 🔄 **COLLABORATIVE**

**Status:** MEDIUM PRIORITY
**Estimated Time:** 2-4 hours (spread over days 8-14)
**You do:** Analyze metrics, decide on changes
**Claude does:** Implement configuration changes

**Week 1 Performance Analysis:**

**Day 8-9: Identify bottlenecks**
```bash
# 1. Database slow queries
docker exec -it colombian_platform_db psql -U colombian_user -d colombian_platform \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 2. Redis cache hit ratio
docker exec -it colombian_platform_redis redis-cli INFO stats | grep keyspace

# 3. Scraper performance
# Review Grafana scraper dashboard
# Identify slowest scrapers

# 4. NLP processing queue
# Check queue length in Grafana
# If backed up (>100 items), increase workers
```

**Day 10-11: Optimize based on findings**

**Option A: Database optimization (if slow queries found)**

Claude will:
```sql
-- Add missing indexes
CREATE INDEX idx_articles_source_created ON articles(source, created_at);
CREATE INDEX idx_articles_published_date ON articles(published_date);
CREATE INDEX idx_vocabulary_word ON vocabulary(word);

-- Analyze tables
ANALYZE articles;
ANALYZE vocabulary;
```

**Option B: Increase connection pool (if connections maxed)**

You configure in `.env`:
```env
DATABASE_POOL_SIZE=20  # Increase from 10
DATABASE_MAX_OVERFLOW=10  # Increase from 5
```

**Option C: Redis memory optimization (if cache full)**

You configure in `.env`:
```env
REDIS_MAXMEMORY=2gb  # Increase from 1gb
REDIS_MAXMEMORY_POLICY=allkeys-lru  # Evict least recently used
```

**Option D: Scale NLP workers (if queue backed up)**

Update `docker-compose.production.yml`:
```yaml
worker:
  # Scale up workers
  deploy:
    replicas: 4  # Increase from 1
```

**Day 12-14: Monitor improvements**
- Re-run performance analysis
- Compare metrics before/after
- Document optimizations made

---

### Task 10.4: User Acceptance Testing 👤 **MANUAL** (Optional)

**Status:** OPTIONAL
**Estimated Time:** Variable (depends on user base)

**If you have beta users:**

1. **Create test user accounts:**
   ```bash
   # Access Django admin or create via API
   curl -X POST https://api.openlearn.co/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "beta-user@example.com",
       "password": "SecurePassword123!",
       "role": "beta_tester"
     }'
   ```

2. **Provide access:**
   - Send beta users the frontend URL
   - Provide test credentials
   - Share feedback form/survey

3. **Collect feedback:**
   - Feature requests
   - Bug reports
   - Usability issues
   - Performance complaints

4. **Prioritize fixes:**
   - Critical bugs: Fix immediately
   - High-priority features: Sprint planning
   - Low-priority: Backlog

---

## Phase 11: Documentation Finalization (Ongoing)

### Task 11.1: Update README with Deployment Info 🤖 **AUTOMATED**

**Status:** MEDIUM PRIORITY
**Estimated Time:** 5 minutes (automated)
**You do:** Review accuracy
**Claude does:** Update README.md

**What will be updated:**
- Production URL (https://api.openlearn.co)
- Deployment status badge (✅ Deployed)
- Actual test coverage (from pytest run)
- Link to production deployment guide
- Known limitations section

---

### Task 11.2: Create CHANGELOG 🤖 **AUTOMATED**

**Status:** MEDIUM PRIORITY
**Estimated Time:** 10 minutes (automated)
**You do:** Review and add notes
**Claude does:** Generate initial CHANGELOG.md

**What Claude will create:**
```
CHANGELOG.md
```

**Initial entry:**
```markdown
# Changelog

## [1.0.0] - 2025-12-03

### Added
- Initial production deployment
- 13 news source scrapers implemented
- 7 government API clients
- Colombian Spanish NLP pipeline
- PostgreSQL, Redis, Elasticsearch infrastructure
- Prometheus + Grafana monitoring
- SSL/TLS encryption
- APScheduler for recurring tasks

### Security
- SECRET_KEY generated (64 bytes)
- Database password secured (32 bytes)
- CORS configured for production
- Security headers enabled
- Let's Encrypt SSL certificate

### Known Issues
- Email password reset not implemented
- User timezone handling missing
- Test coverage at 45% (target 85%)
- Exporter modules not tested
```

**You add:**
- Specific version numbers
- Breaking changes (if any)
- Migration notes (if applicable)

---

### Task 11.3: Create Production Runbook 🤖 **AUTOMATED**

**Status:** HIGH PRIORITY
**Estimated Time:** 15 minutes (automated)
**You do:** Add environment-specific notes
**Claude does:** Generate comprehensive runbook

**What Claude will create:**
```
backend/docs/PRODUCTION_RUNBOOK.md
```

**Will include:**

1. **Daily Operations:**
   - Morning health check routine
   - Log review process
   - Metrics review process
   - Backup verification

2. **Weekly Operations:**
   - Performance review
   - Security updates check
   - Disk space cleanup
   - Certificate expiry check

3. **Monthly Operations:**
   - Full security audit
   - Dependency updates
   - Backup restore test
   - Disaster recovery drill

4. **Maintenance Windows:**
   - When to schedule (low-traffic hours)
   - Communication template
   - Pre-maintenance checklist
   - Post-maintenance verification

5. **Common Tasks:**
   - Restart services
   - Clear caches
   - Add new scraper
   - Update environment variable
   - Rotate secrets
   - Scale resources

**You add:**
- Your organization's maintenance schedule
- Stakeholder notification procedures
- Environment-specific commands

---

## Summary: Time & Effort Estimates

### Total Time by Phase

| Phase | Description | Automated | Manual | Total |
|-------|-------------|-----------|--------|-------|
| **Phase 1** | Critical Fixes | 10 min | 45 min | 55 min |
| **Phase 2** | Code Fixes | 15 min | 10 min | 25 min |
| **Phase 3** | Dependencies | 5 min | 60 min | 65 min |
| **Phase 4** | Database Setup | 7 min | 10 min | 17 min |
| **Phase 5** | Testing | 5 min | 40 min | 45 min |
| **Phase 6** | SSL/TLS Setup | 20 min | 90 min | 110 min |
| **Phase 7** | Monitoring | 120 min | 60 min | 180 min |
| **Phase 8** | Pre-Deployment | 30 min | 30 min | 60 min |
| **Phase 9** | Deployment | 0 min | 60 min | 60 min |
| **Phase 10** | Post-Deploy | 10 min | 240 min | 250 min |
| **Phase 11** | Documentation | 30 min | 30 min | 60 min |
| **TOTAL** | **~4 hours** | **~12 hours** | **~16 hours** |

### Deployment Timeline

**Fast Track (1 week):**
- Day 1-2: Phases 1-4 (Configuration & Setup)
- Day 3-4: Phases 5-6 (Testing & SSL)
- Day 5-6: Phases 7-8 (Monitoring & Pre-deploy)
- Day 7: Phase 9 (Deployment)
- Week 2: Phase 10 (Monitoring)

**Recommended (1.5-2 weeks):**
- Week 1: Phases 1-8 (thorough testing)
- Week 2: Phases 9-11 (deployment + monitoring)

### Next Steps

**Start here:**
1. Review this entire walkthrough
2. Block calendar time for each phase
3. Begin with Phase 1, Task 1.1 (Redis fix)
4. Work through sequentially
5. Don't skip validation steps

**Ready to begin?**
```bash
# Claude will start with automated tasks when you approve
# You handle manual tasks as they come up
# We'll work through this together
```

---

**Document Version:** 1.0
**Last Updated:** December 3, 2025
**Status:** Ready for execution
**Estimated Completion:** 1.5-2 weeks from start
