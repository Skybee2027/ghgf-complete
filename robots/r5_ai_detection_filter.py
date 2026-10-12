#!/usr/bin/env python3
"""
R5: AI Detection Filter (Multi-Provider Fallback)
Purpose: Detect AI-written content <70%; regenerate if flagged
Input: Blog post content (from R4 plagiarism check)
Output: Approved content or regenerated with human-like characteristics
Frequency: Every 6 hours (after R4 completes)
Dependencies: R4 (provides content)
Threshold: <70% AI = PASS, >70% = REGENERATE with human-like characteristics

Provider Chain: Groq → Gemini → Cohere → OpenAI
"""

import os
import sys
import mysql.connector
from datetime import datetime
import re
import logging
import traceback
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class AIDetectionFilter:
    def __init__(self):
        """Initialize AI detection filter with multi-provider API support"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.ai_threshold = 0.70  # 70%

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
            logger.warning("No LLM API keys found - will only do AI detection without regeneration")

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
        """Get latest blog post in draft status (already plagiarism checked)"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, content, topic, plagiarism_score
                FROM blog_posts
                WHERE status = 'draft' AND plagiarism_score >= 0
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

    def analyze_sentence_length_variance(self, content):
        """Analyze sentence length variance - AI tends to have consistent lengths"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 3:
            return 0.5

        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        variance = sum((x - avg_length) ** 2 for x in lengths) / len(lengths)

        # High variance = more human-like. AI texts have low variance
        # Normalize to 0-1 scale where 1 = very human-like
        variance_score = min(variance / 20, 1.0)

        logger.info(f"Sentence variance: {variance:.2f} (humanness: {variance_score:.2%})")
        return variance_score

    def analyze_word_frequency(self, content):
        """Analyze word frequency distribution - AI overuses certain words"""
        words = re.findall(r'\b\w+\b', content.lower())
        words = [w for w in words if len(w) > 3]  # Skip short words

        word_counts = Counter(words)
        total_words = len(words)

        # Top 10 words
        top_10_freq = sum(count for word, count in word_counts.most_common(10)) / total_words

        # Human texts: top 10 words ≈ 10-15% of total
        # AI texts: top 10 words ≈ 25%+
        if top_10_freq < 0.15:
            frequency_score = 0.9  # Very human-like
        elif top_10_freq < 0.20:
            frequency_score = 0.7
        elif top_10_freq < 0.25:
            frequency_score = 0.5
        else:
            frequency_score = 0.2  # Likely AI

        logger.info(f"Word frequency (top 10): {top_10_freq:.2%} (humanness: {frequency_score:.2%})")
        return frequency_score

    def analyze_contractions_and_colloquialisms(self, content):
        """Analyze use of contractions - AI avoids them"""
        # Count contractions
        contractions = re.findall(r"\b(?:can't|won't|don't|shouldn't|isn't|aren't|wasn't|weren't|haven't|hasn't|hadn't|isn't|aren't|wasn't|weren't|don't|doesn't|didn't|won't|wouldn't|shan't|shouldn't|can't|couldn't|mustn't|let's|that's|who's|what's|where's|when's|why's|how's|I'm|you're|we're|they're|he's|she's|it's|I've|you've|we've|they've|I'd|you'd|we'd|they'd|he'd|she'd|it'd)\b", content)

        words = re.findall(r'\b\w+\b', content)
        contraction_ratio = len(contractions) / len(words) if words else 0

        # Human texts: 5-15% contractions
        # AI texts: 0-5% contractions
        if contraction_ratio > 0.10:
            colloquialism_score = 0.9
        elif contraction_ratio > 0.05:
            colloquialism_score = 0.7
        else:
            colloquialism_score = 0.3

        logger.info(f"Contractions: {contraction_ratio:.2%} (humanness: {colloquialism_score:.2%})")
        return colloquialism_score

    def analyze_passive_voice(self, content):
        """Analyze passive voice usage - AI tends to use more passive"""
        passive_patterns = re.findall(r'\b(?:is|are|was|were|be|been)\s+\w+(?:ed|en)\b', content)

        sentences = re.split(r'[.!?]+', content)
        passive_ratio = len(passive_patterns) / len(sentences) if sentences else 0

        # Human texts: 10-20% passive voice
        # AI texts: 25%+
        if passive_ratio < 0.15:
            passive_score = 0.9
        elif passive_ratio < 0.20:
            passive_score = 0.7
        elif passive_ratio < 0.25:
            passive_score = 0.5
        else:
            passive_score = 0.2

        logger.info(f"Passive voice: {passive_ratio:.2%} (humanness: {passive_score:.2%})")
        return passive_score

    def calculate_ai_score(self, content):
        """Calculate overall AI detection score (0-1, where 1 = 100% AI)"""
        logger.info("Running AI detection analysis...")

        # Individual scores (0-1, where 1 = human-like)
        variance_score = self.analyze_sentence_length_variance(content)
        frequency_score = self.analyze_word_frequency(content)
        colloquialism_score = self.analyze_contractions_and_colloquialisms(content)
        passive_score = self.analyze_passive_voice(content)

        # Average human-like score
        human_score = (variance_score + frequency_score + colloquialism_score + passive_score) / 4

        # Convert to AI score (inverted)
        ai_score = 1 - human_score

        logger.info(f"Final AI Detection Score: {ai_score:.2%}")
        return ai_score

    def get_human_prompt(self, blog_title, blog_topic):
        """Generate the shared human-like regeneration prompt for all providers"""
        prompt = f"""Rewrite this blog post to sound MORE human and natural.
