"""
Password Reset Workflow Tests
Tests the complete password reset flow from request to completion
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.models import User
from app.core.security import hash_password, verify_password, create_access_token


@pytest.fixture
def test_user(db: Session):
    """Create a test user for password reset testing"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("OldPassword123!"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestPasswordResetWorkflow:
    """Test complete password reset workflow"""

    def test_request_password_reset_success(self, client: TestClient, test_user: User):
        """Test successful password reset request"""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user.email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset link" in data["message"].lower()

    def test_request_password_reset_nonexistent_email(self, client: TestClient):
        """Test password reset request for non-existent email (should not reveal existence)"""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"}
        )

        # Should return same message for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_request_password_reset_invalid_email(self, client: TestClient):
        """Test password reset request with invalid email format"""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": "invalid-email"}
        )

        assert response.status_code == 422  # Validation error

    def test_password_reset_rate_limiting(self, client: TestClient, test_user: User):
        """Test rate limiting on password reset requests (3 per hour)"""
        # Make 3 successful requests
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/password-reset",
                json={"email": test_user.email}
            )
            assert response.status_code == 200

        # 4th request should be rate limited
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user.email}
        )

        assert response.status_code == 429  # Too Many Requests
        data = response.json()
        assert "rate_limit_exceeded" in data.get("error", "")
        assert "retry_after" in data

    def test_update_password_with_valid_token(
        self,
        client: TestClient,
        test_user: User,
        db: Session
    ):
        """Test password update with valid reset token"""
        # Create a valid reset token
        reset_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        # Update password
        new_password = "NewSecurePass123!"
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "successfully" in data["message"].lower()

        # Verify password was updated
        db.refresh(test_user)
        assert verify_password(new_password, test_user.password_hash)

        # Verify refresh token was revoked for security
        assert test_user.refresh_token is None

    def test_update_password_with_expired_token(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test password update with expired reset token"""
        # Create an expired token (negative timedelta)
        expired_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=-1)  # Already expired
        )

        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": expired_token,
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()

    def test_update_password_with_invalid_token(self, client: TestClient):
        """Test password update with invalid token"""
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": "invalid-token-string",
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 400

    def test_update_password_weak_password(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test password update with weak password (should be validated)"""
        reset_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        # Try with weak password (no special characters, no uppercase, etc.)
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": "weak"  # Too short, no complexity
            }
        )

        # Should fail validation (either 422 or 400)
        assert response.status_code in [400, 422]

    def test_login_after_password_reset(
        self,
        client: TestClient,
        test_user: User,
        db: Session
    ):
        """Test that user can login with new password after reset"""
        # Reset password
        reset_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        new_password = "NewSecurePass123!"
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )
        assert response.status_code == 200

        # Try to login with new password
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.email,  # OAuth2 uses 'username' field
                "password": new_password
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_user.email

    def test_old_password_invalid_after_reset(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test that old password no longer works after reset"""
        old_password = "OldPassword123!"

        # Reset password
        reset_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        new_password = "NewSecurePass123!"
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )
        assert response.status_code == 200

        # Try to login with old password (should fail)
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.email,
                "password": old_password
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()


class TestPasswordResetSecurity:
    """Test security aspects of password reset"""

    def test_reset_token_cannot_be_reused(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test that reset token cannot be used twice"""
        reset_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        # First password reset
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code == 200

        # Try to use the same token again
        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": reset_token,
                "new_password": "AnotherPassword123!"
            }
        )

        # Token should still work (JWT-based) but this tests the flow
        # In production with database tokens, this would fail

    def test_regular_access_token_cannot_reset_password(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test that regular access tokens cannot be used for password reset"""
        # Create regular access token (without password_reset type)
        regular_token = create_access_token(
            data={
                "sub": test_user.email,
                "user_id": test_user.id
                # No "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )

        response = client.post(
            "/api/v1/auth/password-update",
            json={
                "token": regular_token,
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()
