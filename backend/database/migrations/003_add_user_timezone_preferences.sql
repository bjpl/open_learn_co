-- Migration 003: Add User Timezone and Preference Fields
-- Created: 2025-10-08
-- Purpose: Add timezone support and enhanced user preferences for notification system

-- Add timezone field to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS timezone VARCHAR(100) DEFAULT 'America/Bogota';

-- Add preferred UI language
ALTER TABLE users
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'es';

-- Add preferred content categories
ALTER TABLE users
ADD COLUMN IF NOT EXISTS preferred_categories JSON DEFAULT NULL;

-- Add comments for documentation
COMMENT ON COLUMN users.timezone IS 'User timezone in IANA format (e.g., America/Bogota). Used for notification scheduling and activity tracking.';
COMMENT ON COLUMN users.language IS 'Preferred UI language code (ISO 639-1). Default: es (Spanish)';
COMMENT ON COLUMN users.preferred_categories IS 'JSON array of preferred content categories for personalized notifications';

-- Create index on timezone for scheduling queries
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone)
WHERE timezone IS NOT NULL;

-- Update existing users to have Colombia timezone if NULL
UPDATE users
SET timezone = 'America/Bogota'
WHERE timezone IS NULL;

-- Update existing users to have Spanish language if NULL
UPDATE users
SET language = 'es'
WHERE language IS NULL;

-- Migration verification
DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users WHERE timezone IS NULL OR language IS NULL;

    IF user_count > 0 THEN
        RAISE WARNING 'Migration 003: % users still have NULL timezone or language', user_count;
    ELSE
        RAISE NOTICE 'Migration 003: All users have timezone and language configured';
    END IF;
END $$;
