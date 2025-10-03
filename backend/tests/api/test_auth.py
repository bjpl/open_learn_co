"""
Comprehensive tests for JWT authentication system

Tests cover:
- User registration
- Login flow with access + refresh tokens
- Token validation
- Token refresh mechanism
- Invalid credentials handling
- Expired tokens
- Password reset flow
- Account deactivation
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.models import Base, User
from app.database.connection import get_db
from app.core.security import hash_password, create_access_token, create_refresh_token
from app.config.settings import settings

# Configure in-memory SQLite for testing
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop database tables for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "username": "testuser"
    }


@pytest.fixture
def registered_user(test_user_data):
    """Create a registered user in the database"""
    db = TestingSessionLocal()
    user = User(
        email=test_user_data["email"],
        password_hash=hash_password(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        username=test_user_data["username"],
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


# ============================================================================
# User Registration Tests
# ============================================================================

def test_user_registration_success(test_user_data):
    """Test successful user registration"""
    response = client.post("/api/auth/register", json=test_user_data)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["username"] == test_user_data["username"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_user_registration_duplicate_email(test_user_data, registered_user):
    """Test registration with duplicate email fails"""
    response = client.post("/api/auth/register", json=test_user_data)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_user_registration_duplicate_username(test_user_data, registered_user):
    """Test registration with duplicate username fails"""
    new_user_data = test_user_data.copy()
    new_user_data["email"] = "different@example.com"

    response = client.post("/api/auth/register", json=new_user_data)

    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()


def test_user_registration_invalid_email():
    """Test registration with invalid email fails"""
    response = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })

    assert response.status_code == 422  # Validation error


def test_user_registration_short_password():
    """Test registration with short password fails"""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "short",
        "full_name": "Test User"
    })

    assert response.status_code == 422  # Validation error


# ============================================================================
# Login Tests
# ============================================================================

def test_login_success(test_user_data, registered_user):
    """Test successful login returns access and refresh tokens"""
    response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],  # OAuth2 uses 'username' field
        "password": test_user_data["password"]
    })

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Verify user object is returned
    assert data["user"]["email"] == test_user_data["email"]
    assert data["user"]["full_name"] == test_user_data["full_name"]
    assert data["user"]["is_active"] is True


def test_login_invalid_email(test_user_data):
    """Test login with invalid email fails"""
    response = client.post("/api/auth/token", data={
        "username": "nonexistent@example.com",
        "password": test_user_data["password"]
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_invalid_password(test_user_data, registered_user):
    """Test login with invalid password fails"""
    response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": "WrongPassword123!"
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_inactive_user(test_user_data, registered_user):
    """Test login with inactive account fails"""
    # Deactivate user
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == test_user_data["email"]).first()
    user.is_active = False
    db.commit()
    db.close()

    response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })

    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


# ============================================================================
# Token Validation Tests
# ============================================================================

def test_verify_valid_token(test_user_data, registered_user):
    """Test token verification with valid token"""
    # Login to get token
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Verify token
    response = client.get(
        "/api/auth/verify-token",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["email"] == test_user_data["email"]


def test_verify_invalid_token():
    """Test token verification with invalid token"""
    response = client.get(
        "/api/auth/verify-token",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


def test_verify_missing_token():
    """Test accessing protected endpoint without token"""
    response = client.get("/api/auth/verify-token")

    assert response.status_code == 401


def test_get_current_user_with_valid_token(test_user_data, registered_user):
    """Test getting current user profile with valid token"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Get profile
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]


# ============================================================================
# Refresh Token Tests
# ============================================================================

def test_refresh_token_success(test_user_data, registered_user):
    """Test refreshing access token with valid refresh token"""
    # Login to get tokens
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    refresh_token = login_response.json()["refresh_token"]
    old_access_token = login_response.json()["access_token"]

    # Refresh token
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != old_access_token  # New token
    assert data["refresh_token"] != refresh_token  # Rotated refresh token
    assert data["user"]["email"] == test_user_data["email"]


