# OpenLearn Platform - Production Deployment Checklist

**Version:** 1.0
**Last Updated:** 2025-10-03
**Target Environment:** Production

---

## Pre-Flight Checklist (Before Any Deployment)

### ✅ Code Quality
- [ ] All tests passing (`pytest backend/tests/ -v`)
- [ ] Test coverage ≥ 85% (`pytest --cov-report=html`)
- [ ] No linting errors (`black . && flake8`)
- [ ] All TODO/FIXME addressed in critical paths
- [ ] Code reviewed and approved
- [ ] CHANGELOG.md updated

### ✅ Security Audit
- [ ] SECRET_KEY changed from default
- [ ] DEBUG=False in production
- [ ] No hardcoded credentials
- [ ] CORS origins configured for production domains
- [ ] All dependencies up to date (`pip list --outdated`)
- [ ] Security scan completed (`bandit -r backend/`)
- [ ] Vulnerability scan passed (`safety check`)

### ✅ Dependencies Installed
```bash
# Python environment
- [ ] Python 3.12+ installed
- [ ] Virtual environment created
- [ ] pip install -r requirements.txt
- [ ] pip install -r requirements-dev.txt (for testing)
- [ ] python -m spacy download es_core_news_lg

# System dependencies
- [ ] PostgreSQL 15+ installed and running
- [ ] Redis 7+ installed and running
- [ ] Elasticsearch 8+ installed and running
```

### ✅ Database Setup
- [ ] Production database created
- [ ] Database user created with appropriate permissions
- [ ] Migrations run (`alembic upgrade head`)
- [ ] APScheduler tables created
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] Indexes created for performance

---

## Critical Fixes (MUST DO BEFORE PRODUCTION)

### 🔴 Priority 1: Health Checks (BLOCKING)

**Issue:** Health checks return placeholders instead of real status

**Location:** `backend/app/api/monitoring.py`

**Fix Required:**
```python
# Replace placeholder health checks with real implementations

async def check_database() -> bool:
    """Check PostgreSQL connectivity"""
    try:
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        from app.cache import redis_client
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

async def check_elasticsearch() -> bool:
    """Check Elasticsearch connectivity"""
    try:
        from app.search import es_client
        await es_client.ping()
        return True
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return False
```

**Verification:**
```bash
curl http://localhost:8000/health/ready
# Should return actual dependency status
```

- [ ] Database health check implemented
- [ ] Redis health check implemented
- [ ] Elasticsearch health check implemented
- [ ] Health checks tested with dependencies down
- [ ] Health checks tested with dependencies up

### 🔴 Priority 2: Environment Configuration

**Create production .env file:**
```bash
cp backend/.env.example backend/.env
```

**Required changes:**
```bash
# Application
APP_NAME="Colombia Intel Platform"
DEBUG=False  # CRITICAL: Must be False
ENVIRONMENT=production

# Security
SECRET_KEY=[GENERATE 32+ CHAR RANDOM KEY]
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Database
DATABASE_URL=postgresql://[user]:[password]@[host]:5432/[database]

# Cache
REDIS_URL=redis://:[password]@[host]:6379/0

# Search
ELASTICSEARCH_URL=http://[host]:9200
ELASTICSEARCH_INDEX=colombia_content

# CORS
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Monitoring
METRICS_ENABLED=True
SENTRY_DSN=https://[your-sentry-dsn]
SENTRY_ENVIRONMENT=production

# Alerting
SMTP_HOST=[smtp-server]
SMTP_PORT=587
SMTP_USER=[email]
SMTP_PASSWORD=[password]
ALERT_EMAIL_TO=alerts@yourdomain.com
SLACK_WEBHOOK_URL=[webhook-url]
```

**Checklist:**
- [ ] .env file created from template
- [ ] SECRET_KEY generated and set
- [ ] DEBUG=False verified
- [ ] DATABASE_URL configured
- [ ] REDIS_URL configured
- [ ] ELASTICSEARCH_URL configured
- [ ] CORS_ORIGINS set to production domains only
- [ ] Monitoring credentials configured
- [ ] Alert channels configured

### 🔴 Priority 3: APScheduler PostgreSQL Persistence

**Issue:** Scheduler uses in-memory storage, jobs lost on restart

**Location:** `backend/app/config/scheduler_config.py`

**Fix Required:**
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os

