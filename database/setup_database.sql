-- ============================================================================
-- GHGF Database Setup & Verification Script
-- Purpose: Initialize or update database with all required tables and columns
-- Run this before executing the pipeline
-- ============================================================================

USE ghgf_blogging;

-- ============================================================================
-- CORE: Blog Posts Table - MASTER TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    content LONGTEXT,
    slug VARCHAR(500) UNIQUE,
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, published, archived
    author_id INT,
    featured_image_url VARCHAR(500),
    featured_image_id INT,
    excerpt VARCHAR(1000),
    keywords VARCHAR(500),
    category_id INT,
    tags VARCHAR(500),
    publication_date TIMESTAMP NULL,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    quality_score DECIMAL(5, 2) DEFAULT 0,
    plagiarism_score DECIMAL(5, 2) DEFAULT 0,
    ai_detection_score DECIMAL(5, 2) DEFAULT 0,
    wordpress_post_id INT UNIQUE,
    has_digital_product BOOLEAN DEFAULT FALSE,
    digital_product_price DECIMAL(10, 2),
    ready_for_wordpress BOOLEAN DEFAULT FALSE,
    final_qa_passed BOOLEAN DEFAULT FALSE,
    version INT DEFAULT 1,
    topic VARCHAR(500),
    meta_description VARCHAR(500),
    INDEX (status),
    INDEX (created_at),
    INDEX (publication_date),
    INDEX (wordpress_post_id),
    INDEX (ready_for_wordpress),
    INDEX (final_qa_passed)
);

-- ============================================================================
-- ENSURE ALL COLUMNS EXIST - Add any missing columns
-- ============================================================================

-- Add QA/Validation columns if missing
ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS headline_locked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qa_check_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qa_checked_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS plagiarism_checked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qi_check_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revalidation_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revalidation_report TEXT,
ADD COLUMN IF NOT EXISTS revalidation_checked_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS selected_headline_id INT,
ADD COLUMN IF NOT EXISTS headline_testing_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS headline_tested_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS headline_test_results TEXT,
ADD COLUMN IF NOT EXISTS images_found INT DEFAULT 0;

-- Add WordPress publication tracking columns if missing
ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS published_to_wordpress_at TIMESTAMP NULL;

-- Create indexes for performance
ALTER TABLE blog_posts
ADD INDEX IF NOT EXISTS idx_headline_locked (headline_locked),
ADD INDEX IF NOT EXISTS idx_qa_check_passed (qa_check_passed),
ADD INDEX IF NOT EXISTS idx_revalidation_passed (revalidation_passed),
ADD INDEX IF NOT EXISTS idx_published_at (published_at);

-- ============================================================================
-- Image Tracking Table - Used by R7, R8, R31
-- ============================================================================
CREATE TABLE IF NOT EXISTS image_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blog_id INT NOT NULL,
    image_url VARCHAR(2000),
    topic VARCHAR(255),
    source VARCHAR(255),
    title VARCHAR(500),
    alt_text TEXT,
    alt_text_generated_at TIMESTAMP NULL,
    used_date DATE,
    expires_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_id),
    INDEX (topic),
    INDEX (expires_date),
    INDEX (created_at)
);

-- ============================================================================
-- Topic to WordPress Category Mapping - Used by R31
-- ============================================================================
CREATE TABLE IF NOT EXISTS topic_category_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL UNIQUE,
    wordpress_category_id INT,
    wordpress_category_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (topic),
    INDEX (wordpress_category_id)
);

-- ============================================================================
-- WordPress Publication Log - Tracks all published posts
-- ============================================================================
CREATE TABLE IF NOT EXISTS wordpress_publication_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blog_id INT NOT NULL,
    wordpress_post_id INT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_by VARCHAR(100),
    publication_status VARCHAR(50),
    notes TEXT,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_id),
    INDEX (wordpress_post_id),
    INDEX (published_at)
);

-- ============================================================================
-- OTHER REQUIRED TABLES FOR FULL PIPELINE
-- ============================================================================

CREATE TABLE IF NOT EXISTS topics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    keyword_focus VARCHAR(500),
    monthly_searches INT DEFAULT 0,
    competition_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (monthly_searches)
);

CREATE TABLE IF NOT EXISTS blog_titles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    topic_id INT,
    keyword_focused VARCHAR(500),
    engagement_score DECIMAL(5, 2),
    seo_score DECIMAL(5, 2),
    selected BOOLEAN DEFAULT FALSE,
    used_in_post INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (used_in_post) REFERENCES blog_posts(id),
    INDEX (topic_id),
    INDEX (selected)
);

