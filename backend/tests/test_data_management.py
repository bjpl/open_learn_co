"""
Integration tests for data management and GDPR compliance features.

Tests:
- Account deletion cascade (GDPR Article 17)
- Progress clearing
- Data export (GDPR Article 15, 20)
- Audit logging
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select, func

from app.database.models import (
    User, UserVocabulary, UserContentProgress, LearningSession
)
from app.database.notification_models import (
    Notification, NotificationPreference, EmailLog
)
from app.services.data_deletion_service import (
    DataDeletionService, delete_user_account, clear_user_progress, get_deletion_preview
)


@pytest.mark.asyncio
class TestAccountDeletion:
    """Test GDPR-compliant account deletion"""

    async def test_complete_account_deletion(self, async_db, test_user):
        """Test complete cascade deletion of user account"""
        user_id = test_user.id

        # Add test data across all tables
        # 1. Vocabulary progress
        for i in range(5):
            vocab = UserVocabulary(
                user_id=user_id,
                vocabulary_id=i + 1,
                times_seen=i + 1,
                mastery_level=0.5
            )
            async_db.add(vocab)

        # 2. Content progress
        for i in range(3):
            progress = UserContentProgress(
                user_id=user_id,
                content_id=i + 1,
                read_percentage=50.0
            )
            async_db.add(progress)

        # 3. Learning sessions
        for i in range(4):
            session = LearningSession(
                user_id=user_id,
                session_type='vocabulary',
                duration_seconds=300
            )
            async_db.add(session)

        # 4. Notifications
        for i in range(2):
            notification = Notification(
                user_id=user_id,
                type='info',
                category='system',
                title='Test notification',
                message='Test message'
            )
            async_db.add(notification)

        await async_db.commit()

        # Verify data exists
        vocab_count = await async_db.execute(
            select(func.count()).where(UserVocabulary.user_id == user_id)
        )
        assert vocab_count.scalar() == 5

        # Delete account
        service = DataDeletionService(async_db)
        result = await service.delete_user_completely(user_id, reason="test")

        # Verify all data deleted
        assert result['user_id'] == user_id
        assert result['gdpr_compliant'] == True
        assert result['total_records_deleted'] == 15  # 5+3+4+2+1(user)=15

        # Verify no records remain
        summary = await service.get_user_data_summary(user_id)
        assert summary['total_records'] == 0

    async def test_account_deletion_atomicity(self, async_db, test_user):
        """Test that deletion is atomic (all-or-nothing)"""
        # This would require mocking a database error midway through deletion
        # to ensure rollback works properly
        pass  # TODO: Implement with database mocking

    async def test_deletion_audit_logging(self, async_db, test_user, caplog):
        """Test that deletions are properly logged for audit"""
        service = DataDeletionService(async_db)

        with caplog.at_level('INFO'):
            result = await service.delete_user_completely(test_user.id)

        # Verify audit log entries
        assert f"Starting complete deletion for user {test_user.id}" in caplog.text
        assert f"User {test_user.id} deletion complete" in caplog.text


@pytest.mark.asyncio
class TestProgressClearing:
    """Test selective progress clearing"""

    async def test_clear_learning_progress(self, async_db, test_user):
        """Test clearing progress while preserving account"""
        user_id = test_user.id

        # Add learning data
        vocab = UserVocabulary(
            user_id=user_id,
            vocabulary_id=1,
            mastery_level=0.8
        )
        async_db.add(vocab)

        session = LearningSession(
            user_id=user_id,
            session_type='vocabulary',
            duration_seconds=600
        )
        async_db.add(session)

        await async_db.commit()

        # Clear progress
        service = DataDeletionService(async_db)
        result = await service.clear_learning_progress(user_id)

        # Verify progress cleared
        assert result['deletion_breakdown']['vocabulary_items'] == 1
        assert result['deletion_breakdown']['learning_sessions'] == 1

        # Verify account still exists
        user_query = await async_db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_query.scalar_one_or_none()
        assert user is not None
        assert user.email == test_user.email

    async def test_clear_progress_preserves_preferences(self, async_db, test_user):
        """Test that clearing progress doesn't affect preferences"""
        # Add notification preference
        pref = NotificationPreference(
            user_id=test_user.id,
            email_digest_enabled=True
        )
        async_db.add(pref)
        await async_db.commit()

        # Clear progress
        service = DataDeletionService(async_db)
        await service.clear_learning_progress(test_user.id)

        # Verify preference still exists
        pref_query = await async_db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == test_user.id
            )
        )
        pref_after = pref_query.scalar_one_or_none()
        assert pref_after is not None
        assert pref_after.email_digest_enabled == True


