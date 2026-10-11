#!/usr/bin/env python3
"""
R10: Revalidation - Second Pass
Purpose: Re-validate content AFTER R6 modifications to catch any breakage
Input: Modified content from R6 (keyword optimization)
Output: Pass/Fail confirmation that R6 changes didn't break validation
Frequency: Every 6 hours (after R6 completes)
Dependencies: R6 (provides optimized content), R9 (first pass baseline)
Key Difference: Checks if R6's modifications maintained all validation standards
Checks Same: HTML validity, keyword density, images, alt text, links
"""

import os
import sys
import mysql.connector
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class RevalidationChecker:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.issues = []
        self.warnings = []
        self.passes = 0
        self.breakage_detected = False

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_latest_draft_blog(self, conn):
        """Get latest draft blog post that was optimized by R6"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic, bp.version,
                       bp.qa_check_passed, bp.qa_check_report
                FROM blog_posts bp
                WHERE bp.status = 'draft'
                ORDER BY bp.created_at DESC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting blog: {str(e)}")
            return None

    def get_previous_version(self, conn, blog_id):
        """Get version history to compare before/after R6"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT version, content, robot_modified_by, change_type, created_at
                FROM version_history
                WHERE blog_id = %s
                ORDER BY version DESC
                LIMIT 2
            """
            cursor.execute(query, (blog_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []

    def get_blog_keywords(self, conn, topic):
        """Get top keywords for this blog's topic"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT keyword FROM trending_keywords
                WHERE topic = %s
                ORDER BY search_volume DESC
                LIMIT 5
            """
            cursor.execute(query, (topic,))
            results = cursor.fetchall()
            cursor.close()
            return [r['keyword'] for r in results]
        except Exception as e:
            logger.error(f"Error getting keywords: {str(e)}")
            return []

    def compare_content_integrity(self, original_content, modified_content):
        """Check if R6 modifications maintained content integrity"""
        issues = []

        # Check if HTML tags are still balanced
        orig_open = len(re.findall(r'<(h[23]|p|ul|ol|li)>', original_content))
        mod_open = len(re.findall(r'<(h[23]|p|ul|ol|li)>', modified_content))

        if orig_open > mod_open:
            issues.append(f"HTML opening tags reduced: {orig_open} → {mod_open} (possible breakage)")

        # Check if closing tags still match
        for tag_type in ['h2', 'h3', 'p', 'ul', 'ol', 'li']:
            orig_open = len(re.findall(rf'<{tag_type}>', original_content))
            orig_close = len(re.findall(rf'</{tag_type}>', original_content))
            mod_open = len(re.findall(rf'<{tag_type}>', modified_content))
            mod_close = len(re.findall(rf'</{tag_type}>', modified_content))

            if mod_open != mod_close:
                issues.append(f"Tag mismatch after modification <{tag_type}>: {mod_open} open vs {mod_close} close")

        return len(issues) == 0, issues

    def check_content_length_preserved(self, original_content, modified_content):
        """Check if R6 maintained content within length bounds"""
        orig_words = len(re.findall(r'\b\w+\b', original_content))
        mod_words = len(re.findall(r'\b\w+\b', modified_content))

        issues = []

        # Allow 5% variance (R6 may add/remove content slightly)
        variance = abs(mod_words - orig_words) / orig_words * 100

        if mod_words < 800:
            issues.append(f"Content too short after optimization: {mod_words} words")
        elif mod_words > 1500:
            issues.append(f"Content too long after optimization: {mod_words} words")
        elif variance > 10:  # More than 10% change
            issues.append(f"Significant word count change: {orig_words} → {mod_words} ({variance:.1f}% variance)")

        return len(issues) == 0, issues

    def check_keywords_enhanced(self, content, keywords):
        """Check that R6 actually enhanced keyword density"""
        issues = []
        enhanced = 0

        words = re.findall(r'\b\w+\b', content.lower())
        total_words = len(words)

        for keyword in keywords[:3]:
            keyword_count = content.lower().count(keyword.lower())
            density = (keyword_count / total_words * 100) if total_words > 0 else 0

            # After R6, keywords should be in optimal range
            if density < 0.8:
                issues.append(f"Keyword '{keyword}' still too low after optimization: {density:.2f}%")
            elif density > 2.2:
                issues.append(f"Keyword '{keyword}' over-optimized: {density:.2f}%")
            else:
                enhanced += 1

        return len(issues) == 0, issues, enhanced

    def check_images_preserved(self, conn, blog_id):
        """Check that R6 didn't remove image references"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT COUNT(*) as count
                FROM image_tracking
                WHERE blog_id = %s
            """
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()
            cursor.close()

            img_count = result['count']
            if img_count < 3:
                return False, ["Not enough images preserved after optimization"], img_count

            return True, [], img_count
        except Exception as e:
            logger.error(f"Error checking images: {str(e)}")
            return False, ["Error checking images"], 0

    def check_links_preserved(self, original_content, modified_content):
        """Check that R6 preserved link placeholders"""
        issues = []

        orig_internal = len(re.findall(r'\[\[INTERNAL_LINK:[^\]]+\]\]', original_content))
        mod_internal = len(re.findall(r'\[\[INTERNAL_LINK:[^\]]+\]\]', modified_content))

        orig_affiliate = len(re.findall(r'\[\[AFFILIATE_LINK:[^\]]+\]\]', original_content))
        mod_affiliate = len(re.findall(r'\[\[AFFILIATE_LINK:[^\]]+\]\]', modified_content))

        if mod_internal < orig_internal:
            issues.append(f"Internal links removed: {orig_internal} → {mod_internal}")

        if mod_affiliate < orig_affiliate:
            issues.append(f"Affiliate links removed: {orig_affiliate} → {mod_affiliate}")

        return len(issues) == 0, issues

    def detect_optimization_quality(self, original_content, modified_content):
        """Check if R6's keyword optimization improved readability"""
        # Check for excessive keyword insertion (reads unnaturally)
        keywords_in_first_100 = len(re.findall(r'\[\[', modified_content[:1000]))

        if keywords_in_first_100 > 8:
            return False, ["Over-optimization detected: too many keyword instances in opening"]

        # Check headers were improved
        orig_headers = len(re.findall(r'<h2>[^<]*</h2>', original_content))
        mod_headers = len(re.findall(r'<h2>[^<]*</h2>', modified_content))

        if mod_headers < orig_headers:
            return False, ["Headers were reduced during optimization"]

        return True, []

    def save_revalidation_result(self, conn, blog_id, revalidation_passed, report):
        """Save revalidation result"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE blog_posts
                SET revalidation_passed = %s, revalidation_report = %s,
                    revalidation_checked_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (revalidation_passed, report, blog_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving revalidation result: {str(e)}")
            return False

    def run(self):
        self.print_header("R10: REVALIDATION - SECOND PASS")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Modified Blog (from R6){RESET}")
            blog_data = self.get_latest_draft_blog(conn)
            if not blog_data:
                logger.error("No draft blogs found")
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Version: {blog_data['version']}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            print(f"{BOLD}Step 2: Getting Version History{RESET}")
            versions = self.get_previous_version(conn, blog_data['id'])
            if len(versions) < 2:
                print(f"  ⚠ {YELLOW}Only {len(versions)} version(s) in history, skipping before/after comparison{RESET}\n")
                original_content = versions[0]['content'] if versions else blog_data['content']
            else:
                original_content = versions[1]['content']
                print(f"  ✓ Comparing version {versions[1]['version']} → {versions[0]['version']}\n")

            print(f"{BOLD}Step 3: Content Integrity Check{RESET}")
            integrity_valid, integrity_issues = self.compare_content_integrity(original_content, blog_data['content'])
            if integrity_valid:
                print(f"  ✓ {GREEN}HTML structure intact after R6 modifications{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Content integrity issues:{RESET}")
                for issue in integrity_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                    self.breakage_detected = True
                print()

            print(f"{BOLD}Step 4: Content Length Check{RESET}")
            length_valid, length_issues = self.check_content_length_preserved(original_content, blog_data['content'])
            if length_valid:
                mod_words = len(re.findall(r'\b\w+\b', blog_data['content']))
                print(f"  ✓ {GREEN}Content length preserved: {mod_words} words{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Content length issues:{RESET}")
                for issue in length_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 5: Keyword Optimization Verification{RESET}")
            keywords = self.get_blog_keywords(conn, blog_data['topic'])
            kw_valid, kw_issues, kw_enhanced = self.check_keywords_enhanced(blog_data['content'], keywords)
            if kw_valid:
                print(f"  ✓ {GREEN}Keywords optimized successfully: {kw_enhanced}/{len(keywords[:3])} in optimal range{RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Keyword optimization issues:{RESET}")
                for issue in kw_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            print(f"{BOLD}Step 6: Images Preservation Check{RESET}")
            img_valid, img_issues, img_count = self.check_images_preserved(conn, blog_data['id'])
            if img_valid:
                print(f"  ✓ {GREEN}All images preserved: {img_count} images still present{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Image preservation issues:{RESET}")
                for issue in img_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 7: Links Preservation Check{RESET}")
            links_valid, links_issues = self.check_links_preserved(original_content, blog_data['content'])
            if links_valid:
                internal_count = len(re.findall(r'\[\[INTERNAL_LINK:[^\]]+\]\]', blog_data['content']))
                affiliate_count = len(re.findall(r'\[\[AFFILIATE_LINK:[^\]]+\]\]', blog_data['content']))
                print(f"  ✓ {GREEN}Links preserved: {internal_count} internal, {affiliate_count} affiliate{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Links issues:{RESET}")
                for issue in links_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 8: Optimization Quality Check{RESET}")
            quality_valid, quality_issues = self.detect_optimization_quality(original_content, blog_data['content'])
            if quality_valid:
                print(f"  ✓ {GREEN}Optimization quality verified (natural keyword placement){RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Optimization quality concerns:{RESET}")
                for issue in quality_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            # Determine overall result
            revalidation_passed = len(self.issues) == 0 and not self.breakage_detected
            report = f"Passes: {self.passes}/8 | Issues: {len(self.issues)} | Warnings: {len(self.warnings)}"
            self.save_revalidation_result(conn, blog_data['id'], revalidation_passed, report)

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Revalidation Passes: {self.passes}/8")
            print(f"  Critical Issues: {RED}{len(self.issues)}{RESET}")
            print(f"  Warnings: {YELLOW}{len(self.warnings)}{RESET}")
            if self.breakage_detected:
                print(f"  Breakage Status: {RED}DETECTED - R6 modifications caused issues{RESET}")
            if revalidation_passed:
                print(f"  Status: {GREEN}PASS - R6 modifications validated, ready for R11{RESET}")
            else:
                print(f"  Status: {RED}FAIL - R6 modifications introduced issues{RESET}")
            print('='*70 + "\n")
            return revalidation_passed

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    checker = RevalidationChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
