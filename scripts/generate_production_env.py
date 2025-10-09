#!/usr/bin/env python3
"""
Production .env File Generator
Generates secure production environment file with random secrets
"""

import secrets
import sys
from pathlib import Path


def generate_secret_key(length: int = 64) -> str:
    """Generate cryptographically secure secret key"""
    return secrets.token_urlsafe(length)


def generate_password(length: int = 32) -> str:
    """Generate secure password for databases"""
    return secrets.token_urlsafe(length)


def generate_production_env(domain: str, sendgrid_api_key: str = "", admin_email: str = "admin@example.com") -> str:
    """Generate complete production .env file"""

    secret_key = generate_secret_key(64)
    db_password = generate_password(32)
    redis_password = generate_password(32)

    env_content = f"""# ============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# OpenLearn Colombia - Auto-Generated
# Generated: {secrets.token_hex(8)}
# ============================================================================
# ⚠️  SECURITY WARNING: This file contains sensitive credentials
# - Never commit to Git
# - Never share publicly
# - Restrict permissions: chmod 600 .env
# ============================================================================

# ══════════════════════════════════════════════════
# CORE APPLICATION SETTINGS
# ══════════════════════════════════════════════════
ENVIRONMENT=production
DEBUG=false
APP_NAME=OpenLearn Colombia
APP_VERSION=1.0.0

# ══════════════════════════════════════════════════
# SECURITY (CRITICAL - Auto-Generated Secure Values)
# ══════════════════════════════════════════════════
SECRET_KEY={secret_key}
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ══════════════════════════════════════════════════
# FRONTEND CONFIGURATION
# ══════════════════════════════════════════════════
FRONTEND_URL=https://{domain}
CORS_ORIGINS=https://{domain},https://www.{domain}
CORS_ALLOW_CREDENTIALS=true

# ══════════════════════════════════════════════════
# DATABASE (PostgreSQL)
# ══════════════════════════════════════════════════
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=openlearn_prod
POSTGRES_PASSWORD={db_password}
POSTGRES_DB=openlearn_production

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_ECHO=false

# ══════════════════════════════════════════════════
# REDIS (Cache & Sessions)
# ══════════════════════════════════════════════════
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}
REDIS_DB=0

# ══════════════════════════════════════════════════
# ELASTICSEARCH (Search Engine)
# ══════════════════════════════════════════════════
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX_PREFIX=openlearn_prod
ELASTICSEARCH_TIMEOUT=30
ELASTICSEARCH_MAX_RETRIES=3

# ══════════════════════════════════════════════════
# EMAIL SERVICE (SendGrid)
# ══════════════════════════════════════════════════
# ⚠️  YOU MUST UPDATE THESE WITH YOUR ACTUAL SendGrid CREDENTIALS
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD={sendgrid_api_key if sendgrid_api_key else "YOUR_SENDGRID_API_KEY_HERE"}

ALERT_EMAIL_FROM=OpenLearn Colombia <noreply@{domain}>
ALERT_EMAIL_TO={admin_email}

# ══════════════════════════════════════════════════
# LOGGING & MONITORING
# ══════════════════════════════════════════════════
LOG_LEVEL=INFO
LOG_DIR=/app/logs
LOG_ENABLE_CONSOLE=true
LOG_ENABLE_FILE=true
LOG_FORMAT=json

METRICS_ENABLED=true
METRICS_PORT=9090
ENABLE_PERFORMANCE_LOGGING=true
SLOW_REQUEST_THRESHOLD_MS=1000

# ══════════════════════════════════════════════════
# SCRAPING CONFIGURATION
# ══════════════════════════════════════════════════
SCRAPER_USER_AGENT=OpenLearn Bot 1.0 (+https://{domain}/about)
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RATE_LIMIT=5
MAX_CONCURRENT_SCRAPERS=5
RESPECT_ROBOTS_TXT=true

# ══════════════════════════════════════════════════
# NLP CONFIGURATION
# ══════════════════════════════════════════════════
NLP_MODEL=es_core_news_sm
NLP_BATCH_SIZE=32
NLP_MAX_LENGTH=1000000

# ══════════════════════════════════════════════════
# CACHING
# ══════════════════════════════════════════════════
DEFAULT_CACHE_TTL=3600
API_CACHE_TTL=1800
SCRAPER_CACHE_TTL=7200
NLP_CACHE_TTL=86400

# ══════════════════════════════════════════════════
# SCHEDULER
# ══════════════════════════════════════════════════
ENABLE_SCHEDULER=true
SCRAPING_INTERVAL_MINUTES=30

# ══════════════════════════════════════════════════
# SECURITY HEADERS
# ══════════════════════════════════════════════════
ALLOWED_HOSTS={domain},www.{domain}
ENABLE_COMPRESSION=true

# ══════════════════════════════════════════════════
# OPTIONAL: Government API Keys (Add if you have them)
# ══════════════════════════════════════════════════
DANE_API_KEY=
BANREP_BASE_URL=https://www.banrep.gov.co/api
SECOP_API_TOKEN=
IDEAM_API_KEY=

# ══════════════════════════════════════════════════
# SENTRY ERROR TRACKING (Optional - Recommended for production)
# ══════════════════════════════════════════════════
# Sign up at https://sentry.io for free error tracking
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=1.0

# ============================================================================
# END OF CONFIGURATION
# ============================================================================
# Generated by scripts/generate_production_env.py
# Next steps:
# 1. Update SMTP_PASSWORD with your SendGrid API key
# 2. Update ALERT_EMAIL_TO with your admin email
# 3. (Optional) Add government API keys if you have them
# 4. (Optional) Add Sentry DSN for error tracking
# 5. Save and run: chmod 600 .env
# ============================================================================
"""

    return env_content


def main():
    """Main execution"""
    print("🔐 OpenLearn Production Environment Generator")
    print("=" * 60)

    # Get domain from user
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    else:
        domain = input("Enter your domain name (e.g., openlearn.co): ").strip()

    # Get SendGrid API key (optional)
    sendgrid_key = input("Enter SendGrid API key (or press Enter to add later): ").strip()

    # Get admin email
    admin_email = input(f"Enter admin email (default: admin@{domain}): ").strip()
    if not admin_email:
        admin_email = f"admin@{domain}"

    print("\n⚙️  Generating secure credentials...")

    # Generate .env content
    env_content = generate_production_env(domain, sendgrid_key, admin_email)

    # Write to file
    output_path = Path(".env.production")
    output_path.write_text(env_content)

    print(f"\n✅ Production environment file created: {output_path}")
    print("\n📋 Generated Credentials:")
    print(f"   - SECRET_KEY: 64 characters (cryptographically secure)")
    print(f"   - Database Password: 32 characters (secure)")
    print(f"   - Redis Password: 32 characters (secure)")

    if not sendgrid_key:
        print("\n⚠️  IMPORTANT: You still need to:")
        print("   1. Get SendGrid API key from https://sendgrid.com")
        print(f"   2. Update SMTP_PASSWORD in {output_path}")

    print("\n🔒 Security reminder:")
    print(f"   Run: chmod 600 {output_path}")
    print(f"   Then: mv {output_path} .env")

    print("\n🚀 Next step:")
    print("   Run: ./scripts/deploy.sh")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
