-- GHGF Database Schema Fix
-- This script fixes all database schema issues that were causing 11 robots to fail
-- Created: 2026-10-12
-- Purpose: Align database schema with robot code expectations

-- ============================================================================
-- STEP 1: BACKUP OLD TABLES (rename them with _old suffix)
-- ============================================================================

ALTER TABLE IF EXISTS topic_rotation RENAME TO topic_rotation_old;
ALTER TABLE IF EXISTS blog_titles RENAME TO blog_titles_old;
ALTER TABLE IF EXISTS blog_posts RENAME TO blog_posts_old;

-- ============================================================================
-- STEP 2: CREATE FIXED topic_rotation TABLE
-- ============================================================================
-- This table manages the 18-topic rotation cycle
-- Expected by: R2 (Blog Title Generator)

CREATE TABLE IF NOT EXISTS topic_rotation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(500) NOT NULL,
    cycle_number INT DEFAULT 1,
    topic_sequence INT DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active',
    start_date DATE,
    last_rotated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_cycle (cycle_number, topic_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- STEP 3: CREATE FIXED blog_titles TABLE
-- ============================================================================
-- Stores generated blog titles from R2
-- Expected by: R2 (creator), R3 (reader)

CREATE TABLE IF NOT EXISTS blog_titles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    title VARCHAR(500) NOT NULL,
    topic VARCHAR(255),
    keywords TEXT,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ctr_score FLOAT DEFAULT 0.0,
    INDEX idx_topic (topic),
    INDEX idx_used (used),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- STEP 4: CREATE FIXED blog_posts TABLE
-- ============================================================================
-- Stores generated blog post content
-- Expected by: R3, R4, R5 and all downstream robots

CREATE TABLE IF NOT EXISTS blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500),
    content LONGTEXT,
    topic VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    plagiarism_score FLOAT DEFAULT 0.0,
    ai_detection_score FLOAT DEFAULT 0.0,
    qa_check_report TEXT,
    version INT DEFAULT 1,
    bp_version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_topic (topic),
    INDEX idx_plagiarism (plagiarism_score),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- STEP 5: CREATE trending_keywords TABLE
-- ============================================================================
-- Stores trending keywords data
-- Expected by: R13 (Trend Scout), R2 (Title Generator), R3 (Content Generator)

CREATE TABLE IF NOT EXISTS trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(500) NOT NULL,
    topic VARCHAR(255),
    search_volume INT DEFAULT 0,
    competition_level VARCHAR(50),
    trend_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_keyword (keyword),
    INDEX idx_topic (topic),
    INDEX idx_search_volume (search_volume)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- STEP 6: CREATE SUPPORTING TABLES FOR ROBOT PIPELINE
-- ============================================================================

-- R4: Plagiarism Detection
CREATE TABLE IF NOT EXISTS plagiarism_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    similarity_percentage FLOAT DEFAULT 0.0,
    plagiarism_report TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_version VARCHAR(50),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- R5: AI Detection
CREATE TABLE IF NOT EXISTS ai_detection_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    ai_score FLOAT DEFAULT 0.0,
    human_score FLOAT DEFAULT 0.0,
    mixed_score FLOAT DEFAULT 0.0,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- R6: Quality Assurance
CREATE TABLE IF NOT EXISTS qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    qa_score FLOAT DEFAULT 0.0,
    issues_found INT DEFAULT 0,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- R7-R11: Content Enhancement & Formatting
