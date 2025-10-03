-- Migration 003: Add Notification System
-- Creates tables for in-app notifications, email preferences, and email logs

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification properties
    type VARCHAR(20) NOT NULL DEFAULT 'INFO',
    category VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',

    -- Content
    title VARCHAR(100) NOT NULL,
    message VARCHAR(500) NOT NULL,

    -- Action (optional)
    action_url VARCHAR(500),
    action_label VARCHAR(50),

    -- Metadata
    metadata JSONB,

    -- Status
    read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Notification preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Email notification preferences
    email_digest_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_digest_time VARCHAR(5) DEFAULT '08:00',
    email_weekly_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_vocabulary_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- In-app notification preferences
    in_app_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Category preferences
    notification_categories JSONB DEFAULT '[]',

    -- Quiet hours
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),

    -- Frequency limits
    max_emails_per_day INTEGER DEFAULT 5,
    max_in_app_per_hour INTEGER DEFAULT 10,

    -- User timezone
    timezone VARCHAR(50) DEFAULT 'America/Bogota',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Email logs table
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Email details
    email_type VARCHAR(50) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),

    -- Status
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    error_message TEXT,

    -- Engagement (optional)
    opened BOOLEAN DEFAULT FALSE,
    opened_at TIMESTAMP,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for notifications
CREATE INDEX idx_notification_user_read_created
    ON notifications(user_id, read, created_at DESC);

CREATE INDEX idx_notification_user_category
    ON notifications(user_id, category);

CREATE INDEX idx_notification_created_at
    ON notifications(created_at);

CREATE INDEX idx_notification_active
    ON notifications(user_id, expires_at)
    WHERE expires_at IS NOT NULL;

CREATE INDEX idx_notification_priority
    ON notifications(priority);

-- Indexes for notification preferences
CREATE INDEX idx_notif_pref_user_id
    ON notification_preferences(user_id);

-- Indexes for email logs
CREATE INDEX idx_email_log_user_created
    ON email_logs(user_id, created_at DESC);

CREATE INDEX idx_email_log_type
    ON email_logs(email_type);

CREATE INDEX idx_email_log_sent
    ON email_logs(sent);

-- Comments
COMMENT ON TABLE notifications IS 'In-app notifications for users';
COMMENT ON TABLE notification_preferences IS 'User notification preferences and settings';
COMMENT ON TABLE email_logs IS 'Email send logs for analytics and debugging';

-- Update timestamp trigger for notification_preferences
CREATE OR REPLACE FUNCTION update_notification_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notification_preferences_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_preferences_updated_at();
