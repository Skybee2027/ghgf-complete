-- ============================================================================
-- R0 Migration: Add missing columns required by R2 (Blog Title Generator)
-- ============================================================================
-- This migration adds columns that R2 expects but are missing from the base schema
-- Without these columns, R2 cannot generate blog titles

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

-- Populate topic_name from topics table if topics exist
UPDATE topic_rotation tr
SET tr.topic_name = (SELECT t.name FROM topics t WHERE t.id = tr.topic_id)
WHERE tr.topic_name IS NULL AND tr.topic_id IS NOT NULL;

-- Set initial status to active for the first topic if none are active
UPDATE topic_rotation
SET status = 'active', start_date = CURDATE()
WHERE status = 'pending'
  AND cycle_number = 1
  AND topic_sequence = 1
  AND id = (SELECT MIN(id) FROM topic_rotation t WHERE t.status = 'pending');

-- ============================================================================
-- 2. Add missing columns to trending_keywords table
-- ============================================================================
ALTER TABLE trending_keywords
ADD COLUMN IF NOT EXISTS topic VARCHAR(255);

-- Add index for topic column
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
-- 4. Initialize topics table if empty
-- ============================================================================
-- This ensures R2 has at least one topic to work with
INSERT IGNORE INTO topics (id, name, description, keyword_focus, monthly_searches, competition_level, created_at)
VALUES
  (1, 'Weight Loss', 'Tips and strategies for healthy weight loss', 'weight loss, lose weight, diet', 10000, 'high', NOW()),
  (2, 'Fitness Training', 'Workout routines and fitness guidance', 'fitness, workout, exercise', 8000, 'high', NOW()),
  (3, 'Nutrition', 'Healthy eating and nutrition advice', 'nutrition, diet, healthy eating', 7000, 'medium', NOW()),
  (4, 'Mental Health', 'Mental wellness and stress management', 'mental health, stress relief, anxiety', 6000, 'medium', NOW()),
  (5, 'Sleep Quality', 'Sleep improvement and sleep hygiene', 'better sleep, sleep quality, insomnia', 5000, 'medium', NOW()),
  (6, 'Yoga & Flexibility', 'Yoga practices and flexibility training', 'yoga, stretching, flexibility', 4500, 'medium', NOW()),
  (7, 'Running & Cardio', 'Running tips and cardiovascular fitness', 'running, cardio, jogging', 4000, 'medium', NOW()),
  (8, 'Strength Training', 'Muscle building and strength exercises', 'strength training, weightlifting, muscles', 6500, 'high', NOW()),
  (9, 'Supplements', 'Nutritional supplements and vitamins', 'supplements, vitamins, protein', 5500, 'high', NOW()),
  (10, 'Wellness Habits', 'Daily habits for better health', 'healthy habits, wellness, self-care', 3500, 'low', NOW()),
  (11, 'Sports Performance', 'Athletic training and performance', 'sports training, athletic performance', 3000, 'medium', NOW()),
  (12, 'Recovery Techniques', 'Post-workout recovery methods', 'recovery, stretching, massage', 2500, 'low', NOW()),
  (13, 'Age-Specific Fitness', 'Fitness for different age groups', 'fitness over 40, senior fitness', 2000, 'low', NOW()),
  (14, 'Group Fitness', 'Classes and group workout activities', 'group fitness, classes, community', 1800, 'low', NOW()),
  (15, 'Home Workouts', 'Exercises that can be done at home', 'home workout, no equipment, bodyweight', 7500, 'high', NOW()),
  (16, 'Outdoor Activities', 'Outdoor fitness and recreation', 'hiking, outdoor exercise, cycling', 3200, 'low', NOW()),
  (17, 'Injury Prevention', 'How to prevent fitness-related injuries', 'injury prevention, joint health', 2800, 'low', NOW()),
  (18, 'Women Health Fitness', 'Fitness guidance for women', 'women fitness, female health', 4000, 'medium', NOW());

-- ============================================================================
-- 5. Initialize topic_rotation table if empty
-- ============================================================================
INSERT IGNORE INTO topic_rotation (topic_id, cycle_number, topic_sequence, status, start_date, created_at)
SELECT
  t.id,
  1 as cycle_number,
  t.id as topic_sequence,
  CASE WHEN t.id = 1 THEN 'active' ELSE 'pending' END as status,
  CASE WHEN t.id = 1 THEN CURDATE() ELSE NULL END as start_date,
  NOW() as created_at
FROM topics t
WHERE NOT EXISTS (SELECT 1 FROM topic_rotation WHERE topic_id = t.id);

-- ============================================================================
-- 6. Initialize trending_keywords table if empty
-- ============================================================================
INSERT IGNORE INTO trending_keywords (keyword, search_volume, competition_level, topic, created_at)
VALUES
  ('weight loss', 10000, 'high', 'Weight Loss', NOW()),
  ('how to lose weight', 8000, 'high', 'Weight Loss', NOW()),
  ('weight loss diet', 7000, 'high', 'Weight Loss', NOW()),
  ('fitness workout', 8000, 'high', 'Fitness Training', NOW()),
  ('home workout', 7500, 'high', 'Home Workouts', NOW()),
  ('strength training', 6500, 'high', 'Strength Training', NOW()),
  ('best nutrition', 7000, 'medium', 'Nutrition', NOW()),
  ('mental health tips', 6000, 'medium', 'Mental Health', NOW()),
  ('better sleep', 5000, 'medium', 'Sleep Quality', NOW()),
  ('yoga for beginners', 4500, 'medium', 'Yoga & Flexibility', NOW());

-- ============================================================================
-- 7. Verification
-- ============================================================================
-- This section verifies that all required tables and columns exist

-- Check topic_rotation table structure
SELECT 'topic_rotation table check' as verification;
SHOW COLUMNS FROM topic_rotation LIKE 'status';
SHOW COLUMNS FROM topic_rotation LIKE 'topic_name';
SHOW COLUMNS FROM topic_rotation LIKE 'topic_sequence';
SHOW COLUMNS FROM topic_rotation LIKE 'start_date';

-- Check trending_keywords table structure
SELECT 'trending_keywords table check' as verification;
SHOW COLUMNS FROM trending_keywords LIKE 'topic';

-- Check that we have data
SELECT 'Data availability check' as verification;
SELECT COUNT(*) as topic_count FROM topics;
SELECT COUNT(*) as topic_rotation_count FROM topic_rotation;
SELECT COUNT(*) as trending_keyword_count FROM trending_keywords;

-- Verify at least one active topic
SELECT COUNT(*) as active_topics FROM topic_rotation WHERE status = 'active';

