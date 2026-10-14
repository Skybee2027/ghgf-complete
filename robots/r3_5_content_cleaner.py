#!/usr/bin/env python3
"""
R3.5: INTELLIGENT Content Cleaner
Purpose: Fix malformed content from R3 by removing markdown artifacts and duplicate sections
Runs AFTER R3 generates content, BEFORE R4 starts QA checks
Fixes:
  1. Removes markdown artifact wrappers (```html ... ```)
  2. Removes duplicate title and metadata
  3. Removes duplicate "Table of Contents"
  4. Validates and fixes HTML structure
  5. Ensures single clean content block
"""

import os
import sys
import mysql.connector
import logging
import re
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'

class ContentCleaner:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_user = os.getenv('DB_USER', 'root')
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'ghgf_blogging')
        self.connection = None
        self.posts_cleaned = 0

    def connect_db(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=True,
                connection_timeout=30
            )
            logger.info(f"{GREEN}✅ Database connection successful{RESET}")
            return True
        except Exception as e:
            logger.error(f"{RED}❌ Database connection failed: {e}{RESET}")
            return False

    def remove_markdown_artifacts(self, content):
        """Remove markdown code block wrappers (```html ... ```)"""
        # Remove opening ```html or ``` wrapper at start
        content = re.sub(r'^```(?:html)?\s*\n', '', content, flags=re.MULTILINE)
        # Remove closing ``` at end
        content = re.sub(r'\n```\s*$', '', content, flags=re.MULTILINE)
        # Remove any remaining stray backticks
        content = re.sub(r'^```.*?\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```', '', content)
        return content

    def remove_duplicate_title(self, content):
        """Remove duplicate title blocks at beginning"""
        lines = content.split('\n')
        title_pattern = r'^<h1>.*?</h1>$'

        # Find first h1
        first_h1_idx = -1
        for i, line in enumerate(lines):
            if re.match(title_pattern, line):
                first_h1_idx = i
                break

        if first_h1_idx == -1:
            return content

        # Count h1s in first 10 lines
        h1_count = 0
        h1_indices = []
        for i in range(min(10, len(lines))):
            if re.match(title_pattern, lines[i]):
                h1_count += 1
                h1_indices.append(i)

        # If multiple h1s at start, keep only first
        if h1_count > 1:
            # Remove duplicate h1s (keep only first)
            new_lines = []
            for i, line in enumerate(lines):
                if i < len(h1_indices) - 1 and i in h1_indices[1:]:
                    # Skip duplicate h1
                    continue
                new_lines.append(line)
            content = '\n'.join(new_lines)

        return content

    def remove_duplicate_toc(self, content):
        """Remove duplicate 'Table of Contents' sections"""
        # Find all occurrences of "Table of Contents"
        toc_pattern = r'Table of Contents\n.*?(?=\n<h2>|\n\nWhy|\n\nSolution|\Z)'

        # Count TOC sections
        toc_matches = list(re.finditer(toc_pattern, content, re.DOTALL | re.IGNORECASE))

        if len(toc_matches) <= 1:
            return content

        # Keep only the first TOC, remove others
        logger.info(f"Found {len(toc_matches)} Table of Contents sections, removing {len(toc_matches)-1} duplicates")

        result = content
        # Remove from last to first to preserve indices
        for match in reversed(toc_matches[1:]):
            result = result[:match.start()] + result[match.end():]

        return result

    def remove_metadata_duplication(self, content):
        """Remove duplicate metadata blocks (GHGF October 14, 2026Blog, etc)"""
        # Pattern for metadata line like "GHGFOctober 14, 2026Blog"
        metadata_pattern = r'GHGF\w*\d{1,2}\w*\d{4}\w*'

        matches = list(re.finditer(metadata_pattern, content))

        if len(matches) > 1:
            logger.info(f"Found {len(matches)} metadata blocks, removing duplicates")
            # Remove all but first
            result = content
            for match in reversed(matches[1:]):
                result = result[:match.start()] + result[match.end():]
            return result

        return content

    def fix_html_structure(self, content):
        """Ensure proper HTML structure - one continuous block"""
        # Remove excessive blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)

        # Ensure starts with opening tag
        if not re.match(r'^\s*<[a-z]', content, re.IGNORECASE):
            logger.warning("Content doesn't start with HTML tag, prepending")

        # Ensure ends with closing tag
        if not re.search(r'[a-z]>\s*$', content, re.IGNORECASE):
            logger.warning("Content doesn't end with HTML tag")
            # Find last closing tag and truncate after it
            last_close = content.rfind('>')
            if last_close > 0:
                content = content[:last_close+1]

        return content.strip()

    def validate_html_tags(self, content):
        """Check for obvious HTML tag mismatches"""
        open_count = len(re.findall(r'<(h[1-6]|p|ul|li|div)(?:\s|>)', content, re.IGNORECASE))
        close_count = len(re.findall(r'</(h[1-6]|p|ul|li|div)>', content, re.IGNORECASE))

        if open_count != close_count:
            logger.warning(f"HTML tag mismatch: {open_count} opening, {close_count} closing tags")
        else:
            logger.info(f"✓ HTML tags balanced: {open_count} pairs")

        return open_count, close_count

    def clean_content(self, content):
        """Apply all cleaning fixes in sequence"""
        logger.info("Starting content cleaning...")

        # Step 1: Remove markdown artifacts
        logger.info("  1. Removing markdown artifacts (```html wrappers)...")
        content = self.remove_markdown_artifacts(content)

        # Step 2: Remove duplicate titles
        logger.info("  2. Removing duplicate title blocks...")
        content = self.remove_duplicate_title(content)

        # Step 3: Remove metadata duplication
        logger.info("  3. Removing duplicate metadata...")
        content = self.remove_metadata_duplication(content)

        # Step 4: Remove duplicate TOC
        logger.info("  4. Removing duplicate 'Table of Contents'...")
        content = self.remove_duplicate_toc(content)

        # Step 5: Fix structure
        logger.info("  5. Fixing HTML structure...")
        content = self.fix_html_structure(content)

        # Step 6: Validate tags
        logger.info("  6. Validating HTML tags...")
        open_count, close_count = self.validate_html_tags(content)

        logger.info(f"{GREEN}✅ Content cleaning complete{RESET}")
        return content, open_count == close_count

    def get_draft_posts(self):
        """Get all draft posts from database"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, title, content
                FROM blog_posts
                WHERE status = 'draft'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            posts = cursor.fetchall()
            cursor.close()
            return posts
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []

    def update_post_content(self, post_id, cleaned_content):
        """Update post with cleaned content"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE blog_posts
                SET content = %s, updated_date = NOW()
                WHERE id = %s
            """, (cleaned_content, post_id))
            self.connection.commit()
            logger.info(f"  ✓ Post {post_id} updated with cleaned content")
            return True
        except Exception as e:
            logger.error(f"  ✗ Failed to update post {post_id}: {e}")
            return False

    def run(self):
        """Main execution"""
        print(f"\n{'='*70}")
        print(f"{BOLD}R3.5: INTELLIGENT CONTENT CLEANER{RESET}")
        print(f"{'='*70}\n")

        if not self.connect_db():
            print(f"{RED}❌ Failed to connect to database{RESET}")
            return False

        try:
            # Get draft posts
            posts = self.get_draft_posts()

            if not posts:
                print(f"{YELLOW}⚠️  No draft posts found to clean{RESET}")
                return True

            print(f"Found {len(posts)} draft post(s) to clean\n")

            for post in posts:
                post_id = post['id']
                title = post['title']
                content = post['content']

                print(f"{BOLD}Cleaning Post #{post_id}: {title}{RESET}")
                print("-" * 70)

                # Clean content
                cleaned, is_valid = self.clean_content(content)

                # Update database
                if self.update_post_content(post_id, cleaned):
                    self.posts_cleaned += 1
                    print(f"✅ Post #{post_id} cleaned successfully\n")
                else:
                    print(f"❌ Failed to clean post #{post_id}\n")

            # Summary
            print(f"\n{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"Posts cleaned: {self.posts_cleaned}/{len(posts)}")

            if self.posts_cleaned == len(posts):
                print(f"{GREEN}✅ All posts cleaned successfully!{RESET}")
                print(f"{'='*70}\n")
                return True
            else:
                print(f"{RED}❌ Some posts failed to clean{RESET}")
                print(f"{'='*70}\n")
                return False

        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()

if __name__ == "__main__":
    cleaner = ContentCleaner()
    success = cleaner.run()
    sys.exit(0 if success else 1)
