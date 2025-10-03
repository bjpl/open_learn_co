-- Database Migration for JWT Authentication
-- Phase 1: Add refresh token fields to users table
-- Execute this migration after implementing JWT authentication

-- Add refresh token columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS refresh_token VARCHAR(500),
ADD COLUMN IF NOT EXISTS refresh_token_expires_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_refresh_token ON users(refresh_token);

-- Set default values for existing users
UPDATE users
SET is_active = TRUE
WHERE is_active IS NULL;

-- Add trigger for updated_at auto-update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
    AND column_name IN ('refresh_token', 'refresh_token_expires_at', 'is_active', 'last_login', 'updated_at')
ORDER BY column_name;

-- Migration complete
SELECT 'JWT Authentication migration completed successfully!' AS status;
