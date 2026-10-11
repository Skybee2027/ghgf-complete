#!/usr/bin/env python3
"""
R0: WordPress Post Importer
Purpose: Fetch existing posts from WordPress and import into MySQL database
Input: WordPress REST API
Output: Populated blog_posts table in MySQL
"""

import os
import sys
import mysql.connector
from datetime import datetime
import logging
import requests
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'

class WordPressPostImporter:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', 'https://greathealthgreatfitness.com')
        self.posts_imported = 0
        self.posts_failed = 0

    def print_header(self, title):
        print(f"\n{'='*80}\n{BOLD}{title}{RESET}\n{'='*80}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def fetch_wordpress_posts(self):
        """Fetch all posts from WordPress REST API"""
        try:
            all_posts = []
            page = 1
            per_page = 100
            
            while True:
                url = f"{self.wordpress_url}/wp-json/wp/v2/posts?page={page}&per_page={per_page}"
                response = requests.get(url, timeout=30)
                
                if response.status_code != 200:
                    break
                
                posts = response.json()
                if not posts:
                    break
                
                all_posts.extend(posts)
                page += 1
            
            logger.info(f"Fetched {len(all_posts)} posts from WordPress")
            return all_posts
        except Exception as e:
            logger.error(f"Error fetching WordPress posts: {str(e)}")
            return []

    def import_posts_to_mysql(self, conn, posts):
        """Import posts into MySQL database"""
        try:
            cursor = conn.cursor()
            
            for post in posts:
                try:
                    # Extract post data
                    post_id = post.get('id')
                    title = post.get('title', {}).get('rendered', 'Untitled')
                    slug = post.get('slug', '')
                    content = post.get('content', {}).get('rendered', '')
                    status = post.get('status', 'draft')
                    published = post.get('date', datetime.now().isoformat())
                    
                    # Calculate word count
                    word_count = len(content.split()) if content else 0
                    
                    # Check if post already exists
                    cursor.execute(
                        "SELECT id FROM blog_posts WHERE id = %s",
                        (post_id,)
                    )
                    
                    if cursor.fetchone():
                        # Update existing post
                        cursor.execute("""
                            UPDATE blog_posts 
                            SET title = %s, slug = %s, content = %s, 
                                word_count = %s, publish_date = %s, status = %s
                            WHERE id = %s
                        """, (title, slug, content, word_count, published, status, post_id))
                    else:
                        # Insert new post
                        cursor.execute("""
                            INSERT INTO blog_posts 
                            (id, title, slug, content, word_count, publish_date, status, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (post_id, title, slug, content, word_count, published, status))
                    
                    self.posts_imported += 1
                    
                except Exception as e:
                    logger.error(f"Error importing post {post_id}: {str(e)}")
                    self.posts_failed += 1
                    continue
            
            conn.commit()
            cursor.close()
            logger.info(f"Successfully imported {self.posts_imported} posts")
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")

    def run(self):
        self.print_header("R0: WORDPRESS POST IMPORTER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            print(f"{RED}✗ Database connection failed{RESET}")
            return False

        try:
            print(f"{BOLD}Step 1: Fetching WordPress Posts{RESET}")
            posts = self.fetch_wordpress_posts()
            
            if not posts:
                print(f"{YELLOW}  No posts found to import{RESET}\n")
                return True
            
            print(f"  Found {len(posts)} posts\n")

            print(f"{BOLD}Step 2: Importing Posts to MySQL{RESET}")
            self.import_posts_to_mysql(conn, posts)
            print(f"  ✓ Import complete\n")

            print(f"{'='*80}")
            print(f"{BOLD}IMPORT SUMMARY{RESET}")
            print(f"  Posts Imported: {GREEN}{self.posts_imported}{RESET}")
            print(f"  Posts Failed: {RED if self.posts_failed > 0 else GREEN}{self.posts_failed}{RESET}")
            print(f"  Status: {GREEN}COMPLETE{RESET}")
            print('='*80 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"{RED}✗ Error: {str(e)}{RESET}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    importer = WordPressPostImporter()
    success = importer.run()
    sys.exit(0 if success else 1)
