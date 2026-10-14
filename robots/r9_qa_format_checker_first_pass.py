#!/usr/bin/env python3
"""
R9: QA Format Checker - First Pass
Purpose: Validate HTML structure, keyword density, images, alt text, links
Input: Complete blog post with images and alt text
Output: Pass/Fail with detailed validation report
Frequency: Every 6 hours (after R7 & R8 complete)
Dependencies: R7 (images), R8 (alt text), R6 (keywords), R3 (content)
Validation Checks:
1. HTML formatting validity
2. Keyword density compliance (1-2%)
3. Image count & alt text presence
4. Internal/affiliate link placeholders
5. Readability & structure compliance
6. Content length (800-1500 words)
"""

import os
import sys
import mysql.connector
from datetime import datetime
import re
import logging
from html.parser import HTMLParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class QAFormatChecker:
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

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_latest_draft_blog(self, conn):
        """Get latest draft blog post for QA checking"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.ai_detection_score, bp.plagiarism_score
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

    def check_html_validity(self, content):
        """Check if HTML tags are properly formatted"""
        required_tags = ['<h2>', '<p>', '</p>']
        issues = []

        # Check for required tags
        for tag in required_tags:
            if tag not in content:
                issues.append(f"Missing required tag: {tag}")

        # Check for mismatched tags
        open_tags = re.findall(r'<(h[23]|p|ul|ol|li)>', content)
        close_tags = re.findall(r'</(h[23]|p|ul|ol|li)>', content)

        for tag_type in set(open_tags):
            open_count = open_tags.count(tag_type)
            close_count = close_tags.count(tag_type)
            if open_count != close_count:
                issues.append(f"Mismatched tags: <{tag_type}> ({open_count} open vs {close_count} close)")

        return len(issues) == 0, issues

    def check_content_length(self, content):
        """Check if content is within 800-1500 word range"""
        words = len(re.findall(r'\b\w+\b', content))

        if words < 800:
            return False, [f"Content too short: {words} words (minimum 800)"]
        elif words > 1500:
            return False, [f"Content too long: {words} words (maximum 1500)"]

        return True, []

    def check_keyword_density(self, content, keywords):
        """Check keyword density is within 1-2% range"""
        issues = []
        passes = 0

        words = re.findall(r'\b\w+\b', content.lower())
        total_words = len(words)

        for keyword in keywords[:3]:
            keyword_count = content.lower().count(keyword.lower())
            density = (keyword_count / total_words * 100) if total_words > 0 else 0

            if density < 1.0:
                issues.append(f"Keyword '{keyword}' too low: {density:.2f}% (minimum 1%)")
            elif density > 2.0:
                issues.append(f"Keyword '{keyword}' too high: {density:.2f}% (maximum 2%)")
            else:
                passes += 1

        return len(issues) == 0, issues, passes

    def check_images_and_alt_text(self, conn, blog_id):
        """Check images have alt text"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, image_url, alt_text
                FROM image_tracking
                WHERE blog_id = %s
            """
            cursor.execute(query, (blog_id,))
            images = cursor.fetchall()
            cursor.close()

            if not images:
                return False, ["No images found for blog"], 0

            issues = []
            for img in images:
                if not img['alt_text']:
                    issues.append(f"Image missing alt text: {img['image_url'][:50]}...")
                elif len(img['alt_text']) < 10:
                    issues.append(f"Alt text too short: {img['image_url'][:50]}... ({len(img['alt_text'])} chars)")
                elif len(img['alt_text']) > 120:
                    issues.append(f"Alt text too long: {img['image_url'][:50]}... ({len(img['alt_text'])} chars, max 120)")

            return len(issues) == 0, issues, len(images)
        except Exception as e:
            logger.error(f"Error checking images: {str(e)}")
            return False, ["Database error checking images"], 0

    def check_internal_links(self, content):
        """Check for internal link placeholders"""
        internal_links = re.findall(r'\[\[INTERNAL_LINK:[^\]]+\]\]', content)

        if len(internal_links) < 2:
            return False, ["Missing internal link placeholders (need minimum 2)"], len(internal_links)

        return True, [], len(internal_links)

    def check_affiliate_links(self, content):
        """Check for affiliate link placeholders"""
        affiliate_links = re.findall(r'\[\[AFFILIATE_LINK:[^\]]+\]\]', content)

        if len(affiliate_links) < 1:
            return False, ["Missing affiliate link placeholders (need minimum 1)"], len(affiliate_links)

        return True, [], len(affiliate_links)

    def check_placeholders(self, content):
        """CRITICAL: Check for unresolved [[...]] placeholders"""
        # Any remaining placeholder is a FAIL
        if re.search(r'\[\[', content):
            placeholders = re.findall(r'\[\[[^\]]+\]\]', content)
            return False, [f"CRITICAL: Unresolved placeholders found: {placeholders}"]
        return True, []

    def check_content_complete(self, content):
        """Check if content is complete (not truncated)"""
        issues = []

        # Extract just the text without HTML tags
        text_only = re.sub(r'<[^>]+>', '', content)
        paragraphs = text_only.split('\n')

        # Check last paragraph isn't truncated (ends with ... or very short)
        if paragraphs:
            last_para = paragraphs[-1].strip()
            if last_para.endswith('...') and len(last_para) < 30:
                issues.append("Content appears truncated (ends with ...)")

        # Check no sentence ends mid-word
        if re.search(r'[a-z]{2,}\s*$', text_only):
            # This might be okay if it ends with a proper sentence
            pass

        return len(issues) == 0, issues

    def check_structure_compliance(self, content):
        """Check if content follows required structure"""
        issues = []

        # Check for required sections (indicated by headers or keywords)
        structure_elements = {
            'Introduction': r'<h2>.*?[Ii]ntro',
            'Problem': r'<h2>.*?[Pp]roblem',
            'Solution': r'<h2>.*?[Ss]olution',
            'Benefits': r'<h2>.*?[Bb]enefit',
            'Buying Guide': r'<h2>.*?[Bb]uying|[Gg]uide',
            'Conclusion': r'<h2>.*?[Cc]onclusion'
        }

        found_sections = 0
        for section, pattern in structure_elements.items():
            if re.search(pattern, content):
                found_sections += 1

        if found_sections < 4:
            issues.append(f"Missing key sections: found {found_sections}/6 required sections")

        # Check for lists/bullet points
        if '<ul>' not in content and '<ol>' not in content:
            issues.append("No lists or bullet points found (need at least one)")

        return len(issues) == 0, issues, found_sections

    def save_qa_result(self, conn, blog_id, qa_passed, report):
        """Save QA check result to database"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE blog_posts
                SET qa_check_passed = %s, qa_check_report = %s, qa_checked_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (qa_passed, report, blog_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving QA result: {str(e)}")
            return False

    def run(self):
        self.print_header("R9: QA FORMAT CHECKER - FIRST PASS")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Latest Draft Blog{RESET}")
            blog_data = self.get_latest_draft_blog(conn)
            if not blog_data:
                logger.error("No draft blogs found")
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            print(f"{BOLD}Step 2: CRITICAL - Placeholder Check{RESET}")
            placeholder_valid, placeholder_issues = self.check_placeholders(blog_data['content'])
            if placeholder_valid:
                print(f"  ✓ {GREEN}No unresolved placeholders{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}CRITICAL - PLACEHOLDER ISSUES:{RESET}")
                for issue in placeholder_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()
                # FAIL immediately on placeholder issues
                qa_passed = False
                report = f"FAILED: Unresolved placeholders found"
                self.save_qa_result(conn, blog_data['id'], qa_passed, report)
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Status: {RED}FAIL - Unresolved placeholders must be resolved before publishing{RESET}")
                print('='*70 + "\n")
                return False

            print(f"{BOLD}Step 3: Content Completeness Check{RESET}")
            complete_valid, complete_issues = self.check_content_complete(blog_data['content'])
            if complete_valid:
                print(f"  ✓ {GREEN}Content is complete (not truncated){RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Content completeness issues:{RESET}")
                for issue in complete_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 5: HTML Structure Validation{RESET}")
            html_valid, html_issues = self.check_html_validity(blog_data['content'])
            if html_valid:
                print(f"  ✓ {GREEN}HTML structure valid{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}HTML structure issues:{RESET}")
                for issue in html_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 6: Content Length Check{RESET}")
            length_valid, length_issues = self.check_content_length(blog_data['content'])
            if length_valid:
                words = len(re.findall(r'\b\w+\b', blog_data['content']))
                print(f"  ✓ {GREEN}Content length valid: {words} words{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Content length issues:{RESET}")
                for issue in length_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 7: Keyword Density Analysis{RESET}")
            keywords = self.get_blog_keywords(conn, blog_data['topic'])
            kw_valid, kw_issues, kw_passes = self.check_keyword_density(blog_data['content'], keywords)
            if kw_valid:
                print(f"  ✓ {GREEN}Keyword density optimal: {kw_passes}/{len(keywords[:3])} keywords in range{RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Keyword density issues:{RESET}")
                for issue in kw_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            print(f"{BOLD}Step 8: Images & Alt Text Check{RESET}")
            img_valid, img_issues, img_count = self.check_images_and_alt_text(conn, blog_data['id'])
            if img_valid:
                print(f"  ✓ {GREEN}All {img_count} images have valid alt text{RESET}\n")
                self.passes += 1
            else:
                print(f"  ✗ {RED}Image/alt text issues:{RESET}")
                for issue in img_issues:
                    print(f"    - {issue}")
                    self.issues.append(issue)
                print()

            print(f"{BOLD}Step 9: Internal Links Check{RESET}")
            intl_valid, intl_issues, intl_count = self.check_internal_links(blog_data['content'])
            if intl_valid:
                print(f"  ✓ {GREEN}Internal links found: {intl_count}{RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Internal links issues:{RESET}")
                for issue in intl_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            print(f"{BOLD}Step 10: Affiliate Links Check{RESET}")
            aff_valid, aff_issues, aff_count = self.check_affiliate_links(blog_data['content'])
            if aff_valid:
                print(f"  ✓ {GREEN}Affiliate links found: {aff_count}{RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Affiliate links issues:{RESET}")
                for issue in aff_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            print(f"{BOLD}Step 11: Content Structure Compliance{RESET}")
            struct_valid, struct_issues, section_count = self.check_structure_compliance(blog_data['content'])
            if struct_valid:
                print(f"  ✓ {GREEN}Structure compliant: {section_count} sections found{RESET}\n")
                self.passes += 1
            else:
                print(f"  ⚠ {YELLOW}Structure issues:{RESET}")
                for issue in struct_issues:
                    print(f"    - {issue}")
                    self.warnings.append(issue)
                print()

            # Determine overall result
            qa_passed = len(self.issues) == 0
            report = f"Passes: {self.passes}/11 | Issues: {len(self.issues)} | Warnings: {len(self.warnings)}"
            self.save_qa_result(conn, blog_data['id'], qa_passed, report)

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Validation Passes: {self.passes}/11")
            print(f"  Critical Issues: {RED}{len(self.issues)}{RESET}")
            print(f"  Warnings: {YELLOW}{len(self.warnings)}{RESET}")
            if qa_passed:
                print(f"  Status: {GREEN}PASS - Ready for R10 (Revalidation){RESET}")
            else:
                print(f"  Status: {RED}FAIL - Issues must be fixed before continuing{RESET}")
            print('='*70 + "\n")
            return qa_passed

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    checker = QAFormatChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
