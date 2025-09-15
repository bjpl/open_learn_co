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
    metadata = Column(JSON)  # Additional metadata

    # Language learning
    difficulty_score = Column(Float)  # 1.0 to 5.0
    is_paywall = Column(Boolean, default=False)

    # Relationships
    analyses = relationship("ContentAnalysis", back_populates="content")
    vocabulary = relationship("ExtractedVocabulary", back_populates="content")
    user_progress = relationship("UserContentProgress", back_populates="content")

    # Indexes for performance
    __table_args__ = (
        Index('idx_source_category', 'source', 'category'),
        Index('idx_published_date', 'published_date'),
        Index('idx_difficulty_score', 'difficulty_score'),
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

    # Indexes
    __table_args__ = (
        Index('idx_word_lemma', 'word', 'lemma'),
        Index('idx_difficulty_level', 'difficulty_level'),
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

    # Colombian context preferences
    preferred_regions = Column(JSON)  # Colombian regions of interest
    preferred_sources = Column(JSON)  # Preferred news sources

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())

    # Relationships
    content_progress = relationship("UserContentProgress", back_populates="user")
    vocabulary_progress = relationship("UserVocabulary", back_populates="user")
    learning_sessions = relationship("LearningSession", back_populates="user")


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

    # Unique constraint
    __table_args__ = (
        Index('idx_user_content', 'user_id', 'content_id', unique=True),
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

    # Unique constraint
    __table_args__ = (
        Index('idx_user_vocabulary', 'user_id', 'vocabulary_id', unique=True),
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

    # Indexes
    __table_args__ = (
        Index('idx_alert_type_status', 'alert_type', 'status'),
        Index('idx_created_at', 'created_at'),
    )