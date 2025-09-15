"""
API routes for authentication and user management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from jwt import PyJWTError

from ..database.database import get_db
from ..database.models import User
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class UserRegistration(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    preferred_language: str = Field(default="es")


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: str
    preferred_language: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordReset(BaseModel):
    """Password reset model."""
    email: EmailStr


class PasswordUpdate(BaseModel):
    """Password update model."""
    token: str
    new_password: str = Field(..., min_length=8)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except PyJWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        preferred_language=user_data.preferred_language,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        preferred_language=new_user.preferred_language,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token.
    """
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            preferred_language=user.preferred_language,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        preferred_language=current_user.preferred_language,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.put("/me")
async def update_current_user(
    full_name: Optional[str] = None,
    preferred_language: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information.
    """
    if full_name:
        current_user.full_name = full_name

    if preferred_language:
        current_user.preferred_language = preferred_language

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        preferred_language=current_user.preferred_language,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/password-reset")
async def request_password_reset(
    request: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.
    """
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        # Don't reveal if user exists
        return {"message": "If the email exists, a reset link has been sent"}

    # Create reset token
    reset_token = create_access_token(
        data={"sub": user.email, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )

    # In production, send email with reset link
    # For now, return token (development only)
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token,
        "expires_in": 3600
    }


@router.post("/password-update")
async def update_password(
    request: PasswordUpdate,
    db: Session = Depends(get_db)
):
    """
    Update password with reset token.
    """
    payload = verify_token(request.token)

    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout user (client should discard token).
    """
    # In production, you might want to blacklist the token
    return {"message": "Successfully logged out"}


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account.
    """
    # Soft delete (deactivate)
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Account deactivated successfully"}


@router.get("/verify-token")
async def verify_auth_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }