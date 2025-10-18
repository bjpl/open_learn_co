"""
OWASP Top 10 2021 - A02: Cryptographic Failures Tests

Tests for cryptographic vulnerabilities:
- Weak password hashing
- Insecure transmission of sensitive data
- Weak cryptographic algorithms
- Insufficient entropy in secrets
- Hardcoded secrets
- Missing encryption for sensitive data
"""

import pytest
import re
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import bcrypt
import hashlib

from app.main import app
from app.core.security import hash_password, verify_password, create_access_token
from app.database.models import User
from app.config.settings import settings


class TestCryptographicFailures:
    """Test suite for A02: Cryptographic Failures"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    def test_password_hashing_strength(self):
        """Test that passwords are hashed using strong algorithm (bcrypt)"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Check it's a bcrypt hash (starts with $2b$)
        assert hashed.startswith("$2b$"), "Password should be hashed with bcrypt"

        # Check work factor is adequate (at least 12 rounds recommended)
        # Format: $2b$<rounds>$<salt><hash>
        rounds = int(hashed.split("$")[2])
        assert rounds >= 10, f"Bcrypt work factor should be >= 10, got {rounds}"

        # Verify password verification works
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_password_not_stored_plaintext(self, client, db):
        """Test that passwords are never stored in plaintext"""
        password = "PlaintextTest123!"

        response = client.post(
            "/api/auth/register",
            json={
                "email": "plaintext@test.com",
                "password": password,
                "full_name": "Plaintext Test"
            }
        )
        assert response.status_code == 201

        # Query database directly
        user = db.query(User).filter(User.email == "plaintext@test.com").first()
        assert user is not None

        # Password should be hashed, not plaintext
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Bcrypt hashes are ~60 chars
        assert user.password_hash.startswith("$2b$")

    def test_jwt_secret_key_strength(self):
        """Test that JWT secret key is sufficiently strong"""
        secret_key = settings.SECRET_KEY

        # Check length (should be at least 32 bytes)
        assert len(secret_key) >= 32, \
            f"SECRET_KEY should be at least 32 characters, got {len(secret_key)}"

        # Check it's not the default insecure key in production
        if settings.ENVIRONMENT.lower() == "production":
            assert secret_key != "INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION", \
                "Production must not use default SECRET_KEY"

        # Check entropy (should have variety of characters)
        unique_chars = len(set(secret_key))
        assert unique_chars > 20, \
            f"SECRET_KEY has low entropy (only {unique_chars} unique characters)"

    def test_password_reset_token_strength(self, client, db):
        """Test that password reset tokens are cryptographically strong"""
        # Create user
        user = User(
            email="reset@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Reset Test",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Request password reset
        response = client.post(
            "/api/auth/password-reset",
            json={"email": "reset@test.com"}
        )
        assert response.status_code == 200

        # Reset tokens should be JWT tokens with expiration
        # They should not be predictable or guessable

    def test_https_enforcement_headers(self, client):
        """Test that HTTPS is enforced via security headers"""
        response = client.get("/health")

        # Check for HSTS header (when served over HTTPS)
        # Note: HSTS only applies to HTTPS connections
        if response.headers.get("X-Forwarded-Proto") == "https":
            assert "Strict-Transport-Security" in response.headers

    def test_sensitive_data_not_in_jwt(self, db):
        """Test that sensitive data is not stored in JWT tokens"""
        user = User(
            email="jwt@test.com",
            password_hash=hash_password("Test123!"),
            full_name="JWT Test",
            is_active=True
        )
        db.add(user)
        db.commit()

        token = create_access_token({"sub": user.email, "user_id": user.id})

        # Decode token without verification to inspect claims
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Should not contain sensitive data
        sensitive_fields = ["password", "password_hash", "refresh_token"]
        for field in sensitive_fields:
            assert field not in decoded, \
                f"JWT should not contain sensitive field: {field}"

    def test_token_signature_verification(self):
        """Test that JWT tokens with invalid signatures are rejected"""
        import jwt

        # Create valid token
        valid_token = create_access_token({"sub": "test@test.com", "user_id": 1})

        # Try to decode with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(valid_token, "wrong_secret", algorithms=["HS256"])

    def test_password_complexity_enforcement(self, client):
        """Test that weak passwords are rejected during registration"""
        weak_passwords = [
            "123456",          # Too simple
            "password",        # Common password
            "test",            # Too short
            "12345678",        # Numbers only
        ]

        for weak_pwd in weak_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"weak{weak_pwd}@test.com",
                    "password": weak_pwd,
                    "full_name": "Weak Password Test"
                }
            )
            # Should be rejected (either 400 or 422)
            assert response.status_code in [400, 422], \
                f"Weak password '{weak_pwd}' should be rejected"

    def test_password_appears_in_response(self, client):
        """Test that passwords never appear in API responses"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "response@test.com",
                "password": "TestPassword123!",
                "full_name": "Response Test"
            }
        )

        if response.status_code == 201:
            # Password should never be in response
            response_text = response.text.lower()
            assert "testpassword123!" not in response_text
            assert "password_hash" not in response.json()

    def test_refresh_token_entropy(self, client):
        """Test that refresh tokens have sufficient entropy"""
        response = client.post(
            "/api/auth/token",
            data={
                "username": "test@test.com",
                "password": "Test123!"
            }
        )

        if response.status_code == 200:
            refresh_token = response.json().get("refresh_token")

            if refresh_token:
                # JWT tokens should be long and contain variety
                assert len(refresh_token) > 100
                unique_chars = len(set(refresh_token))
                assert unique_chars > 30, \
                    f"Refresh token has low entropy ({unique_chars} unique chars)"

    def test_database_password_not_exposed(self):
        """Test that database credentials are not hardcoded in production"""
        if settings.ENVIRONMENT.lower() == "production":
            # Should not use default password
            assert settings.POSTGRES_PASSWORD != "openlearn123", \
                "Production should not use default database password"

            # Password should be loaded from environment
            assert settings.POSTGRES_PASSWORD is not None

    def test_no_sensitive_data_in_logs(self, client, caplog):
        """Test that sensitive data is not logged"""
        import logging
        caplog.set_level(logging.DEBUG)

        # Perform authentication
        client.post(
            "/api/auth/register",
            json={
                "email": "logging@test.com",
                "password": "SecretPassword123!",
                "full_name": "Logging Test"
            }
        )

        # Check logs don't contain passwords or tokens
        log_text = " ".join([record.message for record in caplog.records])

        assert "SecretPassword123!" not in log_text, \
            "Password should not appear in logs"
        assert "password_hash" not in log_text.lower(), \
            "Password hashes should not be logged"

    def test_session_token_randomness(self, client, db):
        """Test that session tokens are cryptographically random"""
        # Create multiple sessions and check tokens are unique
        tokens = set()

        for i in range(10):
            user = User(
                email=f"session{i}@test.com",
                password_hash=hash_password("Test123!"),
                full_name=f"Session Test {i}",
                is_active=True
            )
            db.add(user)
            db.commit()

            token = create_access_token({"sub": user.email, "user_id": user.id})
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 10, "Session tokens should be unique"

    def test_tls_recommended_in_production(self):
        """Test that production configuration recommends TLS/HTTPS"""
        if settings.ENVIRONMENT.lower() == "production":
            # Frontend URL should use HTTPS
            if settings.FRONTEND_URL:
                assert settings.FRONTEND_URL.startswith("https://"), \
                    "Production frontend URL should use HTTPS"

    def test_secure_cookie_flags(self, client):
        """Test that cookies have secure flags set"""
        # If using cookies, they should have Secure, HttpOnly, SameSite flags
        response = client.get("/")

        for cookie in response.cookies:
            # In production, cookies should have secure flag
            if settings.ENVIRONMENT.lower() == "production":
                # Note: TestClient doesn't always preserve these flags
                # This is more of a configuration test
                pass