Title: {blog_title}
Topic: {blog_topic}

Make it sound HUMAN by:
1. Use contractions: can't, won't, don't, I'm, you're, etc (10-15% of text)
2. Vary sentence length: Mix short (5-10 words) and long (20-30 words) sentences
3. Use active voice (not passive): "We found that" not "It was found"
4. Add personal touches: "From my experience...", "I've noticed..."
5. Use casual connectors: "anyway", "honestly", "basically", "actually"
6. Avoid repetition: Don't use same words in consecutive sentences
7. Include rhetorical questions: "What if...?", "Did you know...?"
8. Keep HTML structure: <h2>, <h3>, <p>, <ul>, <li>
9. Length: 800-1500 words
10. Include [[INTERNAL_LINK:topic]] and [[AFFILIATE_LINK:product]] placeholders

Make it feel like written by a real person, not an AI."""
        return prompt

    def regenerate_with_groq_human(self, blog_title, blog_topic):
        """Regenerate with human characteristics using Groq"""
        if not self.groq_key:
            logger.debug("Groq API key not available, skipping Groq provider")
            return None

        try:
            from groq import Groq

            logger.info("Attempting Groq provider...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_human_prompt(blog_title, blog_topic)

            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.85
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

    def regenerate_with_gemini_human(self, blog_title, blog_topic):
        """Regenerate with human characteristics using Gemini"""
        if not self.gemini_key:
            logger.debug("Gemini API key not available, skipping Gemini provider")
            return None

        try:
            import google.generativeai as genai

            logger.info("Attempting Gemini provider...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_human_prompt(blog_title, blog_topic)

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

    def regenerate_with_cohere_human(self, blog_title, blog_topic):
        """Regenerate with human characteristics using Cohere"""
        if not self.cohere_key:
            logger.debug("Cohere API key not available, skipping Cohere provider")
            return None

        try:
            import cohere

            logger.info("Attempting Cohere provider...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            prompt = self.get_human_prompt(blog_title, blog_topic)

            response = client.generate(
                model=self.cohere_model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.85
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

    def regenerate_with_openai_human(self, blog_title, blog_topic):
        """Regenerate with human characteristics using OpenAI"""
        if not self.openai_key:
            logger.debug("OpenAI API key not available, skipping OpenAI provider")
            return None

        try:
            from openai import OpenAI

            logger.info("Attempting OpenAI provider...")
            client = OpenAI(api_key=self.openai_key)
            prompt = self.get_human_prompt(blog_title, blog_topic)

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.85
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

    def regenerate_with_human_characteristics(self, conn, blog_id, original_content):
        """Regenerate content with human-like characteristics using multi-provider fallback"""
        cursor = conn.cursor(dictionary=True)
        query = "SELECT title, topic FROM blog_posts WHERE id = %s"
        cursor.execute(query, (blog_id,))
        blog = cursor.fetchone()
        cursor.close()

        logger.info(f"Regenerating with human-like characteristics (Attempt {self.current_attempt + 1})")
        logger.info("Provider fallback chain: Groq → Gemini → Cohere → OpenAI")

        # Try all providers in order
        content = self.regenerate_with_groq_human(blog['title'], blog['topic'])

        if not content:
            logger.warning("Groq failed, trying Gemini...")
            content = self.regenerate_with_gemini_human(blog['title'], blog['topic'])

        if not content:
            logger.warning("Gemini failed, trying Cohere...")
            content = self.regenerate_with_cohere_human(blog['title'], blog['topic'])

        if not content:
            logger.warning("Cohere failed, trying OpenAI...")
            content = self.regenerate_with_openai_human(blog['title'], blog['topic'])

        if content:
            logger.info(f"Content regenerated successfully via {self.provider_used}")
            return content
        else:
            logger.error("All providers failed - unable to regenerate content")
            return None

    def save_ai_detection_result(self, conn, blog_id, ai_score, status):
        """Save AI detection result to database"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE blog_posts
                SET ai_detection_score = %s, status = %s
                WHERE id = %s
            """
            cursor.execute(query, (ai_score, status, blog_id))
            conn.commit()
            cursor.close()
            logger.info(f"AI detection result saved: {ai_score:.2%} - {status}")
            return True
        except Exception as e:
            logger.error(f"Error saving result: {str(e)}")
            return False

    def run(self):
        """Main execution flow"""
        self.print_header("R5: AI DETECTION FILTER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Threshold: {self.ai_threshold:.1%} - PASS if below\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Content from R4{RESET}")
            blog_data = self.get_pending_content(conn)
            if not blog_data:
                logger.error("No pending blog posts")
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            for attempt in range(1, self.max_retries + 1):
                self.current_attempt = attempt - 1
                print(f"{BOLD}Attempt {attempt}/{self.max_retries}: AI Detection Analysis{RESET}\n")

                ai_score = self.calculate_ai_score(blog_data['content'])
                print(f"  AI Detection Score: {RED if ai_score > self.ai_threshold else GREEN}{ai_score:.2%}{RESET}\n")

                if ai_score <= self.ai_threshold:
                    # PASS
                    print(f"{BOLD}✓ PASSED - Content {GREEN}HUMAN-LIKE{RESET}")
                    self.save_ai_detection_result(conn, blog_data['id'], ai_score, 'draft')

                    print(f"\n{'='*70}")
                    print(f"{BOLD}SUMMARY{RESET}")
                    print(f"  Blog ID: {blog_data['id']}")
                    print(f"  AI Score: {GREEN}{ai_score:.2%}{RESET}")
                    print(f"  Status: {GREEN}PASS - Ready for R6 (Keyword Optimization){RESET}")
                    print('='*70 + "\n")
                    return True
                else:
                    # FAIL - Regenerate
                    if attempt < self.max_retries:
                        print(f"{BOLD}✗ FAILED - Content {RED}TOO AI-LIKE{RESET}")
                        print(f"  Regenerating with human characteristics...\n")

                        new_content = self.regenerate_with_human_characteristics(conn, blog_data['id'], blog_data['content'])
                        if new_content:
                            blog_data['content'] = new_content

                            cursor = conn.cursor()
                            query = "UPDATE blog_posts SET content = %s, version = version + 1 WHERE id = %s"
                            cursor.execute(query, (new_content, blog_data['id']))
                            conn.commit()
                            cursor.close()

                            logger.info("Content regenerated, retesting...")
                        else:
                            return False
                    else:
                        print(f"{BOLD}✗ FAILED - Max retries exhausted{RESET}")
                        self.save_ai_detection_result(conn, blog_data['id'], ai_score, 'failed')

                        print(f"\n{'='*70}")
                        print(f"{BOLD}SUMMARY{RESET}")
                        print(f"  Blog ID: {blog_data['id']}")
                        print(f"  Status: {RED}FAILED - Too AI-like after {self.max_retries} attempts{RESET}")
                        print('='*70 + "\n")
                        return False

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    detector = AIDetectionFilter()
    success = detector.run()
    sys.exit(0 if success else 1)
