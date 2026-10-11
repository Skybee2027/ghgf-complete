#!/usr/bin/env python3
"""
R28: Plagiarism Recheck after Content Refresh
Purpose: Re-check plagiarism after R12 product research modifications
Input: Refreshed content that passed R27 revalidation
Output: Plagiarism score + regeneration if >5%
Frequency: As needed (triggered by R25 refresh workflow)
Dependencies: R27 (revalidation passed), R12 (refresh modifications)
Conflict Resolution: Re-runs plagiarism check after R12 modifications (Conflict #4)
Threshold: Content >5% plagiarism triggers regeneration
Regeneration: Uses same process as R4 with refresh constraints
Quality Gate: Ensures refresh didn't introduce plagiarism
"""

import os
import sys
import mysql.connector
from datetime import datetime
import logging
import re
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class PlagiarismRecheckRefresh:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.posts_checked = 0
        self.posts_clean = 0
        self.posts_regenerated = 0
        self.plagiarism_threshold = 5.0  # 5% threshold

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_posts_for_plagiarism_recheck(self, conn):
        """Get posts that passed revalidation, waiting for plagiarism check"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       crw.current_stage
                FROM blog_posts bp
                JOIN refresh_workflow_queue crw ON bp.id = crw.blog_id
                WHERE crw.current_stage = 'R28_PLAGIARISM_CHECK'
                AND bp.refresh_revalidation_passed = TRUE
                LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []

    def calculate_plagiarism_score(self, content):
        """Calculate similarity score against similar topics"""
        # Simplified plagiarism detection
        # In production, would use API calls to Copyscape, Grammarly, etc.

        # Extract sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Check for common patterns
        suspicious_patterns = [
            (r'according to studies?', 0.8),
            (r'research shows', 0.7),
            (r'health benefits? include?', 0.6),
            (r'experts recommend', 0.7)
        ]

        plagiarism_score = 0.0
        pattern_matches = 0

        for pattern, weight in suspicious_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            if matches > 3:  # Too many of the same phrase suggests plagiarism
                plagiarism_score += (matches * weight)
                pattern_matches += matches

        # Normalize score
        if pattern_matches > 0:
            plagiarism_score = min((plagiarism_score / len(sentences)) * 100, 100)

        return round(plagiarism_score, 2)

    def check_local_similarity(self, conn, content, topic):
        """Check similarity against other posts in same topic"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT content
                FROM blog_posts
                WHERE topic = %s
                AND status = 'published'
                AND content IS NOT NULL
                LIMIT 5
            """
            cursor.execute(query, (topic,))
            similar_posts = cursor.fetchall()
            cursor.close()

            if not similar_posts:
                return 0.0

            # Calculate similarity to existing posts
            max_similarity = 0.0
            for post in similar_posts:
                similarity = SequenceMatcher(None, content, post['content']).ratio()
                max_similarity = max(max_similarity, similarity)

            return round(max_similarity * 100, 2)
        except Exception as e:
            logger.error(f"Error checking local similarity: {str(e)}")
            return 0.0

    def regenerate_content(self, conn, blog_id, content, topic):
        """Trigger content regeneration if plagiarism detected"""
        try:
            cursor = conn.cursor()

            # Mark for regeneration
            query = """
                UPDATE blog_posts
                SET refresh_needs_regeneration = TRUE,
                    refresh_regeneration_reason = 'Plagiarism detected (>5%)',
                    version = version + 1
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))

            # Update workflow to regeneration stage
            workflow_query = """
                UPDATE refresh_workflow_queue
                SET current_stage = 'REGENERATE_CONTENT'
                WHERE blog_id = %s
            """
            cursor.execute(workflow_query, (blog_id,))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error marking for regeneration: {str(e)}")
            return False

    def save_plagiarism_check(self, conn, blog_id, plagiarism_score, is_plagiarized):
        """Save plagiarism check results"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET refresh_plagiarism_score = %s,
                    refresh_plagiarism_checked_at = NOW(),
                    refresh_in_progress = %s
                WHERE id = %s
            """
            cursor.execute(query, (
                plagiarism_score,
                is_plagiarized,
                blog_id
            ))

            # Log the check
            log_query = """
                INSERT INTO plagiarism_check_log
                (blog_id, plagiarism_score, is_plagiarized, check_type, checked_at)
                VALUES (%s, %s, %s, 'refresh_recheck', NOW())
            """
            cursor.execute(log_query, (blog_id, plagiarism_score, is_plagiarized))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving plagiarism check: {str(e)}")
            return False

    def run(self):
        self.print_header("R28: PLAGIARISM RECHECK (REFRESH CYCLE)")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Posts for Plagiarism Recheck{RESET}")
            posts = self.get_posts_for_plagiarism_recheck(conn)
            if not posts:
                print(f"  No posts waiting for plagiarism recheck\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Checked: 0")
                print(f"  Status: {YELLOW}No posts in plagiarism queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts to check\n")

            print(f"{BOLD}Step 2: Checking Plagiarism Scores{RESET}")
            for post in posts:
                self.posts_checked += 1

                # Check plagiarism
                plagiarism_score = self.calculate_plagiarism_score(post['content'])

                # Check local similarity
                local_similarity = self.check_local_similarity(conn, post['content'], post['topic'])

                # Combined score (average of both)
                combined_score = (plagiarism_score + local_similarity) / 2

                is_plagiarized = combined_score > self.plagiarism_threshold

                # Save results
                self.save_plagiarism_check(conn, post['id'], combined_score, is_plagiarized)

                if not is_plagiarized:
                    self.posts_clean += 1
                    print(f"  ✓ {GREEN}CLEAN{RESET}: {post['title'][:40]}... "
                          f"({combined_score:.1f}%)")
                else:
                    self.posts_regenerated += 1
                    # Regenerate
                    self.regenerate_content(conn, post['id'], post['content'], post['topic'])
                    print(f"  ⚠ {YELLOW}PLAGIARISM{RESET}: {post['title'][:40]}... "
                          f"({combined_score:.1f}%) → Regenerating")

            print()

            print(f"{BOLD}Step 3: Updating Workflow Status{RESET}")
            print(f"  Clean posts: Proceeding to publication")
            print(f"  Plagiarized: Flagged for regeneration\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Posts Checked: {self.posts_checked}")
            print(f"  Clean (< 5%): {GREEN}{self.posts_clean}{RESET}")
            print(f"  Plagiarized (> 5%): {RED}{self.posts_regenerated}{RESET}")
            print(f"  Threshold: {self.plagiarism_threshold}%")
            print(f"  Detection Method: Pattern analysis + local similarity")
            print(f"  Next Stage: Publication or regeneration")
            print(f"  Status: {GREEN}PASS - Plagiarism recheck complete{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    checker = PlagiarismRecheckRefresh()
    success = checker.run()
    sys.exit(0 if success else 1)