SCHEDULER_CONFIG = {
    'jobstores': {
        'default': SQLAlchemyJobStore(
            url=os.getenv('DATABASE_URL')
        )
    },
    'executors': {
        'default': {'type': 'threadpool', 'max_workers': 10}
    },
    'job_defaults': {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    },
    'timezone': 'America/Bogota'
}
```

**Database Migration:**
```sql
-- APScheduler requires this table
CREATE TABLE IF NOT EXISTS apscheduler_jobs (
    id VARCHAR(191) PRIMARY KEY,
    next_run_time DOUBLE PRECISION,
    job_state BYTEA NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_apscheduler_jobs_next_run_time
ON apscheduler_jobs(next_run_time);
```

**Checklist:**
- [ ] Scheduler config updated to use PostgreSQL
- [ ] Database migration created for apscheduler_jobs table
- [ ] Migration run and verified
- [ ] Scheduler tested with restart (jobs should persist)
- [ ] Job recovery verified after simulated crash

---

## Infrastructure Setup

### 🔧 Production Server Setup

**System Requirements:**
- [ ] Linux server (Ubuntu 22.04 LTS recommended)
- [ ] 4+ CPU cores
- [ ] 8+ GB RAM
- [ ] 100+ GB SSD storage
- [ ] Firewall configured (ports 80, 443 open)

**Services Installation:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql-15 postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Install Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update && sudo apt install elasticsearch -y
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip -y

# Install Nginx (reverse proxy)
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

**Checklist:**
- [ ] Server provisioned
- [ ] PostgreSQL installed and running
- [ ] Redis installed and running
- [ ] Elasticsearch installed and running
- [ ] Python 3.12+ installed
- [ ] Nginx installed and configured
- [ ] Firewall rules configured
- [ ] SSL certificate obtained (Let's Encrypt)

### 🌐 Nginx Configuration

**Create:** `/etc/nginx/sites-available/openlearn`

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint (for load balancer)
    location /health/live {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health/live;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        allow 10.0.0.0/8;  # Internal network
        deny all;
        proxy_pass http://127.0.0.1:8000/metrics;
    }
}
```

**Checklist:**
- [ ] Nginx config file created
- [ ] SSL certificate obtained
- [ ] Config file symlinked to sites-enabled
- [ ] Nginx configuration tested (`nginx -t`)
- [ ] Nginx reloaded (`systemctl reload nginx`)
- [ ] HTTPS working correctly
- [ ] HTTP redirects to HTTPS

---

## Application Deployment

### 📦 Deploy Application Code

```bash
# Create application user
sudo useradd -m -s /bin/bash openlearn
sudo su - openlearn

# Clone repository (or copy files)
git clone https://github.com/your-org/openlearn.git
cd openlearn

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Download NLP model
python -m spacy download es_core_news_lg

# Set up environment
cp backend/.env.example backend/.env
# Edit .env with production values

# Create log directory
mkdir -p /var/log/openlearn
sudo chown openlearn:openlearn /var/log/openlearn

# Run database migrations
cd backend
alembic upgrade head

# Test application
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Checklist:**
- [ ] Application user created
- [ ] Code deployed to server
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] spaCy model downloaded
- [ ] .env file configured
- [ ] Log directory created with permissions
- [ ] Database migrations run successfully
- [ ] Application starts without errors

### 🔄 Systemd Service Setup

**Create:** `/etc/systemd/system/openlearn-api.service`

```ini
[Unit]
Description=OpenLearn API Service
After=network.target postgresql.service redis.service elasticsearch.service

[Service]
Type=notify
User=openlearn
Group=openlearn
WorkingDirectory=/home/openlearn/openlearn/backend
Environment="PATH=/home/openlearn/openlearn/venv/bin"
ExecStart=/home/openlearn/openlearn/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/openlearn

[Install]
WantedBy=multi-user.target
```

**Create:** `/etc/systemd/system/openlearn-scheduler.service`

```ini
[Unit]
Description=OpenLearn Scheduler Service
After=network.target postgresql.service openlearn-api.service

[Service]
Type=simple
User=openlearn
Group=openlearn
WorkingDirectory=/home/openlearn/openlearn/backend
Environment="PATH=/home/openlearn/openlearn/venv/bin"
ExecStart=/home/openlearn/openlearn/venv/bin/python -m app.services.scheduler

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Checklist:**
- [ ] API service file created
- [ ] Scheduler service file created
- [ ] Systemd daemon reloaded (`systemctl daemon-reload`)
- [ ] API service enabled (`systemctl enable openlearn-api`)
- [ ] Scheduler service enabled (`systemctl enable openlearn-scheduler`)
- [ ] API service started (`systemctl start openlearn-api`)
- [ ] Scheduler service started (`systemctl start openlearn-scheduler`)
- [ ] Services running (`systemctl status openlearn-*`)

---

## Monitoring & Observability

### 📊 Prometheus Setup

**Install Prometheus:**
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus
```

**Configuration:** `/opt/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'openlearn-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Checklist:**
- [ ] Prometheus installed
- [ ] Configuration file created
- [ ] Prometheus service created and started
- [ ] Metrics endpoint accessible
- [ ] Prometheus scraping metrics successfully
- [ ] Retention configured (default 15 days)

### 📈 Grafana Setup

**Install Grafana:**
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

**Initial Setup:**
- [ ] Grafana installed and running (port 3000)
- [ ] Admin password changed from default
- [ ] Prometheus data source added
- [ ] Dashboard created for API metrics
- [ ] Dashboard created for scraper metrics
- [ ] Dashboard created for system resources
- [ ] Alert rules configured
- [ ] Notification channels configured (email/Slack)

### 🐛 Sentry Setup

**Install Sentry SDK:**
```bash
pip install sentry-sdk[fastapi]
```

**Initialize in `app/main.py`:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0')),
        integrations=[FastApiIntegration()],
    )