def test_refresh_token_invalid():
    """Test refresh with invalid token fails"""
    response = client.post("/api/auth/refresh", json={
        "refresh_token": "invalid_refresh_token"
    })

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_refresh_token_revoked(test_user_data, registered_user):
    """Test refresh with revoked token fails"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    refresh_token = login_response.json()["refresh_token"]

    # Revoke token by logging out
    access_token = login_response.json()["access_token"]
    client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Try to use revoked refresh token
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower()


def test_refresh_token_with_access_token_fails(test_user_data, registered_user):
    """Test that access token cannot be used as refresh token"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Try to refresh with access token
    response = client.post("/api/auth/refresh", json={
        "refresh_token": access_token
    })

    assert response.status_code == 401


# ============================================================================
# Logout Tests
# ============================================================================

def test_logout_success(test_user_data, registered_user):
    """Test successful logout revokes refresh token"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200

    # Verify refresh token is revoked
    refresh_response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert refresh_response.status_code == 401


# ============================================================================
# Password Reset Tests
# ============================================================================

def test_password_reset_request(test_user_data, registered_user):
    """Test password reset request generates token"""
    response = client.post("/api/auth/password-reset", json={
        "email": test_user_data["email"]
    })

    assert response.status_code == 200
    data = response.json()
    assert "reset_token" in data  # In dev mode
    assert data["expires_in"] == 3600


def test_password_reset_nonexistent_email():
    """Test password reset for non-existent email doesn't reveal info"""
    response = client.post("/api/auth/password-reset", json={
        "email": "nonexistent@example.com"
    })

    # Should return success to not reveal user existence
    assert response.status_code == 200


def test_password_update_with_valid_token(test_user_data, registered_user):
    """Test password update with valid reset token"""
    # Request reset token
    reset_response = client.post("/api/auth/password-reset", json={
        "email": test_user_data["email"]
    })
    reset_token = reset_response.json()["reset_token"]

    # Update password
    new_password = "NewSecurePass456!"
    response = client.post("/api/auth/password-update", json={
        "token": reset_token,
        "new_password": new_password
    })

    assert response.status_code == 200

    # Verify can login with new password
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": new_password
    })

    assert login_response.status_code == 200

    # Verify old password doesn't work
    old_login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })

    assert old_login_response.status_code == 401


def test_password_update_invalid_token():
    """Test password update with invalid token fails"""
    response = client.post("/api/auth/password-update", json={
        "token": "invalid_token",
        "new_password": "NewSecurePass456!"
    })

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# ============================================================================
# Account Management Tests
# ============================================================================

def test_update_user_profile(test_user_data, registered_user):
    """Test updating user profile"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Update profile
    response = client.put(
        "/api/auth/me?full_name=Updated%20Name&username=newusername",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["username"] == "newusername"


def test_deactivate_account(test_user_data, registered_user):
    """Test account deactivation"""
    # Login
    login_response = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Deactivate
    response = client.delete(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200

    # Verify cannot login
    login_attempt = client.post("/api/auth/token", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })

    assert login_attempt.status_code == 403


# ============================================================================
# Token Expiration Tests
# ============================================================================

def test_expired_access_token(test_user_data, registered_user):
    """Test that expired access token is rejected"""
    # Create expired token
    expired_token = create_access_token(
        data={"sub": test_user_data["email"], "user_id": registered_user.id},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )

    # Try to use expired token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401


def test_expired_refresh_token():
    """Test that expired refresh token is rejected"""
    # Create expired refresh token
    expired_refresh_token = create_refresh_token(
        data={"sub": "test@example.com", "user_id": 1},
        expires_delta=timedelta(seconds=-1)
    )

    # Try to refresh
    response = client.post("/api/auth/refresh", json={
        "refresh_token": expired_refresh_token
    })

    assert response.status_code == 401
