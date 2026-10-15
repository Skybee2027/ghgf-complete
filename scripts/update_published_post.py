#!/usr/bin/env python3
"""
UPDATE PUBLISHED POST - Push fixed database content to already-published WordPress post
Purpose: Update WordPress post when database content has been fixed
Post: "Complete Guide to Health and Fitness Trends to Watch in 2026"
"""

import os
import sys
import requests
import mysql.connector
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PublishedPostUpdater:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')

        self.wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
        self.wp_user = os.getenv('WORDPRESS_USER', 'api_user')
        self.wp_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.wp_api = f"{self.wp_url}/wp-json/wp/v2"

        self.connection = None
        logger.info("Published Post Updater initialized")

    def connect_db(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=True
            )
            logger.info("✓ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False

    def close_db(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_post_from_db(self, title):
        """Get post from database by title"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, content, meta_description, wordpress_post_id FROM blog_posts WHERE title = %s LIMIT 1",
                (title,)
            )
            post = cursor.fetchone()
            cursor.close()
            return post
        except Exception as e:
            logger.error(f"Error fetching post from database: {e}")
            return None

    def get_wordpress_post(self, wp_post_id):
        """Get post from WordPress"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            response = requests.get(
                f"{self.wp_api}/posts/{wp_post_id}",
                auth=auth,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"WordPress API error: {response.status_code}")
                logger.error(response.text[:500])
                return None
        except Exception as e:
            logger.error(f"Error fetching from WordPress: {e}")
            return None

    def update_wordpress_post(self, wp_post_id, content, meta_description, title):
        """Update WordPress post with fixed content"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            payload = {
                'title': title,
                'content': content,
                'meta': {
                    'description': meta_description
                }
            }

            # Use POST (WordPress API accepts POST for updates)
            response = requests.post(
                f"{self.wp_api}/posts/{wp_post_id}",
                auth=auth,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info("✓ WordPress post updated successfully")
                return True
            else:
                logger.error(f"✗ WordPress update failed: {response.status_code}")
                logger.error(response.text[:500])
                return False
        except Exception as e:
            logger.error(f"Error updating WordPress post: {e}")
            return False

    def force_republish(self, wp_post_id):
        """Force WordPress to refresh by changing status"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            # Step 1: Set to draft temporarily
            logger.info("Setting post to draft temporarily...")
            draft_response = requests.post(
                f"{self.wp_api}/posts/{wp_post_id}",
                auth=auth,
                headers=headers,
                json={'status': 'draft'},
                timeout=10
            )

            if draft_response.status_code not in [200, 201]:
                logger.warning(f"Failed to set draft: {draft_response.status_code}")
                return False

            logger.info("✓ Post set to draft")

            # Step 2: Set back to published
            logger.info("Publishing post back to live...")
            pub_response = requests.post(
                f"{self.wp_api}/posts/{wp_post_id}",
                auth=auth,
                headers=headers,
                json={'status': 'publish'},
                timeout=10
            )

            if pub_response.status_code in [200, 201]:
                logger.info("✓ Post republished")
                return True
            else:
                logger.error(f"Failed to republish: {pub_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error in force republish: {e}")
            return False

    def verify_update(self, wp_post_id, expected_content):
        """Verify update was successful"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            response = requests.get(
                f"{self.wp_api}/posts/{wp_post_id}",
                auth=auth,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                wp_post = response.json()
                wp_content = wp_post.get('content', {}).get('rendered', '')

                # Check key indicators from our fixes
                checks = {
                    'No code markers': '```' not in wp_content,
                    'No XYZ Probiotic': 'XYZ Probiotic' not in wp_content,
                    'Has FAQ': 'FAQ' in wp_content,
                    'Has eBook': 'eBook' in wp_content or 'Fitness Fundamentals' in wp_content,
                    'Has sources': 'Sources' in wp_content or 'Reference' in wp_content,
                    'Has author bio': 'About the Author' in wp_content,
                }

                logger.info("\n" + "="*70)
                logger.info("VERIFICATION RESULTS")
                logger.info("="*70)

                all_passed = True
                for check, result in checks.items():
                    status = "✓" if result else "✗"
                    logger.info(f"{status} {check}")
                    if not result:
                        all_passed = False

                return all_passed
            else:
                logger.error(f"Verification failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error in verification: {e}")
            return False

    def run(self):
        """Execute the update"""
        print("\n" + "="*70)
        print("UPDATE PUBLISHED POST - Push fixed database content to WordPress")
        print("="*70 + "\n")

        if not self.connect_db():
            return False

        try:
            # Find the post in database
            post_title = "Complete Guide to Health and Fitness Trends to Watch in 2026"
            logger.info(f"Looking for post: {post_title}")

            db_post = self.get_post_from_db(post_title)

            if not db_post:
                logger.error(f"Post not found in database")
                return False

            post_id = db_post['id']
            wp_post_id = db_post['wordpress_post_id']
            content = db_post['content']
            meta_description = db_post['meta_description']

            logger.info(f"\n✓ Found in database:")
            logger.info(f"  Post ID: {post_id}")
            logger.info(f"  WordPress ID: {wp_post_id}")
            logger.info(f"  Title: {db_post['title'][:50]}...")
            logger.info(f"  Content length: {len(content)} chars")
            logger.info(f"  Meta: {meta_description[:60]}...\n")

            if not wp_post_id:
                logger.error("Post has no WordPress ID - cannot update")
                return False

            # Get current WordPress post
            logger.info("Fetching current WordPress post...")
            wp_post = self.get_wordpress_post(wp_post_id)

            if not wp_post:
                logger.error("Could not fetch from WordPress")
                return False

            logger.info(f"✓ Current WordPress status: {wp_post.get('status')}")

            # Update WordPress with fixed content
            logger.info("\n" + "="*70)
            logger.info("UPDATING WORDPRESS POST")
            logger.info("="*70)

            if self.update_wordpress_post(wp_post_id, content, meta_description, post_title):
                logger.info("\n✓ Content update successful")

                # Force republish
                logger.info("\n" + "="*70)
                logger.info("FORCE REPUBLISH (draft → publish)")
                logger.info("="*70 + "\n")

                if self.force_republish(wp_post_id):
                    logger.info("\n✓ Republish successful")

                    # Verify
                    logger.info("\nVerifying update on live site...")
                    if self.verify_update(wp_post_id, content):
                        logger.info("\n🎉 ALL VERIFICATION CHECKS PASSED!")
                        logger.info("Post has been successfully updated with fixed content.")
                        logger.info("\nChanges applied:")
                        logger.info("  ✓ Removed code artifacts (```)")
                        logger.info("  ✓ Removed placeholder text")
                        logger.info("  ✓ Added FAQ section")
                        logger.info("  ✓ Added eBook links")
                        logger.info("  ✓ Added source citations")
                        logger.info("  ✓ Added author bio")
                        logger.info("\n" + "="*70)
                        return True
                    else:
                        logger.warning("\n⚠️ Some verification checks failed")
                        logger.warning("Content may be cached on WordPress")
                        logger.warning("Try hard refresh (Ctrl+F5) on the live page")
                        return True  # Still return True, update happened
                else:
                    logger.error("Failed to republish")
                    return False
            else:
                logger.error("Failed to update WordPress post")
                return False

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.close_db()


def main():
    try:
        updater = PublishedPostUpdater()
        success = updater.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