@pytest.mark.asyncio
class TestDataExport:
    """Test GDPR data export functionality"""

    async def test_get_user_data_summary(self, async_db, test_user):
        """Test data summary for export preview"""
        # Add various data
        async_db.add(UserVocabulary(
            user_id=test_user.id,
            vocabulary_id=1,
            mastery_level=0.5
        ))
        async_db.add(LearningSession(
            user_id=test_user.id,
            session_type='vocabulary',
            duration_seconds=300
        ))
        await async_db.commit()

        # Get summary
        service = DataDeletionService(async_db)
        summary = await service.get_user_data_summary(test_user.id)

        # Verify counts
        assert summary['user_account'] == 1
        assert summary['vocabulary_items'] == 1
        assert summary['learning_sessions'] == 1
        assert summary['total_records'] == 3


@pytest.mark.asyncio
class TestGDPRCompliance:
    """Test overall GDPR compliance"""

    async def test_deletion_within_timeframe(self, async_db, test_user):
        """Test that deletion happens without undue delay (GDPR requirement)"""
        start_time = datetime.utcnow()

        service = DataDeletionService(async_db)
        result = await service.delete_user_completely(test_user.id)

        end_time = datetime.utcnow()
        deletion_time = (end_time - start_time).total_seconds()

        # GDPR requires "without undue delay" - we aim for <5 seconds
        assert deletion_time < 5.0
        assert 'deleted_at' in result

    async def test_no_orphaned_records_after_deletion(self, async_db, test_user):
        """Test that no orphaned records remain after account deletion"""
        user_id = test_user.id

        # Add data across all tables
        async_db.add(UserVocabulary(user_id=user_id, vocabulary_id=1, mastery_level=0.5))
        async_db.add(UserContentProgress(user_id=user_id, content_id=1, read_percentage=50.0))
        async_db.add(LearningSession(user_id=user_id, session_type='vocabulary', duration_seconds=300))
        async_db.add(Notification(user_id=user_id, type='info', category='system', title='Test', message='Test'))
        async_db.add(NotificationPreference(user_id=user_id, email_digest_enabled=True))
        async_db.add(EmailLog(user_id=user_id, email_type='digest', recipient='test@example.com', subject='Test'))
        await async_db.commit()

        # Delete account
        service = DataDeletionService(async_db)
        await service.delete_user_completely(user_id)

        # Check each table for orphaned records
        tables_to_check = [
            (UserVocabulary, UserVocabulary.user_id),
            (UserContentProgress, UserContentProgress.user_id),
            (LearningSession, LearningSession.user_id),
            (Notification, Notification.user_id),
            (NotificationPreference, NotificationPreference.user_id),
            (EmailLog, EmailLog.user_id),
            (User, User.id)
        ]

        for table, user_id_column in tables_to_check:
            count_query = await async_db.execute(
                select(func.count()).where(user_id_column == user_id)
            )
            count = count_query.scalar()
            assert count == 0, f"Found {count} orphaned records in {table.__tablename__}"


# Fixtures

@pytest.fixture
async def test_user(async_db):
    """Create a test user for deletion tests"""
    user = User(
        email=f"test_{datetime.utcnow().timestamp()}@example.com",
        password_hash="hashed_password",
        full_name="Test User",
        is_active=True
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest.fixture
async def async_db(db_session):
    """Provide async database session"""
    # This would use your actual async database fixture
    # For now, assuming db_session is provided by conftest.py
    return db_session
