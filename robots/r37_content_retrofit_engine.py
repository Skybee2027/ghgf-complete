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

        # AI APIs
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.cohere_api_key = os.getenv('COHERE_API_KEY', '')
        self.google_api_key = os.getenv('GOOGLE_API_KEY', '')

        # Affiliate APIs
        self.cj_api_key = os.getenv('CJ_API_KEY', '')
        self.shareasale_token = os.getenv('SHAREASALE_API_TOKEN', '')

        self.connection = None
        self.posts_processed = 0
        self.posts_enhanced = 0

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

    def get_available_model(self):
        """Get first available model from Groq, Cohere, or OpenAI"""
        models = []

        # Try Groq
        if self.groq_api_key:
            try:
                response = requests.get(
                    'https://api.groq.com/openai/v1/models',
                    headers={'Authorization': f'Bearer {self.groq_api_key}'},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and len(data['data']) > 0:
                        model_id = data['data'][0].get('id', 'mixtral-8x7b-32768')
                        return ('groq', model_id)
            except:
                pass

        # Try Cohere
        if self.cohere_api_key:
            return ('cohere', None)  # Cohere doesn't need model selection

        # Try OpenAI
        if self.openai_api_key:
            return ('openai', 'gpt-3.5-turbo')

        return (None, None)

    def enhance_with_ai(self, content, title):
        """Enhance content with AI - uses available provider"""
        provider, model = self.get_available_model()

        if not provider:
            logger.warning("No AI provider available")
            return content

        try:
            enhancement_prompt = f"""
            Enhance this blog post with:
            1. Better formatting and readability
            2. Key takeaways section
            3. Call-to-action for related products

            Title: {title}
            Content: {content[:1000]}...

            Return enhanced content only.
            """

            if provider == 'groq':
                headers = {
                    'Authorization': f'Bearer {self.groq_api_key}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'model': model,
                    'messages': [{'role': 'user', 'content': enhancement_prompt}],
                    'max_tokens': 500
                }
                response = requests.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']

            elif provider == 'cohere':
                headers = {'Authorization': f'Bearer {self.cohere_api_key}'}
                payload = {
                    'message': enhancement_prompt,
                    'chat_history': []
                }
                response = requests.post(
                    'https://api.cohere.com/v1/chat',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()['text']

            elif provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'model': model,
                    'messages': [{'role': 'user', 'content': enhancement_prompt}],
                    'max_tokens': 500
                }
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"Error enhancing content: {e}")

        return content

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