```

**Checklist:**
- [ ] Sentry project created
- [ ] DSN added to .env
- [ ] SDK initialized in application
- [ ] Test error sent to verify integration
- [ ] Alert rules configured
- [ ] Team notifications set up

---

## Post-Deployment Validation

### ✅ Smoke Tests

**Health Checks:**
```bash
# Liveness probe
curl https://api.yourdomain.com/health/live
# Expected: {"status": "healthy", "timestamp": "..."}

# Readiness probe
curl https://api.yourdomain.com/health/ready
# Expected: {"status": "healthy", "checks": {"database": true, "redis": true, "elasticsearch": true}}

# Detailed health
curl https://api.yourdomain.com/health
# Expected: Full health status with all dependencies
```

**API Endpoints:**
```bash
# API documentation
curl https://api.yourdomain.com/docs
# Expected: Swagger UI

# Scraping endpoints
curl https://api.yourdomain.com/api/scraping/status
# Expected: Scraper status information

# Analysis endpoints
curl https://api.yourdomain.com/api/analysis/trends
# Expected: Trend data or empty array
```

**Checklist:**
- [ ] All health endpoints return 200
- [ ] Health checks show all dependencies healthy
- [ ] API documentation accessible
- [ ] Test scraper run successful
- [ ] Database queries working
- [ ] Redis cache working
- [ ] Elasticsearch indexing working
- [ ] Scheduler jobs running
- [ ] Logs being written correctly
- [ ] Metrics being collected

### 📊 Performance Tests

**Load Testing with Apache Bench:**
```bash
# Test API endpoint
ab -n 1000 -c 10 https://api.yourdomain.com/health/live
# Expected: <500ms average, <1% errors

# Test with authentication
ab -n 100 -c 5 -H "Authorization: Bearer TOKEN" https://api.yourdomain.com/api/scraping/status
```

**Checklist:**
- [ ] Response time p95 < 500ms
- [ ] Error rate < 1%
- [ ] Server handles expected load
- [ ] Database connections stable
- [ ] Memory usage acceptable
- [ ] CPU usage acceptable

### 🔐 Security Validation

**Security Checklist:**
- [ ] HTTPS enforced (HTTP redirects)
- [ ] Security headers present (HSTS, X-Frame-Options, etc.)
- [ ] CORS configured correctly
- [ ] No debug information leaked in errors
- [ ] No sensitive data in logs
- [ ] API rate limiting working (if implemented)
- [ ] Authentication required for protected endpoints
- [ ] SQL injection tests passed
- [ ] XSS tests passed

---

## Rollback Procedure

### 🔙 Emergency Rollback

**If critical issues occur post-deployment:**

1. **Stop new traffic:**
   ```bash
   sudo systemctl stop openlearn-api
   sudo systemctl stop openlearn-scheduler
   ```

2. **Restore previous version:**
   ```bash
   cd /home/openlearn/openlearn
   git checkout [previous-stable-tag]
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Rollback database (if needed):**
   ```bash
   cd backend
   alembic downgrade -1  # or specific revision
   ```

4. **Restart services:**
   ```bash
   sudo systemctl start openlearn-api
   sudo systemctl start openlearn-scheduler
   ```

5. **Verify rollback:**
   ```bash
   curl https://api.yourdomain.com/health
   ```

**Checklist:**
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging
- [ ] Database backup exists before deployment
- [ ] Previous version tagged in git
- [ ] Team notified of rollback
- [ ] Post-mortem scheduled

---

## Sign-Off

### Pre-Deployment Sign-Off

**Technical Lead:**
- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Security audit completed
- [ ] Performance acceptable

**DevOps Lead:**
- [ ] Infrastructure ready
- [ ] Monitoring configured
- [ ] Backup systems tested
- [ ] Rollback plan verified

**Product Owner:**
- [ ] Features validated
- [ ] Acceptance criteria met
- [ ] Business requirements satisfied

### Post-Deployment Sign-Off

**Technical Lead:**
- [ ] All smoke tests passed
- [ ] No errors in logs
- [ ] Metrics looking normal
- [ ] Scheduler running correctly

**DevOps Lead:**
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Backups running
- [ ] Services stable

**Product Owner:**
- [ ] User acceptance testing passed
- [ ] Critical features working
- [ ] Ready for announcement

---

## Quick Reference

### Useful Commands

```bash
# View API logs
sudo journalctl -u openlearn-api -f

# View scheduler logs
sudo journalctl -u openlearn-scheduler -f

# Restart API
sudo systemctl restart openlearn-api

# Restart scheduler
sudo systemctl restart openlearn-scheduler

# Check service status
sudo systemctl status openlearn-api openlearn-scheduler

# Database backup
pg_dump -U openlearn_user openlearn_db > backup_$(date +%Y%m%d).sql

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Emergency Contacts

- **Technical Lead:** [contact info]
- **DevOps Lead:** [contact info]
- **Database Admin:** [contact info]
- **On-Call:** [contact info]

---

**Deployment Checklist Version:** 1.0
**Last Updated:** 2025-10-03
**Next Review:** [Schedule quarterly review]
