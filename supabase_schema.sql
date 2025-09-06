-- Rawbify Database Schema for Supabase
-- Run this in Supabase SQL Editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS r_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Trial/access related fields
    trial_access_granted BOOLEAN DEFAULT FALSE,
    trial_access_date TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    
    -- Optional: keep for migration compatibility
    email VARCHAR(255) UNIQUE,
    user_id VARCHAR(50) UNIQUE
);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_r_users_username ON r_users(username);
CREATE INDEX IF NOT EXISTS idx_r_users_is_active ON r_users(is_active);

-- Waitlist table (existing)
CREATE TABLE IF NOT EXISTS r_waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_notified BOOLEAN DEFAULT FALSE
);

-- Processing jobs table (existing + enhanced)
CREATE TABLE IF NOT EXISTS r_processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES r_users(id) ON DELETE CASCADE,
    job_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    input_file_path TEXT,
    output_file_path TEXT,
    user_prompt TEXT,
    ai_response TEXT,
    processing_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    file_size_bytes INTEGER
);

-- Create indexes for processing jobs
CREATE INDEX IF NOT EXISTS idx_r_processing_jobs_user_id ON r_processing_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_r_processing_jobs_status ON r_processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_r_processing_jobs_created_at ON r_processing_jobs(created_at);

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE r_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE r_processing_jobs ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON r_users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON r_users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Users can only see their own processing jobs
CREATE POLICY "Users can view own processing jobs" ON r_processing_jobs
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own processing jobs" ON r_processing_jobs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own processing jobs" ON r_processing_jobs
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Grant permissions for service role (for your backend)
GRANT ALL ON r_users TO service_role;
GRANT ALL ON r_waitlist TO service_role;
GRANT ALL ON r_processing_jobs TO service_role;

-- Insert a test user (optional)
-- Password is 'testpass123' hashed
INSERT INTO r_users (username, password_hash, trial_access_granted) 
VALUES ('testuser', 'a1b2c3d4e5f6:abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Display table info
SELECT 'Tables created successfully!' as status;
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('r_users', 'r_waitlist', 'r_processing_jobs')
ORDER BY table_name, ordinal_position;
