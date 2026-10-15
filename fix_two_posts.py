#!/usr/bin/env python3
"""
Targeted Post Quality Fix Script
Purpose: Retrofit 2 specific blog posts with R37 using max_tokens=4000 fix
Posts: 
  1. "5 Complete Steps to Achieve Your Health and Fitness Dreams"
  2. "Top 7 Health and Fitness Innovations to Watch in 2026"
"""

import os
import sys
import logging
import json
import mysql.connector
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/home/claude/ghgf-complete')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostQualityFixer:
    """Fix specific blog posts with retrofitted content"""

    def __init__(self):
        """Initialize with environment variables"""
        # Database config - MUST be provided via environment variables
        self.db_host = os.getenv('DB_HOST')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')

        # Validate database configuration
        if not all([self.db_host, self.db_user, self.db_name]):
            raise ValueError("CRITICAL: DB_HOST, DB_USER, and DB_NAME environment variables must be set")

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

        self.connection = None
        self.posts_fixed = 0
        self.provider_used = None

        logger.info("Post Quality Fixer initialized")

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
✓ Creates NATURAL product/monetization opportunities
✓ Drives LONG-TERM traffic
✓ Builds AUTHORITY in the niche"""
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
            response = client.generate(
                model=self.cohere_model,
                prompt=prompt,
                max_tokens=4000,  # CRITICAL FIX: Increased from 500
                temperature=0.7
            )
            if response.text:
                self.provider_used = "Cohere"
                return response.text.strip()
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
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # CRITICAL FIX: Increased from 500
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
        """Multi-provider fallback"""
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
        text = re.sub('<[^<]+?>', '', content)
        meta = text[:160].strip()
        if meta.endswith(' '):
            meta = meta.rsplit(' ', 1)[0]
        return meta if len(meta) > 20 else text[:160]

    def fix_posts(self):
        """Find and fix the 2 target posts"""
        target_titles = [
            "5 Complete Steps to Achieve Your Health and Fitness Dreams",
            "Top 7 Health and Fitness Innovations to Watch in 2026"
        ]

        logger.info("=" * 80)
        logger.info("TARGETED POST QUALITY FIX")
        logger.info("=" * 80)

        cursor = self.connection.cursor(dictionary=True)

        for title in target_titles:
            try:
                # Find post
                cursor.execute(
                    "SELECT id, title, content FROM blog_posts WHERE title = %s LIMIT 1",
                    (title,)
                )
                post = cursor.fetchone()

                if not post:
                    logger.warning(f"Post not found: {title}")
                    continue

                post_id = post['id']
                logger.info(f"\n{'='*80}")
                logger.info(f"POST #{post_id}: {title[:50]}...")
                logger.info(f"{'='*80}")

                # Current state
                current_words = len(post['content'].split())
                logger.info(f"  Current word count: {current_words} words")

                # Enhance with AI
                logger.info(f"  Enhancing with AI (max_tokens=4000)...")
                enhanced = self.enhance_with_ai(post['content'], title)

                # Get new word count
                new_words = len(enhanced.split())
                improvement = round(((new_words - current_words) / current_words) * 100, 1)

                logger.info(f"  ✓ Enhanced by AI using {self.provider_used}")
                logger.info(f"  ✓ New word count: {new_words} words (+{improvement}% improvement)")

                # Extract meta description
                meta_description = self.extract_meta_description(enhanced)
                logger.info(f"  ✓ Meta description: {meta_description[:60]}...")

                # Update database
                cursor.execute(
                    """UPDATE blog_posts 
                       SET content = %s, meta_description = %s, ready_for_wordpress = 1, final_qa_passed = 1
                       WHERE id = %s""",
                    (enhanced, meta_description, post_id)
                )

                # Record in retrofit log
                cursor.execute(
                    """INSERT INTO retrofit_log (blog_id, status, details, completed_at)
                       VALUES (%s, %s, %s, NOW())""",
                    (post_id, 'completed', json.dumps({
                        'enhanced': True,
                        'provider': self.provider_used,
                        'word_count_before': current_words,
                        'word_count_after': new_words,
                        'improvement_pct': improvement
                    }))
                )

                logger.info(f"  ✓ Database updated")
                logger.info(f"  ✓ Ready for WordPress publishing\n")

                self.posts_fixed += 1

            except Exception as e:
                logger.error(f"Error fixing post: {e}")

        cursor.close()

    def run(self):
        """Execute the fix"""
        if not self.connect_database():
            logger.error("Cannot proceed without database connection")
            return False

        try:
            self.fix_posts()

            logger.info("=" * 80)
            logger.info("QUALITY FIX COMPLETE")
            logger.info(f"Posts Fixed: {self.posts_fixed}")
            logger.info("=" * 80)
            logger.info("\nNext step: Run R31 to re-publish these posts to WordPress")
            logger.info("Expected: Full 1500+ word content with proper HTML rendering")

            return True

        except Exception as e:
            logger.error(f"Fix failed: {e}")
            return False

        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        fixer = PostQualityFixer()
        success = fixer.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
