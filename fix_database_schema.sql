-- ============================================================================
-- GHGF 42-ROBOT SYSTEM - COMPREHENSIVE DATABASE SCHEMA FIX
-- Fixes all column mismatches and creates missing tables
-- ============================================================================

-- First, back up existing data by renaming old tables
RENAME TABLE IF EXISTS topic_rotation TO topic_rotation_old;
RENAME TABLE IF EXISTS blog_titles TO blog_titles_old;
RENAME TABLE IF EXISTS blog_posts TO blog_posts_old;
RENAME TABLE IF EXISTS trending_keywords TO trending_keywords_old;

-- ============================================================================
-- CORE CONTENT GENERATION TABLES
-- ============================================================================

-- Topic Rotation Table (for 18-topic rotation schedule)
CREATE TABLE IF NOT EXISTS topic_rotation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(500) NOT NULL,
    cycle_number INT DEFAULT 1,
    topic_sequence INT DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active' COMMENT 'active, inactive, paused',
    start_date DATE,
    last_rotated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_cycle (cycle_number, topic_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Blog Titles (R2 Output)
CREATE TABLE IF NOT EXISTS blog_titles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    title VARCHAR(500) NOT NULL,
    topic VARCHAR(500),
    keywords VARCHAR(1000),
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ctr_score DECIMAL(5,2) DEFAULT 0,
    INDEX idx_used (used),
    INDEX idx_topic (topic),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Blog Posts (Main content table)
CREATE TABLE IF NOT EXISTS blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500),
    topic VARCHAR(500),
    content LONGTEXT,
    status VARCHAR(50) DEFAULT 'draft',

    -- QA & Validation Fields
    plagiarism_score DECIMAL(5,2),
    ai_detection_score DECIMAL(5,2),
    qa_check_report LONGTEXT,
    qa_check_passed BOOLEAN DEFAULT FALSE,

    -- Version Control
    version INT DEFAULT 1,

    -- Monetization
    affiliate_links_injected BOOLEAN DEFAULT FALSE,
    internal_links_injected BOOLEAN DEFAULT FALSE,

    -- Publishing
    wordpress_post_id INT,
    published_at TIMESTAMP NULL,

    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    bp_version INT DEFAULT 1,

    INDEX idx_status (status),
    INDEX idx_topic (topic),
    INDEX idx_wordpress_id (wordpress_post_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- KEYWORD & RESEARCH TABLES
-- ============================================================================

-- Trending Keywords Cache (R13 Output)
CREATE TABLE IF NOT EXISTS trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic VARCHAR(500) NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    search_volume INT DEFAULT 0,
    competition_level VARCHAR(50) DEFAULT 'medium',
    trend_direction VARCHAR(20) DEFAULT 'stable',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_topic (topic),
    INDEX idx_keyword (keyword),
    INDEX idx_search_volume (search_volume)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- QA & VALIDATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS plagiarism_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    plagiarism_score DECIMAL(5,2),
    status VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    word_count INT,
    grammar_score INT,
    readability_score INT,
    seo_score INT,
    status VARCHAR(50),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- IMAGE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS image_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    topic VARCHAR(500),
    image_url VARCHAR(500),
    alt_text TEXT,
    used_date TIMESTAMP,
    expires_date TIMESTAMP,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- MONETIZATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS affiliate_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_name VARCHAR(500),
    product_url VARCHAR(500),
    affiliate_link VARCHAR(500),
    description LONGTEXT,
    network VARCHAR(100),
    commission DECIMAL(5,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_products_placement (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_id INT,
    placement_type VARCHAR(100),
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS link_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    injection_type VARCHAR(100),
    links_count INT,
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_name VARCHAR(500),
    affiliate_link VARCHAR(500),
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- PUBLISHING TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS publication_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    wordpress_post_id INT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS post_publication_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    url_valid BOOLEAN,
    load_time INT,
    seo_valid BOOLEAN,
    links_valid BOOLEAN,
    email_form_valid BOOLEAN,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SOCIAL & EMAIL TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS social_media_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    content TEXT,
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_media_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    content TEXT,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_engagement_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    likes INT,
    shares INT,
    comments INT,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_engagement_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    engagement_score DECIMAL(8,2),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_distribution_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    social_post_id VARCHAR(500),
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS social_publication_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT,
    blog_id INT,
    platform VARCHAR(50),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    content_html LONGTEXT,
    content_hash VARCHAR(500),
    blog_ids VARCHAR(1000),
    subject VARCHAR(500),
    content TEXT,
    sent_at TIMESTAMP,
    open_rate DECIMAL(5,2),
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_newsletters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_html LONGTEXT,
    content_hash VARCHAR(500),
    blog_ids VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS email_send_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    newsletter_id INT,
    subscriber_id INT,
    sent_at TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- ANALYTICS TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS analytics_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_type VARCHAR(100),
    blog_id INT,
    event_data JSON,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SYSTEM CONTROL & HEALTH TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_locks (
    lock_id INT PRIMARY KEY AUTO_INCREMENT,
    resource_type VARCHAR(100),
    resource_id INT,
    lock_type VARCHAR(50),
    acquired_by VARCHAR(100),
    acquired_at TIMESTAMP,
    expires_at TIMESTAMP,
    released_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_error_log (
    error_id INT PRIMARY KEY AUTO_INCREMENT,
    error_type VARCHAR(100),
    severity VARCHAR(50),
    message TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'detected',
    error_handler_needed BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_type VARCHAR(100),
    message LONGTEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_recovery_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_id INT,
    recovery_type VARCHAR(100),
    attempt_number INT,
    status VARCHAR(50),
    recovered_at TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_heartbeat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    coordinator_id VARCHAR(100),
    heartbeat_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robots_active INT,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_health_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    check_type VARCHAR(100),
    metric_value INT,
    threshold INT,
    status VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    snapshot_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(100),
    report_data LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS coordinator_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    status_data JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS robot_locks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_id VARCHAR(100),
    lock_status VARCHAR(50),
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- ROLLBACK & RECOVERY TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS rollback_checkpoints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT,
    checkpoint_type VARCHAR(100),
    snapshot_data JSON,
    rollback_at TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rollback_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rollback_type VARCHAR(100),
    details LONGTEXT,
    rolled_back_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quarantine_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT,
    topic VARCHAR(500),
    quarantine_reason VARCHAR(500),
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS isolation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    isolated_content_id INT,
    isolation_reason VARCHAR(500),
    isolated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- VALIDATION & QA TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS final_validation_checkpoints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    validation_score INT,
    status VARCHAR(50),
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS final_qa_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    qa_score INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS headline_confirmations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    headline VARCHAR(500),
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS plagiarism_check_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    plagiarism_percentage DECIMAL(5,2),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic VARCHAR(500),
    status VARCHAR(50),
    content LONGTEXT,
    last_modified_by VARCHAR(100),
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_refresh_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    refresh_type VARCHAR(100),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_refresh_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    task_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refresh_workflow_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    workflow_type VARCHAR(100),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- COMMENT & ENGAGEMENT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS comment_moderation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    comment_text TEXT,
    moderation_action VARCHAR(50),
    moderated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comment_response_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    response_text TEXT,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- WORDPRESS CONNECTOR TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS wordpress_connector_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    api_endpoint VARCHAR(500),
    status_code INT,
    response_time INT,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SUPPORTING ROBOT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    status VARCHAR(50),
    details LONGTEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS digital_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_type VARCHAR(100),
    product_data LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS affiliate_search_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    search_query VARCHAR(500),
    status VARCHAR(50),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SEED INITIAL DATA
-- ============================================================================

-- Add initial topic rotation (18 topics for rotation)
INSERT INTO topic_rotation (topic_name, cycle_number, topic_sequence, status, start_date) VALUES
('Health and Fitness', 1, 1, 'active', CURDATE()),
('Nutrition and Diet', 1, 2, 'inactive', CURDATE()),
('Mental Health and Wellness', 1, 3, 'inactive', CURDATE()),
('Sleep and Rest', 1, 4, 'inactive', CURDATE()),
('Exercise and Training', 1, 5, 'inactive', CURDATE()),
('Supplements and Vitamins', 1, 6, 'inactive', CURDATE()),
('Weight Management', 1, 7, 'inactive', CURDATE()),
('Chronic Diseases', 1, 8, 'inactive', CURDATE()),
('Heart Health', 1, 9, 'inactive', CURDATE()),
('Bone Health', 1, 10, 'inactive', CURDATE()),
('Skin Health', 1, 11, 'inactive', CURDATE()),
('Hair and Beauty', 1, 12, 'inactive', CURDATE()),
('Sports and Athletics', 1, 13, 'inactive', CURDATE()),
('Yoga and Pilates', 1, 14, 'inactive', CURDATE()),
('Fitness Equipment', 1, 15, 'inactive', CURDATE()),
('Home Workouts', 1, 16, 'inactive', CURDATE()),
('Recovery and Injury', 1, 17, 'inactive', CURDATE()),
('Age-Specific Health', 1, 18, 'inactive', CURDATE())
ON DUPLICATE KEY UPDATE cycle_number=VALUES(cycle_number);

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_topic ON blog_posts(topic);
CREATE INDEX idx_blog_posts_wordpress ON blog_posts(wordpress_post_id);
CREATE INDEX idx_blog_titles_topic ON blog_titles(topic);
CREATE INDEX idx_trending_keywords_topic ON trending_keywords(topic);
CREATE INDEX idx_system_error_log_status ON system_error_log(status);
CREATE INDEX idx_affiliate_products_blog ON affiliate_products(blog_id);

-- ============================================================================
-- COMPLETION MARKER
-- ============================================================================
SELECT 'Database schema migration COMPLETE' AS status;
