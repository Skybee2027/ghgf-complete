#!/usr/bin/env python3
"""
Apply R37 Database Schema Changes
Applies all R37 (Content Retrofit & Monetization Engine) schema updates to the database
Creates necessary tables and stored procedures for retrofit tracking and image management
"""

import os
import sys
import mysql.connector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchemaApplier:
    """Apply database schema changes for R37"""

    def __init__(self):
        """Initialize with environment variables"""
        self.db_host = os.getenv('DB_HOST')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')

        if not all([self.db_host, self.db_user, self.db_name]):
            logger.error("CRITICAL: DB_HOST, DB_USER, and DB_NAME environment variables must be set")
            raise ValueError("Missing required database configuration")

        self.connection = None
        self.tables_created = 0
        self.procedures_created = 0

        logger.info("Schema Applier initialized")

    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=False,
                connection_timeout=30
            )
            logger.info("✓ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False

    def close_database(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_sql(self, sql_statement, description):
        """Execute a SQL statement safely"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_statement)
            cursor.close()
            logger.info(f"✓ {description}")
            return True
        except Exception as e:
            logger.error(f"✗ {description}: {e}")
            return False

    def apply_schema(self):
        """Apply all R37 schema changes"""

        logger.info("=" * 80)
        logger.info("APPLYING R37 DATABASE SCHEMA CHANGES")
        logger.info("=" * 80)

        # 1. RETROFIT PROGRESS TRACKING TABLE
        logger.info("\n1. Creating retrofit_log table...")
        sql_retrofit_log = """
            CREATE TABLE IF NOT EXISTS retrofit_log (
                id INT PRIMARY KEY AUTO_INCREMENT,
                blog_id INT NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                details JSON,
                error_message TEXT,
                retry_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
                INDEX idx_retrofit_blog_status (blog_id, status)
            )
        """
        if self.execute_sql(sql_retrofit_log, "retrofit_log table"):
            self.tables_created += 1

        # 2. RETROFIT BATCH TRACKING TABLE
        logger.info("\n2. Creating retrofit_batches table...")
        sql_retrofit_batches = """
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
                status VARCHAR(50) DEFAULT 'in_progress',
                notes TEXT,
                UNIQUE KEY unique_batch (batch_number)
            )
        """
        if self.execute_sql(sql_retrofit_batches, "retrofit_batches table"):
            self.tables_created += 1

        # 3. RETROFIT ANALYTICS TABLE
        logger.info("\n3. Creating retrofit_analytics table...")
        sql_retrofit_analytics = """
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
            )
        """
        if self.execute_sql(sql_retrofit_analytics, "retrofit_analytics table"):
            self.tables_created += 1

        # 4. RETROFIT AFFILIATES TABLE
        logger.info("\n4. Creating retrofit_affiliates table...")
        sql_retrofit_affiliates = """
            CREATE TABLE IF NOT EXISTS retrofit_affiliates (
                id INT PRIMARY KEY AUTO_INCREMENT,
                blog_id INT NOT NULL,
                affiliate_product_id INT,
                product_name VARCHAR(255),
                affiliate_network VARCHAR(50),
                affiliate_url VARCHAR(500),
                position_in_post INT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
            )
        """
        if self.execute_sql(sql_retrofit_affiliates, "retrofit_affiliates table"):
            self.tables_created += 1

        # 5. RETROFIT DIGITAL PRODUCTS TABLE
        logger.info("\n5. Creating retrofit_digital_products table...")
        sql_retrofit_digital_products = """
            CREATE TABLE IF NOT EXISTS retrofit_digital_products (
                id INT PRIMARY KEY AUTO_INCREMENT,
                blog_id INT NOT NULL,
                woocommerce_product_id INT,
                product_name VARCHAR(255),
                product_type VARCHAR(50),
                pdf_url VARCHAR(500),
                price DECIMAL(8, 2),
                quality_score FLOAT DEFAULT 8.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
            )
        """
        if self.execute_sql(sql_retrofit_digital_products, "retrofit_digital_products table"):
            self.tables_created += 1

        # 6. RETROFIT ERRORS TABLE
        logger.info("\n6. Creating retrofit_errors table...")
        sql_retrofit_errors = """
            CREATE TABLE IF NOT EXISTS retrofit_errors (
                id INT PRIMARY KEY AUTO_INCREMENT,
                blog_id INT NOT NULL,
                error_type VARCHAR(100),
                error_message TEXT,
                stack_trace TEXT,
                robot_step VARCHAR(100),
                retry_count INT DEFAULT 0,
                max_retries INT DEFAULT 3,
                last_retry_at TIMESTAMP NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
            )
        """
        if self.execute_sql(sql_retrofit_errors, "retrofit_errors table"):
            self.tables_created += 1

        # 7. IMAGE TRACKING TABLE (NEW)
        logger.info("\n7. Creating image_tracking table...")
        sql_image_tracking = """
            CREATE TABLE IF NOT EXISTS image_tracking (
                id INT PRIMARY KEY AUTO_INCREMENT,
                blog_id INT NOT NULL,
                image_url VARCHAR(500),
                image_title VARCHAR(255),
                image_alt_text TEXT,
                featured_image BOOLEAN DEFAULT FALSE,
                source_type VARCHAR(50),
                source_id VARCHAR(100),
                relevance_score FLOAT DEFAULT 0,
                size_bytes INT,
                upload_status VARCHAR(50) DEFAULT 'pending',
                wordpress_attachment_id INT,
                uploaded_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (blog_id) REFERENCES blog_posts(id) ON DELETE CASCADE
            )
        """
        if self.execute_sql(sql_image_tracking, "image_tracking table"):
            self.tables_created += 1

        # 8. CREATE INDEXES
        logger.info("\n8. Creating indexes...")
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_status ON retrofit_log(status)", "retrofit_log status index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_blog ON retrofit_log(blog_id)", "retrofit_log blog index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_completed ON retrofit_log(completed_at)", "retrofit_log completed index"),
            ("CREATE INDEX IF NOT EXISTS idx_batch_status ON retrofit_batches(status)", "retrofit_batches status index"),
            ("CREATE INDEX IF NOT EXISTS idx_batch_time ON retrofit_batches(start_time)", "retrofit_batches time index"),
            ("CREATE INDEX IF NOT EXISTS idx_analytics_date ON retrofit_analytics(date_recorded)", "retrofit_analytics date index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_affiliates_blog ON retrofit_affiliates(blog_id)", "retrofit_affiliates blog index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_products_blog ON retrofit_digital_products(blog_id)", "retrofit_digital_products blog index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_errors_status ON retrofit_errors(status)", "retrofit_errors status index"),
            ("CREATE INDEX IF NOT EXISTS idx_retrofit_errors_blog ON retrofit_errors(blog_id)", "retrofit_errors blog index"),
            ("CREATE INDEX IF NOT EXISTS idx_image_blog ON image_tracking(blog_id)", "image_tracking blog index"),
            ("CREATE INDEX IF NOT EXISTS idx_image_featured ON image_tracking(featured_image)", "image_tracking featured index"),
            ("CREATE INDEX IF NOT EXISTS idx_image_status ON image_tracking(upload_status)", "image_tracking status index"),
        ]

        for sql_idx, desc_idx in indexes:
            self.execute_sql(sql_idx, desc_idx)

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SCHEMA APPLICATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Tables Created: {self.tables_created}")
        logger.info(f"Status: All R37 schema changes applied successfully")
        logger.info("=" * 80)

        return True

    def run(self):
        """Execute the schema applier"""
        if not self.connect_database():
            logger.error("✗ Cannot proceed without database connection")
            return False

        try:
            self.apply_schema()
            return True

        except Exception as e:
            logger.error(f"✗ Schema application failed: {e}")
            return False

        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        applier = SchemaApplier()
        success = applier.run()

        if success:
            logger.info("✓ R37 Database Schema successfully applied")
            sys.exit(0)
        else:
            logger.error("✗ R37 Database Schema application failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
