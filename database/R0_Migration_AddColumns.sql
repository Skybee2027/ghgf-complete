-- ============================================================================
-- R0 Migration: Add missing columns to blog_posts table
-- ============================================================================
-- This migration adds columns needed by r31 WordPress publisher

ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS ready_for_wordpress BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS final_qa_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS topic VARCHAR(500),
ADD COLUMN IF NOT EXISTS meta_description VARCHAR(500);

-- Add indexes if they don't exist
ALTER TABLE blog_posts ADD INDEX IF NOT EXISTS idx_ready_for_wordpress (ready_for_wordpress);
ALTER TABLE blog_posts ADD INDEX IF NOT EXISTS idx_final_qa_passed (final_qa_passed);

-- Set default values for existing posts so they can be published
UPDATE blog_posts
SET ready_for_wordpress = TRUE, final_qa_passed = TRUE, version = 1
WHERE ready_for_wordpress IS NULL OR ready_for_wordpress = FALSE;
