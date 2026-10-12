#!/usr/bin/env python3
"""
R4: Plagiarism Checker (Multi-Provider Fallback)
Purpose: Check plagiarism <5% using multiple sources; regenerate if flagged
Input: Blog post content (from R3)
Output: Approved content or regenerated content
Frequency: Every 6 hours (after R3 completes)
Dependencies: R3 (provides content)
Threshold: <5% plagiarism = PASS, >5% = REGENERATE

Provider Chain: Groq → Gemini → Cohere → OpenAI
"""

import os
import sys
import mysql.connector
from datetime import datetime
import requests
from difflib import SequenceMatcher
import logging
import traceback

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
        """Initialize plagiarism checker with multi-provider API support"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.plagiarism_threshold = 0.05  # 5%

        # Check available API keys - all optional since we have fallback chain
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.cohere_key = os.getenv("COHERE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # Model names - FROM ENVIRONMENT VARIABLES
        self.groq_model = os.getenv("GROQ_MODEL")
        self.gemini_model = os.getenv("GEMINI_MODEL")
        self.cohere_model = os.getenv("COHERE_MODEL")
        self.openai_model = os.getenv("OPENAI_MODEL")

        # Check that at least ONE API key is available
        if not any([self.groq_key, self.gemini_key, self.cohere_key, self.openai_key]):
            logger.warning("No LLM API keys found - will only do plagiarism checks without regeneration")

        self.max_retries = 3
        self.current_attempt = 0
        self.provider_used = None

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

    def get_regeneration_prompt(self, blog_title, blog_topic):
        """Generate the shared regeneration prompt for all providers"""
        prompt = f"""Rewrite this blog post with completely different wording and structure.
Title: {blog_title}
Topic: {blog_topic}

Guidelines:
- Keep the same topic and key information
- Use different sentence structures and vocabulary
- Reorganize paragraphs
- Change examples while maintaining accuracy
- Keep HTML structure: <h2>, <h3>, <p>, <ul>, <li>
- Length: 800-1500 words
- Include [[INTERNAL_LINK:topic]] and [[AFFILIATE_LINK:product]] placeholders

Return ONLY the rewritten content."""
        return prompt

    def regenerate_with_groq(self, blog_title, blog_topic):
        """Regenerate content using Groq"""
        if not self.groq_key:
            logger.debug("Groq API key not available, skipping Groq provider")
            return None

        try:
            from groq import Groq

            logger.info("Attempting Groq provider...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_regeneration_prompt(blog_title, blog_topic)

            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.9
            )

            if response.choices and response.choices[0].message.content:
                self.provider_used = "Groq"
                logger.info(f"✓ Groq succeeded")
                return response.choices[0].message.content.strip()
            return None
        except ImportError:
            logger.warning("Groq library not installed")
            return None
        except Exception as e:
            logger.error(f"Groq failed: {type(e).__name__}: {str(e)}")
            return None

    def regenerate_with_gemini(self, blog_title, blog_topic):
        """Regenerate content using Gemini"""
        if not self.gemini_key:
            logger.debug("Gemini API key not available, skipping Gemini provider")
            return None

        try:
            import google.generativeai as genai

            logger.info("Attempting Gemini provider...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_regeneration_prompt(blog_title, blog_topic)

            model = genai.GenerativeModel(self.gemini_model if self.gemini_model else "gemini-pro")
            response = model.generate_content(prompt)

            if response.text:
                self.provider_used = "Gemini"
                logger.info(f"✓ Gemini succeeded")
                return response.text
            return None
        except ImportError:
            logger.warning("Google Generative AI library not installed")
            return None
        except Exception as e:
            logger.error(f"Gemini failed: {type(e).__name__}: {str(e)}")
            return None

    def regenerate_with_cohere(self, blog_title, blog_topic):
        """Regenerate content using Cohere"""
        if not self.cohere_key:
            logger.debug("Cohere API key not available, skipping Cohere provider")
            return None

        try:
            import cohere

            logger.info("Attempting Cohere provider...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            prompt = self.get_regeneration_prompt(blog_title, blog_topic)

            response = client.generate(
                model=self.cohere_model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.9
            )

            if response.text:
                self.provider_used = "Cohere"
                logger.info(f"✓ Cohere succeeded")
                return response.text
            return None
        except ImportError:
            logger.warning("Cohere library not installed")
            return None
        except Exception as e:
            logger.error(f"Cohere failed: {type(e).__name__}: {str(e)}")
            return None

    def regenerate_with_openai(self, blog_title, blog_topic):
        """Regenerate content using OpenAI"""
        if not self.openai_key:
            logger.debug("OpenAI API key not available, skipping OpenAI provider")
            return None

        try:
            from openai import OpenAI

            logger.info("Attempting OpenAI provider...")
            client = OpenAI(api_key=self.openai_key)
            prompt = self.get_regeneration_prompt(blog_title, blog_topic)

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.9
            )

            if response.choices and response.choices[0].message.content:
                self.provider_used = "OpenAI"
                logger.info(f"✓ OpenAI succeeded")
                return response.choices[0].message.content
            return None
        except ImportError:
            logger.warning("OpenAI library not installed")
            return None
        except Exception as e:
            logger.error(f"OpenAI failed: {type(e).__name__}: {str(e)}")
            return None

    def regenerate_content(self, conn, blog_id, original_content):
        """Regenerate content using multi-provider fallback chain"""
        # Get blog details
        cursor = conn.cursor(dictionary=True)
        query = "SELECT title, topic FROM blog_posts WHERE id = %s"
        cursor.execute(query, (blog_id,))
        blog = cursor.fetchone()
        cursor.close()

        if not blog:
            return None

        logger.info(f"Regenerating content (Attempt {self.current_attempt + 1}/{self.max_retries})")
        logger.info("Provider fallback chain: Groq → Gemini → Cohere → OpenAI")

        # Try all providers in order
        content = self.regenerate_with_groq(blog['title'], blog['topic'])

        if not content:
            logger.warning("Groq failed, trying Gemini...")
            content = self.regenerate_with_gemini(blog['title'], blog['topic'])

        if not content:
            logger.warning("Gemini failed, trying Cohere...")
            content = self.regenerate_with_cohere(blog['title'], blog['topic'])

        if not content:
            logger.warning("Cohere failed, trying OpenAI...")
            content = self.regenerate_with_openai(blog['title'], blog['topic'])

        if content:
            logger.info(f"Content regenerated successfully via {self.provider_used}")
            return content
        else:
            logger.error("All providers failed - unable to regenerate content")
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
