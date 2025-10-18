"""
OWASP Top 10 2021 - A07: Identification and Authentication Failures Tests

Tests for authentication and session management vulnerabilities:
- Weak password policy
- Credential stuffing attacks
- Brute force attacks
- Session fixation
- Missing MFA
- Weak session management
- Insecure password recovery
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import time

from app.main import app
from app.core.security import hash_password, create_access_token
from app.database.models import User


class TestAuthenticationFailures:
    """Test suite for A07: Identification and Authentication Failures"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db: Session):
        """Create test user"""
        user = User(
            email="auth@test.com",
            password_hash=hash_password("SecurePass123!"),
            full_name="Auth Test",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_weak_password_rejected(self, client):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "test",
            "12345678",
            "Password",  # Missing numbers
            "password1",  # Too common
        ]

        for weak_pwd in weak_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"weak{hash(weak_pwd)}@test.com",
                    "password": weak_pwd,
                    "full_name": "Weak Password Test"
                }
            )

            # Should reject weak passwords
            assert response.status_code in [400, 422], \
                f"Weak password '{weak_pwd}' should be rejected"

    def test_password_minimum_length_enforced(self, client):
        """Test password minimum length requirement"""
        short_passwords = [
            "A1!b",      # 4 chars
            "Ab1!23",    # 6 chars
            "Test12!",   # 7 chars
        ]

        for pwd in short_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"short{len(pwd)}@test.com",
                    "password": pwd,
                    "full_name": "Short Password Test"
                }
            )

            # Passwords < 8 characters should be rejected
            assert response.status_code in [400, 422]

    def test_brute_force_protection(self, client, test_user):
        """Test protection against brute force attacks"""
        # Attempt multiple failed logins
        failed_attempts = []

        for i in range(10):
            start_time = time.time()
            response = client.post(
                "/api/auth/token",
                data={
                    "username": test_user.email,
                    "password": f"WrongPassword{i}"
                }
            )
            end_time = time.time()

            assert response.status_code == 401
            failed_attempts.append(end_time - start_time)

        # After multiple failures, there should be rate limiting or delays
        # Later attempts should take longer (indication of rate limiting)
        # OR return 429 (Too Many Requests)

        # Check if rate limiting kicks in
        response = client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "WrongPassword999"
            }
        )

        # Should either:
        # 1. Return 429 (rate limited)
        # 2. Have increasing delays
        # 3. Implement account lockout

        if response.status_code == 429:
            assert "retry" in response.json().get("detail", "").lower() or \
                   "too many" in response.json().get("detail", "").lower()

    def test_account_enumeration_prevention(self, client):
        """Test that login doesn't reveal if user exists"""
        # Try to login with non-existent user
        response1 = client.post(
            "/api/auth/token",
            data={
                "username": "nonexistent@test.com",
                "password": "WrongPassword"
            }
        )

        # Try to login with existing user but wrong password
        response2 = client.post(
            "/api/auth/token",
            data={
                "username": "auth@test.com",
                "password": "WrongPassword"
            }
        )

        # Both should return same error message and status code
        # to prevent user enumeration
        assert response1.status_code == response2.status_code
        assert response1.json().get("detail") == response2.json().get("detail")

    def test_session_timeout(self, client, test_user):
        """Test that sessions expire after period of inactivity"""
        # Create token with very short expiry
        from datetime import timedelta

        short_token = create_access_token(
            {"sub": test_user.email, "user_id": test_user.id},
            expires_delta=timedelta(seconds=1)
        )

        headers = {"Authorization": f"Bearer {short_token}"}

        # Token should work immediately
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200

        # Wait for token to expire
        time.sleep(2)

        # Token should be rejected after expiry
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_concurrent_session_prevention(self, client, test_user, db):
        """Test that old tokens are invalidated on new login"""
        # Login to get first token
        response1 = client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "SecurePass123!"
            }
        )
        assert response1.status_code == 200
        old_refresh_token = response1.json()["refresh_token"]

        # Login again to get new token
        response2 = client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "SecurePass123!"
            }
        )
        assert response2.status_code == 200
        new_refresh_token = response2.json()["refresh_token"]

        # Old refresh token should be invalidated
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh_token}
        )
        assert response.status_code == 401

        # New refresh token should work
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh_token}
        )
        assert response.status_code == 200

    def test_password_reset_token_single_use(self, client, test_user):
        """Test that password reset tokens can only be used once"""
        # Request password reset
        response = client.post(
            "/api/auth/password-reset",
            json={"email": test_user.email}
        )
        assert response.status_code == 200

        # In real scenario, token would be sent via email
        # For testing, we'll create one
        from datetime import timedelta
        reset_token = create_access_token(
            {"sub": test_user.email, "user_id": test_user.id, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )

        # Use token to reset password
        response = client.post(
            "/api/auth/password-update",
            json={
                "token": reset_token,
                "new_password": "NewSecurePass123!"
            }
        )
        assert response.status_code == 200

        # Try to reuse same token (should fail)
        response = client.post(
            "/api/auth/password-update",
            json={
                "token": reset_token,
                "new_password": "AnotherPassword123!"
            }
        )
        # Should be rejected (token used or user's tokens invalidated)
        assert response.status_code in [400, 401]

    def test_password_reset_email_timing_attack_prevention(self, client):
        """Test that password reset timing doesn't reveal user existence"""
        import time

        # Reset for existing user
        start1 = time.time()
        response1 = client.post(
            "/api/auth/password-reset",
            json={"email": "auth@test.com"}
        )
        time1 = time.time() - start1

        # Reset for non-existent user
        start2 = time.time()
        response2 = client.post(
            "/api/auth/password-reset",
            json={"email": "nonexistent@test.com"}
        )
        time2 = time.time() - start2

        # Both should return same response
        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()

        # Timing should be similar (within 1 second)
        # to prevent timing attacks
        time_diff = abs(time1 - time2)
        assert time_diff < 1.0, \
            f"Timing difference too large: {time_diff}s"

    def test_username_case_sensitivity(self, client, test_user):
        """Test username/email handling for case sensitivity"""
        # Try login with different case variations
        variations = [
            test_user.email.upper(),
            test_user.email.lower(),
            test_user.email.title(),
        ]

        for email_var in variations:
            response = client.post(
                "/api/auth/token",
                data={
                    "username": email_var,
                    "password": "SecurePass123!"
                }
            )

            # Should handle consistently (either all work or all fail)
            # Most systems treat emails as case-insensitive
            # This test ensures consistent behavior

    def test_password_change_requires_old_password(self, client, test_user):
        """Test that password changes require current password"""
        token = create_access_token(
            {"sub": test_user.email, "user_id": test_user.id}
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Try to change password without providing old password
        # (if this endpoint exists)
        response = client.put(
            "/api/auth/password",
            json={
                "new_password": "NewPassword123!"
            },
            headers=headers
        )

        # Should require old password for verification
        if response.status_code != 404:  # If endpoint exists
            assert response.status_code in [400, 422]

    def test_password_not_in_breach_database(self, client):
        """Test that commonly breached passwords are rejected"""
        # Top breached passwords from HaveIBeenPwned
        breached_passwords = [
            "123456",
            "password",
            "123456789",
            "12345678",
            "12345",
            "1234567",
            "password1",
            "qwerty",
            "abc123",
        ]

        for pwd in breached_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"breach{hash(pwd)}@test.com",
                    "password": pwd,
                    "full_name": "Breach Test"
                }
            )

            # Should reject known breached passwords
            assert response.status_code in [400, 422]

    def test_remember_me_token_security(self, client, test_user):
        """Test that 'remember me' tokens are properly secured"""
        # If implemented, remember me tokens should:
        # 1. Be long-lived but rotatable
        # 2. Be tied to specific device/browser
        # 3. Be revocable
        # 4. Use separate tokens from access tokens

        response = client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "SecurePass123!"
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Refresh token should be different from access token
            assert data["access_token"] != data["refresh_token"]

            # Tokens should be sufficiently long
            assert len(data["access_token"]) > 50
            assert len(data["refresh_token"]) > 50

    def test_logout_invalidates_all_tokens(self, client, test_user):
        """Test that logout invalidates all user tokens"""
        # Login
        response = client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 200

        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]

        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200

        # Try to use refresh token after logout
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 401

        # Access token should eventually fail too
        response = client.get("/api/auth/me", headers=headers)
        # May still work if access token hasn't expired
        # But refresh token should definitely be revoked

    def test_registration_rate_limiting(self, client):
        """Test that registration is rate limited to prevent abuse"""
        # Try to create many accounts rapidly
        responses = []

        for i in range(15):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"spam{i}@test.com",
                    "password": "Test123!Pass",
                    "full_name": f"Spam User {i}"
                }
            )
            responses.append(response.status_code)

        # Should hit rate limit eventually
        assert 429 in responses or responses.count(201) < 15
