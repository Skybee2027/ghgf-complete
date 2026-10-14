#!/usr/bin/env python3
"""
WordPress REST API Post Quality Fixer
Purpose: Fix 2 specific blog posts using REST API instead of direct database
Bypasses: Database connectivity issues from GitHub Actions
Posts:
  1. "5 Complete Steps to Achieve Your Health and Fitness Dreams"
  2. "Top 7 Health and Fitness Innovations to Watch in 2026"
"""

import os
import sys
import logging
import json
import requests
import base64
import time
from datetime import datetime
from html.parser import HTMLParser
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HTMLStripper(HTMLParser):
    """Strip HTML tags for word counting"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)

class WordPressPostFixer:
    """Fix specific blog posts via WordPress REST API"""

    def __init__(self):
        """Initialize with environment variables"""
        self.wordpress_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com').rstrip('/')
        self.wordpress_user = os.getenv('WORDPRESS_USER', '')
        self.wordpress_password = os.getenv('WORDPRESS_PASSWORD', '')

        # AI APIs
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.cohere_key = os.getenv('COHERE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # Model configuration
        self.groq_model = os.getenv('GROQ_MODEL')
        self.gemini_model = os.getenv('GEMINI_MODEL')
        self.cohere_model = os.getenv('COHERE_MODEL')
        self.openai_model = os.getenv('OPENAI_MODEL')

        self.provider_used = None
        self.posts_fixed = 0
        self.api_base = f"{self.wordpress_url}/wp-json/wp/v2"

        # Setup basic auth header
        if self.wordpress_user and self.wordpress_password:
            credentials = base64.b64encode(f"{self.wordpress_user}:{self.wordpress_password}".encode()).decode()
            self.auth_header = f"Basic {credentials}"
        else:
            self.auth_header = None
            logger.warning("WordPress credentials not found in environment")

    def get_headers(self):
        """Get request headers with auth"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'GHGF-PostFixer/1.0'
        }
        if self.auth_header:
            headers['Authorization'] = self.auth_header
        return headers

    def strip_html(self, html_text):
        """Strip HTML tags from content"""
        s = HTMLStripper()
        try:
            s.feed(html_text)
            return s.get_data()
        except:
            return html_text

    def count_words(self, content):
        """Count words in content"""
        text = self.strip_html(content)
        return len(text.split())

    def get_enhancement_prompt(self, content, title):
        """Generate enhancement prompt - simplified for API reliability"""
        # Truncate content to avoid token limits
        content_preview = content[:1500] if len(content) > 1500 else content

        prompt = f"""Enhance this blog post to 1500-2000 words. Make it more detailed, engaging, and actionable.

TITLE: {title}
CURRENT CONTENT: {content_preview}

INSTRUCTIONS:
1. Expand each section with more specific details and examples
2. Add 3-4 new relevant sections if missing
3. Include actionable tips and real-world applications
4. Use conversational, engaging language
5. Add subheadings to break up content
6. Format as HTML with <h2>, <p>, <ul>, <ol>, <strong> tags
7. Target 1500+ words total
8. Keep tone professional but friendly

Return ONLY the enhanced HTML content."""
        return prompt

    def enhance_with_groq(self, content, title, retry_count=0, max_retries=2):
        """Enhance content using Groq with retry logic"""
        if not self.groq_key:
            return None
        try:
            from groq import Groq
            logger.info(f"Attempting Groq provider (attempt {retry_count + 1}/{max_retries + 1})...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_enhancement_prompt(content, title)

            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
                timeout=60
            )
            if response.choices and response.choices[0].message.content:
                self.provider_used = "Groq"
                logger.info("✓ Groq succeeded")
                return response.choices[0].message.content.strip()
            return None
        except requests.exceptions.Timeout as e:
            logger.warning(f"Groq timeout (attempt {retry_count + 1}): {e}")
            if retry_count < max_retries:
                wait_time = 5 * (2 ** retry_count)  # Exponential backoff: 5, 10, 20 seconds
                logger.info(f"Retrying Groq in {wait_time}s...")
                time.sleep(wait_time)
                return self.enhance_with_groq(content, title, retry_count + 1, max_retries)
            return None
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                # Rate limited - wait and retry
                logger.warning(f"Groq rate limited (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    wait_time = 10 * (2 ** retry_count)
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return self.enhance_with_groq(content, title, retry_count + 1, max_retries)
            logger.warning(f"Groq HTTP error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Groq failed: {str(e)[:100]}")
            return None

    def enhance_with_gemini(self, content, title, retry_count=0, max_retries=2):
        """Enhance content using Gemini with retry logic"""
        if not self.gemini_key:
            return None
        try:
            import google.generativeai as genai
            logger.info(f"Attempting Gemini provider (attempt {retry_count + 1}/{max_retries + 1})...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_enhancement_prompt(content, title)
            model = genai.GenerativeModel(self.gemini_model if self.gemini_model else "gemini-1.5-pro")

            response = model.generate_content(prompt, request_options={"timeout": 60})
            if response and response.text:
                self.provider_used = "Gemini"
                logger.info("✓ Gemini succeeded")
                return response.text.strip()
            logger.warning("Gemini returned empty response")
            return None
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"Gemini rate limited (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    wait_time = 10 * (2 ** retry_count)
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return self.enhance_with_gemini(content, title, retry_count + 1, max_retries)
            logger.warning(f"Gemini failed: {error_msg[:100]}")
            return None

    def enhance_with_cohere(self, content, title, retry_count=0, max_retries=2):
        """Enhance content using Cohere with retry logic"""
        if not self.cohere_key:
            return None
        try:
            import cohere
            logger.info(f"Attempting Cohere provider (attempt {retry_count + 1}/{max_retries + 1})...")
            client = cohere.ClientV2(api_key=self.cohere_key, timeout=60)
            prompt = self.get_enhancement_prompt(content, title)
            response = client.chat(
                model=self.cohere_model if self.cohere_model else "command-r-plus",
                messages=[{"role": "user", "content": prompt}]
            )
            if response and response.message and response.message.content:
                self.provider_used = "Cohere"
                logger.info("✓ Cohere succeeded")
                return response.message.content[0].text.strip()
            logger.warning("Cohere returned empty response")
            return None
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"Cohere rate limited (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    wait_time = 10 * (2 ** retry_count)
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return self.enhance_with_cohere(content, title, retry_count + 1, max_retries)
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"Cohere authentication failed: Invalid API key")
            logger.warning(f"Cohere failed: {error_msg[:100]}")
            return None

    def enhance_with_openai(self, content, title, retry_count=0, max_retries=2):
        """Enhance content using OpenAI with retry logic"""
        if not self.openai_key:
            return None
        try:
            from openai import OpenAI
            logger.info(f"Attempting OpenAI provider (attempt {retry_count + 1}/{max_retries + 1})...")
            client = OpenAI(api_key=self.openai_key, timeout=60)
            prompt = self.get_enhancement_prompt(content, title)
            response = client.chat.completions.create(
                model=self.openai_model if self.openai_model else "gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            if response.choices and response.choices[0].message.content:
                self.provider_used = "OpenAI"
                logger.info("✓ OpenAI succeeded")
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning(f"OpenAI rate limited (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    wait_time = 10 * (2 ** retry_count)
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return self.enhance_with_openai(content, title, retry_count + 1, max_retries)
            elif "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg.lower():
                logger.error(f"OpenAI authentication failed: {error_msg[:50]}")
            logger.warning(f"OpenAI failed: {error_msg[:100]}")
            return None

    def clean_markdown_artifacts(self, content):
        """Remove markdown code fence artifacts that AI sometimes adds"""
        import re
        # Remove markdown code fences (```html ... ```)
        content = re.sub(r'```html\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        # Remove backtick artifacts like "`html or "`
        content = content.replace('"`html', '').replace('"`', '')
        # Remove trailing/leading whitespace
        content = content.strip()
        return content

    def enhance_with_ai(self, content, title):
        """Multi-provider fallback enhancement with strategic delays"""
        logger.info("\n" + "="*80)
        logger.info("MULTI-PROVIDER AI ENHANCEMENT ATTEMPT")
        logger.info("="*80)

        providers = [
            ("Groq", self.enhance_with_groq),
            ("Gemini", self.enhance_with_gemini),
            ("Cohere", self.enhance_with_cohere),
            ("OpenAI", self.enhance_with_openai)
        ]

        for i, (name, provider_func) in enumerate(providers):
            enhanced = provider_func(content, title)
            if enhanced:
                # Clean markdown artifacts before returning
                enhanced = self.clean_markdown_artifacts(enhanced)
                logger.info("="*80)
                logger.info(f"SUCCESS: {name} provider succeeded!")
                logger.info(f"Content length after cleaning: {len(enhanced)} chars")
                logger.info("="*80 + "\n")
                return enhanced

            # Add strategic delay between provider attempts to avoid hammering APIs
            if i < len(providers) - 1:
                delay = 3 + (i * 2)  # 3, 5, 7 seconds between attempts
                logger.info(f"Waiting {delay}s before next provider attempt...")
                time.sleep(delay)

        logger.error("\n" + "="*80)
        logger.error("ALL PROVIDERS FAILED - Using original content as fallback")
        logger.error("="*80 + "\n")
        return content

    def extract_meta_description(self, content):
        """Extract meta description from content"""
        import re
        text = self.strip_html(content)
        meta = text[:160].strip()
        if meta.endswith(' '):
            meta = meta.rsplit(' ', 1)[0]
        return meta if len(meta) > 20 else text[:160]

    def find_posts_by_title(self, title_search):
        """Find posts using WordPress REST API search"""
        try:
            url = f"{self.api_base}/posts"
            params = {
                'search': title_search,
                'per_page': 10,
                'orderby': 'relevance'
            }
            response = requests.get(url, params=params, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            posts = response.json()

            for post in posts:
                if post.get('title', {}).get('rendered', '') == title_search:
                    return post

            return None
        except Exception as e:
            logger.error(f"Error finding post by title: {e}")
            return None

    def get_post_content(self, post_id):
        """Get full post content"""
        try:
            url = f"{self.api_base}/posts/{post_id}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None

    def update_post_content(self, post_id, content, excerpt=None):
        """Update post via REST API"""
        try:
            url = f"{self.api_base}/posts/{post_id}"
            data = {
                'content': content,
                'status': 'publish'
            }
            if excerpt:
                data['excerpt'] = excerpt

            response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            return None

    def fix_posts(self):
        """Find and fix the 2 target posts"""
        target_titles = [
            "5 Complete Steps to Achieve Your Health and Fitness Dreams",
            "Top 7 Health and Fitness Innovations to Watch in 2026"
        ]

        logger.info("=" * 80)
        logger.info("WORDPRESS REST API POST QUALITY FIX")
        logger.info(f"Target: {self.wordpress_url}")
        logger.info("=" * 80)

        for title in target_titles:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"FINDING: {title}")
                logger.info(f"{'='*80}")

                # Find post
                post = self.find_posts_by_title(title)
                if not post:
                    logger.warning(f"Post not found: {title}")
                    continue

                post_id = post['id']
                logger.info(f"✓ Found post #{post_id}")

                # Get current content
                full_post = self.get_post_content(post_id)
                if not full_post:
                    logger.warning(f"Could not retrieve full content for post #{post_id}")
                    continue

                current_content = full_post.get('content', {}).get('rendered', '')
                current_words = self.count_words(current_content)
                logger.info(f"  Current word count: {current_words} words")

                # Enhance with AI
                logger.info(f"  Enhancing with AI (max_tokens=4000)...")
                enhanced = self.enhance_with_ai(current_content, title)

                # Get new word count
                new_words = self.count_words(enhanced)
                improvement = round(((new_words - current_words) / current_words) * 100, 1) if current_words > 0 else 0

                logger.info(f"  ✓ Enhanced using {self.provider_used}")
                logger.info(f"  ✓ New word count: {new_words} words (+{improvement}% improvement)")

                # Extract meta description
                meta_description = self.extract_meta_description(enhanced)
                logger.info(f"  ✓ Meta description: {meta_description[:60]}...")

                # Update post
                logger.info(f"  Updating post in WordPress...")
                result = self.update_post_content(post_id, enhanced, meta_description)

                if result:
                    logger.info(f"  ✓ Post updated successfully")
                    logger.info(f"  ✓ Ready for WordPress display\n")
                    self.posts_fixed += 1
                else:
                    logger.error(f"  ✗ Failed to update post in WordPress\n")

            except Exception as e:
                logger.error(f"Error fixing post: {e}")

    def run(self):
        """Execute the fix"""
        if not self.wordpress_url:
            logger.error("WordPress URL not configured")
            return False

        if not self.auth_header:
            logger.error("WordPress credentials not configured")
            return False

        try:
            # Test WordPress connection
            logger.info("Testing WordPress REST API connection...")
            url = f"{self.api_base}/posts?per_page=1"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            logger.info("✓ WordPress REST API connection successful\n")

            self.fix_posts()

            logger.info("=" * 80)
            logger.info("QUALITY FIX COMPLETE")
            logger.info(f"Posts Fixed: {self.posts_fixed}/2")
            logger.info("=" * 80)
            logger.info("\nVerify on WordPress:")
            logger.info("- Both posts should now display 1500+ words")
            logger.info("- Content should be fully rendered with proper HTML")
            logger.info("- No truncation or missing sections")

            return self.posts_fixed == 2

        except requests.exceptions.RequestException as e:
            logger.error(f"WordPress connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Fix failed: {e}")
            return False


def main():
    """Main entry point"""
    try:
        fixer = WordPressPostFixer()
        success = fixer.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
