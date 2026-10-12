-- ============================================================================
-- R0 Migration: Add missing columns required by R2 (Blog Title Generator)
-- ============================================================================
-- This migration ONLY adds missing columns. Data will be created by robot scripts.

-- ============================================================================
-- 1. Add missing columns to topic_rotation table
-- ============================================================================
ALTER TABLE topic_rotation
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending';

ALTER TABLE topic_rotation
ADD COLUMN IF NOT EXISTS topic_name VARCHAR(255);

ALTER TABLE topic_rotation
ADD COLUMN IF NOT EXISTS topic_sequence INT;

ALTER TABLE topic_rotation
ADD COLUMN IF NOT EXISTS start_date DATE;

-- Add indexes on new columns
ALTER TABLE topic_rotation
ADD INDEX IF NOT EXISTS idx_status (status);

ALTER TABLE topic_rotation
ADD INDEX IF NOT EXISTS idx_start_date (start_date);

-- ============================================================================
-- 2. Add missing columns to trending_keywords table
-- ============================================================================
ALTER TABLE trending_keywords
ADD COLUMN IF NOT EXISTS topic VARCHAR(255);

ALTER TABLE trending_keywords
ADD INDEX IF NOT EXISTS idx_topic (topic);

-- ============================================================================
-- 3. Add missing columns to blog_titles table for R2 compatibility
-- ============================================================================
ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS keywords VARCHAR(500);

ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS ctr_score DECIMAL(5, 2) DEFAULT 0;

ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'groq';

ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS topic VARCHAR(500);

ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS used BOOLEAN DEFAULT FALSE;

ALTER TABLE blog_titles
ADD COLUMN IF NOT EXISTS used_at TIMESTAMP NULL;

-- ============================================================================
-- Done - All required columns added
-- ============================================================================
