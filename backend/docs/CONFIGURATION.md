# Environment Configuration Guide

## Overview

This guide provides comprehensive documentation for configuring the OpenLearn Colombia platform across different environments (development, staging, production). The platform uses environment variables for configuration to ensure security, flexibility, and environment-specific customization.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables Reference](#environment-variables-reference)
3. [Security Best Practices](#security-best-practices)
4. [Multi-Environment Setup](#multi-environment-setup)
5. [Secrets Management](#secrets-management)
6. [Configuration Validation](#configuration-validation)
7. [Common Issues](#common-issues)

## Quick Start

### Development Setup

```bash
# 1. Copy the development template
cp .env.development .env

# 2. Generate a secure secret key
python scripts/generate_secret_key.py

# 3. Update database credentials (if needed)
# Edit .env and set POSTGRES_* variables

# 4. Start the application
uvicorn app.main:app --reload
```

### Production Setup

```bash
# 1. Copy the production template
cp .env.production .env

# 2. Generate a unique secret key for production
python scripts/generate_secret_key.py --length 64

# 3. Update ALL required variables (see Required Variables section)

# 4. Validate configuration
python scripts/validate_config.py

# 5. Start with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables Reference

### Application Settings

#### `APP_NAME`
- **Type**: String
- **Required**: No
- **Default**: `"OpenLearn API"`
- **Description**: Application name displayed in logs, metrics, and UI
- **Example**: `APP_NAME="Colombia Intelligence Platform"`

#### `ENVIRONMENT`
- **Type**: String (enum)
- **Required**: Yes
- **Default**: `"development"`
- **Options**: `development`, `staging`, `production`
- **Description**: Deployment environment identifier
- **Example**: `ENVIRONMENT=production`
- **Impact**:
  - Controls debug mode behavior
  - Affects logging verbosity
  - Determines security defaults
  - Influences performance optimizations

#### `DEBUG`
- **Type**: Boolean
- **Required**: No
- **Default**: `True` (dev), `False` (prod)
- **Description**: Enable debug mode with detailed error messages and auto-reload
- **Example**: `DEBUG=false`
- **Security Warning**: MUST be `false` in production to prevent information disclosure

#### `API_V1_PREFIX`
- **Type**: String
- **Required**: No
- **Default**: `"/api/v1"`
- **Description**: API version prefix for all endpoints
- **Example**: `API_V1_PREFIX=/api/v2`

### Security Configuration

#### `SECRET_KEY` 🔐
- **Type**: String (URL-safe base64)
- **Required**: YES (CRITICAL)
- **Minimum Length**: 32 bytes (64 bytes recommended)
- **Description**: Secret key for JWT token signing, encryption, and CSRF protection
- **Generation**:
  ```bash
  # Quick generation
  python -c "import secrets; print(secrets.token_urlsafe(64))"

  # Using provided script
  python backend/scripts/generate_secret_key.py
  ```
- **Security Requirements**:
  1. Generate a UNIQUE key for EACH environment (dev/staging/prod)
  2. NEVER commit the actual key to version control
  3. Store in secure vaults (AWS Secrets Manager, HashiCorp Vault, etc.)
  4. Rotate keys periodically (recommended: every 90 days)
  5. Use minimum 64 bytes for production systems
- **Example**: `SECRET_KEY=your-generated-secret-key-here`
- **Critical**: Using default/weak keys is a CRITICAL SECURITY VULNERABILITY

#### `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Range**: `5` - `1440` (24 hours)
- **Description**: JWT access token expiration time in minutes
- **Example**: `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- **Recommendations**:
  - Development: 1440 (24 hours)
  - Production: 15-60 minutes
  - High-security: 5-15 minutes

#### `REFRESH_TOKEN_EXPIRE_DAYS`
- **Type**: Integer
- **Required**: No
- **Default**: `7`
- **Description**: JWT refresh token expiration in days
- **Example**: `REFRESH_TOKEN_EXPIRE_DAYS=30`

#### `CORS_ORIGINS`
- **Type**: String (comma-separated URLs)
- **Required**: Yes
- **Description**: Allowed origins for Cross-Origin Resource Sharing
- **Example**: `CORS_ORIGINS=http://localhost:3000,https://openlearn.co`
- **Production**: Specify exact domains (avoid wildcards)
- **Development**: Can include localhost with various ports

### Database Configuration

#### `POSTGRES_HOST`
- **Type**: String (hostname or IP)
- **Required**: Yes
- **Default**: `"localhost"`
- **Description**: PostgreSQL database server hostname
- **Example**: `POSTGRES_HOST=db.openlearn.co`

#### `POSTGRES_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `5432`
- **Description**: PostgreSQL server port
- **Example**: `POSTGRES_PORT=5432`

#### `POSTGRES_USER`
- **Type**: String
- **Required**: Yes
- **Description**: PostgreSQL database username
- **Example**: `POSTGRES_USER=openlearn_app`
- **Security**: Use least-privilege principle (dedicated app user)

#### `POSTGRES_PASSWORD` 🔐
- **Type**: String
- **Required**: Yes
- **Description**: PostgreSQL database password
- **Example**: `POSTGRES_PASSWORD=your-secure-password`
- **Security**:
  - Use strong, randomly generated passwords (16+ characters)
  - Store in secrets management system
  - Rotate periodically

#### `POSTGRES_DB`
- **Type**: String
- **Required**: Yes
- **Description**: PostgreSQL database name
- **Example**: `POSTGRES_DB=openlearn_prod`

#### `DB_POOL_SIZE`
- **Type**: Integer
- **Required**: No
- **Default**: `10`
- **Range**: `5` - `50`
- **Description**: Database connection pool size
- **Example**: `DB_POOL_SIZE=20`
- **Tuning**:
  - Development: 5-10
  - Production (low traffic): 10-20
  - Production (high traffic): 20-50

#### `DB_MAX_OVERFLOW`
- **Type**: Integer
- **Required**: No
- **Default**: `20`
- **Description**: Maximum overflow connections beyond pool size
- **Example**: `DB_MAX_OVERFLOW=30`

#### `DB_POOL_TIMEOUT`
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Description**: Connection pool timeout in seconds
- **Example**: `DB_POOL_TIMEOUT=30`

### Cache & Session Storage

#### `REDIS_HOST`
- **Type**: String
- **Required**: Yes
- **Default**: `"localhost"`
- **Description**: Redis server hostname for caching and sessions
- **Example**: `REDIS_HOST=redis.openlearn.co`

#### `REDIS_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `6379`
- **Description**: Redis server port
- **Example**: `REDIS_PORT=6379`

#### `REDIS_DB`
- **Type**: Integer
- **Required**: No
- **Default**: `0`
- **Range**: `0` - `15`
- **Description**: Redis database number
- **Example**: `REDIS_DB=0`

#### `REDIS_PASSWORD` 🔐
- **Type**: String
- **Required**: Strongly Recommended
- **Description**: Redis authentication password
- **Example**: `REDIS_PASSWORD=your-redis-password`
- **Security**: Always set in production environments

### Search Engine

#### `ELASTICSEARCH_HOST`
- **Type**: String
- **Required**: Yes
- **Default**: `"localhost"`
- **Description**: Elasticsearch server hostname
- **Example**: `ELASTICSEARCH_HOST=es.openlearn.co`

#### `ELASTICSEARCH_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `9200`
- **Description**: Elasticsearch server port
- **Example**: `ELASTICSEARCH_PORT=9200`

#### `ELASTICSEARCH_INDEX`
- **Type**: String
- **Required**: No
- **Default**: `"openlearn"`
- **Description**: Elasticsearch index name for content storage
- **Example**: `ELASTICSEARCH_INDEX=colombia_content_prod`

### Colombian Data Sources

#### `DANE_API_KEY` 🔐
- **Type**: String
- **Required**: Optional
- **Description**: DANE (Departamento Administrativo Nacional de Estadística) API key
- **URL**: https://www.dane.gov.co/
- **Example**: `DANE_API_KEY=your-dane-api-key`

#### `BANREP_BASE_URL`
- **Type**: URL
- **Required**: No
- **Default**: `"https://www.banrep.gov.co/api"`
- **Description**: Banco de la República API base URL
- **Example**: `BANREP_BASE_URL=https://www.banrep.gov.co/api`

#### `SECOP_API_TOKEN` 🔐
- **Type**: String
- **Required**: Optional
- **Description**: SECOP (Sistema Electrónico de Contratación Pública) API token
- **URL**: https://www.colombiacompra.gov.co/
- **Example**: `SECOP_API_TOKEN=your-secop-token`

#### `DATOS_GOV_BASE_URL`
- **Type**: URL
- **Required**: No
- **Default**: `"https://www.datos.gov.co/api"`
- **Description**: Datos.gov.co Open Data Portal API base URL
- **Example**: `DATOS_GOV_BASE_URL=https://www.datos.gov.co/api`

#### `IDEAM_API_KEY` 🔐
- **Type**: String
- **Required**: Optional
- **Description**: IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales) API key
- **URL**: http://www.ideam.gov.co/
- **Example**: `IDEAM_API_KEY=your-ideam-key`

#### `DNP_API_KEY` 🔐
- **Type**: String
- **Required**: Optional
- **Description**: Departamento Nacional de Planeación API key
- **Example**: `DNP_API_KEY=your-dnp-key`

#### `MINHACIENDA_API_KEY` 🔐
- **Type**: String
- **Required**: Optional
- **Description**: Ministerio de Hacienda API key
- **Example**: `MINHACIENDA_API_KEY=your-minhacienda-key`

### Web Scraping Configuration

#### `ENABLE_SCHEDULER`
- **Type**: Boolean
- **Required**: No
- **Default**: `True`
- **Description**: Enable/disable scheduled scraping jobs
- **Example**: `ENABLE_SCHEDULER=true`

#### `SCRAPING_INTERVAL_MINUTES`
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Range**: `5` - `1440`
- **Description**: Interval between scraping runs in minutes
- **Example**: `SCRAPING_INTERVAL_MINUTES=60`

#### `MAX_CONCURRENT_SCRAPERS`
- **Type**: Integer
- **Required**: No
- **Default**: `5`
- **Range**: `1` - `20`
- **Description**: Maximum number of concurrent scraper threads
- **Example**: `MAX_CONCURRENT_SCRAPERS=10`
- **Warning**: Higher values may trigger rate limiting

#### `SCRAPER_TIMEOUT`
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Description**: HTTP request timeout for scrapers in seconds
- **Example**: `SCRAPER_TIMEOUT=60`

#### `SCRAPER_RATE_LIMIT`
- **Type**: Integer
- **Required**: No
- **Default**: `10`
- **Description**: Requests per second rate limit
- **Example**: `SCRAPER_RATE_LIMIT=5`
- **Ethics**: Respect target websites' rate limits and robots.txt

#### `SCRAPER_USER_AGENT`
- **Type**: String
- **Required**: No
- **Default**: `"OpenLearn Bot 1.0"`
- **Description**: User agent string for HTTP requests
- **Example**: `SCRAPER_USER_AGENT="OpenLearn Bot 1.0 (+https://openlearn.co/bot)"`

### NLP Configuration

#### `NLP_MODEL`
- **Type**: String
- **Required**: No
- **Default**: `"es_core_news_sm"`
- **Options**: `es_core_news_sm`, `es_core_news_md`, `es_core_news_lg`
- **Description**: SpaCy language model for Spanish NLP
- **Example**: `NLP_MODEL=es_core_news_lg`
- **Installation**: `python -m spacy download es_core_news_lg`
- **Model Comparison**:
  - `sm` (small): Fast, 12MB, basic accuracy
  - `md` (medium): Balanced, 43MB, good accuracy
  - `lg` (large): Slow, 545MB, best accuracy

#### `NLP_BATCH_SIZE`
- **Type**: Integer
- **Required**: No
- **Default**: `32`
- **Description**: Batch size for NLP processing
- **Example**: `NLP_BATCH_SIZE=64`

#### `NLP_MAX_LENGTH`
- **Type**: Integer
- **Required**: No
- **Default**: `1000000`
- **Description**: Maximum text length for NLP processing
- **Example**: `NLP_MAX_LENGTH=2000000`

### Logging & Monitoring

#### `LOG_LEVEL`
- **Type**: String (enum)
- **Required**: No
- **Default**: `"INFO"`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Application logging level
- **Example**: `LOG_LEVEL=WARNING`
- **Recommendations**:
  - Development: `DEBUG`
  - Staging: `INFO`
  - Production: `WARNING` or `ERROR`

#### `LOG_DIR`
- **Type**: Path
- **Required**: No
- **Default**: `"logs"`
- **Description**: Directory for log file storage
- **Example**: `LOG_DIR=/var/log/openlearn`

#### `LOG_ENABLE_CONSOLE`
- **Type**: Boolean
- **Required**: No
- **Default**: `True`
- **Description**: Enable console logging output
- **Example**: `LOG_ENABLE_CONSOLE=true`

#### `LOG_ENABLE_FILE`
- **Type**: Boolean
- **Required**: No
- **Default**: `True`
- **Description**: Enable file-based logging
- **Example**: `LOG_ENABLE_FILE=true`

#### `LOG_FORMAT`
- **Type**: String (enum)
- **Required**: No
- **Default**: `"json"`
- **Options**: `json`, `text`
- **Description**: Log output format
- **Example**: `LOG_FORMAT=json`
- **Recommendations**:
  - Development: `text` (human-readable)
  - Production: `json` (machine-parseable)

#### `METRICS_ENABLED`
- **Type**: Boolean
- **Required**: No
- **Default**: `True`
- **Description**: Enable Prometheus metrics collection
- **Example**: `METRICS_ENABLED=true`

#### `METRICS_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `9090`
- **Description**: Prometheus metrics server port
- **Example**: `METRICS_PORT=9090`

#### `SENTRY_DSN` 🔐
- **Type**: URL
- **Required**: Optional
- **Description**: Sentry DSN for error tracking and monitoring
- **Example**: `SENTRY_DSN=https://key@sentry.io/project`
- **Setup**: Sign up at https://sentry.io

#### `SENTRY_ENVIRONMENT`
- **Type**: String
- **Required**: No
- **Default**: `"development"`
- **Description**: Sentry environment tag
- **Example**: `SENTRY_ENVIRONMENT=production`

#### `SENTRY_TRACES_SAMPLE_RATE`
- **Type**: Float
- **Required**: No
- **Default**: `1.0`
- **Range**: `0.0` - `1.0`
- **Description**: Performance tracing sample rate
- **Example**: `SENTRY_TRACES_SAMPLE_RATE=0.1`
- **Recommendations**:
  - Development: 1.0 (100%)
  - Production: 0.01-0.1 (1-10%)

### Alerting Configuration

#### `SMTP_HOST`
- **Type**: String
- **Required**: No (required for email alerts)
- **Description**: SMTP server hostname for email alerts
- **Example**: `SMTP_HOST=smtp.gmail.com`

#### `SMTP_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `587`
- **Description**: SMTP server port
- **Example**: `SMTP_PORT=587`

#### `SMTP_USER`
- **Type**: String
- **Required**: No (required for email alerts)
- **Description**: SMTP authentication username
- **Example**: `SMTP_USER=alerts@openlearn.co`

#### `SMTP_PASSWORD` 🔐
- **Type**: String
- **Required**: No (required for email alerts)
- **Description**: SMTP authentication password
- **Example**: `SMTP_PASSWORD=your-smtp-password`

#### `ALERT_EMAIL_FROM`
- **Type**: String (email)
- **Required**: No
- **Description**: From address for alert emails
- **Example**: `ALERT_EMAIL_FROM=noreply@openlearn.co`

#### `ALERT_EMAIL_TO`
- **Type**: String (comma-separated emails)
- **Required**: No
- **Description**: Recipient addresses for alert emails
- **Example**: `ALERT_EMAIL_TO=admin@openlearn.co,ops@openlearn.co`

#### `SLACK_WEBHOOK_URL` 🔐
- **Type**: URL
- **Required**: No (required for Slack alerts)
- **Description**: Slack incoming webhook URL for alerts
- **Example**: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
- **Setup**: Create at https://api.slack.com/messaging/webhooks

#### `SLACK_CHANNEL`
- **Type**: String
- **Required**: No
- **Default**: `"#alerts"`
- **Description**: Slack channel for alert notifications
- **Example**: `SLACK_CHANNEL=#production-alerts`

## Security Best Practices

### Secret Key Management

1. **Never Commit Secrets to Version Control**
   ```bash
   # Always add to .gitignore
   echo ".env" >> .gitignore
   echo ".env.production" >> .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **Use Strong, Randomly Generated Keys**
   ```bash
   # Generate 64-byte URL-safe secret key
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. **Unique Keys Per Environment**
   - Development: Unique key (can be less strict)
   - Staging: Unique key (production-like)
   - Production: Unique key (maximum security)

4. **Key Rotation Strategy**
   - Schedule: Every 90 days minimum
   - Process: Generate new key, update config, restart services
   - Rollback: Keep previous key for 24 hours

### Secrets Management Solutions

#### AWS Secrets Manager
```python
import boto3

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='openlearn/prod/secret-key')
    return response['SecretString']
```

#### HashiCorp Vault
```python
import hvac

def get_secret():
    client = hvac.Client(url='https://vault.example.com')
    client.token = 'your-vault-token'
    secret = client.secrets.kv.read_secret_version(path='openlearn/secret-key')
    return secret['data']['data']['value']
```

#### Environment-based (Development Only)
```bash
# .env.local (gitignored)
SECRET_KEY=your-local-development-key
```

### Database Security

1. **Use Dedicated Application User**
   ```sql
   -- Create dedicated user with limited privileges
   CREATE USER openlearn_app WITH PASSWORD 'strong-password';
   GRANT CONNECT ON DATABASE openlearn_prod TO openlearn_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO openlearn_app;
   ```

2. **Enable SSL/TLS Connections**
   ```python
   # Add to DATABASE_URL
   ?sslmode=require&sslrootcert=/path/to/ca-cert.pem
   ```

3. **Restrict Network Access**
   ```bash
   # PostgreSQL pg_hba.conf
   hostssl all openlearn_app 10.0.1.0/24 md5
   ```

### API Key Protection

1. **Store in Environment Variables**
   ```bash
   # Never hardcode in code
   DANE_API_KEY=your-api-key
   ```

2. **Use Read-Only Keys When Possible**
3. **Monitor API Usage**
4. **Rotate Keys Regularly**

### CORS Configuration

1. **Production: Exact Domains Only**
   ```bash
   # ❌ Wrong (too permissive)
   CORS_ORIGINS=*

   # ✅ Correct (specific domains)
   CORS_ORIGINS=https://openlearn.co,https://api.openlearn.co
   ```

2. **Development: Localhost Only**
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

## Multi-Environment Setup

### Directory Structure
```
backend/
├── .env.example           # Template with all variables
├── .env.development       # Development defaults
├── .env.staging          # Staging configuration
├── .env.production       # Production template (secrets removed)
├── .env                  # Active environment (gitignored)
└── .env.local            # Local overrides (gitignored)
```

### Environment Loading Priority

1. `.env.local` (highest priority, local overrides)
2. `.env.{ENVIRONMENT}` (environment-specific)
3. `.env` (general defaults)
4. System environment variables (highest precedence)

### Switching Environments

```bash
# Development
cp .env.development .env
uvicorn app.main:app --reload

# Staging
cp .env.staging .env
uvicorn app.main:app --host 0.0.0.0

# Production
cp .env.production .env
# Update secrets from vault
uvicorn app.main:app --host 0.0.0.0 --workers 4
```

## Secrets Management

### Development Environment

```bash
# .env.development
SECRET_KEY=dev-key-not-for-production
DATABASE_URL=postgresql://openlearn:openlearn123@localhost:5432/openlearn_dev
REDIS_URL=redis://localhost:6379/0
DEBUG=true
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
SECRET_KEY=${STAGING_SECRET_KEY}  # From vault
DATABASE_URL=${STAGING_DATABASE_URL}  # From vault
DEBUG=false
SENTRY_ENVIRONMENT=staging
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
SECRET_KEY=${PROD_SECRET_KEY}  # From AWS Secrets Manager
DATABASE_URL=${PROD_DATABASE_URL}  # From AWS Secrets Manager
DEBUG=false
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.01
```

### Docker Secrets

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    image: openlearn-api
    secrets:
      - secret_key
      - database_url
    environment:
      SECRET_KEY_FILE: /run/secrets/secret_key
      DATABASE_URL_FILE: /run/secrets/database_url

secrets:
  secret_key:
    external: true
  database_url:
    external: true
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openlearn-secrets
type: Opaque
data:
  SECRET_KEY: <base64-encoded-value>
  DATABASE_URL: <base64-encoded-value>
```

## Configuration Validation

### Startup Validation

The application validates configuration on startup:

```python
from app.config.settings import settings

# Automatic validation via Pydantic
try:
    settings.validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)
```

### Manual Validation

```bash
# Validate current configuration
python scripts/validate_config.py

# Validate specific environment
python scripts/validate_config.py --env production
```

### Required Variables Check

```python
REQUIRED_PRODUCTION_VARS = [
    'SECRET_KEY',
    'POSTGRES_HOST',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DB',
    'REDIS_HOST',
    'CORS_ORIGINS',
]
```

## Common Issues

### Issue: Missing Required Variables

**Error**: `ValidationError: SECRET_KEY is required`

**Solution**:
```bash
# Generate and set secret key
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
```

### Issue: Database Connection Failed

**Error**: `OperationalError: could not connect to server`

**Solutions**:
1. Check database is running: `pg_isready -h localhost -p 5432`
2. Verify credentials in `.env`
3. Check network connectivity
4. Verify PostgreSQL accepts connections: `pg_hba.conf`

### Issue: Redis Connection Timeout

**Error**: `ConnectionError: Error connecting to Redis`

**Solutions**:
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_URL format
3. Check firewall rules
4. Verify Redis authentication (if enabled)

### Issue: CORS Errors in Browser

**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solutions**:
1. Add frontend URL to `CORS_ORIGINS`
2. Verify format: `http://localhost:3000` (no trailing slash)
3. Check protocol matches (http vs https)
4. Restart backend after changes

### Issue: NLP Model Not Found

**Error**: `OSError: Can't find model 'es_core_news_lg'`

**Solution**:
```bash
# Download the Spanish model
python -m spacy download es_core_news_lg
```

### Issue: Slow Performance

**Symptoms**: High response times, timeouts

**Solutions**:
1. Increase `DB_POOL_SIZE`: `DB_POOL_SIZE=20`
2. Tune connection pool: `DB_MAX_OVERFLOW=30`
3. Enable query caching
4. Check `SLOW_REQUEST_THRESHOLD_MS` logs
5. Review Sentry performance traces

## Environment Variables Checklist

### Minimum Required (All Environments)
- [ ] `SECRET_KEY` (generated, unique per environment)
- [ ] `POSTGRES_HOST`
- [ ] `POSTGRES_USER`
- [ ] `POSTGRES_PASSWORD`
- [ ] `POSTGRES_DB`
- [ ] `REDIS_HOST`
- [ ] `CORS_ORIGINS`

### Recommended Production
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=WARNING`
- [ ] `SENTRY_DSN`
- [ ] `REDIS_PASSWORD`
- [ ] `DB_POOL_SIZE` (tuned)
- [ ] `METRICS_ENABLED=true`

### Optional (Feature-Dependent)
- [ ] `DANE_API_KEY` (if using DANE data)
- [ ] `SECOP_API_TOKEN` (if using procurement data)
- [ ] `SLACK_WEBHOOK_URL` (if using Slack alerts)
- [ ] `SMTP_*` variables (if using email alerts)

## Support

For configuration assistance:
- Documentation: `/backend/docs/`
- Example: `.env.example`
- Validation: `python scripts/validate_config.py`
- GitHub Issues: [Report configuration problems]

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/usage/settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Twelve-Factor App](https://12factor.net/config)
