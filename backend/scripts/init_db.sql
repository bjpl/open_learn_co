-- Database Initialization Script for Colombian Intelligence Platform
-- Creates necessary extensions and initial setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- Set timezone to Colombia
SET timezone = 'America/Bogota';

-- Create initial database user if not exists (already created by Docker)
-- This is just for documentation
-- The user 'colombian_user' is created automatically by Docker with the password from environment

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for Colombian Intelligence Platform';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm, btree_gin';
    RAISE NOTICE 'Timezone: America/Bogota';
END $$;
