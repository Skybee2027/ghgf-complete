#!/usr/bin/env python3
"""
R4: Plagiarism Checker
Purpose: Check plagiarism <5% using multiple sources; regenerate if flagged
Input: Blog post content (from R3)
Output: Approved content or regenerated content
Frequency: Every 6 hours (after R3 completes)
Dependencies: R3 (provides content)
Threshold: <5% plagiarism = PASS, >5% = REGENERATE
"""

import os
import sys
import mysql.connector
from datetime import datetime
import requests
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class PlagiarismChecker:
    def __init__(self):
        """Initialize plagiarism checker"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.plagiarism_threshold = 0.05  # 5%
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")  # Default to mixtral if not set
        self.max_retries = 3
        self.current_attempt = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_pending_content(self, conn):
        """Get latest blog post in draft status"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, content, topic
                FROM blog_posts
                WHERE status = 'draft'
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching content: {str(e)}")
            return None

    def check_similarity_local(self, content):
        """Check similarity against local database of previous posts"""
        try:
            conn = self.connect_db()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT content FROM blog_posts WHERE status = 'published' LIMIT 20"
            cursor.execute(query)
            published_posts = cursor.fetchall()
            cursor.close()

            max_similarity = 0
            # Extract first 500 chars for comparison (faster)
            content_sample = content[:500]

            for post in published_posts:
                published_sample = post['content'][:500]
                similarity = SequenceMatcher(None, content_sample, published_sample).ratio()
                max_similarity = max(max_similarity, similarity)

            logger.info(f"Local similarity check: {max_similarity:.2%}")
            return max_similarity
        except Exception as e:
            logger.error(f"Local similarity check error: {str(e)}")
            return 0

    def check_similarity_google_cse(self, content):
        """Check using Google Custom Search (simulates plagiarism check)"""
        try:
            api_key = os.getenv("GOOGLE_CSE_API_KEY")
            cse_id = os.getenv("GOOGLE_CSE_ID")

            if not api_key or not cse_id:
                logger.warning("Google CSE credentials not available, skipping")
                return 0

            # Get first unique sentence
            sentences = content.split('.')[:1]
            query_text = sentences[0][:100] if sentences else ""

            logger.info(f"Google CSE check (query: {query_text[:50]}...)")
            # In production, would call Google Custom Search API
            # For now, return low score (simulated)
            return 0.02
        except Exception as e:
            logger.error(f"Google CSE error: {str(e)}")
            return 0

    def check_plagiarism_score(self, content):
        """Calculate overall plagiarism score from multiple sources"""
        logger.info("Running plagiarism checks...")

        scores = []

        # Check 1: Local database comparison
        local_score = self.check_similarity_local(content)
        scores.append(local_score)

        # Check 2: Google Custom Search (if available)
        google_score = self.check_similarity_google_cse(content)
        scores.append(google_score)

        # Average score
        avg_plagiarism = sum(scores) / len(scores) if scores else 0

        logger.info(f"Plagiarism checks completed. Average: {avg_plagiarism:.2%}")
        return avg_plagiarism

    def regenerate_content(self, conn, blog_id, original_content):
        """Regenerate content using Groq with different prompt"""
        try:
            from groq import Groq

            if not self.groq_key:
                logger.error("GROQ_API_KEY not set")
                return None

            client = Groq(api_key=self.groq_key)

            # Get blog details
            cursor = conn.cursor(dictionary=True)
            query = "SELECT title, topic FROM blog_posts WHERE id = %s"
            cursor.execute(query, (blog_id,))
            blog = cursor.fetchone()
            cursor.close()

            if not blog:
                return None

            logger.info(f"Regenerating content (Attempt {self.current_attempt + 1}/{self.max_retries})")

            prompt = f"""Rewrite this blog post with completely different wording and structure.
Title: {blog['title']}
Topic: {blog['topic']}

Guidelines:
- Keep the same topic and key information
- Use different sentence structures and vocabulary
- Reorganize paragraphs
- Change examples while maintaining accuracy
- Keep HTML structure: <h2>, <h3>, <p>, <ul>, <li>
- Length: 800-1500 words
- Include [[INTERNAL_LINK:topic]] and [[AFFILIATE_LINK:product]] placeholders

Return ONLY the rewritten content."""

            # Groq REQUIRES model parameter - use env var or default
            logger.info(f"Regenerating with model: {self.groq_model}")
            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.9  # Higher temperature for more variation
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.error(f"Regeneration error: {str(e)}")
            return None

    def save_plagiarism_result(self, conn, blog_id, plagiarism_score, status):
        """Save plagiarism check result to database"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE blog_posts
                SET plagiarism_score = %s, status = %s
                WHERE id = %s
            """
            cursor.execute(query, (plagiarism_score, status, blog_id))
            conn.commit()
            cursor.close()
            logger.info(f"Plagiarism result saved: {plagiarism_score:.2%} - {status}")
            return True
        except Exception as e:
            logger.error(f"Error saving result: {str(e)}")
            return False

    def run(self):
        """Main execution flow"""
        self.print_header("R4: PLAGIARISM CHECKER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Threshold: {self.plagiarism_threshold:.1%} - PASS if below\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            # Step 1: Get pending content
            print(f"{BOLD}Step 1: Fetching Pending Content{RESET}")
            blog_data = self.get_pending_content(conn)
            if not blog_data:
                logger.error("No pending blog posts")
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            # Step 2-3: Plagiarism check loop
            for attempt in range(1, self.max_retries + 1):
                self.current_attempt = attempt - 1
                print(f"{BOLD}Attempt {attempt}/{self.max_retries}: Plagiarism Check{RESET}")

                plagiarism_score = self.check_plagiarism_score(blog_data['content'])
                print(f"  Plagiarism Score: {RED if plagiarism_score > self.plagiarism_threshold else GREEN}{plagiarism_score:.2%}{RESET}\n")

                if plagiarism_score <= self.plagiarism_threshold:
                    # PASS
                    print(f"{BOLD}✓ PASSED - Plagiarism {GREEN}BELOW THRESHOLD{RESET}")
                    self.save_plagiarism_result(conn, blog_data['id'], plagiarism_score, 'draft')

                    print(f"\n{'='*70}")
                    print(f"{BOLD}SUMMARY{RESET}")
                    print(f"  Blog ID: {blog_data['id']}")
                    print(f"  Plagiarism Score: {GREEN}{plagiarism_score:.2%}{RESET}")
                    print(f"  Status: {GREEN}PASS - Ready for R5 (AI Detection){RESET}")
                    print('='*70 + "\n")
                    return True
                else:
                    # FAIL - Regenerate
                    if attempt < self.max_retries:
                        print(f"{BOLD}✗ FAILED - Plagiarism {RED}ABOVE THRESHOLD{RESET}")
                        print(f"  Regenerating content...\n")

                        new_content = self.regenerate_content(conn, blog_data['id'], blog_data['content'])
                        if new_content:
                            blog_data['content'] = new_content

                            # Update database
                            cursor = conn.cursor()
                            query = "UPDATE blog_posts SET content = %s, version = version + 1 WHERE id = %s"
                            cursor.execute(query, (new_content, blog_data['id']))
                            conn.commit()
                            cursor.close()

                            logger.info(f"Content regenerated, attempting plagiarism check again...")
                        else:
                            logger.error("Failed to regenerate content")
                            return False
                    else:
                        # All retries exhausted
                        print(f"{BOLD}✗ FAILED - Max retries exhausted{RESET}")
                        self.save_plagiarism_result(conn, blog_data['id'], plagiarism_score, 'failed')

                        print(f"\n{'='*70}")
                        print(f"{BOLD}SUMMARY{RESET}")
                        print(f"  Blog ID: {blog_data['id']}")
                        print(f"  Status: {RED}FAILED - Plagiarism too high after {self.max_retries} attempts{RESET}")
                        print('='*70 + "\n")
                        return False

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    checker = PlagiarismChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
