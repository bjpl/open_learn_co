-- Performance Indexes for OpenLearn Colombia Platform
-- Phase 2: Database Optimization
-- Target: <50ms query performance (p95)

-- ============================================================================
-- SCRAPED_CONTENT TABLE INDEXES
-- ============================================================================

-- Single-column indexes for filtering and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_source
    ON scraped_content(source);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_category
    ON scraped_content(category);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_scraped_at
    ON scraped_content(scraped_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_is_paywall
    ON scraped_content(is_paywall)
    WHERE is_paywall = false;  -- Partial index for free content

-- Composite indexes for common query patterns
-- Query: Filter by source + category + published date (common in API)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_source_category_published
    ON scraped_content(source, category, published_date DESC);

-- Query: Difficulty-based filtering with date sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_difficulty_published
    ON scraped_content(difficulty_score, published_date DESC)
    WHERE difficulty_score IS NOT NULL;

-- Full-text search indexes (GIN for better text search performance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_title_gin
    ON scraped_content USING gin(to_tsvector('spanish', title));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_content_gin
    ON scraped_content USING gin(to_tsvector('spanish', content));

-- Combined title + content search index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_fulltext_gin
    ON scraped_content USING gin(
        (to_tsvector('spanish', coalesce(title, '')) ||
         to_tsvector('spanish', coalesce(content, '')))
    );

-- JSON column indexes for entity and tag searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_tags_gin
    ON scraped_content USING gin(tags);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_entities_gin
    ON scraped_content USING gin(colombian_entities);


-- ============================================================================
-- CONTENT_ANALYSIS TABLE INDEXES
-- ============================================================================

-- Foreign key index (critical for joins)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_content_id
    ON content_analysis(content_id);

-- Sentiment analysis queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_sentiment_score
    ON content_analysis(sentiment_score)
    WHERE sentiment_score IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_sentiment_label
    ON content_analysis(sentiment_label);

-- Composite for content-based time-series analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_content_processed
    ON content_analysis(content_id, processed_at DESC);

-- Processed date for analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_processed_at
    ON content_analysis(processed_at DESC);

-- JSON indexes for entity and topic searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_entities_gin
    ON content_analysis USING gin(entities);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analysis_topics_gin
    ON content_analysis USING gin(topics);


-- ============================================================================
-- EXTRACTED_VOCABULARY TABLE INDEXES
-- ============================================================================

-- Foreign key index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_content_id
    ON extracted_vocabulary(content_id);

-- Word search and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_word
    ON extracted_vocabulary(word);

-- Difficulty-based filtering (enhanced from existing)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_difficulty
    ON extracted_vocabulary(difficulty_level)
    WHERE difficulty_level IS NOT NULL;

-- Colombian-specific vocabulary
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_colombian
    ON extracted_vocabulary(is_colombian_specific)
    WHERE is_colombian_specific = true;

-- Part-of-speech filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_pos
    ON extracted_vocabulary(pos_tag);

-- Composite for word search with context
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_word_difficulty
    ON extracted_vocabulary(word, difficulty_level);

-- Frequency-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_vocab_frequency
    ON extracted_vocabulary(frequency_in_article DESC);


-- ============================================================================
-- USERS TABLE INDEXES
-- ============================================================================

-- Authentication indexes (critical for login performance)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_unique
    ON users(lower(email));  -- Case-insensitive email

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_unique
    ON users(lower(username))
    WHERE username IS NOT NULL;

-- Active user filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active
    ON users(is_active)
    WHERE is_active = true;

-- Session management
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_refresh_token
    ON users(refresh_token)
    WHERE refresh_token IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_refresh_expires
    ON users(refresh_token_expires_at)
    WHERE refresh_token_expires_at > NOW();

-- User activity tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login
    ON users(last_login DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at
    ON users(created_at DESC);

-- Role-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role
    ON users(role);

-- Spanish level filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_spanish_level
    ON users(spanish_level)
    WHERE spanish_level IS NOT NULL;


-- ============================================================================
-- USER_CONTENT_PROGRESS TABLE INDEXES
-- ============================================================================

-- Composite primary access pattern (user viewing their progress)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_user_content
    ON user_content_progress(user_id, content_id);

-- User activity timeline
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_user_accessed
    ON user_content_progress(user_id, last_accessed DESC);

-- Completion tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_user_completed
    ON user_content_progress(user_id, completed, completed_at DESC);

-- Content popularity metrics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_content_id
    ON user_content_progress(content_id);

-- Reading progress filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_progress_read_percentage
    ON user_content_progress(read_percentage)
    WHERE completed = false;


-- ============================================================================
-- USER_VOCABULARY TABLE INDEXES
-- ============================================================================

-- Composite for spaced repetition queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_user_review
    ON user_vocabulary(user_id, next_review)
    WHERE next_review IS NOT NULL;

-- Mastery level tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_user_mastery
    ON user_vocabulary(user_id, mastery_level DESC);

-- Vocabulary review scheduling
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_next_review
    ON user_vocabulary(next_review)
    WHERE next_review <= NOW() + INTERVAL '1 day';

-- User vocabulary lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_user_id
    ON user_vocabulary(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_vocabulary_id
    ON user_vocabulary(vocabulary_id);


-- ============================================================================
-- LEARNING_SESSIONS TABLE INDEXES
-- ============================================================================

-- User session history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_user_started
    ON learning_sessions(user_id, started_at DESC);

-- Session type analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_type
    ON learning_sessions(session_type);

-- Recent sessions for streak calculation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_user_date
    ON learning_sessions(user_id, started_at::date DESC);

-- Active sessions (not yet ended)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_active
    ON learning_sessions(user_id, started_at DESC)
    WHERE ended_at IS NULL;

-- JSON indexes for content and vocabulary tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_content_gin
    ON learning_sessions USING gin(content_ids);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_session_vocab_gin
    ON learning_sessions USING gin(vocabulary_ids);


-- ============================================================================
-- INTELLIGENCE_ALERTS TABLE INDEXES
-- ============================================================================

-- Alert status filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_status
    ON intelligence_alerts(status)
    WHERE status IN ('active', 'pending');

-- Alert type + severity for prioritization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_type_severity
    ON intelligence_alerts(alert_type, severity, created_at DESC);

-- Time-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_created_at
    ON intelligence_alerts(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_expires_at
    ON intelligence_alerts(expires_at)
    WHERE expires_at IS NOT NULL AND expires_at > NOW();

-- User acknowledgment tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_acknowledged_by
    ON intelligence_alerts(acknowledged_by)
    WHERE acknowledged_by IS NOT NULL;

-- JSON indexes for pattern matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_keywords_gin
    ON intelligence_alerts USING gin(keywords);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_entities_gin
    ON intelligence_alerts USING gin(entities);


-- ============================================================================
-- COVERING INDEXES (Include frequently accessed columns)
-- ============================================================================

-- Scraped content list queries (avoid table lookups)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraped_content_list_covering
    ON scraped_content(published_date DESC)
    INCLUDE (id, source, category, title, difficulty_score, is_paywall);

-- User vocabulary mastery queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_vocab_mastery_covering
    ON user_vocabulary(user_id, mastery_level DESC)
    INCLUDE (vocabulary_id, next_review, times_seen, times_correct);


-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
-- To rollback these indexes, run:
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_source;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_category;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_scraped_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_is_paywall;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_source_category_published;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_difficulty_published;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_title_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_content_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_fulltext_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_tags_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_entities_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_content_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_sentiment_score;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_sentiment_label;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_content_processed;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_processed_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_entities_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_analysis_topics_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_content_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_word;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_difficulty;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_colombian;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_pos;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_word_difficulty;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_extracted_vocab_frequency;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_email_unique;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_username_unique;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_is_active;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_refresh_token;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_refresh_expires;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_last_login;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_created_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_role;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_users_spanish_level;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_user_content;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_user_accessed;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_user_completed;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_content_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_progress_read_percentage;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_user_review;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_user_mastery;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_next_review;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_user_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_vocabulary_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_user_started;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_type;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_user_date;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_active;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_content_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_learning_session_vocab_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_status;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_type_severity;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_created_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_expires_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_acknowledged_by;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_keywords_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_alerts_entities_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_list_covering;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_user_vocab_mastery_covering;


-- ============================================================================
-- INDEX STATISTICS AND VALIDATION
-- ============================================================================

-- Query to check index sizes after creation:
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
--     idx_scan as times_used,
--     idx_tup_read as tuples_read,
--     idx_tup_fetch as tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- Query to identify unused indexes:
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
--     idx_scan
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public' AND idx_scan = 0
-- ORDER BY pg_relation_size(indexrelid) DESC;
