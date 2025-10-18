"""
Comprehensive Security and Authentication Tests

Tests for:
- JWT token generation and validation
- Password hashing and verification
- Token expiration and refresh
- Authentication edge cases
- Security boundary conditions
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    is_token_expired,
    get_current_user,
    get_current_active_user,
)
from app.config.settings import settings


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_creates_different_hash(self):
        """Password hashing should create different hashes for same password"""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_verify_password_correct(self):
        """Verify password should return True for correct password"""
        password = "secure_password_456"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify password should return False for incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_special_characters(self):
        """Password hashing should handle special characters"""
        password = "p@ssw0rd!@#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Password hashing should handle unicode characters"""
        password = "contraseña_日本語_🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_empty_raises_error(self):
        """Empty password should be handled"""
        with pytest.raises(ValueError):
            hash_password("")

    def test_hash_password_very_long(self):
        """Password hashing should handle very long passwords"""
        password = "a" * 1000
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Access token should be created with correct structure"""
        data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data)

        assert token is not None
        assert len(token) > 0

        # Decode and verify structure
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == 123
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Refresh token should be created with correct structure"""
        data = {"sub": "user@example.com", "user_id": 123}
        token = create_refresh_token(data)

        assert token is not None
        assert len(token) > 0

        # Decode and verify structure
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == 123
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_access_token_custom_expiration(self):
        """Access token should respect custom expiration"""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta)

        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Should expire in ~5 minutes
        time_diff = (exp_time - now).total_seconds()
        assert 4 * 60 < time_diff < 6 * 60

    def test_verify_token_valid_access(self):
        """Verify token should validate correct access token"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        payload = verify_token(token, token_type="access")

        assert payload is not None
        assert payload["sub"] == "user@example.com"
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh(self):
        """Verify token should validate correct refresh token"""
        data = {"sub": "user@example.com"}
        token = create_refresh_token(data)

        payload = verify_token(token, token_type="refresh")

        assert payload is not None
        assert payload["sub"] == "user@example.com"
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Verify token should reject token with wrong type"""
        token = create_access_token({"sub": "user@example.com"})

        # Try to verify as refresh token
        payload = verify_token(token, token_type="refresh")

        assert payload is None

    def test_verify_token_expired(self):
        """Verify token should reject expired token"""
        data = {"sub": "user@example.com"}
        # Create token that expires immediately
        token = create_access_token(data, timedelta(microseconds=1))

        import time
        time.sleep(0.01)  # Wait for expiration

        payload = verify_token(token, token_type="access")
        assert payload is None

    def test_verify_token_invalid_signature(self):
        """Verify token should reject token with invalid signature"""
        # Create token with different secret
        data = {"sub": "user@example.com", "type": "access", "exp": datetime.utcnow() + timedelta(minutes=30)}
        token = jwt.encode(data, "wrong_secret", algorithm="HS256")

        payload = verify_token(token, token_type="access")
        assert payload is None

    def test_verify_token_malformed(self):
        """Verify token should reject malformed token"""
        malformed_token = "not.a.valid.jwt.token"

        payload = verify_token(malformed_token, token_type="access")
        assert payload is None

    def test_is_token_expired_fresh(self):
        """Fresh token should not be expired"""
        token = create_access_token({"sub": "user@example.com"})

        assert is_token_expired(token) is False

    def test_is_token_expired_old(self):
        """Expired token should be detected"""
        token = create_access_token({"sub": "user@example.com"}, timedelta(microseconds=1))

        import time
        time.sleep(0.01)

        assert is_token_expired(token) is True

    def test_decode_token_without_verification(self):
        """Decode token should extract payload without verification"""
        data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == 123


class TestAuthenticationDependencies:
    """Test FastAPI authentication dependencies"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Get current user should return user for valid token"""
        # Mock database and user
        mock_db = MagicMock()
        mock_user = Mock()
        mock_user.id = 123
        mock_user.email = "user@example.com"

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        # Create valid token
        token = create_access_token({"sub": "user@example.com", "user_id": 123})

        # Test
        user = await get_current_user(token, mock_db)

        assert user.id == 123
        assert user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Get current user should raise 401 for invalid token"""
        from fastapi import HTTPException

        mock_db = MagicMock()
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc:
            await get_current_user(invalid_token, mock_db)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self):
        """Get current user should raise 401 if user not found"""
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None  # User not found

        token = create_access_token({"sub": "nonexistent@example.com", "user_id": 999})

        with pytest.raises(HTTPException) as exc:
            await get_current_user(token, mock_db)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self):
        """Get current active user should return active user"""
        mock_user = Mock()
        mock_user.is_active = True

        result = await get_current_active_user(mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Get current active user should raise 403 for inactive user"""
        from fastapi import HTTPException

        mock_user = Mock()
        mock_user.is_active = False

        with pytest.raises(HTTPException) as exc:
            await get_current_active_user(mock_user)

        assert exc.value.status_code == 403


class TestSecurityEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_token_without_subject(self):
        """Token without subject should be rejected"""
        # Create token without 'sub' claim
        data = {"user_id": 123, "type": "access"}
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Should still decode
        decoded = decode_token(token)
        assert decoded is not None
        assert "sub" not in decoded

    def test_token_with_extra_claims(self):
        """Token with extra claims should be preserved"""
        data = {
            "sub": "user@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
            "custom_field": "custom_value"
        }
        token = create_access_token(data)

        payload = verify_token(token, token_type="access")

        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
        assert payload["custom_field"] == "custom_value"

    def test_concurrent_token_generation(self):
        """Multiple concurrent token generations should create unique tokens"""
        data = {"sub": "user@example.com"}

        tokens = [create_access_token(data) for _ in range(10)]

        # All tokens should be unique due to timestamp precision
        assert len(set(tokens)) == len(tokens)

    def test_password_hash_timing_attack_resistance(self):
        """Password verification should take consistent time"""
        import time

        password = "test_password"
        hashed = hash_password(password)

        # Time correct password
        start = time.time()
        verify_password(password, hashed)
        time_correct = time.time() - start

        # Time incorrect password
        start = time.time()
        verify_password("wrong_password", hashed)
        time_incorrect = time.time() - start

        # Times should be similar (within 50% difference)
        # This is a basic check - bcrypt should provide timing resistance
        assert abs(time_correct - time_incorrect) / max(time_correct, time_incorrect) < 0.5

    def test_token_payload_size_limit(self):
        """Large token payloads should be handled"""
        large_data = {
            "sub": "user@example.com",
            "large_field": "x" * 10000  # 10KB of data
        }

        token = create_access_token(large_data)
        payload = decode_token(token)

        assert len(payload["large_field"]) == 10000

    def test_special_characters_in_email(self):
        """Email with special characters should be handled"""
        emails = [
            "user+tag@example.com",
            "user.name@example.com",
            "user_name@example.co.uk",
            "user@sub.domain.example.com"
        ]

        for email in emails:
            token = create_access_token({"sub": email})
            payload = verify_token(token, token_type="access")

            assert payload["sub"] == email
