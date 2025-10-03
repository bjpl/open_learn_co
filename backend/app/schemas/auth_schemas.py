"""
Authentication and user management validation schemas
Enhanced security with password strength validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


class UserRegister(BaseModel):
    """User registration with strict validation"""
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="User email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must include uppercase, lowercase, number)"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name"
    )
    preferred_language: str = Field(
        default="es",
        pattern="^(es|en)$",
        description="Preferred language code (es or en)"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")

        # Optional: Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Sanitize full name"""
        # Remove multiple spaces
        v = ' '.join(v.split())

        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", v):
            raise ValueError("Name contains invalid characters")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "Juan García",
                "preferred_language": "es"
            }
        }
    )


class UserLogin(BaseModel):
    """User login credentials"""
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="User email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class UserResponse(BaseModel):
    """User data response (excludes sensitive info)"""
    id: int
    email: str
    full_name: str
    preferred_language: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "Juan García",
                "preferred_language": "es",
                "is_active": True,
                "created_at": "2025-10-03T12:00:00Z",
                "last_login": "2025-10-03T13:00:00Z"
            }
        }
    )


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "Juan García",
                    "preferred_language": "es",
                    "is_active": True,
                    "created_at": "2025-10-03T12:00:00Z"
                }
            }
        }
    )


class UserUpdate(BaseModel):
    """User profile update"""
    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated full name"
    )
    preferred_language: Optional[str] = Field(
        default=None,
        pattern="^(es|en)$",
        description="Updated preferred language"
    )

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize full name"""
        if v is None:
            return v

        # Remove multiple spaces
        v = ' '.join(v.split())

        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", v):
            raise ValueError("Name contains invalid characters")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Juan Carlos García",
                "preferred_language": "en"
            }
        }
    )


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="User email address"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com"}
        }
    )


class PasswordUpdate(BaseModel):
    """Password update with reset token"""
    token: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Password reset token"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass123!"
            }
        }
    )
