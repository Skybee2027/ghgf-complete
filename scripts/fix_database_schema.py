#!/usr/bin/env python3
"""
Database Schema Update Script
Adds missing columns to blog_posts table for REWORK automation
"""

import os
import sys
import logging
import mysql.connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSchemaUpdater:
    """Updates database schema to support REWORK automation"""

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
        logger.info("Database Schema Updater initialized")

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

    def check_column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}' AND COLUMN_NAME='{column}' AND TABLE_SCHEMA='{self.db_name}'")
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0
        except Exception as e:
            logger.warning(f"⚠ Error checking column: {e}")
            return False

    def add_column_if_missing(self, table: str, column: str, definition: str) -> bool:
        """Add a column to a table if it doesn't exist"""
        try:
            if self.check_column_exists(table, column):
                logger.info(f"✓ Column {table}.{column} already exists")
                return True

            cursor = self.connection.cursor()
            alter_query = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            cursor.execute(alter_query)
            self.connection.commit()
            cursor.close()

            logger.info(f"✓ Added column {table}.{column}")
            return True
        except Exception as e:
            logger.error(f"✗ Error adding column {table}.{column}: {e}")
            self.connection.rollback()
            return False

    def update_schema(self):
        """Update database schema with required columns"""
        logger.info("=" * 80)
        logger.info("UPDATING DATABASE SCHEMA FOR REWORK AUTOMATION")
        logger.info("=" * 80)

        # Check if blog_posts table exists
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'blog_posts'")
            result = cursor.fetchone()
            cursor.close()

            if not result:
                logger.error("✗ blog_posts table does not exist")
                return False

            logger.info("✓ blog_posts table found")
        except Exception as e:
            logger.error(f"✗ Error checking table: {e}")
            return False

        # List of columns to add
        columns_to_add = [
            ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('status', "ENUM('draft', 'published', 'revision', 'locked') DEFAULT 'draft'"),
            ('featured_image_url', 'VARCHAR(500) DEFAULT NULL'),
            ('meta_description', 'TEXT DEFAULT NULL'),
            ('wordpress_post_id', 'BIGINT DEFAULT NULL'),
        ]

        all_success = True
        for column, definition in columns_to_add:
            if not self.add_column_if_missing('blog_posts', column, definition):
                all_success = False

        # Create log table if it doesn't exist
        try:
            cursor = self.connection.cursor()
            create_log_table = """
                CREATE TABLE IF NOT EXISTS rework_automation_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    blogs_processed INT DEFAULT 0,
                    blogs_synced INT DEFAULT 0,
                    issues_fixed INT DEFAULT 0,
                    revenue_items_added INT DEFAULT 0,
                    errors JSON,
                    failed_blogs JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            cursor.execute(create_log_table)
            self.connection.commit()
            cursor.close()
            logger.info("✓ rework_automation_log table ready")
        except Exception as e:
            logger.warning(f"⚠ Error creating log table: {e}")

        return all_success

    def run(self):
        """Execute schema update"""
        if not self.connect_database():
            logger.error("✗ Cannot proceed without database connection")
            return False

        try:
            success = self.update_schema()

            if success:
                logger.info("\n" + "=" * 80)
                logger.info("✓ DATABASE SCHEMA UPDATED SUCCESSFULLY")
                logger.info("=" * 80)
                return True
            else:
                logger.error("\n" + "=" * 80)
                logger.error("✗ SCHEMA UPDATE COMPLETED WITH ERRORS")
                logger.error("=" * 80)
                return False

        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            return False
        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        updater = DatabaseSchemaUpdater()
        success = updater.run()

        if success:
            logger.info("✓ Schema update completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Schema update failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
