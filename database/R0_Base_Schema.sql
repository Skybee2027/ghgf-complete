-- ============================================================================
-- R0: Base Database Schema for GHGF Autonomous Blogging System
-- ============================================================================
-- Purpose: Create core tables required by all robots
-- This must be loaded FIRST before any other schema files

-- ============================================================================
-- Core Blog Posts Table
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
    INDEX (status),
    INDEX (created_at),
    INDEX (publication_date),
    INDEX (wordpress_post_id)
);

-- ============================================================================
-- Topics and Keywords
-- ============================================================================
CREATE TABLE IF NOT EXISTS topics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    keyword_focus VARCHAR(500),
    monthly_searches INT DEFAULT 0,
    competition_level VARCHAR(20), -- low, medium, high
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (monthly_searches)
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

CREATE TABLE IF NOT EXISTS trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(500) NOT NULL,
    search_volume INT,
    competition_level VARCHAR(20),
    cpc DECIMAL(10, 2),
    trend_direction VARCHAR(20), -- up, stable, down
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (keyword),
    INDEX (search_volume),
    INDEX (last_updated)
);

-- ============================================================================
-- Blog Titles and Content
-- ============================================================================
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
    INDEX (created_at),
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
    INDEX (blog_post_id),
    INDEX (status)
);

-- ============================================================================
-- Quality Assurance
-- ============================================================================
CREATE TABLE IF NOT EXISTS qa_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    check_type VARCHAR(100), -- plagiarism, ai_detection, keyword, format, etc
    score DECIMAL(5, 2),
    status VARCHAR(50), -- pass, fail, warning
    details JSON,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (status),
    INDEX (checked_at)
);

CREATE TABLE IF NOT EXISTS keyword_usage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    keyword VARCHAR(500),
    occurrences INT,
    keyword_density DECIMAL(5, 3),
    placement VARCHAR(100), -- title, h1, h2, body, alt_text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (keyword)
);

-- ============================================================================
-- Images and Media
-- ============================================================================
CREATE TABLE IF NOT EXISTS blog_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    image_url VARCHAR(500),
    alt_text VARCHAR(500),
    title VARCHAR(500),
    source VARCHAR(100), -- unsplash, pixabay, pexels
    license_type VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id)
);

-- ============================================================================
-- Affiliate Links
-- ============================================================================
CREATE TABLE IF NOT EXISTS affiliate_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    product_name VARCHAR(500),
    affiliate_url VARCHAR(1000),
    affiliate_network VARCHAR(100), -- CJ, ShareASale, Amazon, etc
    commission_rate DECIMAL(5, 2),
    expected_revenue DECIMAL(10, 2),
    actual_revenue DECIMAL(10, 2) DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    INDEX (blog_post_id),
    INDEX (affiliate_network)
);

-- ============================================================================
-- Social Media & Distribution
-- ============================================================================
CREATE TABLE IF NOT EXISTS social_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    platform VARCHAR(50), -- twitter, facebook, linkedin, pinterest
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
    INDEX (platform),
    INDEX (scheduled_time)
);

-- ============================================================================
-- Email Newsletter
-- ============================================================================
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
    INDEX (blog_post_id),
    INDEX (status)
);

-- ============================================================================
-- Analytics and Monitoring
-- ============================================================================
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
-- System Logs
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_name VARCHAR(100),
    blog_post_id INT,
    action VARCHAR(100),
    status VARCHAR(50), -- success, warning, error
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

