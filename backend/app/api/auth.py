"""
Production-grade JWT Authentication API

This module implements secure authentication with:
- JWT access tokens (short-lived, 30 minutes)
- JWT refresh tokens (long-lived, 7 days)
- Password hashing with bcrypt
- User registration and login
- Token refresh mechanism
- Password reset functionality
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    get_current_user,
    get_current_active_user,
)
from ..database.connection import get_db
from ..database.models import User
from ..config.settings import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegistration(BaseModel):
    """User registration request model."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    username: Optional[str] = Field(None, min_length=3, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@example.com",
                "password": "SecurePass123!",
                "full_name": "Juan Pérez",
                "username": "jperez"
            }
        }


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: str
    username: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiration in seconds
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "User Name",
                    "username": "username",
                    "is_active": True,
                    "created_at": "2025-01-01T00:00:00"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordUpdateRequest(BaseModel):
    """Password update request model."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **email**: Valid email address (required)
    - **password**: Minimum 8 characters (required)
    - **full_name**: User's full name (required)
    - **username**: Unique username (optional)

    Returns the created user object (without password).
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists (if provided)
    if user_data.username:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create new user with hashed password
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        username=user_data.username,
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and obtain access + refresh tokens.

    OAuth2 compatible endpoint using username/password form data.
    The 'username' field should contain the user's email address.

    Returns:
    - **access_token**: Short-lived token (30 minutes)
    - **refresh_token**: Long-lived token (7 days)
    - **user**: User profile information
    """
    # Authenticate user (username field contains email)
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=refresh_token_expires
    )

    # Store refresh token in database
    user.refresh_token = refresh_token
    user.refresh_token_expires_at = datetime.utcnow() + refresh_token_expires
    user.last_login = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Provide a valid refresh token to obtain a new access token
    without requiring the user to log in again.

    - **refresh_token**: Valid refresh token from login

    Returns new access token and refresh token pair.
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from token payload
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if not user_id and not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Query user
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Verify refresh token matches stored token
    if user.refresh_token != request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    # Verify refresh token hasn't expired in database
    if user.refresh_token_expires_at and user.refresh_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    # Create new token pair
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=refresh_token_expires
    )

    # Update stored refresh token
    user.refresh_token = new_refresh_token
    user.refresh_token_expires_at = datetime.utcnow() + refresh_token_expires
    user.last_active = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token.

    Invalidates the current refresh token, requiring the user
    to login again to obtain new tokens.
    """
    # Revoke refresh token
    current_user.refresh_token = None
    current_user.refresh_token_expires_at = None
    db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user's profile.

    Requires valid access token in Authorization header.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: Optional[str] = Field(None, min_length=2, max_length=200),
    username: Optional[str] = Field(None, min_length=3, max_length=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.

    - **full_name**: Update full name (optional)
    - **username**: Update username (optional)
    """
    if full_name:
        current_user.full_name = full_name

    if username:
        # Check if username is already taken
        existing = db.query(User).filter(
            User.username == username,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        current_user.username = username

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.

    Sends a password reset link to the user's email.
    (In production, this would send an actual email)

    - **email**: User's registered email address
    """
    user = db.query(User).filter(User.email == request.email).first()

    # Don't reveal whether user exists (security best practice)
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    # Create reset token (expires in 1 hour)
    reset_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )

    # Send password reset email
    from ..services.email_service import send_password_reset_email

    try:
        email_sent = await send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.full_name
        )

        if email_sent:
            return {"message": "If the email exists, a reset link has been sent"}
        else:
            # Email failed but don't reveal this to user for security
            return {"message": "If the email exists, a reset link has been sent"}

    except Exception as e:
        # Log error but don't reveal to user
        print(f"Error sending password reset email: {e}")
        return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-update")
async def update_password(
    request: PasswordUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update password using reset token.

    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)
    """
    # Verify reset token
    payload = verify_token(request.token, token_type="access")

    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Get user
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.utcnow()

    # Revoke all refresh tokens for security
    user.refresh_token = None
    user.refresh_token_expires_at = None

    db.commit()

    return {"message": "Password updated successfully"}


@router.delete("/me")
async def deactivate_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user account.

    This performs a soft delete by setting is_active to False.
    User data is retained for recovery purposes.
    """
    current_user.is_active = False
    current_user.refresh_token = None
    current_user.refresh_token_expires_at = None
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Account deactivated successfully"}


@router.get("/verify-token")
async def verify_auth_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if access token is valid.

    Useful for client-side token validation.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active
    }
