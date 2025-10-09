"""
Notification Models for OpenLearn Colombia
Supports in-app notifications, email alerts, and user preferences
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.models import Base


class NotificationType(str, enum.Enum):
    """Notification visual types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationCategory(str, enum.Enum):
    """Notification categories for filtering and organization"""
    NEW_CONTENT = "NEW_CONTENT"
    VOCABULARY = "VOCABULARY"
    ACHIEVEMENT = "ACHIEVEMENT"
    SYSTEM = "SYSTEM"
    ALERT = "ALERT"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notification(Base):
    """Model for in-app notifications"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Notification properties
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.INFO)
    category = Column(Enum(NotificationCategory), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)

    # Content
    title = Column(String(100), nullable=False)
    message = Column(String(500), nullable=False)

    # Action (optional)
    action_url = Column(String(500))  # Link to related content
    action_label = Column(String(50))  # Button text (e.g., "Read Now", "Review")

    # Additional data (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    extra_data = Column(JSON)  # Additional data (content_id, vocabulary_id, etc.)

    # Status
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime)  # Optional expiration

    # Relationships
    user = relationship("User", backref="notifications")

    # Performance indexes
    __table_args__ = (
        # Composite index for user's unread notifications (most common query)
        Index('idx_notification_user_read_created', 'user_id', 'read', 'created_at'),

        # Index for filtering by category
        Index('idx_notification_user_category', 'user_id', 'category'),

        # Index for cleanup of old notifications
        Index('idx_notification_created_at', 'created_at'),

        # Partial index for active (non-expired) notifications
        Index('idx_notification_active', 'user_id', 'expires_at',
              postgresql_where=Column('expires_at').isnot(None)),

        # Index for priority sorting
        Index('idx_notification_priority', 'priority'),
    )

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value if self.type else None,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "title": self.title,
            "message": self.message,
            "action_url": self.action_url,
            "action_label": self.action_label,
            "metadata": self.extra_data,  # Return as 'metadata' in API for backwards compatibility
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class NotificationPreference(Base):
    """Model for user notification preferences"""
    __tablename__ = 'notification_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)

    # Email notification preferences
    email_digest_enabled = Column(Boolean, default=True, nullable=False)
    email_digest_time = Column(String(5), default="08:00")  # HH:MM format
    email_weekly_enabled = Column(Boolean, default=True, nullable=False)
    email_alerts_enabled = Column(Boolean, default=True, nullable=False)
    email_vocabulary_enabled = Column(Boolean, default=True, nullable=False)

    # In-app notification preferences
    in_app_notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Category preferences (JSON array of enabled categories)
    notification_categories = Column(JSON, default=list)  # ["NEW_CONTENT", "VOCABULARY", ...]

    # Quiet hours
    quiet_hours_start = Column(String(5))  # HH:MM format (e.g., "22:00")
    quiet_hours_end = Column(String(5))    # HH:MM format (e.g., "07:00")

    # Frequency limits (prevent spam)
    max_emails_per_day = Column(Integer, default=5)
    max_in_app_per_hour = Column(Integer, default=10)

    # User timezone (for digest scheduling)
    timezone = Column(String(50), default="America/Bogota")

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="notification_preferences")

    # Indexes
    __table_args__ = (
        Index('idx_notif_pref_user_id', 'user_id'),
    )

    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            "user_id": self.user_id,
            "email_digest_enabled": self.email_digest_enabled,
            "email_digest_time": self.email_digest_time,
            "email_weekly_enabled": self.email_weekly_enabled,
            "email_alerts_enabled": self.email_alerts_enabled,
            "email_vocabulary_enabled": self.email_vocabulary_enabled,
            "in_app_notifications_enabled": self.in_app_notifications_enabled,
            "notification_categories": self.notification_categories,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "max_emails_per_day": self.max_emails_per_day,
            "max_in_app_per_hour": self.max_in_app_per_hour,
            "timezone": self.timezone,
        }


class EmailLog(Base):
    """Track sent emails for analytics and debugging"""
    __tablename__ = 'email_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Email details
    email_type = Column(String(50), nullable=False)  # digest, alert, reminder, etc.
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500))

    # Status
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    error_message = Column(Text)

    # Engagement (optional)
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime)

    # Additional data (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    extra_data = Column(JSON)  # Template variables, content IDs, etc.

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", backref="email_logs")

    # Indexes
    __table_args__ = (
        Index('idx_email_log_user_created', 'user_id', 'created_at'),
        Index('idx_email_log_type', 'email_type'),
        Index('idx_email_log_sent', 'sent'),
    )
