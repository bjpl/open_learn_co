"""
User Preferences API
OpenLearn Colombia - Phase 3
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import json
import csv
import io

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


@router.delete("/api/preferences/account")
async def delete_user_account(user_id: str = Query(..., description="User ID")):
    """
    Delete user account (GDPR compliance)

    Permanently removes all user data.
    """
    if user_id in preferences_db:
        del preferences_db[user_id]

    # TODO: Delete from other systems (vocabulary, progress, etc.)

    return {"message": "Account deleted successfully"}


@router.get("/api/preferences/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "users_count": len(preferences_db),
        "timestamp": datetime.utcnow().isoformat()
    }
