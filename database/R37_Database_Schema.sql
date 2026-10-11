-- ============================================================================
-- R37: Content Retrofit & Monetization Engine - Database Schema
-- ============================================================================
-- Purpose: Track retrofit progress for 600+ existing blog posts
-- Created: 2026-10-10
-- Part of: 36-Robot Autonomous Blogging System

-- ============================================================================
-- 1. RETROFIT PROGRESS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, failed
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    details JSON,  -- Stores detailed retrofit metadata
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_retrofit (blog_id, status)  -- One retrofit per post
);

CREATE INDEX idx_retrofit_status ON retrofit_log(status);
CREATE INDEX idx_retrofit_blog ON retrofit_log(blog_id);
CREATE INDEX idx_retrofit_completed ON retrofit_log(completed_at);

-- ============================================================================
-- 2. RETROFIT BATCH TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_batches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    batch_number INT NOT NULL,
    batch_size INT DEFAULT 50,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    posts_processed INT DEFAULT 0,
    posts_successful INT DEFAULT 0,
    posts_failed INT DEFAULT 0,
    estimated_revenue DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'in_progress', -- in_progress, completed
    notes TEXT,
    UNIQUE KEY unique_batch (batch_number)
);

CREATE INDEX idx_batch_status ON retrofit_batches(status);
CREATE INDEX idx_batch_time ON retrofit_batches(start_time);

-- ============================================================================
-- 3. RETROFIT STATISTICS & ANALYTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date_recorded DATE NOT NULL,
    total_posts INT DEFAULT 0,
    retrofitted_posts INT DEFAULT 0,
    in_progress_posts INT DEFAULT 0,
    remaining_posts INT DEFAULT 0,
    progress_percentage DECIMAL(5, 2) DEFAULT 0,
    total_affiliates_added INT DEFAULT 0,
    total_ebooks_generated INT DEFAULT 0,
    total_product_cards_inserted INT DEFAULT 0,
    estimated_total_revenue DECIMAL(12, 2) DEFAULT 0,
    average_revenue_per_post DECIMAL(8, 2) DEFAULT 0,
    estimated_completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date_recorded)
);

CREATE INDEX idx_analytics_date ON retrofit_analytics(date_recorded);

-- ============================================================================
-- 4. BLOG POST RETROFIT METADATA (extends blog_posts)
-- ============================================================================

-- Add these columns to blog_posts table if they don't exist:
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS retrofitted BOOLEAN DEFAULT FALSE;
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS retrofitted_at TIMESTAMP NULL;
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS has_affiliate_links BOOLEAN DEFAULT FALSE;
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS has_digital_product BOOLEAN DEFAULT FALSE;
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS digital_product_id INT;
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS digital_product_price DECIMAL(8, 2);
-- ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT 0;

-- ============================================================================
-- 5. AFFILIATE TRACKING FOR RETROFITTED POSTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_affiliates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    affiliate_product_id INT,
    product_name VARCHAR(255),
    affiliate_network VARCHAR(50), -- CJ, ShareASale, Amazon, ClickBank
    affiliate_url VARCHAR(500),
    position_in_post INT, -- 1st, 2nd, 3rd affiliate placement
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (affiliate_product_id) REFERENCES affiliate_products(id)
);

CREATE INDEX idx_retrofit_affiliates_blog ON retrofit_affiliates(blog_id);

-- ============================================================================
-- 6. DIGITAL PRODUCT RETROFIT TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_digital_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    woocommerce_product_id INT,
    product_name VARCHAR(255),
    product_type VARCHAR(50), -- checklist, guide, masterclass, course
    pdf_url VARCHAR(500),
    price DECIMAL(8, 2),
    quality_score FLOAT DEFAULT 8.5, -- Retrofitted products start with 8.5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
);

CREATE INDEX idx_retrofit_products_blog ON retrofit_digital_products(blog_id);

-- ============================================================================
-- 7. RETROFIT ERROR TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS retrofit_errors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT NOT NULL,
    error_type VARCHAR(100), -- content_enhancement_failed, affiliate_failed, ebook_failed, etc
    error_message TEXT,
    stack_trace TEXT,
    robot_step VARCHAR(100), -- which step failed
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    last_retry_at TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, resolved, abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
);

CREATE INDEX idx_retrofit_errors_status ON retrofit_errors(status);
CREATE INDEX idx_retrofit_errors_blog ON retrofit_errors(blog_id);

-- ============================================================================
-- 8. INITIAL DATA & PROCEDURES
-- ============================================================================

-- Enable only if using stored procedures for batch progress
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS get_retrofit_progress()
BEGIN
    SELECT
        COUNT(*) as total_posts,
        SUM(CASE WHEN retrofitted = TRUE THEN 1 ELSE 0 END) as retrofitted_posts,
        COUNT(*) - SUM(CASE WHEN retrofitted = TRUE THEN 1 ELSE 0 END) as remaining_posts,
        ROUND((SUM(CASE WHEN retrofitted = TRUE THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1) as progress_percentage
    FROM blog_posts
    WHERE status = 'published';
END//

CREATE PROCEDURE IF NOT EXISTS start_retrofit_batch(IN batch_number INT, IN batch_size INT)
BEGIN
    INSERT INTO retrofit_batches (batch_number, batch_size, status)
    VALUES (batch_number, batch_size, 'in_progress');
END//

CREATE PROCEDURE IF NOT EXISTS complete_retrofit_batch(
    IN batch_number INT,
    IN posts_successful INT,
    IN posts_failed INT,
    IN estimated_revenue DECIMAL(10, 2)
)
BEGIN
    UPDATE retrofit_batches
    SET
        end_time = NOW(),
        posts_processed = posts_successful + posts_failed,
        posts_successful = posts_successful,
        posts_failed = posts_failed,
        estimated_revenue = estimated_revenue,
        status = 'completed'
    WHERE batch_number = batch_number;
END//

DELIMITER ;

-- ============================================================================
-- 9. INTEGRATION NOTES
-- ============================================================================
--
-- This schema is designed to work alongside the existing 36-robot system:
--
-- Dependencies:
--   - Requires blog_posts table (from main schema)
--   - Requires digital_products table (from R14b schema)
--   - Requires affiliate_products table (from main schema)
--
-- Integration Points:
--   - R37 reads from: blog_posts, affiliate_products, digital_products
--   - R37 writes to: retrofit_log, retrofit_batches, retrofit_analytics
--   - R37 updates: blog_posts (retrofitted, has_digital_product, has_affiliate_links flags)
--
-- Monitoring:
--   - Track progress in retrofit_batches table
--   - View analytics in retrofit_analytics (updated after each batch)
--   - Check errors in retrofit_errors for troubleshooting
--
-- Timeline:
--   - Batch 1-12: Process ~50 posts per batch = 600 posts total
--   - Estimated completion: 3-5 days (12 batches × 6-hour cycles)
--   - Parallel execution: R1-R36 continues generating new posts simultaneously
--
-- Revenue Tracking:
--   - Each retrofitted post estimated at $5 base + $2 per 1000 words
--   - Total expected revenue from retrofit: $4,200-9,000 per month
--   - Track in retrofit_analytics for projections
--
-- ============================================================================
