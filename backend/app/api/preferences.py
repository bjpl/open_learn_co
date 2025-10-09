"""
User Preferences API
OpenLearn Colombia - Phase 3
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import delete
import json
import csv
import io
import logging

from app.core.security import get_current_active_user
from app.database.connection import get_db
from app.database.models import User, UserVocabulary, UserContentProgress, LearningSession
from app.database.notification_models import Notification, NotificationPreference, EmailLog

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class ProfilePreferences(BaseModel):
    fullName: str
    email: str
    avatar: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    preferredLanguage: Literal['es', 'en'] = 'es'
    timezone: str = 'America/Bogota'
    dateFormat: Literal['DD/MM/YYYY', 'MM/DD/YYYY'] = 'DD/MM/YYYY'


class EmailNotifications(BaseModel):
    dailyDigest: bool = True
    weeklySummary: bool = True
    contentAlerts: bool = True
    vocabularyReminders: bool = True
    systemUpdates: bool = True


class InAppNotifications(BaseModel):
    newArticles: bool = True
    vocabularyReview: bool = True
    achievements: bool = True
    systemMessages: bool = True


class DeliveryTimes(BaseModel):
    dailyDigestTime: str = '08:00'
    quietHoursStart: str = '22:00'
    quietHoursEnd: str = '07:00'


class NotificationSettings(BaseModel):
    email: EmailNotifications
    inApp: InAppNotifications
    deliveryTimes: DeliveryTimes


class Appearance(BaseModel):
    theme: Literal['light', 'dark', 'auto'] = 'auto'
    colorScheme: Literal['default', 'blue', 'green', 'purple'] = 'default'
    fontSize: Literal['small', 'medium', 'large', 'xlarge'] = 'medium'
    contentDensity: Literal['comfortable', 'compact'] = 'comfortable'


class Layout(BaseModel):
    defaultPage: Literal['dashboard', 'news', 'vocabulary', 'analytics'] = 'dashboard'
    articlesPerPage: int = Field(25, ge=10, le=100)
    showImages: bool = True
    sidebarPosition: Literal['left', 'right', 'hidden'] = 'left'


class DisplayPreferences(BaseModel):
    appearance: Appearance
    layout: Layout


class LanguageLearningPreferences(BaseModel):
    currentLevel: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'B1'
    targetLevel: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'C1'
    dailyVocabGoal: int = Field(10, ge=5, le=50)
    reviewFrequency: Literal['daily', 'every2days', 'weekly'] = 'daily'
    difficultyPreference: Literal['easy', 'balanced', 'challenge'] = 'balanced'
    showTranslations: Literal['always', 'hover', 'never'] = 'hover'
    colombianSpanishFocus: bool = True
    preferredSources: List[str] = []
    preferredCategories: List[str] = []
    difficultyRange: List[int] = [30, 70]
    contentLengthPreference: Literal['short', 'medium', 'long', 'any'] = 'any'

    @validator('difficultyRange')
    def validate_difficulty_range(cls, v):
        if len(v) != 2:
            raise ValueError('difficultyRange must have exactly 2 values')
        if v[0] < 0 or v[1] > 100 or v[0] > v[1]:
            raise ValueError('difficultyRange must be between 0-100 with min <= max')
        return v


class PrivacyPreferences(BaseModel):
    profileVisibility: Literal['public', 'private'] = 'private'
    shareAnalytics: bool = True
    personalizedRecommendations: bool = True
    dataCollectionConsent: bool = False


class UserPreferences(BaseModel):
    userId: str
    profile: ProfilePreferences
    notifications: NotificationSettings
    display: DisplayPreferences
    learning: LanguageLearningPreferences
    privacy: PrivacyPreferences
    createdAt: datetime
    updatedAt: datetime


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

preferences_db: dict[str, UserPreferences] = {}


def get_default_preferences(user_id: str) -> UserPreferences:
    """Get default preferences for a new user"""
    now = datetime.utcnow()
    return UserPreferences(
        userId=user_id,
        profile=ProfilePreferences(
            fullName="",
            email="",
            preferredLanguage="es",
            timezone="America/Bogota",
            dateFormat="DD/MM/YYYY"
        ),
        notifications=NotificationSettings(
            email=EmailNotifications(),
            inApp=InAppNotifications(),
            deliveryTimes=DeliveryTimes()
        ),
        display=DisplayPreferences(
            appearance=Appearance(),
            layout=Layout()
        ),
        learning=LanguageLearningPreferences(),
        privacy=PrivacyPreferences(),
        createdAt=now,
        updatedAt=now
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/api/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: str = Query(..., description="User ID")):
    """
    Get user preferences

    Returns preferences for the specified user. If no preferences exist,
    returns default preferences.
    """
    if user_id not in preferences_db:
        # Return defaults for new users
        return get_default_preferences(user_id)

    return preferences_db[user_id]


@router.put("/api/preferences", response_model=UserPreferences)
async def update_user_preferences(preferences: UserPreferences):
    """
    Update user preferences

    Updates or creates preferences for a user. All fields are validated.
    """
    # Update timestamp
    preferences.updatedAt = datetime.utcnow()

    # If this is a new user, set creation timestamp
    if preferences.userId not in preferences_db:
        preferences.createdAt = datetime.utcnow()

    # Store preferences
    preferences_db[preferences.userId] = preferences

    return preferences


@router.delete("/api/preferences", response_model=UserPreferences)
async def reset_user_preferences(user_id: str = Query(..., description="User ID")):
    """
    Reset user preferences to defaults

    Removes custom preferences and returns defaults.
    """
    # Remove from storage
    if user_id in preferences_db:
        del preferences_db[user_id]

    # Return defaults
    return get_default_preferences(user_id)


@router.get("/api/preferences/export")
async def export_user_data(
    user_id: str = Query(..., description="User ID"),
    format: Literal['json', 'csv'] = Query('json', description="Export format")
):
    """
    Export user data (GDPR compliance)

    Returns all user data in JSON or CSV format.
    """
    if user_id not in preferences_db:
        raise HTTPException(status_code=404, detail="No data found for user")

    preferences = preferences_db[user_id]

    if format == 'json':
        # JSON export
        data = preferences.dict()
        json_str = json.dumps(data, indent=2, default=str)

        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=openlearn-data-{user_id}.json"
            }
        )

    elif format == 'csv':
        # CSV export (flattened)
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Category', 'Field', 'Value'])

        # Flatten and write preferences
        data = preferences.dict()
        for category, values in data.items():
            if isinstance(values, dict):
                for field, value in values.items():
                    if isinstance(value, dict):
                        for subfield, subvalue in value.items():
                            writer.writerow([f"{category}.{field}", subfield, str(subvalue)])
                    elif isinstance(value, list):
                        writer.writerow([category, field, ', '.join(map(str, value))])
                    else:
                        writer.writerow([category, field, str(value)])
            else:
                writer.writerow(['root', category, str(values)])

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=openlearn-data-{user_id}.csv"
            }
        )


@router.delete("/api/users/me/account")
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account (GDPR Article 17 - Right to be Forgotten)

    Permanently removes all user data in compliance with GDPR:
    - User profile and authentication data
    - Learning progress (vocabulary, content, sessions)
    - Notifications and preferences
    - Email logs and communication history

    This operation is IRREVERSIBLE.
    """
    user_id = current_user.id

    try:
        logger.info(f"Starting account deletion for user {user_id}")

        # Delete in order: dependent tables first, then user table

        # 1. Delete email logs
        db.execute(delete(EmailLog).where(EmailLog.user_id == user_id))
        logger.debug(f"Deleted email logs for user {user_id}")

        # 2. Delete notifications
        db.execute(delete(Notification).where(Notification.user_id == user_id))
        logger.debug(f"Deleted notifications for user {user_id}")

        # 3. Delete notification preferences
        db.execute(delete(NotificationPreference).where(NotificationPreference.user_id == user_id))
        logger.debug(f"Deleted notification preferences for user {user_id}")

        # 4. Delete learning sessions
        db.execute(delete(LearningSession).where(LearningSession.user_id == user_id))
        logger.debug(f"Deleted learning sessions for user {user_id}")

        # 5. Delete vocabulary progress
        db.execute(delete(UserVocabulary).where(UserVocabulary.user_id == user_id))
        logger.debug(f"Deleted vocabulary progress for user {user_id}")

        # 6. Delete content progress
        db.execute(delete(UserContentProgress).where(UserContentProgress.user_id == user_id))
        logger.debug(f"Deleted content progress for user {user_id}")

        # 7. Delete user account (main table)
        db.execute(delete(User).where(User.id == user_id))
        logger.debug(f"Deleted user record for user {user_id}")

        # Commit all deletions
        db.commit()

        logger.info(f"Account deletion complete for user {user_id}")

        return {
            "message": "Account deleted successfully",
            "deleted_at": datetime.utcnow().isoformat(),
            "user_id": user_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete account for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Account deletion failed. Please contact support."
        )


