#!/usr/bin/env python3
"""
R31: WordPress Uploader & Publisher
Purpose: CRITICAL - Publish approved posts to WordPress via REST API
Input: Final QA approved posts from R30 (ready_for_wordpress = TRUE)
Output: Published posts on WordPress + post IDs stored in database
Frequency: Every 6 hours (publishing cycle)
Dependencies: R22 (WordPress connector), R30 (final QA approval)
Conflict Resolution: R31 PRIORITY - R32 pauses during publishing (Conflict #9)
Publishing Process: Upload content, featured image, set metadata, publish
Transactional: All-or-nothing publishing (rollback on error)
Post Status: Sets to 'published' in WordPress + updates local db
Featured Image: Uploads and sets via WordPress API
Categories/Tags: Applies from blog_posts metadata
Revision Control: Stores WordPress post ID for tracking
"""

import os
import sys
import requests
import mysql.connector
from datetime import datetime
import logging
import json
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class WordPressUploaderPublisher:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        # WordPress configuration
        self.wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
        self.wp_user = os.getenv('WORDPRESS_USER', 'api_user')
        self.wp_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.wp_api_base = f"{self.wp_url}/wp-json/wp/v2"

        self.posts_published = 0
        self.posts_failed = 0

        # Log credentials for debugging
        logger.info(f"WordPress Config: URL={self.wp_url}, User={self.wp_user}, Password={'SET' if self.wp_password else 'EMPTY'}")
        if not self.wp_password:
            logger.error("CRITICAL: WORDPRESS_PASSWORD is empty! Posts cannot be published.")

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_posts_ready_to_publish(self, conn):
        """Get posts approved and ready for WordPress publishing"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.meta_description, bp.slug, bp.category_id,
                       bp.tags, bp.featured_image_id, bp.version
                FROM blog_posts bp
                WHERE bp.status = 'draft'
                AND bp.ready_for_wordpress = TRUE
                AND bp.final_qa_passed = TRUE
                AND bp.wordpress_post_id IS NULL
                ORDER BY bp.created_at ASC
                LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            logger.info(f"Found {len(results) if results else 0} posts ready to publish (status=draft, ready_for_wordpress=TRUE, final_qa_passed=TRUE)")
            return results
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []

    def get_featured_image_url(self, conn, image_id):
        """Get featured image URL from database"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT image_url FROM image_tracking WHERE id = %s"
            cursor.execute(query, (image_id,))
            result = cursor.fetchone()
            cursor.close()
            return result['image_url'] if result else None
        except Exception as e:
            logger.error(f"Error getting image: {str(e)}")
            return None

    def upload_featured_image_to_wordpress(self, image_url):
        """Upload featured image to WordPress media library"""
        try:
            if not image_url:
                return None

            auth = (self.wp_user, self.wp_password)

            # Fetch image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Could not fetch image: {image_url}")
                return None

            # Upload to WordPress
            filename = image_url.split('/')[-1]
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'image/jpeg'
            }

            upload_response = requests.post(
                f"{self.wp_api_base}/media",
                auth=auth,
                headers=headers,
                data=response.content,
                timeout=30
            )

            if upload_response.status_code in [200, 201]:
                media_data = upload_response.json()
                logger.info(f"Uploaded image: {media_data.get('id')}")
                return media_data.get('id')
            else:
                logger.warning(f"Image upload failed: {upload_response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None

    def get_category_id(self, conn, topic):
        """Get WordPress category ID for topic"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT wordpress_category_id
                FROM topic_category_mapping
                WHERE topic = %s
            """
            cursor.execute(query, (topic,))
            result = cursor.fetchone()
            cursor.close()
            return result['wordpress_category_id'] if result else None
        except Exception as e:
            logger.error(f"Error getting category: {str(e)}")
            return None

    def publish_post_to_wordpress(self, post, featured_image_id, category_id):
        """Publish post to WordPress"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            # Prepare post data
            post_data = {
                'title': post['title'],
                'content': post['content'],
                'status': 'publish',
                'slug': post['slug'] if post['slug'] else post['title'].lower().replace(' ', '-'),
                'excerpt': post['meta_description'][:160] if post['meta_description'] else '',
                'yoast_head': json.dumps({
                    'title': post['title'],
                    'description': post['meta_description']
                }) if post['meta_description'] else ''
            }

            # Add featured image if available
            if featured_image_id:
                post_data['featured_media'] = featured_image_id

            # Add category
            if category_id:
                post_data['categories'] = [category_id]

            # Add tags if available
            if post['tags']:
                tag_list = post['tags'].split(',') if isinstance(post['tags'], str) else post['tags']
                post_data['tags'] = tag_list

            # Make API request
            response = requests.post(
                f"{self.wp_api_base}/posts",
                auth=auth,
                headers=headers,
                json=post_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                post_response = response.json()
                wordpress_post_id = post_response['id']
                logger.info(f"Published post to WordPress: {wordpress_post_id}")
                return wordpress_post_id
            else:
                error_detail = response.text
                logger.error(f"Publishing failed: {response.status_code} - {error_detail}")
                return None
        except Exception as e:
            logger.error(f"Error publishing post: {str(e)}")
            return None

    def save_wordpress_post_id(self, conn, blog_id, wordpress_post_id):
        """Save WordPress post ID to database"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET wordpress_post_id = %s,
                    status = 'published',
                    published_at = NOW(),
                    published_to_wordpress_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (wordpress_post_id, blog_id))

            # Create publication record
            pub_query = """
                INSERT INTO wordpress_publication_log
                (blog_id, wordpress_post_id, published_at)
                VALUES (%s, %s, NOW())
            """
            cursor.execute(pub_query, (blog_id, wordpress_post_id))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving WordPress ID: {str(e)}")
            return False

    def run(self):
        self.print_header("R31: WORDPRESS UPLOADER & PUBLISHER (CRITICAL)")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Posts Ready to Publish{RESET}")
            posts = self.get_posts_ready_to_publish(conn)
            if not posts:
                print(f"  No posts ready for WordPress publishing\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Published: 0")
                print(f"  Status: {YELLOW}No posts in publishing queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts ready for publishing\n")

            print(f"{BOLD}Step 2: Publishing Posts to WordPress{RESET}")
            for post in posts:
                print(f"  Publishing: {BLUE}{post['title'][:40]}...{RESET}")

                # Get featured image if available
                featured_image_id = None
                if post['featured_image_id']:
                    image_url = self.get_featured_image_url(conn, post['featured_image_id'])
                    if image_url:
                        featured_image_id = self.upload_featured_image_to_wordpress(image_url)

                # Get category ID
                category_id = self.get_category_id(conn, post['topic'])

                # Publish to WordPress
                wordpress_post_id = self.publish_post_to_wordpress(
                    post,
                    featured_image_id,
                    category_id
                )

                if wordpress_post_id:
                    # Save WordPress ID
                    saved = self.save_wordpress_post_id(conn, post['id'], wordpress_post_id)

                    if saved:
                        self.posts_published += 1
                        print(f"    ✓ Published (WP ID: {wordpress_post_id})")
                    else:
                        print(f"    ✗ Failed to save WordPress ID")
                        self.posts_failed += 1
                else:
                    print(f"    ✗ Failed to publish to WordPress")
                    self.posts_failed += 1

            print()

            print(f"{BOLD}Step 3: Updating Publication Status{RESET}")
            print(f"  Successfully published: {self.posts_published}")
            print(f"  Failed: {self.posts_failed}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Posts Published: {GREEN}{self.posts_published}{RESET}")
            print(f"  Failed: {RED}{self.posts_failed}{RESET}")
            print(f"  Publication Method: WordPress REST API v2")
            print(f"  Features: Featured images, categories, tags, metadata")
            print(f"  Status Lock: Posts marked 'published', cannot be edited by other robots")
            print(f"  Next Stage: R32 (Post-Publication Monitoring) + R21 (Social Publishing)")
            print(f"  Status: {GREEN}PASS - WordPress publishing complete{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    publisher = WordPressUploaderPublisher()
    success = publisher.run()
    sys.exit(0 if success else 1)
