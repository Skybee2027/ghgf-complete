#!/usr/bin/env python3
"""
R0 - WordPress Post Importer
Imports all posts from WordPress REST API into MySQL database
Must run FIRST before R1, R14b, and R37
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WordPressPostImporter:
    """Import WordPress posts into MySQL database"""
    
    def __init__(self):
        """Initialize with environment variables"""
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', '').rstrip('/')
        self.db_host = os.getenv('DB_HOST', '193.203.166.223')
        self.db_user = os.getenv('DB_USER', '')
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'u853068512_ghgf_blogging')
        
        self.connection = None
        self.posts_imported = 0
        self.posts_updated = 0
        self.posts_failed = 0
        
        logger.info("WordPress Post Importer initialized")
        logger.info(f"WordPress URL: {self.wordpress_url}")
        logger.info(f"Database: {self.db_name}@{self.db_host}")
    
    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=True,
                connection_timeout=30
            )
            logger.info("✓ Database connection successful")
            return True
        except Error as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def close_database(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    def fetch_wordpress_posts(self):
        """Fetch all posts from WordPress REST API"""
        try:
            all_posts = []
            page = 1
            per_page = 100
            
            logger.info("Fetching posts from WordPress...")
            
            while True:
                url = f"{self.wordpress_url}/wp-json/wp/v2/posts"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'status': 'publish',
                    '_fields': 'id,title,slug,content,excerpt,date,modified'
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                posts = response.json()
                if not posts:
                    break
                
                all_posts.extend(posts)
                logger.info(f"Fetched page {page}: {len(posts)} posts")
                
                # Check if we got less than per_page items (last page)
                if len(posts) < per_page:
                    break
                
                page += 1
            
            logger.info(f"✓ Total posts fetched from WordPress: {len(all_posts)}")
            return all_posts
            
        except requests.RequestException as e:
            logger.error(f"✗ Failed to fetch WordPress posts: {e}")
            return []
    
    def calculate_word_count(self, content_html):
        """Calculate word count from HTML content"""
        try:
            # Remove HTML tags
            import re
            text = re.sub('<[^<]+?>', '', content_html)
            # Remove extra whitespace and count words
            words = text.split()
            return len(words)
        except Exception as e:
            logger.warning(f"Failed to calculate word count: {e}")
            return 0
    
    def import_posts(self, posts):
        """Import posts into MySQL database"""
        if not posts:
            logger.warning("No posts to import")
            return
        
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            for post in posts:
                try:
                    post_id = post.get('id')
                    title = post.get('title', {}).get('rendered', 'Untitled')
                    slug = post.get('slug', f'post-{post_id}')
                    content = post.get('content', {}).get('rendered', '')
                    word_count = self.calculate_word_count(content)
                    publish_date = post.get('date', datetime.utcnow().isoformat())
                    
                    # Check if post already exists
                    check_query = "SELECT id FROM blog_posts WHERE id = %s"
                    cursor.execute(check_query, (post_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing post
                        update_query = """
                            UPDATE blog_posts 
                            SET title = %s, slug = %s, content = %s, 
                                word_count = %s, publish_date = %s, status = 'published'
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (
                            title, slug, content, word_count, 
                            publish_date, post_id
                        ))
                        self.posts_updated += 1
                        logger.debug(f"Updated post {post_id}: {title[:50]}")
                    else:
                        # Insert new post
                        insert_query = """
                            INSERT INTO blog_posts 
                            (id, title, slug, content, word_count, publish_date, status)
                            VALUES (%s, %s, %s, %s, %s, %s, 'published')
                        """
                        cursor.execute(insert_query, (
                            post_id, title, slug, content, word_count, publish_date
                        ))
                        self.posts_imported += 1
                        logger.debug(f"Imported post {post_id}: {title[:50]}")
                    
                except Exception as e:
                    self.posts_failed += 1
                    logger.error(f"Failed to import post {post.get('id')}: {e}")
                    continue
        
        finally:
            cursor.close()
    
    def get_import_summary(self):
        """Get summary statistics"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM blog_posts")
            total_posts = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(word_count) FROM blog_posts")
            total_words = cursor.fetchone()[0] or 0
            
            return {
                'total_posts': total_posts,
                'total_words': total_words,
                'posts_imported': self.posts_imported,
                'posts_updated': self.posts_updated,
                'posts_failed': self.posts_failed
            }
        finally:
            cursor.close()
    
    def run(self):
        """Execute the import process"""
        logger.info("=" * 60)
        logger.info("R0 - WordPress Post Importer Starting")
        logger.info("=" * 60)
        
        # Connect to database
        if not self.connect_database():
            logger.error("✗ Cannot proceed without database connection")
            return False
        
        try:
            # Fetch posts from WordPress
            posts = self.fetch_wordpress_posts()
            
            if not posts:
                logger.warning("No posts found to import")
                return False
            
            # Import posts into database
            self.import_posts(posts)
            
            # Get summary
            summary = self.get_import_summary()
            
            # Log results
            logger.info("=" * 60)
            logger.info("R0 - Import Summary")
            logger.info("=" * 60)
            logger.info(f"Posts imported: {self.posts_imported}")
            logger.info(f"Posts updated: {self.posts_updated}")
            logger.info(f"Posts failed: {self.posts_failed}")
            logger.info(f"Total posts in database: {summary['total_posts']}")
            logger.info(f"Total words in database: {summary['total_words']}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Importer failed: {e}")
            return False
        
        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        importer = WordPressPostImporter()
        success = importer.run()
        
        if success:
            logger.info("✓ R0 - WordPress Post Importer completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ R0 - WordPress Post Importer failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
