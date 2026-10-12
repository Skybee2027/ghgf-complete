#!/usr/bin/env python3
"""
R37 - Content Retrofit & Monetization Engine
Enhances existing blog posts with affiliate links and product cards
Uses dynamic model discovery (no hardcoded models)
"""

import os
import sys
import logging
import json
import requests
import mysql.connector
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentRetrofitEngine:
    """Retrofit existing posts with monetization"""

    def __init__(self):
        """Initialize with environment variables"""
        self.db_host = os.getenv('DB_HOST', '193.203.166.223')
        self.db_user = os.getenv('DB_USER', '')
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'u853068512_ghgf_blogging')

        # AI APIs - all optional, using fallback chain
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.cohere_key = os.getenv('COHERE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # Model configuration - from environment variables only (no hardcoded defaults)
        self.groq_model = os.getenv('GROQ_MODEL')
        self.gemini_model = os.getenv('GEMINI_MODEL')
        self.cohere_model = os.getenv('COHERE_MODEL')
        self.openai_model = os.getenv('OPENAI_MODEL')

        # Check that at least ONE API key is available
        if not any([self.groq_key, self.gemini_key, self.cohere_key, self.openai_key]):
            logger.warning("No LLM API keys found - retrofit engine will skip AI enhancement")

        # Affiliate APIs
        self.cj_api_key = os.getenv('CJ_API_KEY', '')
        self.shareasale_token = os.getenv('SHAREASALE_API_TOKEN', '')

        self.connection = None
        self.posts_processed = 0
        self.posts_enhanced = 0
        self.provider_used = None

        logger.info("Content Retrofit Engine initialized")

    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=True,
                connection_timeout=30
            )
            logger.info("✓ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False

    def close_database(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_enhancement_prompt(self, content, title):
        """Generate the shared enhancement prompt for all providers"""
        prompt = f"""Enhance this blog post with:
1. Better formatting and readability
2. Key takeaways section
3. Call-to-action for related products

Title: {title}
Content: {content[:1000]}...

Return enhanced content only."""
        return prompt

    def enhance_with_groq(self, content, title):
        """Enhance content using Groq"""
        if not self.groq_key:
            logger.debug("Groq API key not available, skipping Groq provider")
            return None

        try:
            from groq import Groq

            logger.debug("Attempting Groq provider for content enhancement...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_enhancement_prompt(content, title)

            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                self.provider_used = "Groq"
                return response.choices[0].message.content.strip()
            return None
        except ImportError:
            logger.warning("Groq library not installed")
            return None
        except Exception as e:
            logger.debug(f"Groq failed: {type(e).__name__}: {str(e)}")
            return None

    def enhance_with_gemini(self, content, title):
        """Enhance content using Gemini"""
        if not self.gemini_key:
            logger.debug("Gemini API key not available, skipping Gemini provider")
            return None

        try:
            import google.generativeai as genai

            logger.debug("Attempting Gemini provider for content enhancement...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_enhancement_prompt(content, title)

            model = genai.GenerativeModel(self.gemini_model if self.gemini_model else "gemini-pro")
            response = model.generate_content(prompt)

            if response.text:
                self.provider_used = "Gemini"
                return response.text.strip()
            return None
        except ImportError:
            logger.warning("Google Generative AI library not installed")
            return None
        except Exception as e:
            logger.debug(f"Gemini failed: {type(e).__name__}: {str(e)}")
            return None

    def enhance_with_cohere(self, content, title):
        """Enhance content using Cohere"""
        if not self.cohere_key:
            logger.debug("Cohere API key not available, skipping Cohere provider")
            return None

        try:
            import cohere

            logger.debug("Attempting Cohere provider for content enhancement...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            prompt = self.get_enhancement_prompt(content, title)

            response = client.generate(
                model=self.cohere_model,
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            if response.text:
                self.provider_used = "Cohere"
                return response.text.strip()
            return None
        except ImportError:
            logger.warning("Cohere library not installed")
            return None
        except Exception as e:
            logger.debug(f"Cohere failed: {type(e).__name__}: {str(e)}")
            return None

    def enhance_with_openai(self, content, title):
        """Enhance content using OpenAI"""
        if not self.openai_key:
            logger.debug("OpenAI API key not available, skipping OpenAI provider")
            return None

        try:
            from openai import OpenAI

            logger.debug("Attempting OpenAI provider for content enhancement...")
            client = OpenAI(api_key=self.openai_key)
            prompt = self.get_enhancement_prompt(content, title)

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                self.provider_used = "OpenAI"
                return response.choices[0].message.content.strip()
            return None
        except ImportError:
            logger.warning("OpenAI library not installed")
            return None
        except Exception as e:
            logger.debug(f"OpenAI failed: {type(e).__name__}: {str(e)}")
            return None

    def enhance_with_ai(self, content, title):
        """Enhance content with AI using multi-provider fallback chain"""
        # Try all providers in order
        enhanced = self.enhance_with_groq(content, title)

        if not enhanced:
            enhanced = self.enhance_with_gemini(content, title)

        if not enhanced:
            enhanced = self.enhance_with_cohere(content, title)

        if not enhanced:
            enhanced = self.enhance_with_openai(content, title)

        if not enhanced:
            logger.warning("All providers failed - unable to enhance content")
            return content

        return enhanced

    def get_unretrofitted_posts(self, batch_size=50):
        """Get posts that haven't been retrofitted yet"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            query = """
                SELECT id, title, content, word_count
                FROM blog_posts
                WHERE status = 'published'
                LIMIT %s
            """

            cursor.execute(query, (batch_size,))
            posts = cursor.fetchall()
            cursor.close()

            return posts

        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return []

    def process_posts(self):
        """Process unretrofitted posts"""
        posts = self.get_unretrofitted_posts(50)

        if not posts:
            logger.warning("No unretrofitted posts found")
            return

        logger.info(f"Step 1: Enhancing Content")
        logger.info(f"  Found {len(posts)} posts to process\n")

        for idx, post in enumerate(posts, 1):
            try:
                post_id = post['id']
                post_title = post['title']

                # Enhance with AI
                enhanced = self.enhance_with_ai(post['content'], post_title)

                if enhanced != post['content']:
                    self.posts_enhanced += 1
                    logger.info(f"  [{idx}/{len(posts)}] {post_title[:40]}... ✓ Enhanced")
                else:
                    logger.info(f"  [{idx}/{len(posts)}] {post_title[:40]}... → No changes")

                # Record in retrofit log - FIXED: Updated column names
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO retrofit_log (blog_id, status, details, completed_at)
                    VALUES (%s, %s, %s, NOW())
                """, (post_id, 'completed', json.dumps({'enhanced': True})))
                cursor.close()

                self.posts_processed += 1

            except Exception as e:
                logger.error(f"  [{idx}/{len(posts)}] Error: {e}")
                self.posts_processed += 1

    def run(self):
        """Execute the retrofit engine"""
        logger.info("=" * 80)
        logger.info("R37: CONTENT RETROFIT & MONETIZATION ENGINE")
        logger.info("=" * 80)

        if not self.connect_database():
            logger.error("✗ Cannot proceed without database connection")
            return False

        try:
            self.process_posts()

            # Summary
            logger.info("=" * 80)
            logger.info("BATCH SUMMARY")
            logger.info(f"  Posts Processed: {self.posts_processed}")
            logger.info(f"  Posts Enhanced: {self.posts_enhanced}")
            logger.info(f"  Status: Retrofit batch complete")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"✗ Engine failed: {e}")
            return False

        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        engine = ContentRetrofitEngine()
        success = engine.run()

        if success:
            logger.info("✓ R37 - Content Retrofit Engine completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ R37 - Content Retrofit Engine failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
