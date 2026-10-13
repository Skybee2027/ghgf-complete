-- ============================================================================
-- R0 Migration: Add missing columns for R10 and R15 robot operations
-- ============================================================================
-- This migration adds columns needed by R10 (Revalidation) and R15 (Affiliate Link Injector)

ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS revalidation_passed BOOLEAN DEFAULT FALSE;

ALTER TABLE blog_posts
ADD INDEX IF NOT EXISTS idx_revalidation_passed (revalidation_passed);

-- Add product_url column to digital_products table for R15 affiliate link injector
ALTER TABLE digital_products
ADD COLUMN IF NOT EXISTS product_url VARCHAR(1000);

-- Create affiliate_products table for R12 and R15
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
    INDEX (source_network),
    INDEX (created_at)
);

-- Add missing columns to existing affiliate_products table if they don't exist
ALTER TABLE affiliate_products
ADD COLUMN IF NOT EXISTS blog_id INT,
ADD COLUMN IF NOT EXISTS product_url VARCHAR(1000),
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5, 2),
ADD COLUMN IF NOT EXISTS source_network VARCHAR(100),
ADD COLUMN IF NOT EXISTS score DECIMAL(5, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Add product_url to affiliate tracking if it exists, or create a products reference
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

-- Ensure blog_posts table has all required columns for full QA pipeline
ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS headline_locked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qa_check_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qa_checked_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS plagiarism_checked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS qi_check_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS revalidation_report TEXT,
ADD COLUMN IF NOT EXISTS revalidation_checked_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS selected_headline_id INT,
ADD COLUMN IF NOT EXISTS headline_testing_passed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS headline_tested_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS headline_test_results TEXT,
ADD COLUMN IF NOT EXISTS images_found INT DEFAULT 0;

-- Create indexes for performance
ALTER TABLE blog_posts
ADD INDEX IF NOT EXISTS idx_headline_locked (headline_locked),
ADD INDEX IF NOT EXISTS idx_qa_check_passed (qa_check_passed),
ADD INDEX IF NOT EXISTS idx_plagiarism_checked (plagiarism_checked),
ADD INDEX IF NOT EXISTS idx_qi_check_passed (qi_check_passed);
