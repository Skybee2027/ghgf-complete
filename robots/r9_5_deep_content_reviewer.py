#!/usr/bin/env python3
"""
R9.5: Deep Content Reviewer (Editorial Quality Check)
Purpose: AI-powered deep reading to verify blog quality beyond technical checks
Input: Blog post content (from R10 revalidation)
Output: Editorial quality score + detailed feedback for human or auto-approval
Frequency: Every 6 hours (after R10, before R11)
Dependencies: R10 (revalidation complete)

CHECKS THAT R9/R10 MISS:
✓ Does the blog actually make sense?
✓ Is the advice accurate/helpful?
✓ Does the logic flow properly?
✓ Are affiliate links relevant to content?
✓ Is the tone consistent?
✓ Does it actually answer the reader's question?

Provider Chain: Groq → Gemini → Cohere → OpenAI
"""

import os
import sys
import json
import mysql.connector
from datetime import datetime
import logging
import traceback

# Setup logging
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
BLUE = '\033[94m'


class DeepContentReviewer:
    def __init__(self):
        """Initialize deep content reviewer with multi-provider LLM support"""
        logger.info("=" * 70)
        logger.info("Initializing R9.5: Deep Content Reviewer")
        logger.info("=" * 70)

        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        # LLM API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.cohere_key = os.getenv("COHERE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # Model names
        self.groq_model = os.getenv("GROQ_MODEL")
        self.gemini_model = os.getenv("GEMINI_MODEL")
        self.cohere_model = os.getenv("COHERE_MODEL")
        self.openai_model = os.getenv("OPENAI_MODEL")

        if not any([self.groq_key, self.gemini_key, self.cohere_key, self.openai_key]):
            logger.error("CRITICAL: No API keys found!")
            sys.exit(1)

        logger.info("✓ LLM providers configured (multi-provider fallback enabled)")

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_pending_content(self, conn):
        """Get latest draft blog post (should be from R10)"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, content, topic, created_at
                FROM blog_posts
                WHERE status = 'draft'
                AND readability_score IS NOT NULL
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

    def review_with_groq(self, blog):
        """Review content using Groq"""
        try:
            import requests

            prompt = self._build_review_prompt(blog)

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={
                    "model": self.groq_model or "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.warning(f"Groq API error: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Groq review failed: {str(e)}")
            return None

    def review_with_gemini(self, blog):
        """Review content using Google Gemini"""
        try:
            import requests

            prompt = self._build_review_prompt(blog)

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                headers={"x-goog-api-key": self.gemini_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1000
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.warning(f"Gemini API error: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Gemini review failed: {str(e)}")
            return None

    def review_with_cohere(self, blog):
        """Review content using Cohere"""
        try:
            import requests

            prompt = self._build_review_prompt(blog)

            response = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers={"Authorization": f"Bearer {self.cohere_key}"},
                json={
                    "model": self.cohere_model or "command-a-plus-05-2026",
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result['generations'][0]['text']
            else:
                logger.warning(f"Cohere API error: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Cohere review failed: {str(e)}")
            return None

    def review_with_openai(self, blog):
        """Review content using OpenAI"""
        try:
            import requests

            prompt = self._build_review_prompt(blog)

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": self.openai_model or "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.warning(f"OpenAI API error: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"OpenAI review failed: {str(e)}")
            return None

    def _build_review_prompt(self, blog):
        """Build comprehensive review prompt"""
        prompt = f"""
EDITORIAL QUALITY REVIEW - Rate each criterion 1-10:

BLOG TITLE: {blog['title']}
TOPIC: {blog['topic']}

CONTENT:
{blog['content'][:2000]}...

EVALUATE ON THESE CRITERIA (respond in JSON format):
{{
  "makes_sense": {{"score": 1-10, "reason": "Does the blog flow logically and make sense?"}},
  "accuracy": {{"score": 1-10, "reason": "Is the advice accurate and helpful?"}},
  "logic_flow": {{"score": 1-10, "reason": "Does the argument flow properly from start to end?"}},
  "answers_question": {{"score": 1-10, "reason": "Does it answer the reader's main question?"}},
  "affiliate_relevance": {{"score": 1-10, "reason": "Are any product recommendations relevant to topic?"}},
  "tone_consistency": {{"score": 1-10, "reason": "Is the tone consistent throughout?"}},
  "provides_value": {{"score": 1-10, "reason": "Would a reader find this valuable/useful?"}},
  "overall": {{"score": 1-10, "reason": "Overall editorial quality assessment"}},
  "major_issues": "List any critical issues found",
  "recommendations": "List 2-3 specific improvements if score < 7"
}}

