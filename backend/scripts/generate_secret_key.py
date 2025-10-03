#!/usr/bin/env python3
"""
Production-Grade Secret Key Generator

Generates cryptographically secure secret keys for FastAPI applications.
Uses Python's secrets module for CSPRNG (Cryptographically Secure Pseudo-Random Number Generator).

Usage:
    python scripts/generate_secret_key.py [--bytes BYTES]

Options:
    --bytes BYTES    Number of bytes for the key (default: 64)

Output:
    Prints a URL-safe base64-encoded secret key suitable for production use.

Security Notes:
    - NEVER commit the generated key to version control
    - Store the key in environment variables or secure vaults
    - Rotate keys periodically in production
    - Use different keys for different environments
"""

import argparse
import secrets
import sys


def generate_secret_key(num_bytes: int = 64) -> str:
    """
    Generate a cryptographically secure secret key.

    Args:
        num_bytes: Number of random bytes to generate (default: 64)

    Returns:
        URL-safe base64-encoded secret key

    Security:
        Uses secrets.token_urlsafe() which:
        - Uses os.urandom() for cryptographic randomness
        - Is suitable for security/cryptographic use
        - Generates URL-safe base64-encoded strings
    """
    return secrets.token_urlsafe(num_bytes)


def main():
    """Main entry point for secret key generation."""
    parser = argparse.ArgumentParser(
        description="Generate cryptographically secure secret keys for FastAPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate default 64-byte key
    python scripts/generate_secret_key.py

    # Generate 32-byte key
    python scripts/generate_secret_key.py --bytes 32

    # Save to .env file (append)
    python scripts/generate_secret_key.py >> .env

Security Best Practices:
    1. NEVER commit the key to version control
    2. Store in environment variables or secure vaults
    3. Use different keys for dev/staging/production
    4. Rotate keys periodically
    5. Minimum recommended size: 32 bytes
        """
    )

    parser.add_argument(
        "--bytes",
        type=int,
        default=64,
        help="Number of bytes for the key (default: 64, minimum: 32)",
    )

    parser.add_argument(
        "--format",
        choices=["raw", "env", "export"],
        default="raw",
        help="Output format: raw (key only), env (.env format), export (shell export)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational messages",
    )

    args = parser.parse_args()

    # Validate minimum key size
    if args.bytes < 32:
        print("ERROR: Minimum key size is 32 bytes for security", file=sys.stderr)
        sys.exit(1)

    # Generate the key
    secret_key = generate_secret_key(args.bytes)

    # Output in requested format
    if args.format == "raw":
        if not args.quiet:
            print("# Generated SECRET_KEY (store securely, DO NOT commit to git)")
            print("# Key size:", args.bytes, "bytes")
            print()
        print(secret_key)

    elif args.format == "env":
        if not args.quiet:
            print("# Add this to your .env file (DO NOT commit to git)")
            print()
        print(f"SECRET_KEY={secret_key}")

    elif args.format == "export":
        if not args.quiet:
            print("# Shell export format (for Docker/CI/CD)")
            print()
        print(f"export SECRET_KEY={secret_key}")

    if not args.quiet:
        print("\n# Security Reminders:", file=sys.stderr)
        print("# - NEVER commit this key to version control", file=sys.stderr)
        print("# - Store in environment variables or secure vaults", file=sys.stderr)
        print("# - Use different keys for different environments", file=sys.stderr)
        print("# - Rotate keys periodically in production", file=sys.stderr)


if __name__ == "__main__":
    main()
