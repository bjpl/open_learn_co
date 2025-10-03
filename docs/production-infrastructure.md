# Production Infrastructure Design
## OpenLearn Platform - Colombia Intelligence & Language Learning

**Version:** 1.0.0
**Date:** October 2025
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#overview)
2. [APScheduler Integration](#apscheduler-integration)
3. [Logging Infrastructure](#logging-infrastructure)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Error Handling & Recovery](#error-handling--recovery)
6. [Production Deployment Strategy](#production-deployment-strategy)
7. [Security Hardening](#security-hardening)
8. [Scaling Strategy](#scaling-strategy)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Architecture Principles

- **High Availability**: 99.9% uptime target
- **Scalability**: Horizontal scaling for scrapers and API
- **Observability**: Comprehensive logging, metrics, and tracing
- **Resilience**: Automatic recovery from failures
- **Security**: Zero-trust architecture with defense in depth

### Technology Stack

- **Application**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ (async)
- **Cache**: Redis 7+
- **Search**: Elasticsearch 8+
- **Task Queue**: APScheduler 3.10+ (persistent jobstore)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured JSON logs → ELK Stack / CloudWatch
- **Tracing**: OpenTelemetry

---

## APScheduler Integration

### Design Philosophy

APScheduler provides lightweight, persistent background job scheduling without requiring external workers like Celery. Perfect for medium-scale scraping operations with predictable schedules.

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │          APScheduler Singleton                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │ PostgreSQL   │  │  Executor    │  │ Triggers │ │    │
│  │  │  JobStore    │  │  (ThreadPool)│  │ (Cron)   │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Scraping Jobs                          │    │
│  │  • High Priority: Every 15 min                      │    │
│  │  • Medium Priority: Every 30 min                    │    │
│  │  • Low Priority: Every 60 min                       │    │
│  │  • Daily Analytics: 2:00 AM                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Details

#### 1. Scheduler Configuration (`backend/app/services/scheduler_config.py`)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import timezone

SCHEDULER_CONFIG = {
    'jobstores': {
        'default': SQLAlchemyJobStore(
            url='postgresql://user:pass@localhost:5432/colombia_jobs',
            tablename='apscheduler_jobs'
        )
    },
    'executors': {
        'default': ThreadPoolExecutor(max_workers=10),
        'scrapers': ThreadPoolExecutor(max_workers=5)
    },
    'job_defaults': {
        'coalesce': True,  # Combine multiple missed executions
        'max_instances': 1,  # Prevent concurrent job instances
        'misfire_grace_time': 300,  # 5 minutes grace for missed jobs
        'replace_existing': True
    },
    'timezone': timezone('America/Bogota')  # Colombia timezone
}
```

#### 2. Job Definitions

**High Priority Sources** (Every 15 minutes)
- El Tiempo
- El Espectador
- Semana
- Portafolio

**Medium Priority Sources** (Every 30 minutes)
- Regional news sources
- Government sources (DANE, Banco de la República)

**Low Priority Sources** (Every 60 minutes)
- Academic sources
- Long-form content

**Scheduled Analytics Jobs**
- Daily content analysis: 2:00 AM
- Weekly trend aggregation: Sunday 3:00 AM
- Monthly reports: 1st of month, 4:00 AM

#### 3. Job Persistence & Recovery

**Features:**
- Jobs stored in PostgreSQL `apscheduler_jobs` table
- Automatic recovery after application restart
- Missed job detection and execution
- Job history tracking

**Recovery Strategy:**
```python
# On application startup
1. Load persisted jobs from database
2. Check for missed executions during downtime
3. Execute missed jobs based on misfire_grace_time
4. Resume normal schedule
```

#### 4. Concurrency Management

**Strategies:**
- **Job-level concurrency**: `max_instances=1` prevents duplicate runs
- **Executor pools**: Separate pools for different job types
- **Rate limiting**: Per-scraper rate limits via Redis
- **Database connection pooling**: Async pool with max 20 connections

#### 5. Error Handling & Retries

**Retry Strategy:**
```python
from apscheduler.triggers.interval import IntervalTrigger

scheduler.add_job(
    scrape_source,
    trigger='cron',
    minute='*/15',
    args=['El Tiempo'],
    max_instances=1,
    retry_policy={
        'max_attempts': 3,
        'backoff_factor': 2,  # 2^n seconds
        'exceptions': [HTTPError, Timeout]
    }
)
```

**Failure Actions:**
- Log error to structured logging
- Send alert to monitoring system
- Store failure in `scraping_failures` table
- Attempt retry according to policy
- Escalate to admin after max retries

### Job Registration Example

```python
from app.services.scheduler_service import scheduler
from scrapers.sources.media.el_tiempo import ElTiempoScraper

# High priority: Every 15 minutes
scheduler.add_job(
    id='scrape_el_tiempo',
    func=scrape_source_job,
    trigger='cron',
    minute='*/15',
    args=['El Tiempo', ElTiempoScraper],
    executor='scrapers',
    max_instances=1,
    replace_existing=True
)

# Daily analytics
scheduler.add_job(
    id='daily_analytics',
    func=run_daily_analytics,
    trigger='cron',
    hour=2,
    minute=0,
    executor='default',
    max_instances=1
)
```

---

## Logging Infrastructure

### Architecture Design

```
┌──────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  FastAPI   │  │  Scrapers  │  │  Workers   │            │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│         │                │                │                   │
│         └────────────────┴────────────────┘                   │
│                          │                                     │
│              ┌───────────▼───────────┐                        │
│              │  Structured Logger    │                        │
│              │  (Python logging +    │                        │
│              │   structlog)          │                        │
│              └───────────┬───────────┘                        │
└──────────────────────────┼───────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Log Aggregation       │
              │  • File rotation        │
              │  • ELK Stack (optional) │
              │  • CloudWatch (AWS)     │
              │  • GCP Logging          │
              └─────────────────────────┘
```

### Structured Logging Format (JSON)

**Standard Log Entry:**
```json
{
  "timestamp": "2025-10-02T12:34:56.789Z",
  "level": "INFO",
  "logger": "app.api.scraping",
  "message": "Scraping completed successfully",
  "context": {
    "source": "El Tiempo",
    "scraper": "ElTiempoScraper",
    "articles_scraped": 25,
    "duration_ms": 3421,
    "job_id": "scrape_el_tiempo",
    "success": true
  },
  "trace_id": "7f3d9a8b-1c2e-4f5a-9b3c-1a2b3c4d5e6f",
  "span_id": "a1b2c3d4e5f6",
  "user_id": null,
  "ip_address": "192.168.1.100",
  "environment": "production",
  "version": "1.0.0",
  "hostname": "web-server-01"
}
```

### Log Levels & Categories

**Levels:**
- **DEBUG**: Development debugging (disabled in production)
- **INFO**: Normal operations (scraping success, job completion)
- **WARNING**: Concerning but non-critical (rate limit approached, slow response)
- **ERROR**: Errors requiring attention (scraping failure, API error)
- **CRITICAL**: System-threatening issues (database connection lost, disk full)

**Categories:**
```python
LOGGERS = {
    'app.api': 'INFO',
    'app.scrapers': 'INFO',
    'app.nlp': 'WARNING',
    'app.database': 'WARNING',
    'app.scheduler': 'INFO',
    'app.security': 'WARNING',
    'app.performance': 'INFO'
}
```

### Log Configuration (`backend/app/core/logging_config.py`)

```python
import logging
import structlog
from pythonjsonlogger import jsonlogger

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# JSON formatter for standard logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['hostname'] = socket.gethostname()
        log_record['version'] = '1.0.0'
```

### Log Rotation & Retention

**File-based Logging:**
```python
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Application logs - rotate daily, keep 30 days
app_handler = TimedRotatingFileHandler(
    filename='/var/log/openlearn/app.log',
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)

# Error logs - rotate by size, keep 10 files
error_handler = RotatingFileHandler(
    filename='/var/log/openlearn/error.log',
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=10,
    encoding='utf-8'
)

# Scraping logs - separate file, rotate daily
scraping_handler = TimedRotatingFileHandler(
    filename='/var/log/openlearn/scraping.log',
    when='midnight',
    interval=1,
    backupCount=60  # Keep 60 days for analytics
)
```

**Retention Policy:**
- Application logs: 30 days
- Error logs: 90 days
- Scraping logs: 60 days
- Security logs: 365 days
- Audit logs: 7 years (regulatory compliance)

### Centralized Logging (Optional)

**Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)**
```yaml
# docker-compose.elk.yml
services:
  elasticsearch:
    image: elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - elk_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.10.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

**Option 2: Cloud Logging**
- **AWS CloudWatch**: Automatic log ingestion via CloudWatch Logs agent
- **GCP Cloud Logging**: Stackdriver integration
- **Azure Monitor**: Application Insights

---

## Monitoring & Alerting

### Health Check System

#### 1. Health Check Endpoints

**Liveness Probe** (`/health/live`):
```python
@router.get("/health/live")
async def liveness_check():
    """Check if application is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Readiness Probe** (`/health/ready`):
```python
@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_async_db)):
    """Check if application is ready to serve traffic"""
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(),
        "elasticsearch": await check_elasticsearch(),
        "scheduler": check_scheduler_status()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

**Startup Probe** (`/health/startup`):
```python
@router.get("/health/startup")
async def startup_check():
    """Check if application has completed startup"""
    return {
        "status": "started",
        "uptime_seconds": time.time() - app_start_time,
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### 2. Metrics Collection

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge, Summary

# Scraping metrics
scraping_requests_total = Counter(
    'scraping_requests_total',
    'Total number of scraping requests',
    ['source', 'status']
)

scraping_duration_seconds = Histogram(
    'scraping_duration_seconds',
    'Time spent scraping',
    ['source'],
    buckets=[1, 2, 5, 10, 30, 60, 120, 300]
)

articles_scraped_total = Counter(
    'articles_scraped_total',
    'Total articles scraped',
    ['source', 'category']
)

scraping_errors_total = Counter(
    'scraping_errors_total',
    'Total scraping errors',
    ['source', 'error_type']
)

# API metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Scheduler metrics
scheduled_jobs_total = Gauge(
    'scheduled_jobs_total',
    'Total scheduled jobs'
)

job_execution_duration_seconds = Histogram(
    'job_execution_duration_seconds',
    'Job execution duration',
    ['job_id']
)

job_failures_total = Counter(
    'job_failures_total',
    'Total job failures',
    ['job_id', 'error_type']
)
```

**Metrics Endpoint:**
```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

#### 3. Alerting Thresholds

**Critical Alerts:**
```yaml
alerts:
  # Database connectivity
  - name: DatabaseDown
    condition: db_connections_active == 0
    duration: 1m
    severity: critical
    action: page_oncall

  # High error rate
  - name: HighErrorRate
    condition: rate(scraping_errors_total[5m]) > 0.5
    duration: 5m
    severity: critical
    action: page_oncall

  # Disk space
  - name: DiskSpaceLow
    condition: node_filesystem_avail_bytes < 10GB
    duration: 5m
    severity: critical
    action: page_oncall
```

**Warning Alerts:**
```yaml
  # Slow scraping
  - name: SlowScrapingPerformance
    condition: scraping_duration_seconds_p95 > 60
    duration: 10m
    severity: warning
    action: notify_slack

  # High API latency
  - name: HighAPILatency
    condition: http_request_duration_seconds_p95 > 2
    duration: 5m
    severity: warning
    action: notify_slack

  # Job failures
  - name: ScheduledJobFailures
    condition: rate(job_failures_total[10m]) > 0.1
    duration: 10m
    severity: warning
    action: notify_email
```

#### 4. Dashboard Design (Grafana)

**Dashboard 1: System Overview**
- System health status (green/yellow/red)
- Active database connections
- Redis memory usage
- CPU and memory utilization
- Request rate and error rate

**Dashboard 2: Scraping Operations**
- Articles scraped per hour (by source)
- Scraping success rate
- Average scraping duration
- Top error sources
- Content growth over time

**Dashboard 3: API Performance**
- Request rate (requests/sec)
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Active connections
- Cache hit rate

**Dashboard 4: Scheduler Health**
- Total scheduled jobs
- Job execution timeline
- Job success/failure ratio
- Missed job count
- Next scheduled runs

---

## Error Handling & Recovery

### Error Classification

**Level 1: Transient Errors (Automatic Retry)**
- Network timeouts
- Rate limit responses (429)
- Temporary server errors (502, 503, 504)
- Database deadlocks

**Level 2: Recoverable Errors (Manual Intervention)**
- Authentication failures
- Parse errors (HTML structure changed)
- Data validation errors
- Disk space warnings

**Level 3: Critical Errors (Immediate Escalation)**
- Database connection lost
- Redis unavailable
- Disk full
- Memory exhausted

### Recovery Mechanisms

#### 1. Automatic Retry with Exponential Backoff

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((HTTPError, Timeout)),
    before_sleep=log_retry_attempt
)
async def fetch_with_retry(url: str):
    """Fetch URL with automatic retry"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response
```

#### 2. Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def scrape_source(scraper_class, source_config):
    """Scrape with circuit breaker protection"""
    try:
        async with scraper_class(source_config) as scraper:
            return await scraper.scrape()
    except Exception as e:
        logger.error(f"Scraping failed: {source_config['name']}", exc_info=e)
        raise
```

#### 3. Dead Letter Queue (DLQ)

**Failed Job Storage:**
```python
class FailedJob(Base):
    __tablename__ = 'failed_jobs'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), nullable=False)
    job_type = Column(String(50), nullable=False)
    source = Column(String(100))

    # Error details
    error_type = Column(String(100))
    error_message = Column(Text)
    stack_trace = Column(Text)

    # Job data
    job_args = Column(JSON)
    job_kwargs = Column(JSON)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry = Column(DateTime)

    # Timestamps
    failed_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

    # Status
    status = Column(String(20), default='pending')  # pending, retrying, failed, resolved
```

**DLQ Processor:**
```python
async def process_dead_letter_queue():
    """Process failed jobs for retry"""
    query = select(FailedJob).where(
        FailedJob.status == 'pending',
        FailedJob.retry_count < FailedJob.max_retries,
        FailedJob.next_retry <= datetime.utcnow()
    )

    async with get_async_db() as db:
        result = await db.execute(query)
        failed_jobs = result.scalars().all()

        for job in failed_jobs:
            try:
                await retry_failed_job(job)
                job.status = 'resolved'
                job.resolved_at = datetime.utcnow()
            except Exception as e:
                job.retry_count += 1
                job.next_retry = calculate_next_retry(job.retry_count)
                if job.retry_count >= job.max_retries:
                    job.status = 'failed'
                    await send_failure_alert(job)

            await db.commit()
```

#### 4. Graceful Degradation

**Fallback Strategies:**
```python
async def get_content_with_fallback(content_id: int):
    """Fetch content with multiple fallback strategies"""
    try:
        # Primary: Elasticsearch
        return await fetch_from_elasticsearch(content_id)
    except ElasticsearchException:
        logger.warning("Elasticsearch unavailable, falling back to database")
        try:
            # Fallback 1: PostgreSQL
            return await fetch_from_database(content_id)
        except DatabaseException:
            logger.error("Database unavailable, falling back to cache")
            # Fallback 2: Redis cache (stale data acceptable)
            return await fetch_from_cache(content_id, allow_stale=True)
```

### Error Notification Strategy

**Notification Channels:**
1. **Slack/Teams**: Real-time alerts for critical errors
2. **Email**: Daily digest of warnings and errors
3. **SMS/Pager**: Critical system failures only
4. **Dashboard**: Real-time error trends visualization

**Notification Rules:**
```python
ERROR_NOTIFICATION_RULES = {
    'critical': {
        'channels': ['slack', 'email', 'pagerduty'],
        'throttle': '5m',  # Max 1 per 5 minutes
        'deduplicate': True
    },
    'warning': {
        'channels': ['slack'],
        'throttle': '15m',
        'deduplicate': True
    },
    'info': {
        'channels': ['email'],
        'throttle': '1h',
        'batch': True  # Send as digest
    }
}
```

---

## Production Deployment Strategy

### Environment Configuration

**Environment Files:**

`.env.production`:
```bash
# Application
APP_NAME="OpenLearn Platform"
ENVIRONMENT=production
DEBUG=False

# Security
SECRET_KEY=<GENERATED_64_CHAR_SECRET>
ACCESS_TOKEN_EXPIRE_HOURS=24
ALGORITHM=HS256

# Database (use connection pooling)
DATABASE_URL=postgresql+asyncpg://user:pass@db-primary:5432/openlearn?pool_size=20&max_overflow=40

# Redis (use sentinel for HA)
REDIS_URL=redis://sentinel:26379/0?sentinel_master=mymaster

# Elasticsearch
ELASTICSEARCH_URL=https://es-cluster:9200
ELASTICSEARCH_INDEX=openlearn_prod

# CORS
CORS_ORIGINS=https://openlearn.example.com,https://app.openlearn.example.com

# Scraping
ENABLE_SCHEDULER=True
SCRAPING_INTERVAL_MINUTES=30
MAX_CONCURRENT_SCRAPERS=5
REQUEST_TIMEOUT=30
SCRAPER_RATE_LIMIT=5

# NLP
SPACY_MODEL=es_core_news_lg
MIN_ENTITY_CONFIDENCE=0.7

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=<SENTRY_DSN>

# Monitoring
PROMETHEUS_ENABLED=True
METRICS_PORT=9090
```

### Database Migration Strategy

**Migration Tool:** Alembic

```bash
# 1. Generate migration
alembic revision --autogenerate -m "Add production indexes"

# 2. Review migration script
cat alembic/versions/001_add_production_indexes.py

# 3. Test migration on staging
ENVIRONMENT=staging alembic upgrade head

# 4. Create backup before production migration
pg_dump -h db-primary -U openlearn_user openlearn > backup_$(date +%Y%m%d_%H%M%S).sql

# 5. Apply migration to production
ENVIRONMENT=production alembic upgrade head

# 6. Verify migration
alembic current
```

**Migration Checklist:**
- [ ] Generate migration script
- [ ] Review SQL changes manually
- [ ] Test on development environment
- [ ] Test on staging environment
- [ ] Create full database backup
- [ ] Schedule maintenance window
- [ ] Apply migration during low-traffic period
- [ ] Verify data integrity
- [ ] Monitor application after migration
- [ ] Keep rollback script ready

### Deployment Pipeline

**CI/CD Workflow (GitHub Actions):**

```yaml
name: Production Deployment

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=app --cov-report=xml

      - name: Security scan
        run: |
          bandit -r app/
          safety check

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t openlearn:${{ github.sha }} .

      - name: Push to registry
        run: docker push openlearn:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/openlearn \
            openlearn=openlearn:${{ github.sha }}
          kubectl rollout status deployment/openlearn
```

### Blue-Green Deployment

**Strategy:**
```
┌─────────────────────────────────────────────┐
│            Load Balancer (NGINX)            │
└──────────────┬──────────────────────────────┘
               │
      ┌────────┴─────────┐
      │                  │
┌─────▼──────┐   ┌──────▼─────┐
│   BLUE     │   │   GREEN    │
│ (Current)  │   │   (New)    │
│ v1.0.0     │   │  v1.1.0    │
└────────────┘   └────────────┘

Deployment Steps:
1. Deploy to GREEN (inactive)
2. Run health checks on GREEN
3. Switch traffic to GREEN
4. Monitor for errors
5. Keep BLUE for rollback (24h)
6. Decommission BLUE if stable
```

### Container Orchestration (Kubernetes)

**Deployment Configuration:**

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openlearn-backend
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: openlearn
      tier: backend
  template:
    metadata:
      labels:
        app: openlearn
        tier: backend
    spec:
      containers:
      - name: api
        image: openlearn:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: openlearn-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 5
          failureThreshold: 30
```

### Rollback Strategy

**Automatic Rollback Triggers:**
- Health check failures > 50%
- Error rate > 10% for 5 minutes
- Response time p95 > 5 seconds
- Manual trigger via command

**Rollback Procedure:**
```bash
# 1. Immediate rollback to previous version
kubectl rollout undo deployment/openlearn-backend

# 2. Verify rollback
kubectl rollout status deployment/openlearn-backend

# 3. Check pods are healthy
kubectl get pods -l app=openlearn

# 4. Monitor metrics
kubectl top pods -l app=openlearn
```

---

## Security Hardening

### 1. Application Security

**Input Validation:**
- Pydantic models for all API inputs
- SQL injection prevention via ORM
- XSS prevention via content sanitization
- CSRF tokens for state-changing operations

**Authentication & Authorization:**
- JWT tokens with short expiration (24h)
- Refresh token rotation
- Role-based access control (RBAC)
- API key authentication for scrapers

**Secrets Management:**
```python
# Use environment variables, never hardcode
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    redis_url: str

    class Config:
        env_file = '.env'
        case_sensitive = False

# In production, use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
```

### 2. Network Security

**Firewall Rules:**
```yaml
# Allow only necessary ports
- Port 443: HTTPS (public)
- Port 8000: Application (internal)
- Port 5432: PostgreSQL (internal, DB subnet only)
- Port 6379: Redis (internal, cache subnet only)
- Port 9200: Elasticsearch (internal, search subnet only)
```

**TLS/SSL Configuration:**
```nginx
# NGINX SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### 3. Database Security

**Connection Security:**
- SSL/TLS for all database connections
- Connection pooling with max limits
- Read replicas for read-heavy operations
- Prepared statements to prevent SQL injection

**Access Control:**
```sql
-- Create read-only user for reporting
CREATE USER openlearn_readonly WITH PASSWORD '<strong_password>';
GRANT CONNECT ON DATABASE openlearn TO openlearn_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO openlearn_readonly;

-- Create app user with limited privileges
CREATE USER openlearn_app WITH PASSWORD '<strong_password>';
GRANT CONNECT ON DATABASE openlearn TO openlearn_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO openlearn_app;
REVOKE CREATE ON SCHEMA public FROM openlearn_app;
```

### 4. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global rate limit
@app.get("/api/content")
@limiter.limit("100/minute")
async def get_content():
    pass

# Stricter limit for expensive operations
@app.post("/api/scraping/trigger")
@limiter.limit("10/hour")
async def trigger_scraping():
    pass
```

### 5. Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## Scaling Strategy

### Horizontal Scaling

**Stateless Application Design:**
- No in-memory session storage (use Redis)
- Shared cache across instances
- Database connection pooling
- Load balancer distributes traffic

**Auto-scaling Configuration (Kubernetes):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: openlearn-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: openlearn-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### Vertical Scaling

**Resource Allocation:**
```yaml
# Small instance (development)
resources:
  requests: { memory: "256Mi", cpu: "250m" }
  limits: { memory: "512Mi", cpu: "500m" }

# Medium instance (staging)
resources:
  requests: { memory: "512Mi", cpu: "500m" }
  limits: { memory: "1Gi", cpu: "1000m" }

# Large instance (production)
resources:
  requests: { memory: "1Gi", cpu: "1000m" }
  limits: { memory: "2Gi", cpu: "2000m" }
```

### Database Scaling

**Read Replicas:**
```python
# Primary database for writes
DATABASE_PRIMARY_URL = "postgresql://user:pass@db-primary:5432/openlearn"

# Read replicas for reads
DATABASE_REPLICA_URLS = [
    "postgresql://user:pass@db-replica-1:5432/openlearn",
    "postgresql://user:pass@db-replica-2:5432/openlearn"
]

# Load balancer for read queries
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

write_engine = create_async_engine(DATABASE_PRIMARY_URL)
read_engines = [create_async_engine(url) for url in DATABASE_REPLICA_URLS]

def get_read_engine():
    """Round-robin load balancing for read replicas"""
    return random.choice(read_engines)
```

**Connection Pooling:**
```python
DATABASE_POOL_CONFIG = {
    'pool_size': 20,          # Base connections
    'max_overflow': 40,       # Additional connections under load
    'pool_timeout': 30,       # Wait time for connection
    'pool_recycle': 3600,     # Recycle connections every hour
    'pool_pre_ping': True     # Test connection before use
}
```

### Caching Strategy

**Multi-tier Caching:**
```
┌──────────────┐
│  Client      │
│  (Browser)   │ ← Cache-Control headers
└──────┬───────┘
       │
┌──────▼───────┐
│  CDN         │ ← Static assets, images
│  (CloudFlare)│
└──────┬───────┘
       │
┌──────▼───────┐
│  NGINX       │ ← Proxy cache for API responses
│  (Reverse    │
│   Proxy)     │
└──────┬───────┘
       │
┌──────▼───────┐
│  Redis       │ ← Application cache (query results, sessions)
│  (Cache)     │
└──────┬───────┘
       │
┌──────▼───────┐
│  Application │ ← In-memory cache (rarely changing data)
└──────┬───────┘
       │
┌──────▼───────┐
│  PostgreSQL  │ ← Database
└──────────────┘
```

**Cache Implementation:**
```python
from functools import wraps
import redis.asyncio as redis

# Redis cache decorator
def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash((args, tuple(kwargs.items())))}"

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)  # Cache for 10 minutes
async def get_trending_articles():
    """Fetch trending articles with caching"""
    query = select(ScrapedContent).order_by(ScrapedContent.published_date.desc()).limit(10)
    result = await db.execute(query)
    return result.scalars().all()
```

---

## Implementation Checklist

### Phase 1: APScheduler Integration (Week 1)

- [ ] Install APScheduler dependencies
- [ ] Create `scheduler_service.py` with AsyncIOScheduler
- [ ] Configure PostgreSQL jobstore for persistence
- [ ] Implement job registration for all scrapers
- [ ] Add high-priority jobs (every 15 min)
- [ ] Add medium-priority jobs (every 30 min)
- [ ] Add low-priority jobs (every 60 min)
- [ ] Add daily analytics job
- [ ] Implement error handling and retry logic
- [ ] Test job persistence across restarts
- [ ] Document job configuration

### Phase 2: Logging Infrastructure (Week 1-2)

- [ ] Install structlog and pythonjsonlogger
- [ ] Create `logging_config.py` with JSON formatting
- [ ] Configure log levels by module
- [ ] Implement rotating file handlers
- [ ] Add context injection (trace_id, user_id, etc.)
- [ ] Create structured logger wrapper
- [ ] Update all modules to use structured logging
- [ ] Test log rotation and retention
- [ ] Configure log aggregation (optional ELK/CloudWatch)
- [ ] Document logging standards

### Phase 3: Monitoring & Metrics (Week 2)

- [ ] Install prometheus-client
- [ ] Create `metrics.py` with Prometheus metrics
- [ ] Implement `/metrics` endpoint
- [ ] Add scraping metrics (duration, success rate, errors)
- [ ] Add API metrics (requests, latency, errors)
- [ ] Add database metrics (connections, query time)
- [ ] Add scheduler metrics (jobs, failures)
- [ ] Create health check endpoints (`/health/*`)
- [ ] Set up Prometheus server (docker-compose)
- [ ] Create Grafana dashboards
- [ ] Document metrics and dashboards

### Phase 4: Alerting System (Week 2-3)

- [ ] Configure Prometheus alerting rules
- [ ] Set up Alertmanager
- [ ] Configure Slack webhook for alerts
- [ ] Configure email alerts
- [ ] Implement alert throttling and deduplication
- [ ] Create runbooks for common alerts
- [ ] Test alert notifications
- [ ] Document alerting procedures

### Phase 5: Error Handling (Week 3)

- [ ] Install tenacity for retries
- [ ] Implement exponential backoff retry decorator
- [ ] Create circuit breaker for scrapers
- [ ] Create `FailedJob` model for DLQ
- [ ] Implement DLQ processor
- [ ] Add graceful degradation for dependencies
- [ ] Test error recovery mechanisms
- [ ] Document error handling patterns

### Phase 6: Production Configuration (Week 3-4)

- [ ] Create `.env.production` template
- [ ] Generate production secrets
- [ ] Configure database connection pooling
- [ ] Set up Redis Sentinel for HA
- [ ] Configure Elasticsearch cluster
- [ ] Implement security headers middleware
- [ ] Configure rate limiting
- [ ] Set up SSL/TLS certificates
- [ ] Test production configuration on staging

### Phase 7: Deployment Pipeline (Week 4)

- [ ] Create Dockerfile for production
- [ ] Create docker-compose for local production testing
- [ ] Configure GitHub Actions CI/CD
- [ ] Create Kubernetes manifests
- [ ] Set up HPA (Horizontal Pod Autoscaler)
- [ ] Configure rolling updates
- [ ] Test blue-green deployment
- [ ] Create rollback procedures
- [ ] Document deployment process

### Phase 8: Database Migration (Week 4)

- [ ] Set up Alembic for migrations
- [ ] Create production indexes
- [ ] Test migrations on development
- [ ] Test migrations on staging
- [ ] Create database backup procedures
- [ ] Schedule production migration
- [ ] Execute production migration
- [ ] Verify data integrity
- [ ] Document migration process

### Phase 9: Security Hardening (Week 5)

- [ ] Implement JWT authentication
- [ ] Add RBAC for API endpoints
- [ ] Configure CORS properly
- [ ] Set up secrets management (Vault/AWS Secrets)
- [ ] Implement input validation
- [ ] Run security audit (Bandit, Safety)
- [ ] Configure firewall rules
- [ ] Test penetration testing
- [ ] Document security procedures

### Phase 10: Performance Testing & Optimization (Week 5-6)

- [ ] Run load tests with Locust/K6
- [ ] Identify performance bottlenecks
- [ ] Optimize database queries
- [ ] Implement caching strategy
- [ ] Configure CDN for static assets
- [ ] Test auto-scaling behavior
- [ ] Optimize Docker images
- [ ] Document performance benchmarks

### Phase 11: Monitoring & Observability (Week 6)

- [ ] Set up distributed tracing (OpenTelemetry)
- [ ] Configure Sentry for error tracking
- [ ] Create custom dashboards for business metrics
- [ ] Set up log analytics
- [ ] Configure uptime monitoring (Pingdom/UptimeRobot)
- [ ] Test monitoring during incidents
- [ ] Document observability stack

### Phase 12: Documentation & Training (Week 6)

- [ ] Create runbook for common issues
- [ ] Document deployment procedures
- [ ] Create disaster recovery plan
- [ ] Document backup and restore procedures
- [ ] Create onboarding guide for new developers
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Create architecture diagrams
- [ ] Conduct team training

---

## Summary

This production infrastructure design provides:

1. **Robust Scheduling**: APScheduler with PostgreSQL persistence for reliable background jobs
2. **Comprehensive Logging**: Structured JSON logging with centralized aggregation
3. **Advanced Monitoring**: Prometheus metrics, Grafana dashboards, and proactive alerting
4. **Resilient Error Handling**: Automatic retries, circuit breakers, and dead letter queues
5. **Production-Ready Deployment**: CI/CD pipeline, blue-green deployment, and auto-scaling
6. **Enterprise Security**: Multi-layer security hardening and secrets management
7. **High Performance**: Multi-tier caching, connection pooling, and horizontal scaling

**Next Steps:**
1. Review this design with the team
2. Prioritize implementation phases
3. Begin with Phase 1 (APScheduler Integration)
4. Iterate and improve based on production feedback

---

**Document Version:** 1.0.0
**Last Updated:** October 2, 2025
**Author:** Backend Infrastructure Team
**Status:** Ready for Implementation