RESPOND ONLY WITH JSON, NO OTHER TEXT.
"""
        return prompt

    def parse_review_response(self, response_text):
        """Parse LLM review response"""
        try:
            # Extract JSON from response
            import json

            # Try to find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in LLM response")
                return None

            json_str = response_text[start_idx:end_idx]
            review_data = json.loads(json_str)
            return review_data
        except Exception as e:
            logger.error(f"Failed to parse review response: {str(e)}")
            return None

    def calculate_overall_score(self, review_data):
        """Calculate weighted editorial score"""
        if not review_data:
            return 0

        try:
            scores = [
                review_data.get('makes_sense', {}).get('score', 5),
                review_data.get('accuracy', {}).get('score', 5),
                review_data.get('logic_flow', {}).get('score', 5),
                review_data.get('answers_question', {}).get('score', 5),
                review_data.get('affiliate_relevance', {}).get('score', 5),
                review_data.get('tone_consistency', {}).get('score', 5),
                review_data.get('provides_value', {}).get('score', 5),
            ]

            # Weight: logic/accuracy/value more important
            weighted_score = (
                scores[0] * 1.2 +  # makes_sense
                scores[1] * 1.3 +  # accuracy
                scores[2] * 1.2 +  # logic_flow
                scores[3] * 1.3 +  # answers_question
                scores[4] * 0.8 +  # affiliate_relevance
                scores[5] * 1.0 +  # tone_consistency
                scores[6] * 1.2    # provides_value
            ) / (1.2 + 1.3 + 1.2 + 1.3 + 0.8 + 1.0 + 1.2)

            return round(weighted_score, 1)
        except Exception as e:
            logger.error(f"Score calculation error: {str(e)}")
            return 0

    def perform_review(self, blog):
        """Run editorial review with multi-provider fallback"""
        self.print_header(f"Deep Content Review - {blog['title'][:50]}...")

        review_response = None
        provider_used = None

        # Try providers in order
        providers = [
            ("Groq", self.groq_key, self.review_with_groq),
            ("Gemini", self.gemini_key, self.review_with_gemini),
            ("Cohere", self.cohere_key, self.review_with_cohere),
            ("OpenAI", self.openai_key, self.review_with_openai),
        ]

        for provider_name, api_key, review_func in providers:
            if not api_key:
                logger.info(f"⊘ {provider_name} API key not set, skipping")
                continue

            logger.info(f"▶ Attempting review with {provider_name}...")
            try:
                review_response = review_func(blog)
                if review_response:
                    provider_used = provider_name
                    logger.info(f"✅ {provider_name} review successful")
                    break
            except Exception as e:
                logger.warning(f"⚠️  {provider_name} failed: {str(e)}")
                continue

        if not review_response:
            logger.error("❌ All providers failed")
            return None, None

        # Parse response
        review_data = self.parse_review_response(review_response)
        if not review_data:
            logger.error("❌ Could not parse review response")
            return None, None

        # Calculate score
        overall_score = self.calculate_overall_score(review_data)

        # Display results
        print(f"\n{BOLD}Editorial Quality Review Results{RESET}")
        print(f"Provider: {BLUE}{provider_used}{RESET}")
        print(f"Overall Score: {self._score_color(overall_score)}{overall_score}/10{RESET}")
        print(f"\nDetailed Scores:")

        for criterion in ['makes_sense', 'accuracy', 'logic_flow', 'answers_question',
                         'affiliate_relevance', 'tone_consistency', 'provides_value']:
            score = review_data.get(criterion, {}).get('score', 'N/A')
            reason = review_data.get(criterion, {}).get('reason', '')
            print(f"  • {criterion.replace('_', ' ').title()}: {score}/10")

        if review_data.get('major_issues'):
            print(f"\n{YELLOW}⚠️  Major Issues:{RESET}")
            print(f"  {review_data['major_issues']}")

        if review_data.get('recommendations'):
            print(f"\n{BLUE}💡 Recommendations:{RESET}")
            print(f"  {review_data['recommendations']}")

        return overall_score, review_data

    def _score_color(self, score):
        """Return color code for score"""
        if score >= 8:
            return GREEN
        elif score >= 6:
            return YELLOW
        else:
            return RED

    def save_review(self, conn, blog_id, score, review_data):
        """Save review results to database"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET editorial_quality_score = %s,
                    editorial_review = %s,
                    editorial_review_date = %s
                WHERE id = %s
            """

            import json
            review_json = json.dumps(review_data) if review_data else None

            cursor.execute(query, (score, review_json, datetime.now(), blog_id))
            conn.commit()
            cursor.close()

            logger.info(f"✓ Review saved for blog_id {blog_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving review: {str(e)}")
            return False

    def run(self):
        """Main execution"""
        print(f"\n{BOLD}R9.5: Deep Content Reviewer{RESET}")
        print(f"Editorial Quality Check - AI-Powered Content Review\n")

        conn = self.connect_db()
        if not conn:
            print(f"{RED}✗ Database connection failed{RESET}")
            return 1

        # Get pending content
        blog = self.get_pending_content(conn)
        if not blog:
            print(f"{YELLOW}No pending content to review{RESET}")
            conn.close()
            return 0

        print(f"{GREEN}Found blog post #{blog['id']}: {blog['title']}{RESET}\n")

        # Perform deep review
        score, review_data = self.perform_review(blog)

        if score is None:
            print(f"\n{RED}✗ Review failed{RESET}")
            conn.close()
            return 1

        # Save results
        self.save_review(conn, blog['id'], score, review_data)

        # Determine pass/fail
        PASS_THRESHOLD = 7.0

        print(f"\n{'='*70}")
        if score >= PASS_THRESHOLD:
            print(f"{GREEN}✅ EDITORIAL QUALITY PASSED{RESET}")
            print(f"Score {score}/10 exceeds threshold of {PASS_THRESHOLD}/10")
            print(f"Blog is ready for monetization & publishing steps")
            result = 0
        else:
            print(f"{RED}❌ EDITORIAL QUALITY FAILED{RESET}")
            print(f"Score {score}/10 below threshold of {PASS_THRESHOLD}/10")
            print(f"RECOMMENDATION: Manual review needed before publishing")
            result = 1

        print(f"{'='*70}\n")

        conn.close()
        return result


if __name__ == '__main__':
    reviewer = DeepContentReviewer()
    exit_code = reviewer.run()
    sys.exit(exit_code)
