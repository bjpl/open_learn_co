"""
Database models for Colombia Intelligence & Language Learning Platform
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ScrapedContent(Base):
    """Model for scraped news articles and content"""
    __tablename__ = 'scraped_content'

    id = Column(Integer, primary_key=True)
    source = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=False, unique=True)
    category = Column(String(50))

    # Content fields
    title = Column(String(500), nullable=False)
    subtitle = Column(Text)
    content = Column(Text, nullable=False)
    author = Column(String(200))
    word_count = Column(Integer)

    # Metadata
    published_date = Column(DateTime)
    scraped_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    content_hash = Column(String(64), unique=True)

    # Colombian context
    colombian_entities = Column(JSON)  # Extracted entities
    tags = Column(JSON)  # Article tags
    extra_metadata = Column(JSON)  # Additional metadata

    # Language learning
    difficulty_score = Column(Float)  # 1.0 to 5.0
    is_paywall = Column(Boolean, default=False)

    # Relationships
    analyses = relationship("ContentAnalysis", back_populates="content")
    vocabulary = relationship("ExtractedVocabulary", back_populates="content")
    user_progress = relationship("UserContentProgress", back_populates="content")

    # Indexes for performance (Phase 2 optimization - see migration 002)
    # Target: <50ms p95 latency for common queries
    __table_args__ = (
        # Existing indexes (basic)
        Index('idx_source_category', 'source', 'category'),
        Index('idx_published_date', 'published_date'),
        Index('idx_difficulty_score', 'difficulty_score'),

        # Additional indexes added in migration 002:
        # - idx_scraped_content_source (filter by source)
        # - idx_scraped_content_category (filter by category)
        # - idx_scraped_content_scraped_at (sort by scrape date)
        # - idx_scraped_content_is_paywall (partial: free content only)
        # - idx_scraped_content_source_category_published (composite for common API queries)
        # - idx_scraped_content_difficulty_published (difficulty filtering + date sort)
        # - idx_scraped_content_title_gin (Spanish full-text search)
        # - idx_scraped_content_content_gin (Spanish full-text search)
        # - idx_scraped_content_fulltext_gin (combined title+content search)
        # - idx_scraped_content_tags_gin (JSON tag searches)
        # - idx_scraped_content_entities_gin (JSON entity searches)
        # - idx_scraped_content_list_covering (covering index for list views)
    )


class ContentAnalysis(Base):
    """Model for NLP analysis results"""
    __tablename__ = 'content_analysis'

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('scraped_content.id'), nullable=False)

    # NLP results
    entities = Column(JSON)  # Named entities with types
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_label = Column(String(20))  # positive, negative, neutral
    key_phrases = Column(JSON)
    topics = Column(JSON)  # Topic modeling results
    summary = Column(Text)  # Auto-generated summary

    # Colombian Spanish specific
    colombian_slang = Column(JSON)  # Detected Colombian expressions
    regional_variations = Column(JSON)  # Regional language patterns

    # Processing metadata
    processed_at = Column(DateTime, default=func.now())
    processing_time_ms = Column(Integer)
    model_version = Column(String(50))

    # Relationships
    content = relationship("ScrapedContent", back_populates="analyses")

    # Indexes added in migration 002 for performance:
    # - idx_content_analysis_content_id (FK join optimization)
    # - idx_content_analysis_sentiment_score (partial: non-null only)
    # - idx_content_analysis_sentiment_label (filter by sentiment)
    # - idx_content_analysis_content_processed (composite time-series)
    # - idx_content_analysis_processed_at (analytics queries)
    # - idx_content_analysis_entities_gin (JSON entity search)
    # - idx_content_analysis_topics_gin (JSON topic search)


class ExtractedVocabulary(Base):
    """Model for vocabulary extracted for language learning"""
    __tablename__ = 'extracted_vocabulary'

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('scraped_content.id'), nullable=False)

    # Word information
    word = Column(String(100), nullable=False)
    lemma = Column(String(100))  # Base form
    pos_tag = Column(String(20))  # Part of speech

    # Context
    sentence = Column(Text)  # Example sentence from article
    context_before = Column(String(200))  # Words before
    context_after = Column(String(200))  # Words after

    # Language learning metrics
    frequency_in_article = Column(Integer)
    difficulty_level = Column(Integer)  # 1-5
    is_colombian_specific = Column(Boolean, default=False)

    # Translations and definitions
    english_translation = Column(String(200))
    spanish_definition = Column(Text)
    usage_notes = Column(Text)  # Colombian usage specifics

    # Relationships
    content = relationship("ScrapedContent", back_populates="vocabulary")
    user_vocabulary = relationship("UserVocabulary", back_populates="vocabulary")

    # Indexes for vocabulary search and filtering
    __table_args__ = (
        Index('idx_word_lemma', 'word', 'lemma'),
        Index('idx_difficulty_level', 'difficulty_level'),

        # Additional indexes in migration 002:
        # - idx_extracted_vocab_content_id (FK join)
        # - idx_extracted_vocab_word (word search)
        # - idx_extracted_vocab_difficulty (partial: non-null difficulty)
        # - idx_extracted_vocab_colombian (partial: Colombian-specific only)
        # - idx_extracted_vocab_pos (part-of-speech filtering)
        # - idx_extracted_vocab_word_difficulty (composite search)
        # - idx_extracted_vocab_frequency (frequency-based queries)
    )


class User(Base):
    """Model for platform users"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(200))
    role = Column(String(50), default='learner')  # learner, analyst, admin
    spanish_level = Column(String(20))  # A1, A2, B1, B2, C1, C2
    learning_goals = Column(JSON)
    interests = Column(JSON)  # Topics of interest

    # Localization
    timezone = Column(String(100), default='America/Bogota')  # User's timezone (IANA format)
    language = Column(String(10), default='es')  # Preferred UI language

    # Colombian context preferences
    preferred_regions = Column(JSON)  # Colombian regions of interest
    preferred_sources = Column(JSON)  # Preferred news sources
    preferred_categories = Column(JSON)  # Preferred content categories

    # Authentication & Security
    refresh_token = Column(String(500))  # Current valid refresh token
    refresh_token_expires_at = Column(DateTime)  # Refresh token expiration
    is_active = Column(Boolean, default=True)  # Account active status
    last_login = Column(DateTime)  # Last successful login

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_active = Column(DateTime, default=func.now())

    # Relationships
    content_progress = relationship("UserContentProgress", back_populates="user")
    vocabulary_progress = relationship("UserVocabulary", back_populates="user")
    learning_sessions = relationship("LearningSession", back_populates="user")

    # Indexes for authentication and user management (critical performance)
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_refresh_token', 'refresh_token'),

        # Additional indexes in migration 002 (auth optimization - target <50ms):
        # - idx_users_email_unique (case-insensitive unique email for login)
        # - idx_users_username_unique (case-insensitive unique username)
        # - idx_users_is_active (partial: active users only)
        # - idx_users_refresh_token (session management - non-null only)
        # - idx_users_refresh_expires (partial: valid tokens only)
        # - idx_users_last_login (activity tracking)
        # - idx_users_created_at (user analytics)
        # - idx_users_role (role-based queries)
        # - idx_users_spanish_level (partial: users with level set)
    )


