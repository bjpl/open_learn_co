#!/usr/bin/env python3
"""
Production Security Validation Script

Validates critical security configurations before deployment.
Run this script in CI/CD pipeline to prevent insecure deployments.

Usage:
    python scripts/validate_security.py [--strict]

Options:
    --strict    Enable strict mode (fails on warnings)

Exit Codes:
    0 - All checks passed
    1 - Critical security issues found
    2 - Warnings found (only fails in strict mode)
"""

import argparse
import os
import sys
from pathlib import Path


class SecurityValidator:
    """Validates security configurations for production deployment."""

    INSECURE_KEYS = [
        "your-secret-key-here-change-in-production",
        "INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION",
        "your-secret-key-change-this-in-production",
        "REPLACE_THIS_IN_PRODUCTION_USE_generate_secret_key_script",
        "secret",
        "changeme",
        "password",
        "test",
    ]

    MINIMUM_KEY_LENGTH = 32  # bytes in URL-safe base64

    def __init__(self, strict: bool = False):
        """Initialize validator."""
        self.strict = strict
        self.errors = []
        self.warnings = []

    def validate_secret_key(self) -> bool:
        """
        Validate SECRET_KEY configuration.

        Checks:
        - Key is set and not empty
        - Key is not a default/insecure value
        - Key meets minimum length requirement
        - Key appears to be properly generated
        """
        secret_key = os.getenv("SECRET_KEY", "")

        # Check if key is set
        if not secret_key:
            self.errors.append("SECRET_KEY is not set in environment")
            return False

        # Check for insecure default values
        for insecure_key in self.INSECURE_KEYS:
            if insecure_key.lower() in secret_key.lower():
                self.errors.append(
                    f"SECRET_KEY contains insecure default value: {insecure_key}"
                )
                return False

        # Check minimum length
        if len(secret_key) < self.MINIMUM_KEY_LENGTH:
            self.errors.append(
                f"SECRET_KEY is too short ({len(secret_key)} chars). "
                f"Minimum: {self.MINIMUM_KEY_LENGTH} chars"
            )
            return False

        # Check key entropy (simple check)
        unique_chars = len(set(secret_key))
        if unique_chars < 20:
            self.warnings.append(
                f"SECRET_KEY has low entropy ({unique_chars} unique chars). "
                "Consider regenerating with scripts/generate_secret_key.py"
            )

        return True

    def validate_environment(self) -> bool:
        """Validate ENVIRONMENT configuration."""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        debug = os.getenv("DEBUG", "False").lower() == "true"

        if environment == "production" and debug:
            self.errors.append(
                "DEBUG mode is enabled in production environment! "
                "This exposes sensitive information."
            )
            return False

        if environment == "production":
            # Additional production checks
            if not os.getenv("SENTRY_DSN"):
                self.warnings.append("SENTRY_DSN not set in production")

            if os.getenv("LOG_LEVEL", "INFO") == "DEBUG":
                self.warnings.append("LOG_LEVEL=DEBUG in production (use INFO or WARNING)")

        return True

    def validate_database(self) -> bool:
        """Validate database configuration."""
        database_url = os.getenv("DATABASE_URL", "")

        if not database_url:
            self.warnings.append("DATABASE_URL is not set")
            return True

        # Check for insecure database passwords in production
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "production":
            insecure_passwords = ["password", "123", "admin", "root"]
            for pwd in insecure_passwords:
                if pwd in database_url.lower():
                    self.errors.append(
                        f"Database URL contains insecure password pattern: {pwd}"
                    )
                    return False

        return True

    def validate_cors(self) -> bool:
        """Validate CORS configuration."""
        cors_origins = os.getenv("CORS_ORIGINS", "")
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            if "*" in cors_origins or not cors_origins:
                self.warnings.append(
                    "CORS_ORIGINS allows all origins (*) in production. "
                    "Specify exact allowed origins."
                )

        return True

    def run_all_checks(self) -> bool:
        """Run all security validation checks."""
        print("=" * 70)
        print("PRODUCTION SECURITY VALIDATION")
        print("=" * 70)
        print()

        checks = [
            ("SECRET_KEY", self.validate_secret_key),
            ("Environment", self.validate_environment),
            ("Database", self.validate_database),
            ("CORS", self.validate_cors),
        ]

        all_passed = True
        for name, check_func in checks:
            print(f"Checking {name}...", end=" ")
            try:
                result = check_func()
                if result:
                    print("✓ PASS")
                else:
                    print("✗ FAIL")
                    all_passed = False
            except Exception as e:
                print(f"✗ ERROR: {e}")
                self.errors.append(f"{name} check failed: {e}")
                all_passed = False

        print()
        return all_passed

    def print_results(self) -> int:
        """Print validation results and return exit code."""
        # Print errors
        if self.errors:
            print("=" * 70)
            print("CRITICAL SECURITY ISSUES")
            print("=" * 70)
            for error in self.errors:
                print(f"✗ {error}")
            print()

        # Print warnings
        if self.warnings:
            print("=" * 70)
            print("SECURITY WARNINGS")
            print("=" * 70)
            for warning in self.warnings:
                print(f"⚠ {warning}")
            print()

        # Print summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print()

        # Determine exit code
        if self.errors:
            print("✗ VALIDATION FAILED - Critical security issues found")
            print("DO NOT DEPLOY until all issues are resolved!")
            return 1
        elif self.warnings and self.strict:
            print("⚠ VALIDATION WARNING - Warnings found in strict mode")
            return 2
        else:
            print("✓ VALIDATION PASSED - All security checks passed")
            if self.warnings:
                print("Note: Some warnings were found but are not blocking")
            return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate production security configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (warnings fail validation)",
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        help="Load environment from .env file",
    )

    args = parser.parse_args()

    # Load .env file if specified
    if args.env_file:
        if not args.env_file.exists():
            print(f"Error: .env file not found: {args.env_file}", file=sys.stderr)
            sys.exit(1)

        # Simple .env parser
        with open(args.env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

    # Run validation
    validator = SecurityValidator(strict=args.strict)
    validator.run_all_checks()
    exit_code = validator.print_results()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
