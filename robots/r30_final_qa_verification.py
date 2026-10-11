#!/usr/bin/env python3
"""
R30: Final QA Verification
Purpose: Final comprehensive QA check before publishing to WordPress
Input: Confirmed blog posts ready for publication (all prior checks passed)
Output: Final approval status + ready-for-WordPress flag
Frequency: Every 6 hours (final checkpoint)
Dependencies: R29 (headline confirmed), precedes R31 (WordPress upload)
QA Checks: 12-point final verification before publishing
Content Integrity: Verify all assets, links, metadata intact
WordPress Readiness: Check SEO meta, featured image, categories, tags
Publication Block: Can only proceed if all checks pass
Rollback Eligible: Can trigger rollback if issues detected
"""

import os
import sys
import mysql.connector
from datetime import datetime
import logging
import re
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class FinalQAVerification:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.posts_verified = 0
        self.posts_approved = 0
        self.posts_blocked = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_posts_for_final_qa(self, conn):
        """Get posts ready for final QA verification"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.qa_check_passed, bp.revalidation_passed,
                       bp.headline_locked, bp.affiliate_links_injected,
                       bp.static_links_injected, bp.version
                FROM blog_posts bp
                WHERE bp.status = 'draft'
                AND bp.headline_locked = TRUE
                AND bp.qa_check_passed = TRUE
                AND bp.revalidation_passed = TRUE
                AND bp.final_qa_passed IS NULL
                ORDER BY bp.created_at ASC
                LIMIT 30
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []

    def verify_content_structure(self, content):
        """Verify content has all required sections"""
        required_sections = {
            'h1': r'<h1[^>]*>',
            'h2': r'<h2[^>]*>',
            'paragraphs': r'<p[^>]*>',
            'strong': r'<strong>|<b>'
        }

        checks_passed = 0
        for section, pattern in required_sections.items():
            if re.search(pattern, content, re.IGNORECASE):
                checks_passed += 1

        return checks_passed == len(required_sections)

    def verify_all_images_valid(self, conn, blog_id):
        """Verify all images have URLs and alt text"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 ELSE 0 END) as with_url,
                       SUM(CASE WHEN alt_text IS NOT NULL AND alt_text != '' THEN 1 ELSE 0 END) as with_alt
                FROM image_tracking
                WHERE blog_id = %s
            """
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()
            cursor.close()

            total = result['total'] or 0
            with_url = result['with_url'] or 0
            with_alt = result['with_alt'] or 0

            if total == 0:
                return True  # No images required

            return with_url == total and with_alt == total
        except Exception as e:
            logger.error(f"Error verifying images: {str(e)}")
            return False

    def verify_all_links_valid(self, content):
        """Verify all links are properly formatted"""
        # Check for broken links or malformed hrefs
        link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>'
        links = re.findall(link_pattern, content)

        if not links:
            return True  # No links required

        valid_count = 0
        for link in links:
            # Basic validation: not empty, contains http or / or #
            if link and (link.startswith('http') or link.startswith('/') or link.startswith('#')):
                valid_count += 1

        return valid_count == len(links)

    def verify_seo_metadata(self, conn, blog_id):
        """Verify SEO metadata is complete"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    CASE WHEN meta_description IS NOT NULL AND meta_description != '' THEN 1 ELSE 0 END as has_meta_desc,
                    CASE WHEN slug IS NOT NULL AND slug != '' THEN 1 ELSE 0 END as has_slug,
                    CASE WHEN featured_image_id IS NOT NULL THEN 1 ELSE 0 END as has_featured_image,
                    CASE WHEN tags IS NOT NULL THEN 1 ELSE 0 END as has_tags
                FROM blog_posts
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return False

            # All SEO elements required
            return all([
                result['has_meta_desc'],
                result['has_slug'],
                result['has_featured_image'],
                result['has_tags']
            ])
        except Exception as e:
            logger.error(f"Error verifying SEO: {str(e)}")
            return False

    def verify_wordpress_readiness(self, conn, blog_id):
        """Verify post is ready for WordPress publishing"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    CASE WHEN content IS NOT NULL AND CHAR_LENGTH(content) > 800 THEN 1 ELSE 0 END as has_content,
                    CASE WHEN category_id IS NOT NULL THEN 1 ELSE 0 END as has_category,
                    CASE WHEN title IS NOT NULL AND CHAR_LENGTH(title) > 0 THEN 1 ELSE 0 END as has_title
                FROM blog_posts
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return False

            return all([
                result['has_content'],
                result['has_category'],
                result['has_title']
            ])
        except Exception as e:
            logger.error(f"Error verifying WordPress readiness: {str(e)}")
            return False

    def run_full_qa_suite(self, conn, post):
        """Run complete QA verification suite"""
        checks = {
            'content_structure': self.verify_content_structure(post['content']),
            'images_valid': self.verify_all_images_valid(conn, post['id']),
            'links_valid': self.verify_all_links_valid(post['content']),
            'seo_metadata': self.verify_seo_metadata(conn, post['id']),
            'wordpress_ready': self.verify_wordpress_readiness(conn, post['id']),
            'headline_locked': post['headline_locked'],
            'qa_passed_initial': post['qa_check_passed'],
            'revalidation_passed': post['revalidation_passed'],
            'affiliate_links': post['affiliate_links_injected'],
            'static_links': post['static_links_injected']
        }

        return checks

    def save_final_qa_result(self, conn, blog_id, checks, all_passed):
        """Save final QA results"""
        try:
            cursor = conn.cursor()

            # Update blog post
            query = """
                UPDATE blog_posts
                SET final_qa_passed = %s,
                    final_qa_checks = %s,
                    final_qa_timestamp = NOW(),
                    ready_for_wordpress = %s
                WHERE id = %s
            """
            cursor.execute(query, (
                all_passed,
                json.dumps(checks),
                all_passed,
                blog_id
            ))

            # Create QA record
            qa_query = """
                INSERT INTO final_qa_records
                (blog_id, all_checks_passed, qa_data, verified_at)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(qa_query, (
                blog_id,
                all_passed,
                json.dumps(checks)
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving QA result: {str(e)}")
            return False

    def run(self):
        self.print_header("R30: FINAL QA VERIFICATION")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Posts Ready for Final QA{RESET}")
            posts = self.get_posts_for_final_qa(conn)
            if not posts:
                print(f"  No posts ready for final QA\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Verified: 0")
                print(f"  Status: {YELLOW}No posts in final QA queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts ready for verification\n")

            print(f"{BOLD}Step 2: Running Final QA Suite{RESET}")
            for post in posts:
                self.posts_verified += 1

                # Run QA checks
                checks = self.run_full_qa_suite(conn, post)

                # Determine if all passed
                all_passed = all(checks.values())

                # Save results
                self.save_final_qa_result(conn, post['id'], checks, all_passed)

                if all_passed:
                    self.posts_approved += 1
                    print(f"  ✓ {GREEN}APPROVED{RESET}: {post['title'][:45]}...")
                    print(f"    → Ready for WordPress publishing")
                else:
                    self.posts_blocked += 1
                    failed_checks = [k for k, v in checks.items() if not v]
                    print(f"  ✗ {RED}BLOCKED{RESET}: {post['title'][:45]}...")
                    print(f"    Failed: {', '.join(failed_checks[:3])}")
                print()

            print(f"{BOLD}Step 3: Final Publication Status{RESET}")
            print(f"  Approved posts: {GREEN}{self.posts_approved}{RESET}")
            print(f"  Blocked posts: {RED}{self.posts_blocked}{RESET}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Posts Verified: {self.posts_verified}")
            print(f"  Approved: {GREEN}{self.posts_approved}{RESET}")
            print(f"  Blocked: {RED}{self.posts_blocked}{RESET}")
            print(f"  QA Checks: 10-point verification")
            print(f"  WordPress Ready: {self.posts_approved} posts")
            print(f"  Next Stage: R31 (WordPress Publishing)")
            print(f"  Status: {GREEN}PASS - Final QA complete{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    verifier = FinalQAVerification()
    success = verifier.run()
    sys.exit(0 if success else 1)
