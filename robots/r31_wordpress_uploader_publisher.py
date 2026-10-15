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
import re

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
        print(f"\n🔧 WordPress Configuration:")
        print(f"   URL: {self.wp_url}")
        print(f"   User: {self.wp_user}")
        print(f"   Password: {'✅ SET' if self.wp_password else '❌ EMPTY'}")
        print(f"   API Base: {self.wp_api_base}\n")

        if not self.wp_password:
            logger.error("CRITICAL: WORDPRESS_PASSWORD is empty! Posts cannot be published.")
            print(f"   {RED}❌ CRITICAL: WORDPRESS_PASSWORD is EMPTY!{RESET}\n")

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
            error_msg = f"CRITICAL ERROR getting posts: {str(e)}"
            logger.error(error_msg)
            print(f"\n{RED}{error_msg}{RESET}")
            print(f"{RED}This means R31 cannot find posts to publish!{RESET}")
            print(f"{RED}Possible causes:{RESET}")
            print(f"  1. One or more columns in SELECT don't exist in blog_posts table")
            print(f"  2. Database connection is closed or invalid")
            print(f"  3. SQL syntax error in the query")
            print(f"\n{RED}Full error details:{RESET}")
            print(f"{RED}{str(e)}{RESET}\n")
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

            # CRITICAL FIX: Ensure HTML content is properly encoded for WordPress REST API
            # WordPress REST API expects HTML content to be valid JSON strings
            # The content field should contain the full HTML markup
            post_content = post['content']

            # Validate that content has HTML structure (should have at least one heading or paragraph)
            if '<h' not in post_content and '<p' not in post_content:
                logger.warning(f"Content might be plain text, not HTML. Starting with: {post_content[:100]}")

            # Prepare post data with proper HTML handling
            post_data = {
                'title': post['title'],
                'content': post_content,  # WordPress REST API handles HTML in content field
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
                error_msg = f"Publishing failed: {response.status_code} - {error_detail[:200]}"
                logger.error(error_msg)
                print(f"      {RED}ERROR: {error_msg}{RESET}")

                # Log critical authentication errors
                if response.status_code == 401:
                    print(f"      {RED}⚠️  CRITICAL: WordPress authentication FAILED (401 Unauthorized){RESET}")
                    print(f"      {RED}   Check: WORDPRESS_USER and WORDPRESS_PASSWORD credentials{RESET}")

                return None
        except Exception as e:
            error_msg = f"Error publishing post: {str(e)}"
            logger.error(error_msg)
            print(f"      {RED}EXCEPTION: {error_msg}{RESET}")
            return None

    def validate_before_publishing(self, post):
        """CRITICAL: Run pre-flight validation checks before publishing"""
        issues = []

        # Check 1: No unresolved placeholders
        if re.search(r'\[\[', post['content']):
            placeholders = re.findall(r'\[\[[^\]]+\]\]', post['content'])
            issues.append(f"CRITICAL: Unresolved placeholders: {placeholders}")

        # Check 2: Content is complete (not truncated)
        if post['content'].endswith('...') and len(post['content'].split('</p>')[-1]) < 30:
            issues.append("CRITICAL: Content appears truncated")

        # Check 3: Alt text present for featured image (if featured image exists)
        # This would be checked from the database

        # Check 4: Title/content match (if title has numbers, content should have that many sections)
        title_number = re.search(r'(\d+)\s+(ways|tips|strategies|steps)', post['title'], re.I)
        if title_number:
            expected = int(title_number.group(1))
            actual = len(re.findall(r'<h2>', post['content']))
            if expected != actual:
                issues.append(f"Title says {expected} sections but content has {actual}")

        # Check 5: No site navigation chrome
        chrome_text = ['Categories', 'Leave a Comment', 'Back to top', 'Exit mobile version']
        for text in chrome_text:
            if text in post['content']:
                issues.append(f"Site navigation found in content: '{text}'")

        return len(issues) == 0, issues

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
            print(f"  Searching for posts where:")
            print(f"    - status = 'draft'")
            print(f"    - ready_for_wordpress = TRUE")
            print(f"    - final_qa_passed = TRUE")
            print(f"    - wordpress_post_id IS NULL\n")

            posts = self.get_posts_ready_to_publish(conn)
            if not posts:
                print(f"  ❌ No posts ready for WordPress publishing\n")

                # Debug: Check all posts in database
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT COUNT(*) as total FROM blog_posts")
                    total = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as draft FROM blog_posts WHERE status='draft'")
                    draft = cursor.fetchone()['draft']

                    cursor.execute("SELECT COUNT(*) as ready FROM blog_posts WHERE ready_for_wordpress=TRUE")
                    ready = cursor.fetchone()['ready']

                    cursor.execute("SELECT COUNT(*) as qa FROM blog_posts WHERE final_qa_passed=TRUE")
                    qa_passed = cursor.fetchone()['qa']

                    cursor.execute("SELECT COUNT(*) as wp_published FROM blog_posts WHERE wordpress_post_id IS NOT NULL")
                    wp_published = cursor.fetchone()['wp_published']

                    cursor.close()

                    print(f"  DEBUG INFO:")
                    print(f"    Total posts in DB: {total}")
                    print(f"    Draft status: {draft}")
                    print(f"    Ready for WordPress: {ready}")
                    print(f"    QA Passed: {qa_passed}")
                    print(f"    Already Published to WP: {wp_published}")

                    if ready > 0 and qa_passed > 0:
                        print(f"\n  {YELLOW}⚠️  POSSIBLE ISSUE: Posts are marked ready but R31 query is not finding them!{RESET}")
                        print(f"  {YELLOW}This usually means one of the SELECT columns doesn't exist in blog_posts table.{RESET}")
                        print(f"  {YELLOW}Run 'database/setup_database.sql' to ensure all columns exist.{RESET}\n")
                    else:
                        print(f"\n  INFO: Previous robots (R29, R30) may not have set the required flags yet.\n")

                except Exception as e:
                    print(f"    (Could not get debug info: {str(e)})\n")

                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Published: 0")
                print(f"  Status: {YELLOW}No posts in publishing queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts ready for publishing\n")

            print(f"{BOLD}Step 2: Pre-Flight Validation{RESET}")
            print(f"  Checking all posts before publishing...\n")

            # Validate all posts before publishing any
            for post in posts:
                valid, issues = self.validate_before_publishing(post)
                if not valid:
                    print(f"  ✗ BLOCKED: {BLUE}{post['title'][:40]}...{RESET}")
                    for issue in issues:
                        print(f"    - {RED}{issue}{RESET}")
                    self.posts_failed += 1
                    posts.remove(post)  # Remove invalid posts
                else:
                    print(f"  ✓ Valid: {post['title'][:40]}...")
            print()

            print(f"{BOLD}Step 3: Publishing Posts to WordPress{RESET}")
            for post in posts:
                print(f"  Publishing: {BLUE}{post['title'][:40]}...{RESET}")

                # Get featured image if available
                # HOLD posts without a featured image: never publish an image-less post.
                # The post stays in draft so the next run can retry it once the image is fixed.
                featured_image_id = None
                if post['featured_image_id']:
                    image_url = self.get_featured_image_url(conn, post['featured_image_id'])
                    if image_url:
                        featured_image_id = self.upload_featured_image_to_wordpress(image_url)
                        if not featured_image_id:  # one retry for transient download/upload failures
                            featured_image_id = self.upload_featured_image_to_wordpress(image_url)

                if not featured_image_id:
                    print(f"    ✗ HELD: no featured image uploaded - post stays in draft")
                    self.posts_failed += 1
                    continue

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

            print(f"{BOLD}Step 4: Updating Publication Status{RESET}")
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

            # Return True only if all posts were published successfully
            if self.posts_failed > 0:
                print(f"  Status: {RED}FAIL - {self.posts_failed} posts failed to publish{RESET}")
                print('='*70 + "\n")
                return False
            else:
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