class UserContentProgress(Base):
    """Track user progress with content"""
    __tablename__ = 'user_content_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('scraped_content.id'), nullable=False)

    # Reading progress
    read_percentage = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)

    # Comprehension
    comprehension_score = Column(Float)  # Quiz results
    notes = Column(Text)  # User notes

    # Timestamps
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    last_accessed = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="content_progress")
    content = relationship("ScrapedContent", back_populates="user_progress")

    # Unique constraint and performance indexes
    __table_args__ = (
        Index('idx_user_content', 'user_id', 'content_id', unique=True),

        # Additional indexes in migration 002:
        # - idx_user_progress_user_content (composite lookup)
        # - idx_user_progress_user_accessed (user activity timeline)
        # - idx_user_progress_user_completed (completion tracking)
        # - idx_user_progress_content_id (content popularity)
        # - idx_user_progress_read_percentage (partial: incomplete reads)
    )


class UserVocabulary(Base):
    """Track user vocabulary learning progress"""
    __tablename__ = 'user_vocabulary'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vocabulary_id = Column(Integer, ForeignKey('extracted_vocabulary.id'), nullable=False)

    # Learning metrics
    times_seen = Column(Integer, default=1)
    times_correct = Column(Integer, default=0)
    times_incorrect = Column(Integer, default=0)
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0

    # Spaced repetition
    next_review = Column(DateTime)
    review_interval_days = Column(Integer, default=1)

    # Timestamps
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    mastered_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="vocabulary_progress")
    vocabulary = relationship("ExtractedVocabulary", back_populates="user_vocabulary")

    # Unique constraint and spaced repetition indexes
    __table_args__ = (
        Index('idx_user_vocabulary', 'user_id', 'vocabulary_id', unique=True),

        # Additional indexes in migration 002 (spaced repetition optimization):
        # - idx_user_vocab_user_review (partial: due for review)
        # - idx_user_vocab_user_mastery (mastery level tracking)
        # - idx_user_vocab_next_review (partial: reviews within 24h)
        # - idx_user_vocab_user_id (user lookup)
        # - idx_user_vocab_vocabulary_id (vocabulary lookup)
        # - idx_user_vocab_mastery_covering (covering: avoid table lookup)
    )


