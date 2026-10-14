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
from datetime import datetime
from html.parser import HTMLParser

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
        """Generate enhancement prompt (same as R37)"""
        prompt = f"""SUPER ADVANCED CONTENT ENHANCEMENT - Make this HIGHLY ENGAGING, TRAFFIC-OPTIMIZED, and MONETIZATION-READY:

TITLE: {title}
CONTENT: {content[:2000]}...

ENHANCEMENT REQUIREMENTS:

1. CONTENT REGENERATION (Not just polish):
   - Rewrite for maximum clarity and engagement
   - Add compelling hooks and storytelling elements
   - Use concrete examples, statistics, real-world scenarios
   - Make it feel written by an expert, not AI
   - Add personal insights and unique perspective
   - Remove fluff, filler phrases, and generic language

2. STRUCTURE & FLOW (Reader-Optimized):
   - Hook: Compelling opening (question/stat/story) in first 2 sentences
   - Problem statement: Clear pain point readers face
   - Solution section: Step-by-step actionable advice
   - Benefits section: Why this matters (emotional + practical)
   - Detailed examples: Real-world applications with specifics
   - Pro tips: Advanced insights readers won't find elsewhere
   - Call-to-action: Natural integration (NO SALES-Y tone)
   - Summary: Key takeaways in bullet points

3. ENGAGEMENT OPTIMIZATION:
   - Shorter paragraphs (2-3 sentences max)
   - Active voice, conversational tone
   - Address reader directly ("you", "your")
   - Break up text with subheadings every 150 words
   - Use bold for key terms and insights
   - Add tables/lists to visualize complex info
   - Include "did you know?" style callouts

4. SEO & TRAFFIC OPTIMIZATION:
   - Include target keywords naturally (2-3% density)
   - Add LSI keywords (related terms) throughout
   - Strong H2 headers with keywords
   - Longer content depth (1500+ words)
   - Internal link suggestions: "Related: [topic]"
   - FAQ section: Answer common questions
   - Meta description suggestion (160 chars)

5. MONETIZATION-READY STRUCTURE:
   - Position 1 (25% into post): "Recommended solution" box
   - Position 2 (60% into post): "Tools/Products that help" comparison table
   - Position 3 (end): "Premium resource" CTA
   - Natural product integration points (not salesy)
   - Problem → Product connection clarity
   - Trust signals: expert credentials, studies cited

6. ENGAGEMENT HOOKS (to get clicks/shares):
   - Surprising facts or statistics
   - Common misconceptions debunked
   - "Before/after" comparisons
   - Actionable steps readers can implement immediately
   - Visual elements descriptions (charts, images)

7. QUALITY STANDARDS:
   - Fact-check all claims and statistics
   - Remove outdated information
   - Ensure accuracy and credibility
   - Professional tone with friendly delivery
   - No grammatical errors
   - Consistent formatting throughout

OUTPUT FORMAT:
- Return ONLY the enhanced HTML content
- Use <h2> for main sections
- Use <p> for paragraphs
- Use <strong> for emphasis
- Use <ul> or <ol> for lists
- Use <table> for comparisons
- Keep engaging but professional

GOAL: Transform this post into a 1500-2000 word HIGH-VALUE resource that:
✓ Readers will LOVE and SHARE
✓ Google will RANK highly
✓ Monetization-ready with natural product placement"""
        return prompt

    def enhance_with_groq(self, content, title):
        """Enhance content using Groq"""
        if not self.groq_key:
            return None
        try:
            from groq import Groq
            logger.debug("Attempting Groq provider...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_enhancement_prompt(content, title)
            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # CRITICAL FIX: Increased from 500
                temperature=0.7
            )
            if response.choices and response.choices[0].message.content:
                self.provider_used = "Groq"
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.debug(f"Groq failed: {e}")
            return None

    def enhance_with_gemini(self, content, title):
        """Enhance content using Gemini"""
        if not self.gemini_key:
            return None
        try:
            import google.generativeai as genai
            logger.debug("Attempting Gemini provider...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_enhancement_prompt(content, title)
            model = genai.GenerativeModel(self.gemini_model if self.gemini_model else "gemini-pro")
            response = model.generate_content(prompt)
            if response.text:
                self.provider_used = "Gemini"
                return response.text.strip()
            return None
        except Exception as e:
            logger.debug(f"Gemini failed: {e}")
            return None

    def enhance_with_cohere(self, content, title):
        """Enhance content using Cohere"""
        if not self.cohere_key:
            return None
        try:
            import cohere
            logger.debug("Attempting Cohere provider...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            prompt = self.get_enhancement_prompt(content, title)
            response = client.chat(
                model=self.cohere_model if self.cohere_model else "command-r-plus",
                messages=[{"role": "user", "content": prompt}]
            )
            if response.message.content:
                self.provider_used = "Cohere"
                return response.message.content[0].text.strip()
            return None
        except Exception as e:
            logger.debug(f"Cohere failed: {e}")
            return None

    def enhance_with_openai(self, content, title):
        """Enhance content using OpenAI"""
        if not self.openai_key:
            return None
        try:
            from openai import OpenAI
            logger.debug("Attempting OpenAI provider...")
            client = OpenAI(api_key=self.openai_key)
            prompt = self.get_enhancement_prompt(content, title)
            response = client.chat.completions.create(
                model=self.openai_model if self.openai_model else "gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            if response.choices and response.choices[0].message.content:
                self.provider_used = "OpenAI"
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.debug(f"OpenAI failed: {e}")
            return None

    def enhance_with_ai(self, content, title):
        """Multi-provider fallback enhancement"""
        enhanced = self.enhance_with_groq(content, title)
        if not enhanced:
            enhanced = self.enhance_with_gemini(content, title)
        if not enhanced:
            enhanced = self.enhance_with_cohere(content, title)
        if not enhanced:
            enhanced = self.enhance_with_openai(content, title)
        if not enhanced:
            logger.warning("All providers failed")
            return content
        return enhanced

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
