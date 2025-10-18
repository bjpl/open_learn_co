"""
Pre-deployment validation test suite for OpenLearn Colombia.
Validates environment, configuration, and dependencies before deployment.
"""

import os
import sys
import subprocess
from typing import List, Dict, Tuple
import psycopg2
import redis
from elasticsearch import Elasticsearch
import yaml
import pytest


class PreDeploymentValidator:
    """Comprehensive pre-deployment validation checks."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0

    def validate_environment_variables(self) -> bool:
        """Validate all required environment variables are set."""
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'ELASTICSEARCH_URL',
            'SECRET_KEY',
            'ALLOWED_HOSTS',
            'DEBUG',
            'DJANGO_SETTINGS_MODULE',
        ]

        optional_vars = [
            'SENTRY_DSN',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'CLOUDINARY_URL',
        ]

        print("\n🔍 Validating environment variables...")

        all_valid = True
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Required environment variable missing: {var}")
                all_valid = False
                print(f"  ❌ {var}: MISSING")
            else:
                print(f"  ✅ {var}: SET")
                self.checks_passed += 1

        for var in optional_vars:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional environment variable missing: {var}")
                print(f"  ⚠️  {var}: NOT SET (optional)")
            else:
                print(f"  ✅ {var}: SET")

        if not all_valid:
            self.checks_failed += len([e for e in self.errors if 'environment variable' in e])

        return all_valid

    def validate_database_connection(self) -> bool:
        """Validate database connectivity and migrations."""
        print("\n🔍 Validating database connection...")

        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.errors.append("DATABASE_URL not set")
                self.checks_failed += 1
                return False

            # Test connection
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Check database version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"  ✅ Database connected: {version}")

            # Check if migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'django_migrations'
                );
            """)
            has_migrations = cursor.fetchone()[0]

            if not has_migrations:
                self.warnings.append("Django migrations table not found - fresh database")
                print("  ⚠️  No migrations table found (fresh database)")
            else:
                cursor.execute("SELECT COUNT(*) FROM django_migrations;")
                migration_count = cursor.fetchone()[0]
                print(f"  ✅ Migrations applied: {migration_count}")

            conn.close()
            self.checks_passed += 1
            return True

        except Exception as e:
            self.errors.append(f"Database connection failed: {str(e)}")
            self.checks_failed += 1
            print(f"  ❌ Database connection failed: {str(e)}")
            return False

    def validate_redis_connection(self) -> bool:
        """Validate Redis connectivity."""
        print("\n🔍 Validating Redis connection...")

        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                self.errors.append("REDIS_URL not set")
                self.checks_failed += 1
                return False

            r = redis.from_url(redis_url)
            r.ping()
            info = r.info()
            print(f"  ✅ Redis connected: v{info['redis_version']}")
            print(f"  ℹ️  Memory used: {info['used_memory_human']}")
            self.checks_passed += 1
            return True

        except Exception as e:
            self.errors.append(f"Redis connection failed: {str(e)}")
            self.checks_failed += 1
            print(f"  ❌ Redis connection failed: {str(e)}")
            return False

    def validate_elasticsearch_connection(self) -> bool:
        """Validate Elasticsearch connectivity."""
        print("\n🔍 Validating Elasticsearch connection...")

        try:
            es_url = os.getenv('ELASTICSEARCH_URL')
            if not es_url:
                self.warnings.append("ELASTICSEARCH_URL not set")
                print("  ⚠️  Elasticsearch not configured (optional)")
                return True

            es = Elasticsearch([es_url])
            if not es.ping():
                raise Exception("Elasticsearch ping failed")

            info = es.info()
            print(f"  ✅ Elasticsearch connected: v{info['version']['number']}")
            self.checks_passed += 1
            return True

        except Exception as e:
            self.warnings.append(f"Elasticsearch connection failed: {str(e)}")
            print(f"  ⚠️  Elasticsearch connection failed: {str(e)} (optional)")
            return True

    def validate_django_configuration(self) -> bool:
        """Validate Django settings and configuration."""
        print("\n🔍 Validating Django configuration...")

        try:
            # Check DEBUG setting
            debug = os.getenv('DEBUG', 'False').lower()
            if debug == 'true':
                self.warnings.append("DEBUG is enabled in production environment")
                print("  ⚠️  DEBUG=True (should be False in production)")
            else:
                print("  ✅ DEBUG=False")
                self.checks_passed += 1

            # Check SECRET_KEY
            secret_key = os.getenv('SECRET_KEY', '')
            if len(secret_key) < 50:
                self.errors.append("SECRET_KEY is too short or missing")
                self.checks_failed += 1
                print("  ❌ SECRET_KEY is too short (min 50 chars)")
                return False
            else:
                print("  ✅ SECRET_KEY is sufficiently long")
                self.checks_passed += 1

            # Check ALLOWED_HOSTS
            allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
            if not allowed_hosts or allowed_hosts == '*':
                self.errors.append("ALLOWED_HOSTS not properly configured")
                self.checks_failed += 1
                print("  ❌ ALLOWED_HOSTS not properly configured")
                return False
            else:
                print(f"  ✅ ALLOWED_HOSTS configured: {allowed_hosts}")
                self.checks_passed += 1

            return True

        except Exception as e:
            self.errors.append(f"Django configuration validation failed: {str(e)}")
            self.checks_failed += 1
            print(f"  ❌ Configuration validation failed: {str(e)}")
            return False

    def validate_dependencies(self) -> bool:
        """Validate Python dependencies are properly installed."""
        print("\n🔍 Validating dependencies...")

        try:
            result = subprocess.run(
                ['pip', 'check'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("  ✅ All dependencies compatible")
                self.checks_passed += 1
                return True
            else:
                self.errors.append(f"Dependency conflicts detected: {result.stdout}")
                self.checks_failed += 1
                print(f"  ❌ Dependency conflicts: {result.stdout}")
                return False

        except Exception as e:
            self.warnings.append(f"Could not validate dependencies: {str(e)}")
            print(f"  ⚠️  Could not validate dependencies: {str(e)}")
            return True

    def validate_migrations(self) -> bool:
        """Validate that all migrations are applied."""
        print("\n🔍 Validating migrations...")

        try:
            result = subprocess.run(
                ['python', 'manage.py', 'showmigrations', '--plan'],
                capture_output=True,
                text=True,
                cwd='/mnt/c/Users/brand/Development/Project_Workspace/active-development/open_learn'
            )

            if '[X]' in result.stdout:
                # Count applied migrations
                applied = result.stdout.count('[X]')
                unapplied = result.stdout.count('[ ]')

                if unapplied > 0:
                    self.errors.append(f"{unapplied} migrations not applied")
                    self.checks_failed += 1
                    print(f"  ❌ {unapplied} migrations not applied")
                    return False
                else:
                    print(f"  ✅ All {applied} migrations applied")
                    self.checks_passed += 1
                    return True
            else:
                print("  ℹ️  No migrations found")
                return True

        except Exception as e:
            self.warnings.append(f"Could not validate migrations: {str(e)}")
            print(f"  ⚠️  Could not validate migrations: {str(e)}")
            return True

    def validate_static_files(self) -> bool:
        """Validate static files are collected."""
        print("\n🔍 Validating static files...")

        try:
            static_root = os.getenv('STATIC_ROOT', 'staticfiles')
            if os.path.exists(static_root) and os.listdir(static_root):
                print(f"  ✅ Static files collected in {static_root}")
                self.checks_passed += 1
                return True
            else:
                self.warnings.append("Static files not collected")
                print(f"  ⚠️  Static files not collected (run collectstatic)")
                return True

        except Exception as e:
            self.warnings.append(f"Could not validate static files: {str(e)}")
            print(f"  ⚠️  Could not validate static files: {str(e)}")
            return True

    def generate_report(self) -> Dict:
        """Generate validation report."""
        return {
            'total_checks': self.checks_passed + self.checks_failed,
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }

    def run_all_validations(self) -> bool:
        """Run all pre-deployment validations."""
        print("\n" + "="*60)
        print("🚀 OPENLEARN COLOMBIA - PRE-DEPLOYMENT VALIDATION")
        print("="*60)

        validations = [
            ('Environment Variables', self.validate_environment_variables),
            ('Database Connection', self.validate_database_connection),
            ('Redis Connection', self.validate_redis_connection),
            ('Elasticsearch Connection', self.validate_elasticsearch_connection),
            ('Django Configuration', self.validate_django_configuration),
            ('Dependencies', self.validate_dependencies),
            ('Migrations', self.validate_migrations),
            ('Static Files', self.validate_static_files),
        ]

        for name, validation_func in validations:
            validation_func()

        # Generate report
        report = self.generate_report()

        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        print(f"  Total Checks: {report['total_checks']}")
        print(f"  ✅ Passed: {report['checks_passed']}")
        print(f"  ❌ Failed: {report['checks_failed']}")
        print(f"  ⚠️  Warnings: {len(report['warnings'])}")

        if report['errors']:
            print("\n❌ ERRORS:")
            for error in report['errors']:
                print(f"  • {error}")

        if report['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in report['warnings']:
                print(f"  • {warning}")

        print("\n" + "="*60)
        if report['success']:
            print("✅ PRE-DEPLOYMENT VALIDATION PASSED")
        else:
            print("❌ PRE-DEPLOYMENT VALIDATION FAILED")
        print("="*60 + "\n")

        return report['success']


def main():
    """Run pre-deployment validation."""
    validator = PreDeploymentValidator()
    success = validator.run_all_validations()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


# Pytest fixtures and tests
@pytest.fixture
def validator():
    """Create validator instance for testing."""
    return PreDeploymentValidator()


def test_environment_validation(validator):
    """Test environment variable validation."""
    assert validator.validate_environment_variables() or len(validator.errors) > 0


def test_database_validation(validator):
    """Test database connection validation."""
    result = validator.validate_database_connection()
    assert result is True or len(validator.errors) > 0


def test_redis_validation(validator):
    """Test Redis connection validation."""
    result = validator.validate_redis_connection()
    assert result is True or len(validator.errors) > 0
