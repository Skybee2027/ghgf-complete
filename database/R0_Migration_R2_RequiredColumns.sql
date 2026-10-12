-- ============================================================================
-- R0 Migration: Add missing columns required by R2 (Blog Title Generator)
-- ============================================================================
-- This migration adds columns that R2 expects but are missing from the base schema

-- ============================================================================
-- 1. Add missing columns to topic_rotation table
-- ============================================================================
ALTER TABLE topic_rotation
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS topic_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS topic_sequence INT,
ADD COLUMN IF NOT EXISTS start_date DATE;

-- Add indexes
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
ADD COLUMN IF NOT EXISTS keywords VARCHAR(500),
ADD COLUMN IF NOT EXISTS ctr_score DECIMAL(5, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'groq';

-- ============================================================================
-- 4. Ensure we have a default topic if none exist
-- ============================================================================
INSERT IGNORE INTO topics (id, name, description, monthly_searches, competition_level)
VALUES (1, 'Health and Fitness', 'General health and fitness topics', 50000, 'high');

-- ============================================================================
-- 5. Ensure we have a topic rotation entry if none exist
-- ============================================================================
INSERT IGNORE INTO topic_rotation (id, topic_id, cycle_number, topic_sequence, status, start_date)
VALUES (1, 1, 1, 1, 'active', CURDATE());

-- ============================================================================
-- 6. Ensure we have trending keywords if none exist
-- ============================================================================
INSERT IGNORE INTO trending_keywords (keyword, search_volume, competition_level, topic)
VALUES
  ('health and fitness', 50000, 'high', 'Health and Fitness'),
  ('healthy lifestyle', 45000, 'high', 'Health and Fitness'),
  ('fitness tips', 40000, 'high', 'Health and Fitness'),
  ('wellness goals', 35000, 'high', 'Health and Fitness'),
  ('health trends 2026', 30000, 'medium', 'Health and Fitness');

-- ============================================================================
-- Done - All required columns and minimal data added
-- ============================================================================
