#!/usr/bin/env python3
"""
Configuration Validation Script for OpenLearn Colombia Platform

Validates environment configuration before deployment.

Usage:
    python scripts/validate_config.py
    python scripts/validate_config.py --env production
    python scripts/validate_config.py --strict
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import re


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ConfigValidator:
    """Validate application configuration"""

    # Required variables for all environments
    REQUIRED_BASE = [
        'ENVIRONMENT',
        'SECRET_KEY',
        'POSTGRES_HOST',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB',
        'REDIS_HOST',
        'CORS_ORIGINS',
    ]

    # Additional required variables for production
    REQUIRED_PRODUCTION = [
        'SENTRY_DSN',
        'REDIS_PASSWORD',
        'DB_POOL_SIZE',
        'METRICS_ENABLED',
    ]

    # Recommended variables
    RECOMMENDED_PRODUCTION = [
        'SMTP_HOST',
        'ALERT_EMAIL_TO',
        'SLACK_WEBHOOK_URL',
        'DANE_API_KEY',
    ]

    # Insecure default values
    INSECURE_DEFAULTS = {
        'SECRET_KEY': [
            'INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION',
            'dev-insecure-key',
            'REPLACE_WITH_GENERATED_SECRET_KEY',
            'REPLACE_',
        ],
        'POSTGRES_PASSWORD': [
            'openlearn123',
            'password',
            'postgres',
            'REPLACE_',
        ],
        'REDIS_PASSWORD': [
            'redis',
            'password',
            'REPLACE_',
        ],
    }

    def __init__(self, environment: str = 'development', strict: bool = False):
        self.environment = environment
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate(self) -> bool:
        """Run all validation checks. Returns True if valid."""
        print("=" * 80)
        print(f"VALIDATING {self.environment.upper()} CONFIGURATION")
        print("=" * 80)
        print()

        # Load environment
        self._load_env()

        # Run checks
        self._check_required_variables()
        self._check_secret_key()
        self._check_database_config()
        self._check_redis_config()
        self._check_cors_config()
        self._check_security_settings()
        self._check_monitoring()

        if self.environment == 'production':
            self._check_production_specific()

        # Display results
        self._display_results()

        # Return success status
        return len(self.errors) == 0

    def _load_env(self):
        """Load environment variables from .env file"""
        env_file = Path(__file__).parent.parent / '.env'

        if not env_file.exists():
            self.errors.append(f".env file not found at {env_file}")
            return

        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            self.info.append(f"Loaded configuration from {env_file}")
        except ImportError:
            self.warnings.append("python-dotenv not installed. Reading from system environment only.")

    def _check_required_variables(self):
        """Check all required variables are set"""
        required = self.REQUIRED_BASE.copy()

        if self.environment == 'production':
            required.extend(self.REQUIRED_PRODUCTION)

        for var in required:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Required variable not set: {var}")
            elif value.strip() == '':
                self.errors.append(f"Required variable is empty: {var}")

    def _check_secret_key(self):
        """Validate SECRET_KEY security"""
        secret_key = os.getenv('SECRET_KEY', '')

        if not secret_key:
            self.errors.append("SECRET_KEY is not set")
            return

        # Check length
        if len(secret_key) < 32:
            self.errors.append(f"SECRET_KEY is too short ({len(secret_key)} chars). Minimum: 32 bytes")
        elif len(secret_key) < 64 and self.environment == 'production':
            self.warnings.append(f"SECRET_KEY is short for production ({len(secret_key)} chars). Recommended: 64+ bytes")

        # Check for insecure defaults
        for insecure in self.INSECURE_DEFAULTS.get('SECRET_KEY', []):
            if insecure.lower() in secret_key.lower():
                self.errors.append(f"SECRET_KEY contains insecure default value. Generate a new key!")
                break

        # Check complexity
        if secret_key.isalnum() and len(secret_key) < 50:
            self.warnings.append("SECRET_KEY appears to be simple. Use cryptographically secure generation.")

    def _check_database_config(self):
        """Validate database configuration"""
        password = os.getenv('POSTGRES_PASSWORD', '')

        # Check password strength
        if password:
            if len(password) < 8:
                self.errors.append(f"POSTGRES_PASSWORD is too weak ({len(password)} chars). Minimum: 8 chars")
            elif len(password) < 16 and self.environment == 'production':
                self.warnings.append(f"POSTGRES_PASSWORD is weak for production. Recommended: 16+ chars")

            # Check for insecure defaults
            for insecure in self.INSECURE_DEFAULTS.get('POSTGRES_PASSWORD', []):
                if insecure.lower() in password.lower():
                    self.errors.append("POSTGRES_PASSWORD uses insecure default value")
                    break

        # Check pool settings
        pool_size = os.getenv('DB_POOL_SIZE')
        if pool_size:
            try:
                size = int(pool_size)
                if size < 5:
                    self.warnings.append(f"DB_POOL_SIZE is low ({size}). Consider 10-20 for production")
                elif size > 100:
                    self.warnings.append(f"DB_POOL_SIZE is very high ({size}). May exhaust connections")
            except ValueError:
                self.errors.append(f"DB_POOL_SIZE is not a valid integer: {pool_size}")

    def _check_redis_config(self):
        """Validate Redis configuration"""
        if self.environment == 'production':
            password = os.getenv('REDIS_PASSWORD', '')
            if not password:
                self.errors.append("REDIS_PASSWORD must be set in production")
            else:
                # Check for insecure defaults
                for insecure in self.INSECURE_DEFAULTS.get('REDIS_PASSWORD', []):
                    if insecure.lower() in password.lower():
                        self.errors.append("REDIS_PASSWORD uses insecure default value")
                        break

    def _check_cors_config(self):
        """Validate CORS configuration"""
        origins = os.getenv('CORS_ORIGINS', '')

        if not origins:
            self.warnings.append("CORS_ORIGINS is not set")
            return

        # Check for wildcards in production
        if self.environment == 'production':
            if '*' in origins:
                self.errors.append("CORS_ORIGINS contains wildcard (*) in production. Specify exact domains!")

            # Check for localhost in production
            if 'localhost' in origins or '127.0.0.1' in origins:
                self.warnings.append("CORS_ORIGINS contains localhost in production")

            # Check protocol
            if 'http://' in origins and 'https://' not in origins:
                self.warnings.append("CORS_ORIGINS uses HTTP in production. Use HTTPS!")

    def _check_security_settings(self):
        """Validate security settings"""
        debug = os.getenv('DEBUG', '').lower()

        if self.environment == 'production':
            if debug in ('true', '1', 'yes'):
                self.errors.append("DEBUG must be False in production!")

        # Check log level
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        if self.environment == 'production':
            if log_level.upper() == 'DEBUG':
                self.warnings.append("LOG_LEVEL=DEBUG in production may leak sensitive information")

    def _check_monitoring(self):
        """Validate monitoring configuration"""
        sentry_dsn = os.getenv('SENTRY_DSN', '')

        if self.environment == 'production':
            if not sentry_dsn:
                self.warnings.append("SENTRY_DSN not set. Error tracking recommended for production")
            elif 'REPLACE_' in sentry_dsn:
                self.errors.append("SENTRY_DSN contains placeholder value")

        # Check metrics
        metrics_enabled = os.getenv('METRICS_ENABLED', '').lower()
        if self.environment == 'production' and metrics_enabled in ('false', '0', 'no'):
            self.warnings.append("METRICS_ENABLED is disabled. Monitoring recommended for production")

    def _check_production_specific(self):
        """Production-specific validation checks"""
        # Check recommended variables
        for var in self.RECOMMENDED_PRODUCTION:
            value = os.getenv(var, '')
            if not value:
                self.warnings.append(f"Recommended for production but not set: {var}")

        # Check alerting
        has_email = os.getenv('SMTP_HOST') and os.getenv('ALERT_EMAIL_TO')
        has_slack = os.getenv('SLACK_WEBHOOK_URL')

        if not (has_email or has_slack):
            self.warnings.append("No alerting configured (email or Slack). Recommended for production")

        # Check NLP model
        nlp_model = os.getenv('NLP_MODEL', '')
        if nlp_model and 'sm' in nlp_model:
            self.warnings.append("Using small NLP model in production. Consider 'lg' for better accuracy")

    def _display_results(self):
        """Display validation results"""
        print("\nVALIDATION RESULTS")
        print("=" * 80)

        # Info messages
        if self.info:
            print("\nℹ️  INFO:")
            for msg in self.info:
                print(f"  • {msg}")

        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for msg in self.warnings:
                print(f"  • {msg}")

        # Errors
        if self.errors:
            print("\n❌ ERRORS:")
            for msg in self.errors:
                print(f"  • {msg}")

        print("\n" + "=" * 80)

        # Summary
        if self.errors:
            print(f"\n❌ VALIDATION FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            print("\nFix all errors before deploying to production!")
            return False
        elif self.warnings:
            if self.strict:
                print(f"\n⚠️  VALIDATION FAILED (STRICT MODE): {len(self.warnings)} warning(s)")
                print("\nResolve warnings or remove --strict flag")
                return False
            else:
                print(f"\n✅ VALIDATION PASSED: {len(self.warnings)} warning(s)")
                print("\nReview warnings before deploying to production")
                return True
        else:
            print("\n✅ VALIDATION PASSED: Configuration is valid!")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate OpenLearn environment configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate development environment
  python scripts/validate_config.py

  # Validate production environment
  python scripts/validate_config.py --env production

  # Strict mode (warnings = errors)
  python scripts/validate_config.py --env production --strict

Exit Codes:
  0 = Validation passed
  1 = Validation failed (errors found)
  2 = Strict mode failed (warnings found)
        """
    )

    parser.add_argument(
        '--env',
        choices=['development', 'staging', 'production'],
        default='development',
        help='Environment to validate (default: development)'
    )

    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )

    args = parser.parse_args()

    # Run validation
    validator = ConfigValidator(environment=args.env, strict=args.strict)
    success = validator.validate()

    # Exit with appropriate code
    if success:
        sys.exit(0)
    else:
        if args.strict and validator.warnings and not validator.errors:
            sys.exit(2)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