class LearningSession(Base):
    """Track learning sessions for analytics"""
    __tablename__ = 'learning_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Session details
    session_type = Column(String(50))  # reading, vocabulary, quiz
    duration_seconds = Column(Integer)

    # Progress metrics
    items_completed = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    score = Column(Float)

    # Content covered
    content_ids = Column(JSON)  # List of content IDs
    vocabulary_ids = Column(JSON)  # List of vocabulary IDs

    # Timestamps
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="learning_sessions")

    # Indexes added in migration 002 for session tracking:
    # - idx_learning_session_user_started (user session history)
    # - idx_learning_session_type (session type analytics)
    # - idx_learning_session_user_date (streak calculation - date-based)
    # - idx_learning_session_active (partial: active sessions only)
    # - idx_learning_session_content_gin (JSON content tracking)
    # - idx_learning_session_vocab_gin (JSON vocabulary tracking)


class IntelligenceAlert(Base):
    """Model for intelligence alerts and notifications"""
    __tablename__ = 'intelligence_alerts'

    id = Column(Integer, primary_key=True)

    # Alert configuration
    alert_type = Column(String(50))  # entity_mention, topic_trend, sentiment_shift
    keywords = Column(JSON)  # Keywords to monitor
    entities = Column(JSON)  # Entities to track
    sources = Column(JSON)  # Specific sources to monitor

    # Alert details
    title = Column(String(500))
    description = Column(Text)
    severity = Column(String(20))  # low, medium, high, critical

    # Triggering content
    triggered_by_content_ids = Column(JSON)
    matched_patterns = Column(JSON)

    # Status
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    acknowledged_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)

    # Indexes for alert filtering and monitoring
    __table_args__ = (
        Index('idx_alert_type_status', 'alert_type', 'status'),
        Index('idx_created_at', 'created_at'),

        # Additional indexes in migration 002:
        # - idx_alerts_status (partial: active/pending alerts only)
        # - idx_alerts_type_severity (composite prioritization)
        # - idx_alerts_created_at (time-based queries)
        # - idx_alerts_expires_at (partial: valid unexpired alerts)
        # - idx_alerts_acknowledged_by (partial: acknowledged alerts)
        # - idx_alerts_keywords_gin (JSON keyword search)
        # - idx_alerts_entities_gin (JSON entity search)
    )