CREATE TABLE IF NOT EXISTS blog_content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    content_version INT DEFAULT 1,
    raw_content LONGTEXT,
    optimized_content LONGTEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

CREATE TABLE IF NOT EXISTS qa_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    check_type VARCHAR(100),
    score DECIMAL(5, 2),
    status VARCHAR(50),
    details JSON,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (status)
);

CREATE TABLE IF NOT EXISTS keyword_usage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    keyword VARCHAR(500),
    occurrences INT,
    keyword_density DECIMAL(5, 3),
    placement VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

CREATE TABLE IF NOT EXISTS blog_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    image_url VARCHAR(500),
    alt_text VARCHAR(500),
    title VARCHAR(500),
    source VARCHAR(100),
    license_type VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

CREATE TABLE IF NOT EXISTS affiliate_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    product_name VARCHAR(500),
    affiliate_url VARCHAR(1000),
    affiliate_network VARCHAR(100),
    commission_rate DECIMAL(5, 2),
    expected_revenue DECIMAL(10, 2),
    actual_revenue DECIMAL(10, 2) DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

CREATE TABLE IF NOT EXISTS social_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    platform VARCHAR(50),
    post_content TEXT,
    post_url VARCHAR(500),
    post_id VARCHAR(500),
    scheduled_time TIMESTAMP NULL,
    published_time TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'draft',
    engagement_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (platform)
);

CREATE TABLE IF NOT EXISTS email_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    subject_line VARCHAR(500),
    preview_text VARCHAR(500),
    email_content LONGTEXT,
    recipient_count INT,
    sent_count INT DEFAULT 0,
    open_rate DECIMAL(5, 2),
    click_rate DECIMAL(5, 2),
    conversion_rate DECIMAL(5, 2),
    scheduled_time TIMESTAMP NULL,
    sent_time TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

CREATE TABLE IF NOT EXISTS blog_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    date DATE,
    views INT DEFAULT 0,
    unique_visitors INT DEFAULT 0,
    bounce_rate DECIMAL(5, 2),
    avg_time_on_page INT,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (date)
);

-- ============================================================================
-- Logging Tables
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_name VARCHAR(100),
    blog_post_id INT,
    action VARCHAR(100),
    status VARCHAR(50),
    message TEXT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (robot_name),
    INDEX (status),
    INDEX (created_at)
);

CREATE TABLE IF NOT EXISTS error_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_name VARCHAR(100),
    blog_post_id INT,
    error_message TEXT,
    error_type VARCHAR(100),
    stack_trace TEXT,
    resolution_status VARCHAR(50) DEFAULT 'unresolved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (robot_name),
    INDEX (resolution_status),
    INDEX (created_at)
);

-- ============================================================================
-- Additional Support Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(500) NOT NULL,
    search_volume INT,
    competition_level VARCHAR(20),
    cpc DECIMAL(10, 2),
    trend_direction VARCHAR(20),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (keyword),
    INDEX (search_volume)
);

CREATE TABLE IF NOT EXISTS topic_rotation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT NOT NULL,
    cycle_number INT,
    last_used TIMESTAMP NULL,
    next_use TIMESTAMP NULL,
    post_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    INDEX (topic_id),
    INDEX (next_use)
);

CREATE TABLE IF NOT EXISTS affiliate_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blog_id INT NOT NULL,
    product_name VARCHAR(255),
    product_url VARCHAR(1000),
    description TEXT,
    commission_rate DECIMAL(5, 2),
    source_network VARCHAR(100),
    score DECIMAL(5, 2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id),
    INDEX (blog_id),
    INDEX (source_network)
);

CREATE TABLE IF NOT EXISTS digital_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_url VARCHAR(1000),
    description LONGTEXT,
    price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (product_name)
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255),
    product_url VARCHAR(1000),
    affiliate_url VARCHAR(1000),
    affiliate_program VARCHAR(100),
    commission_rate DECIMAL(5, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (product_name),
    INDEX (affiliate_program)
);

-- ============================================================================
-- VERIFICATION: Check all required columns exist
-- ============================================================================
SELECT 'blog_posts Table Structure:' AS Info;
DESCRIBE blog_posts;

-- ============================================================================
-- Final Status Message
-- ============================================================================
SELECT 'Database setup completed successfully!' AS Status;
SELECT 'All required tables and columns are ready for R31 (WordPress Publisher)' AS Message;
