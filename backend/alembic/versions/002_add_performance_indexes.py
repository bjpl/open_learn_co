"""Add performance indexes for query optimization

Revision ID: 002_performance_indexes
Revises: 001_initial_schema
Create Date: 2025-10-03 16:30:00.000000

Performance Impact:
- Target: <50ms p95 latency for common queries
- Expected improvement: 80-95% reduction in query time
- Index size: ~15-20% of table size
- Zero-downtime deployment using CONCURRENTLY

Critical Indexes:
- ScrapedContent: source, category, published_date, full-text search
- Users: email, refresh_token (authentication)
- ContentAnalysis: content_id, sentiment_score, processed_at
- ExtractedVocabulary: word, difficulty_level
- UserVocabulary: user_id + next_review (spaced repetition)
- LearningSession: user_id + started_at (streak calculation)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_performance_indexes'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply performance indexes with CONCURRENTLY option.

    Note: CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
    Alembic handles this automatically when using op.create_index with postgresql_concurrently=True
    """

    # ========================================================================
    # SCRAPED_CONTENT TABLE INDEXES
    # ========================================================================

    # Single-column indexes for filtering
    op.create_index(
        'idx_scraped_content_source',
        'scraped_content',
        ['source'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_scraped_content_category',
        'scraped_content',
        ['category'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_scraped_content_scraped_at',
        'scraped_content',
        [sa.text('scraped_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    # Partial index for free content only
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_is_paywall
        ON scraped_content(is_paywall)
        WHERE is_paywall = false
    """)

    # Composite indexes for common query patterns
    op.create_index(
        'idx_scraped_content_source_category_published',
        'scraped_content',
        ['source', 'category', sa.text('published_date DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    # Difficulty-based filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_difficulty_published
        ON scraped_content(difficulty_score, published_date DESC)
        WHERE difficulty_score IS NOT NULL
    """)

    # Full-text search indexes (GIN)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_title_gin
        ON scraped_content USING gin(to_tsvector('spanish', title))
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_content_gin
        ON scraped_content USING gin(to_tsvector('spanish', content))
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_fulltext_gin
        ON scraped_content USING gin(
            (to_tsvector('spanish', coalesce(title, '')) ||
             to_tsvector('spanish', coalesce(content, '')))
        )
    """)

    # JSON indexes
    op.create_index(
        'idx_scraped_content_tags_gin',
        'scraped_content',
        ['tags'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_scraped_content_entities_gin',
        'scraped_content',
        ['colombian_entities'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    # Covering index for list queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_list_covering
        ON scraped_content(published_date DESC)
        INCLUDE (id, source, category, title, difficulty_score, is_paywall)
    """)

    # ========================================================================
    # CONTENT_ANALYSIS TABLE INDEXES
    # ========================================================================

    op.create_index(
        'idx_content_analysis_content_id',
        'content_analysis',
        ['content_id'],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_sentiment_score
        ON content_analysis(sentiment_score)
        WHERE sentiment_score IS NOT NULL
    """)

    op.create_index(
        'idx_content_analysis_sentiment_label',
        'content_analysis',
        ['sentiment_label'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_content_analysis_content_processed',
        'content_analysis',
        ['content_id', sa.text('processed_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_content_analysis_processed_at',
        'content_analysis',
        [sa.text('processed_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    # JSON indexes for entity and topic searches
    op.create_index(
        'idx_content_analysis_entities_gin',
        'content_analysis',
        ['entities'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_content_analysis_topics_gin',
        'content_analysis',
        ['topics'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    # ========================================================================
    # EXTRACTED_VOCABULARY TABLE INDEXES
    # ========================================================================

    op.create_index(
        'idx_extracted_vocab_content_id',
        'extracted_vocabulary',
        ['content_id'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_extracted_vocab_word',
        'extracted_vocabulary',
        ['word'],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_difficulty
        ON extracted_vocabulary(difficulty_level)
        WHERE difficulty_level IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_colombian
        ON extracted_vocabulary(is_colombian_specific)
        WHERE is_colombian_specific = true
    """)

    op.create_index(
        'idx_extracted_vocab_pos',
        'extracted_vocabulary',
        ['pos_tag'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_extracted_vocab_word_difficulty',
        'extracted_vocabulary',
        ['word', 'difficulty_level'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_extracted_vocab_frequency',
        'extracted_vocabulary',
        [sa.text('frequency_in_article DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    # ========================================================================
    # USERS TABLE INDEXES
    # ========================================================================

    # Case-insensitive unique email
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_unique
        ON users(lower(email))
    """)

    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_unique
        ON users(lower(username))
        WHERE username IS NOT NULL
    """)

    # Active users filter
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active
        ON users(is_active)
        WHERE is_active = true
    """)

    # Session management
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_refresh_token
        ON users(refresh_token)
        WHERE refresh_token IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_refresh_expires
        ON users(refresh_token_expires_at)
        WHERE refresh_token_expires_at > NOW()
    """)

    # Activity tracking
    op.create_index(
        'idx_users_last_login',
        'users',
        [sa.text('last_login DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_users_created_at',
        'users',
        [sa.text('created_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_users_role',
        'users',
        ['role'],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_spanish_level
        ON users(spanish_level)
        WHERE spanish_level IS NOT NULL
    """)

    # ========================================================================
    # USER_CONTENT_PROGRESS TABLE INDEXES
    # ========================================================================

    op.create_index(
        'idx_user_progress_user_content',
        'user_content_progress',
        ['user_id', 'content_id'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_user_progress_user_accessed',
        'user_content_progress',
        ['user_id', sa.text('last_accessed DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_user_progress_user_completed',
        'user_content_progress',
        ['user_id', 'completed', sa.text('completed_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_user_progress_content_id',
        'user_content_progress',
        ['content_id'],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_read_percentage
        ON user_content_progress(read_percentage)
        WHERE completed = false
    """)

    # ========================================================================
    # USER_VOCABULARY TABLE INDEXES
    # ========================================================================

    # Spaced repetition queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_user_review
        ON user_vocabulary(user_id, next_review)
        WHERE next_review IS NOT NULL
    """)

    op.create_index(
        'idx_user_vocab_user_mastery',
        'user_vocabulary',
        ['user_id', sa.text('mastery_level DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_next_review
        ON user_vocabulary(next_review)
        WHERE next_review <= NOW() + INTERVAL '1 day'
    """)

    op.create_index(
        'idx_user_vocab_user_id',
        'user_vocabulary',
        ['user_id'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_user_vocab_vocabulary_id',
        'user_vocabulary',
        ['vocabulary_id'],
        unique=False,
        postgresql_concurrently=True
    )

    # Covering index for mastery queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_mastery_covering
        ON user_vocabulary(user_id, mastery_level DESC)
        INCLUDE (vocabulary_id, next_review, times_seen, times_correct)
    """)

    # ========================================================================
    # LEARNING_SESSIONS TABLE INDEXES
    # ========================================================================

    op.create_index(
        'idx_learning_session_user_started',
        'learning_sessions',
        ['user_id', sa.text('started_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_learning_session_type',
        'learning_sessions',
        ['session_type'],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_user_date
        ON learning_sessions(user_id, (started_at::date) DESC)
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_active
        ON learning_sessions(user_id, started_at DESC)
        WHERE ended_at IS NULL
    """)

    # JSON indexes
    op.create_index(
        'idx_learning_session_content_gin',
        'learning_sessions',
        ['content_ids'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_learning_session_vocab_gin',
        'learning_sessions',
        ['vocabulary_ids'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    # ========================================================================
    # INTELLIGENCE_ALERTS TABLE INDEXES
    # ========================================================================

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_status
        ON intelligence_alerts(status)
        WHERE status IN ('active', 'pending')
    """)

    op.create_index(
        'idx_alerts_type_severity',
        'intelligence_alerts',
        ['alert_type', 'severity', sa.text('created_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_alerts_created_at',
        'intelligence_alerts',
        [sa.text('created_at DESC')],
        unique=False,
        postgresql_concurrently=True
    )

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_expires_at
        ON intelligence_alerts(expires_at)
        WHERE expires_at IS NOT NULL AND expires_at > NOW()
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_acknowledged_by
        ON intelligence_alerts(acknowledged_by)
        WHERE acknowledged_by IS NOT NULL
    """)

    # JSON indexes
    op.create_index(
        'idx_alerts_keywords_gin',
        'intelligence_alerts',
        ['keywords'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )

    op.create_index(
        'idx_alerts_entities_gin',
        'intelligence_alerts',
        ['entities'],
        unique=False,
        postgresql_using='gin',
        postgresql_concurrently=True
    )


def downgrade():
    """
    Remove all performance indexes.

    Note: DROP INDEX CONCURRENTLY is also supported for zero-downtime rollback.
    """

    # Intelligence Alerts
    op.drop_index('idx_alerts_entities_gin', table_name='intelligence_alerts')
    op.drop_index('idx_alerts_keywords_gin', table_name='intelligence_alerts')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_acknowledged_by')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_expires_at')
    op.drop_index('idx_alerts_created_at', table_name='intelligence_alerts')
    op.drop_index('idx_alerts_type_severity', table_name='intelligence_alerts')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_status')

    # Learning Sessions
    op.drop_index('idx_learning_session_vocab_gin', table_name='learning_sessions')
    op.drop_index('idx_learning_session_content_gin', table_name='learning_sessions')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_active')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_user_date')
    op.drop_index('idx_learning_session_type', table_name='learning_sessions')
    op.drop_index('idx_learning_session_user_started', table_name='learning_sessions')

    # User Vocabulary
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_mastery_covering')
    op.drop_index('idx_user_vocab_vocabulary_id', table_name='user_vocabulary')
    op.drop_index('idx_user_vocab_user_id', table_name='user_vocabulary')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_next_review')
    op.drop_index('idx_user_vocab_user_mastery', table_name='user_vocabulary')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_user_review')

    # User Content Progress
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_read_percentage')
    op.drop_index('idx_user_progress_content_id', table_name='user_content_progress')
    op.drop_index('idx_user_progress_user_completed', table_name='user_content_progress')
    op.drop_index('idx_user_progress_user_accessed', table_name='user_content_progress')
    op.drop_index('idx_user_progress_user_content', table_name='user_content_progress')

    # Users
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_spanish_level')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_last_login', table_name='users')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_refresh_expires')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_refresh_token')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_is_active')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_username_unique')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_users_email_unique')

    # Extracted Vocabulary
    op.drop_index('idx_extracted_vocab_frequency', table_name='extracted_vocabulary')
    op.drop_index('idx_extracted_vocab_word_difficulty', table_name='extracted_vocabulary')
    op.drop_index('idx_extracted_vocab_pos', table_name='extracted_vocabulary')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_colombian')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_difficulty')
    op.drop_index('idx_extracted_vocab_word', table_name='extracted_vocabulary')
    op.drop_index('idx_extracted_vocab_content_id', table_name='extracted_vocabulary')

    # Content Analysis
    op.drop_index('idx_content_analysis_topics_gin', table_name='content_analysis')
    op.drop_index('idx_content_analysis_entities_gin', table_name='content_analysis')
    op.drop_index('idx_content_analysis_processed_at', table_name='content_analysis')
    op.drop_index('idx_content_analysis_content_processed', table_name='content_analysis')
    op.drop_index('idx_content_analysis_sentiment_label', table_name='content_analysis')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_sentiment_score')
    op.drop_index('idx_content_analysis_content_id', table_name='content_analysis')

    # Scraped Content
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_list_covering')
    op.drop_index('idx_scraped_content_entities_gin', table_name='scraped_content')
    op.drop_index('idx_scraped_content_tags_gin', table_name='scraped_content')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_fulltext_gin')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_content_gin')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_title_gin')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_difficulty_published')
    op.drop_index('idx_scraped_content_source_category_published', table_name='scraped_content')
    op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_is_paywall')
    op.drop_index('idx_scraped_content_scraped_at', table_name='scraped_content')
    op.drop_index('idx_scraped_content_category', table_name='scraped_content')
    op.drop_index('idx_scraped_content_source', table_name='scraped_content')