CREATE TABLE IF NOT EXISTS content_enhancements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    enhancement_type VARCHAR(100),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- R12: SEO Optimization
CREATE TABLE IF NOT EXISTS seo_optimization (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    meta_title VARCHAR(255),
    meta_description VARCHAR(255),
    keywords_targeted TEXT,
    seo_score FLOAT DEFAULT 0.0,
    optimized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- R13: Trend Scout (already has trending_keywords table)

-- R14: Heading Generation
CREATE TABLE IF NOT EXISTS heading_suggestions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    h1 VARCHAR(255),
    h2s TEXT,
    h3s TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Image Management (R15-R16)
CREATE TABLE IF NOT EXISTS image_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    image_url VARCHAR(500),
    alt_text VARCHAR(255),
    image_source VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Affiliate Management (R17-R18)
CREATE TABLE IF NOT EXISTS affiliate_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(255),
    affiliate_link VARCHAR(500),
    affiliate_network VARCHAR(100),
    commission_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_network (affiliate_network)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_products_placement (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    product_id INT,
    placement_type VARCHAR(50),
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS link_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    link_type VARCHAR(50),
    links_added INT DEFAULT 0,
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    affiliate_links_added INT DEFAULT 0,
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Publishing & Distribution (R19-R25)
CREATE TABLE IF NOT EXISTS publication_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    published_url VARCHAR(500),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    post_id INT,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS post_publication_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    check_type VARCHAR(100),
    status VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Social Media & Email (R26-R32)
CREATE TABLE IF NOT EXISTS social_media_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    platforms TEXT,
    scheduled_at TIMESTAMP,
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_media_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    platform VARCHAR(100),
    post_content TEXT,
    post_id VARCHAR(255),
    posted_at TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_engagement_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    platform VARCHAR(100),
    engagements INT DEFAULT 0,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_engagement_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    platform VARCHAR(100),
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    comments INT DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_distribution_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    distribution_status VARCHAR(50),
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_publication_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    platform VARCHAR(100),
    status VARCHAR(50),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    campaign_name VARCHAR(255),
    recipient_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_newsletters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    newsletter_subject VARCHAR(255),
    newsletter_body TEXT,
    sent_at TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_send_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    recipients_sent INT DEFAULT 0,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Analytics & Monitoring (R33-R36)
CREATE TABLE IF NOT EXISTS analytics_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    event_type VARCHAR(100),
    event_data TEXT,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_locks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    lock_type VARCHAR(100),
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP NULL,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    error_message TEXT,
    error_code VARCHAR(50),
    error_level VARCHAR(50),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_error_level (error_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    error_type VARCHAR(100),
    error_details TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_occurred (occurred_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_recovery_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    recovery_action VARCHAR(255),
    status VARCHAR(50),
    recovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_heartbeat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_id VARCHAR(10),
    status VARCHAR(50),
    heartbeat_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_robot (robot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_health_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    check_type VARCHAR(100),
    status VARCHAR(50),
    health_score FLOAT DEFAULT 0.0,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (check_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    health_score FLOAT DEFAULT 0.0,
    active_robots INT DEFAULT 0,
    failed_robots INT DEFAULT 0,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(100),
    report_data TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS coordinator_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    status VARCHAR(50),
    active_blogs INT DEFAULT 0,
    processed_blogs INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS robot_locks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_id VARCHAR(10),
    blog_id INT,
    lock_acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lock_released_at TIMESTAMP NULL,
    INDEX idx_robot (robot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rollback_checkpoints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    checkpoint_name VARCHAR(255),
    checkpoint_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rollback_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    rollback_action VARCHAR(255),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quarantine_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    quarantine_reason VARCHAR(255),
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS isolation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    isolation_reason VARCHAR(255),
    isolated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS final_validation_checkpoints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    validation_type VARCHAR(100),
    status VARCHAR(50),
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS final_qa_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    qa_result VARCHAR(50),
    qa_notes TEXT,
    qa_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS headline_confirmations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    headline VARCHAR(500),
    confirmed BOOLEAN DEFAULT FALSE,
    confirmed_at TIMESTAMP NULL,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS plagiarism_check_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plagiarism_percentage FLOAT DEFAULT 0.0,
    status VARCHAR(50),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_refresh_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    refresh_requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_refresh_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    task_type VARCHAR(100),
    task_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refresh_workflow_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    workflow_step VARCHAR(100),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comment_moderation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    comment_id VARCHAR(255),
    moderation_status VARCHAR(50),
    moderated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comment_response_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    original_comment_id VARCHAR(255),
    response_posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS wordpress_connector_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    action VARCHAR(100),
    status VARCHAR(50),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS retrofit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    retrofit_action VARCHAR(255),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_id VARCHAR(10),
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS digital_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(255),
    product_url VARCHAR(500),
    product_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_search_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    search_query VARCHAR(500),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    INDEX idx_blog (blog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- STEP 7: SEED INITIAL DATA
-- ============================================================================

-- Insert 18 health & fitness topics for the rotation cycle
INSERT INTO topic_rotation (topic_name, cycle_number, topic_sequence, status) VALUES
('Health and Fitness', 1, 1, 'active'),
('Weight Loss', 1, 2, 'pending'),
('Muscle Building', 1, 3, 'pending'),
('Nutrition and Diet', 1, 4, 'pending'),
('Cardiovascular Health', 1, 5, 'pending'),
('Mental Health and Wellness', 1, 6, 'pending'),
('Yoga and Flexibility', 1, 7, 'pending'),
('High Intensity Training', 1, 8, 'pending'),
('Sleep and Recovery', 1, 9, 'pending'),
('Joint and Bone Health', 1, 10, 'pending'),
('Immune System Boosting', 1, 11, 'pending'),
('Energy and Stamina', 1, 12, 'pending'),
('Stress Management', 1, 13, 'pending'),
('Aging and Longevity', 1, 14, 'pending'),
('Sports Performance', 1, 15, 'pending'),
('Home Fitness Solutions', 1, 16, 'pending'),
('Supplement Guide', 1, 17, 'pending'),
('Habit Building and Lifestyle', 1, 18, 'pending');

-- ============================================================================
-- STEP 8: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Performance indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_blog_posts_status_created ON blog_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_blog_posts_topic_status ON blog_posts(topic, status);
CREATE INDEX IF NOT EXISTS idx_trending_keywords_volume ON trending_keywords(search_volume DESC);
CREATE INDEX IF NOT EXISTS idx_plagiarism_blog_score ON plagiarism_checks(blog_id, similarity_percentage);

-- ============================================================================
-- SUCCESS CONFIRMATION
-- ============================================================================
-- Schema migration complete. All 11 robot failures should now be resolved.
-- Database is ready for full pipeline execution.
-- Expected result: 35/35 robots successfully executing
