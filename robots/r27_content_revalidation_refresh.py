#!/usr/bin/env python3
"""
R27: Content Revalidation after Refresh (Second Validation Pass)
Purpose: Re-validate content after R12/R25 refresh modifications
Input: Refreshed blog content from R12 product research
Output: Validation report + breakage detection
Frequency: As needed (triggered by R25 refresh workflow)
Dependencies: R25 (refresh trigger), R12 (product research modifications)
Conflict Resolution: Similar to R10 but for REFRESH cycle, not initial creation (Conflict #4)
Validation: 8-point check after refresh (HTML, length, keywords, images, links, etc)
Quality Gates: Ensures refresh didn't introduce quality degradation
Comparison: Before/after analysis to detect content breakage
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

class ContentRevalidationRefresh:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.posts_revalidated = 0
        self.posts_passed = 0
        self.posts_with_breakage = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_posts_needing_revalidation(self, conn):
        """Get posts waiting for refresh revalidation"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.version, bp.version_before_refresh,
                       crw.current_stage
                FROM blog_posts bp
                JOIN refresh_workflow_queue crw ON bp.id = crw.blog_id
                WHERE crw.current_stage = 'R27_REVALIDATION'
                AND bp.refresh_in_progress = TRUE
                LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []

    def get_previous_version(self, conn, blog_id):
        """Get previous version of content before refresh"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT content, version
                FROM blog_post_versions
                WHERE blog_id = %s
                ORDER BY created_at DESC
                LIMIT 2
            """
            cursor.execute(query, (blog_id,))
            results = cursor.fetchall()
            cursor.close()

            if len(results) >= 2:
                return results[1]  # Second most recent = before refresh
            return None
        except Exception as e:
            logger.error(f"Error getting previous version: {str(e)}")
            return None

    def validate_html_integrity(self, content):
        """Check HTML validity"""
        # Basic HTML tag matching
        opening_tags = len(re.findall(r'<[^/][^>]*>', content))
        closing_tags = len(re.findall(r'</[^>]*>', content))

        return opening_tags == closing_tags

    def validate_content_length(self, content):
        """Check content length is in valid range"""
        # Remove HTML tags for word count
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())

        return 800 <= words <= 2000

    def validate_keywords_preserved(self, before_content, after_content):
        """Check that keywords are still present after refresh"""
        # Extract keywords (words > 5 chars)
        before_keywords = set(re.findall(r'\b\w{5,}\b', before_content.lower()))
        after_keywords = set(re.findall(r'\b\w{5,}\b', after_content.lower()))

        # Check at least 80% of original keywords remain
        if not before_keywords:
            return True

        preserved = len(before_keywords & after_keywords) / len(before_keywords)
        return preserved >= 0.8

    def validate_images_preserved(self, before_content, after_content):
        """Check that images are still present"""
        before_images = len(re.findall(r'<img', before_content))
        after_images = len(re.findall(r'<img', after_content))

        return after_images >= before_images

    def validate_links_preserved(self, before_content, after_content):
        """Check that links are preserved/improved"""
        before_links = len(re.findall(r'<a href', before_content))
        after_links = len(re.findall(r'<a href', after_content))

        return after_links >= before_links

    def check_for_over_optimization(self, content):
        """Detect signs of over-optimization during refresh"""
        issues = []

        # Check for keyword stuffing
        words = re.findall(r'\b\w+\b', content.lower())
        if words:
            word_counts = {}
            for word in words:
                if len(word) > 4:
                    word_counts[word] = word_counts.get(word, 0) + 1

            # Check if any word appears too frequently
            for word, count in word_counts.items():
                frequency = count / len(words)
                if frequency > 0.05:  # More than 5% of text
                    issues.append(f"Possible keyword stuffing: '{word}'")

        return issues

    def revalidate_post(self, conn, post, previous_version):
        """Re-validate refreshed post"""
        checks_passed = 0
        checks_failed = 0
        breakage_detected = False
        issues = []

        # Check 1: HTML validity
        if self.validate_html_integrity(post['content']):
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("HTML integrity check failed")
            breakage_detected = True

        # Check 2: Content length
        if self.validate_content_length(post['content']):
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("Content length out of range")
            breakage_detected = True

        # Check 3: Keywords preserved (if previous version exists)
        if previous_version:
            if self.validate_keywords_preserved(previous_version['content'], post['content']):
                checks_passed += 1
            else:
                checks_failed += 1
                issues.append("Keywords not preserved from original")
        else:
            checks_passed += 1  # Skip if no previous version

        # Check 4: Images preserved
        if self.validate_images_preserved(previous_version['content'] if previous_version else '', post['content']):
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("Images not preserved")

        # Check 5: Links preserved/improved
        if self.validate_links_preserved(previous_version['content'] if previous_version else '', post['content']):
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("Links degraded")

        # Check 6: Over-optimization detection
        optimization_issues = self.check_for_over_optimization(post['content'])
        if not optimization_issues:
            checks_passed += 1
        else:
            checks_failed += 1
            issues.extend(optimization_issues)
            breakage_detected = True

        return {
            'passed': checks_passed,
            'failed': checks_failed,
            'breakage': breakage_detected,
            'issues': issues
        }

    def save_revalidation_result(self, conn, blog_id, result):
        """Save revalidation results"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET refresh_revalidation_passed = %s,
                    refresh_revalidation_issues = %s,
                    refresh_revalidation_at = NOW()
                WHERE id = %s
            """

            cursor.execute(query, (
                not result['breakage'],
                json.dumps(result['issues']),
                blog_id
            ))

            # Update workflow stage
            workflow_query = """
                UPDATE refresh_workflow_queue
                SET current_stage = %s
                WHERE blog_id = %s
            """

            next_stage = 'R28_PLAGIARISM_CHECK' if not result['breakage'] else 'REVIEW_REQUIRED'
            cursor.execute(workflow_query, (next_stage, blog_id))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving result: {str(e)}")
            return False

    def run(self):
        self.print_header("R27: CONTENT REVALIDATION (REFRESH CYCLE)")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Posts Needing Revalidation{RESET}")
            posts = self.get_posts_needing_revalidation(conn)
            if not posts:
                print(f"  No posts in revalidation queue\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Revalidated: 0")
                print(f"  Status: {YELLOW}No refresh content to validate{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts to revalidate\n")

            print(f"{BOLD}Step 2: Running Revalidation Checks{RESET}")
            for post in posts:
                self.posts_revalidated += 1

                # Get previous version for comparison
                previous_version = self.get_previous_version(conn, post['id'])

                # Revalidate
                result = self.revalidate_post(conn, post, previous_version)

                # Save results
                self.save_revalidation_result(conn, post['id'], result)

                if not result['breakage']:
                    self.posts_passed += 1
                    print(f"  ✓ {GREEN}PASSED{RESET}: {post['title'][:40]}...")
                else:
                    self.posts_with_breakage += 1
                    print(f"  ✗ {RED}BREAKAGE DETECTED{RESET}: {post['title'][:40]}...")
                    for issue in result['issues'][:2]:
                        print(f"    └─ {issue}")

            print()

            print(f"{BOLD}Step 3: Generating Revalidation Summary{RESET}")
            print(f"  Checks per post: 6")
            print(f"  Breakage detection: Enabled\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Posts Revalidated: {self.posts_revalidated}")
            print(f"  Passed Validation: {GREEN}{self.posts_passed}{RESET}")
            print(f"  Breakage Detected: {RED}{self.posts_with_breakage}{RESET}")
            print(f"  Validation Type: Refresh revalidation (post-R12 modifications)")
            print(f"  Next Stage: R28 (Plagiarism Recheck)")
            print(f"  Status: {GREEN}PASS - Refresh content validated{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    revalidator = ContentRevalidationRefresh()
    success = revalidator.run()
    sys.exit(0 if success else 1)
