-- R14b: Digital Product Creator - Database Schema
-- Create these tables in your ghgf_blogging database

-- Store generated digital products
CREATE TABLE IF NOT EXISTS digital_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blog_id INT NOT NULL,
    woocommerce_id INT,
    product_type VARCHAR(50), -- 'checklist', 'guide', 'masterclass', 'course'
    title VARCHAR(255),
    description TEXT,
    price DECIMAL(10, 2),
    cover_url VARCHAR(500),
    pdf_url VARCHAR(500),
    file_path VARCHAR(500),
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_id) REFERENCES blog_posts(id),
    INDEX (blog_id),
    INDEX (woocommerce_id),
    INDEX (created_at)
);

-- Track digital product sales
CREATE TABLE IF NOT EXISTS digital_product_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    order_id INT,
    customer_email VARCHAR(255),
    amount DECIMAL(10, 2),
    payment_method VARCHAR(50), -- 'paypal', 'stripe', 'woocommerce'
    transaction_id VARCHAR(255) UNIQUE,
    status VARCHAR(50), -- 'pending', 'completed', 'refunded'
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES digital_products(id),
    INDEX (product_id),
    INDEX (purchased_at),
    INDEX (payment_method)
);

-- Track product performance
CREATE TABLE IF NOT EXISTS digital_product_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    views INT DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    conversion_rate DECIMAL(5, 2),
    total_revenue DECIMAL(10, 2) DEFAULT 0,
    average_price DECIMAL(10, 2),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES digital_products(id),
    INDEX (product_id),
    INDEX (tracked_at)
);

-- Store payment gateway configurations
CREATE TABLE IF NOT EXISTS payment_gateways (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gateway_name VARCHAR(100), -- 'paypal', 'stripe', 'woocommerce'
    is_active BOOLEAN DEFAULT TRUE,
    configuration JSON,
    test_mode BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (gateway_name)
);

-- Add columns to blog_posts table if not exist
ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS has_digital_product BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS digital_product_price DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS quality_score DECIMAL(5, 2) DEFAULT 0;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_digital_product_created ON digital_products(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_product ON digital_product_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_payment ON digital_product_sales(payment_method);
CREATE INDEX IF NOT EXISTS idx_analytics_tracked ON digital_product_analytics(tracked_at);
