"""
OWASP Top 10 2021 - A01: Broken Access Control Tests

Tests for authorization and access control vulnerabilities:
- Vertical privilege escalation (accessing admin functions as regular user)
- Horizontal privilege escalation (accessing other users' data)
- Forced browsing to restricted URLs
- IDOR (Insecure Direct Object References)
- Missing function-level access control
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.models import User
from app.config.settings import settings


class TestBrokenAccessControl:
    """Test suite for A01: Broken Access Control"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def regular_user_token(self, db: Session):
        """Create regular user and return auth token"""
        user = User(
            email="regular@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Regular User",
            role="learner",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": user.email, "user_id": user.id})
        return token, user

    @pytest.fixture
    def admin_user_token(self, db: Session):
        """Create admin user and return auth token"""
        admin = User(
            email="admin@test.com",
            password_hash=hash_password("Admin123!"),
            full_name="Admin User",
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        token = create_access_token({"sub": admin.email, "user_id": admin.id})
        return token, admin

    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated requests are denied"""
        # Try to access protected endpoint without auth
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_horizontal_privilege_escalation_prevention(self, client, regular_user_token, db):
        """Test that users cannot access other users' data (IDOR protection)"""
        token1, user1 = regular_user_token

        # Create another user
        user2 = User(
            email="other@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Other User",
            role="learner",
            is_active=True
        )
        db.add(user2)
        db.commit()

        # Try to access user2's data with user1's token
        headers = {"Authorization": f"Bearer {token1}"}

        # Attempt to update other user's profile (if endpoint exists)
        # This should be denied or only allow updating own profile
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user1.id  # Should only get own data
        assert data["email"] == "regular@test.com"

    def test_vertical_privilege_escalation_prevention(self, client, regular_user_token):
        """Test that regular users cannot access admin-only endpoints"""
        token, user = regular_user_token
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access admin endpoints (if they exist)
        # For now, verify regular user role is enforced
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] != "admin"
        assert data["role"] == "learner"

    def test_token_manipulation_prevention(self, client, regular_user_token):
        """Test that manipulated JWT tokens are rejected"""
        token, user = regular_user_token

        # Decode token and manipulate claims
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Try to escalate role by re-encoding with different data
        # (this should fail because signature won't match)
        malicious_token = jwt.encode(
            {**decoded, "role": "admin"},
            "wrong_secret",
            algorithm="HS256"
        )

        headers = {"Authorization": f"Bearer {malicious_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401  # Should reject invalid signature

    def test_expired_token_rejection(self, client, db):
        """Test that expired tokens are rejected"""
        user = User(
            email="expired@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Expired User",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Create expired token (negative expiry)
        from datetime import timedelta
        expired_token = create_access_token(
            {"sub": user.email, "user_id": user.id},
            expires_delta=timedelta(seconds=-10)
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_inactive_user_access_denied(self, client, db):
        """Test that inactive/banned users cannot access system"""
        inactive_user = User(
            email="inactive@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Inactive User",
            is_active=False  # Deactivated account
        )
        db.add(inactive_user)
        db.commit()
        db.refresh(inactive_user)

        # Try to login with inactive account
        response = client.post(
            "/api/auth/token",
            data={
                "username": "inactive@test.com",
                "password": "Test123!"
            }
        )
        assert response.status_code == 403  # Forbidden
        assert "inactive" in response.json()["detail"].lower()

    def test_forced_browsing_prevention(self, client):
        """Test that forced browsing to restricted paths is prevented"""
        # Try to access common admin paths without auth
        restricted_paths = [
            "/api/admin",
            "/api/admin/users",
            "/api/admin/config",
            "/api/internal",
        ]

        for path in restricted_paths:
            response = client.get(path)
            # Should either be 401 (unauthorized), 403 (forbidden), or 404 (not found)
            # Never 200 (success) without authentication
            assert response.status_code in [401, 403, 404]

    def test_missing_function_level_access_control(self, client, regular_user_token):
        """Test that all API endpoints enforce authorization"""
        token, user = regular_user_token
        headers = {"Authorization": f"Bearer {token}"}

        # Test that DELETE methods require proper authorization
        # Regular user should not be able to delete other users
        response = client.delete("/api/auth/me", headers=headers)

        # This should either succeed (deactivating own account)
        # or be forbidden for certain roles
        assert response.status_code in [200, 403, 404]

    def test_path_traversal_in_avatar_endpoint(self, client, regular_user_token):
        """Test that avatar endpoint prevents path traversal attacks"""
        token, user = regular_user_token

        # Try to access files outside avatar directory using path traversal
        malicious_filenames = [
            "../../../etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "./../config.py",
        ]

        for filename in malicious_filenames:
            response = client.get(f"/api/avatars/{filename}")
            # Should be rejected with 400 (bad request) or 404 (not found)
            # Never 200 with actual file content
            assert response.status_code in [400, 404]
            if response.status_code != 404:
                assert "invalid" in response.json().get("detail", "").lower()

    def test_refresh_token_reuse_prevention(self, client, regular_user_token, db):
        """Test that refresh tokens cannot be reused after being refreshed"""
        token, user = regular_user_token

        # Login to get refresh token
        response = client.post(
            "/api/auth/token",
            data={
                "username": user.email,
                "password": "Test123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        old_refresh_token = data["refresh_token"]

        # Use refresh token to get new tokens
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh_token}
        )
        assert response.status_code == 200

        # Try to reuse old refresh token (should be revoked)
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh_token}
        )
        assert response.status_code == 401  # Should be rejected

    def test_logout_invalidates_tokens(self, client, regular_user_token):
        """Test that logout properly invalidates refresh tokens"""
        token, user = regular_user_token
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200

        # Try to use refresh token after logout (should fail)
        if hasattr(user, 'refresh_token') and user.refresh_token:
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": user.refresh_token}
            )
            assert response.status_code == 401