@router.delete("/api/users/me/progress")
async def clear_user_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Clear user's learning progress.

    Removes:
    - Vocabulary progress (resets all learned words)
    - Content progress (reading history)
    - Learning sessions (activity history)

    Does NOT delete:
    - User account
    - Preferences and settings
    - Notifications

    This operation is IRREVERSIBLE.
    """
    user_id = current_user.id

    try:
        logger.info(f"Clearing progress for user {user_id}")

        # Delete learning data
        vocab_result = db.execute(delete(UserVocabulary).where(UserVocabulary.user_id == user_id))
        content_result = db.execute(delete(UserContentProgress).where(UserContentProgress.user_id == user_id))
        session_result = db.execute(delete(LearningSession).where(LearningSession.user_id == user_id))

        db.commit()

        deleted_counts = {
            "vocabulary_items": vocab_result.rowcount,
            "content_progress": content_result.rowcount,
            "learning_sessions": session_result.rowcount
        }

        logger.info(f"Progress cleared for user {user_id}: {deleted_counts}")

        return {
            "message": "Learning progress cleared successfully",
            "cleared_at": datetime.utcnow().isoformat(),
            "deleted_counts": deleted_counts
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear progress for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear progress. Please try again."
        )


@router.get("/api/preferences/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "users_count": len(preferences_db),
        "timestamp": datetime.utcnow().isoformat()
    }
