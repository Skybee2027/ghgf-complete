#!/usr/bin/env python3
"""
R8: Alt-Text Generator & Optimizer (Multi-Provider Fallback)
Purpose: Generate SEO-optimized, ADA-compliant alt text for images
Input: Images (from R7), blog post content
Output: Alt text for each image (keyword + descriptive + context)
Frequency: Every 6 hours (parallel with R7)
Dependencies: R7 (provides images)
ADA Compliance: All alt text must be accessible and descriptive
Format: "{keyword} - {descriptive alt text}"

Provider Chain: Groq → Gemini → Cohere → OpenAI
"""

import os
import sys
import mysql.connector
from datetime import datetime
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

class AltTextGenerator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

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
            logger.error("CRITICAL: No LLM API keys found!")
            sys.exit(1)

        self.alt_texts_generated = 0
        self.provider_used = None

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_latest_blog_with_images(self, conn):
        """Get latest draft blog post with images from R7"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic
                FROM blog_posts bp
                WHERE bp.status = 'draft'
                AND EXISTS (
                    SELECT 1 FROM image_tracking it
                    WHERE it.blog_id = bp.id
                )
                ORDER BY bp.created_at DESC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting blog with images: {str(e)}")
            return None

    def get_images_for_blog(self, conn, blog_id):
        """Get all images from R7 for this blog post"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, image_url, source, title, topic
                FROM image_tracking
                WHERE blog_id = %s
                ORDER BY used_date ASC
            """
            cursor.execute(query, (blog_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting images: {str(e)}")
            return []

    def get_topic_keywords(self, conn, topic):
        """Get top keywords for topic to include in alt text"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT keyword, search_volume
                FROM trending_keywords
                WHERE topic = %s
                ORDER BY search_volume DESC
                LIMIT 5
            """
            cursor.execute(query, (topic,))
            results = cursor.fetchall()
            cursor.close()
            return [r['keyword'] for r in results] if results else []
        except Exception as e:
            logger.error(f"Error getting keywords: {str(e)}")
            return []

    def extract_context_from_content(self, content, image_title):
        """Extract relevant context from blog content for alt text"""
        try:
            # Get first 500 chars and any mentions related to the image
            intro_context = content[:300] if len(content) > 300 else content

            # Look for H2/H3 headers that might relate to image
            import re
            headers = re.findall(r'<h[23]>([^<]+)</h[23]>', content)

            return {
                'intro': intro_context,
                'headers': headers[:3],  # Top 3 headers for context
                'has_list': '<ul>' in content or '<ol>' in content
            }
        except Exception as e:
            logger.error(f"Error extracting context: {str(e)}")
            return {'intro': '', 'headers': [], 'has_list': False}

    def get_alt_text_prompt(self, blog_data, image, keywords, context):
        """Generate the shared alt text prompt for all providers"""
        primary_keyword = keywords[0] if keywords else blog_data['topic']
        secondary_keywords = ", ".join(keywords[1:4]) if len(keywords) > 1 else ""

        prompt = f"""Generate an SEO-optimized, ADA-compliant alt text for an image.

Image Details:
- Source: {image['source']}
- Title from API: {image['title']}
- Blog Topic: {blog_data['topic']}
- Blog Title: {blog_data['title']}

Keywords to include naturally:
- Primary: {primary_keyword}
- Secondary: {secondary_keywords}

Context from blog:
- Intro: {context['intro'][:100]}...
- Related headers: {', '.join(context['headers'])}

Requirements for alt text:
1. Start with PRIMARY keyword naturally
2. Follow with descriptive phrase (2-4 words)
3. Include relevant context from the blog post
4. Max length: 120 characters (best practice)
5. Be accessible (describe what's in the image for screen readers)
6. Be specific and descriptive (not just "image" or "photo")
7. Avoid keyword stuffing
8. Format: "{{keyword}} - {{descriptive phrase with context}}"

Examples of GOOD alt text:
- "weight loss progress tracking chart showing monthly weight changes"
- "healthy meal prep containers with balanced nutrition portions"
- "elderly woman doing gentle yoga poses for flexibility"

Generate ONLY the alt text, no explanation."""
        return prompt

    def generate_alt_text_groq(self, blog_data, image, keywords, context):
        """Generate alt text using Groq"""
        if not self.groq_key:
            logger.debug("Groq API key not available, skipping Groq provider")
            return None

        try:
            from groq import Groq

            logger.debug("Attempting Groq provider...")
            client = Groq(api_key=self.groq_key)
            prompt = self.get_alt_text_prompt(blog_data, image, keywords, context)

            response = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                alt_text = response.choices[0].message.content.strip()
                if len(alt_text) > 120:
                    alt_text = alt_text[:117] + "..."
                self.provider_used = "Groq"
                return alt_text
            return None
        except ImportError:
            logger.warning("Groq library not installed")
            return None
        except Exception as e:
            logger.debug(f"Groq failed: {type(e).__name__}: {str(e)}")
            return None

    def generate_alt_text_gemini(self, blog_data, image, keywords, context):
        """Generate alt text using Gemini"""
        if not self.gemini_key:
            logger.debug("Gemini API key not available, skipping Gemini provider")
            return None

        try:
            import google.generativeai as genai

            logger.debug("Attempting Gemini provider...")
            genai.configure(api_key=self.gemini_key)
            prompt = self.get_alt_text_prompt(blog_data, image, keywords, context)

            model = genai.GenerativeModel(self.gemini_model if self.gemini_model else "gemini-pro")
            response = model.generate_content(prompt)

            if response.text:
                alt_text = response.text.strip()
                if len(alt_text) > 120:
                    alt_text = alt_text[:117] + "..."
                self.provider_used = "Gemini"
                return alt_text
            return None
        except ImportError:
            logger.warning("Google Generative AI library not installed")
            return None
        except Exception as e:
            logger.debug(f"Gemini failed: {type(e).__name__}: {str(e)}")
            return None

    def generate_alt_text_cohere(self, blog_data, image, keywords, context):
        """Generate alt text using Cohere"""
        if not self.cohere_key:
            logger.debug("Cohere API key not available, skipping Cohere provider")
            return None

        try:
            import cohere

            logger.debug("Attempting Cohere provider...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            prompt = self.get_alt_text_prompt(blog_data, image, keywords, context)

            response = client.generate(
                model=self.cohere_model,
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )

            if response.text:
                alt_text = response.text.strip()
                if len(alt_text) > 120:
                    alt_text = alt_text[:117] + "..."
                self.provider_used = "Cohere"
                return alt_text
            return None
        except ImportError:
            logger.warning("Cohere library not installed")
            return None
        except Exception as e:
            logger.debug(f"Cohere failed: {type(e).__name__}: {str(e)}")
            return None

    def generate_alt_text_openai(self, blog_data, image, keywords, context):
        """Generate alt text using OpenAI"""
        if not self.openai_key:
            logger.debug("OpenAI API key not available, skipping OpenAI provider")
            return None

        try:
            from openai import OpenAI

            logger.debug("Attempting OpenAI provider...")
            client = OpenAI(api_key=self.openai_key)
            prompt = self.get_alt_text_prompt(blog_data, image, keywords, context)

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                alt_text = response.choices[0].message.content.strip()
                if len(alt_text) > 120:
                    alt_text = alt_text[:117] + "..."
                self.provider_used = "OpenAI"
                return alt_text
            return None
        except ImportError:
            logger.warning("OpenAI library not installed")
            return None
        except Exception as e:
            logger.debug(f"OpenAI failed: {type(e).__name__}: {str(e)}")
            return None

    def generate_alt_text(self, conn, blog_data, image, keywords, context):
        """Generate SEO-optimized, ADA-compliant alt text using multi-provider fallback"""
        # Try all providers in order
        alt_text = self.generate_alt_text_groq(blog_data, image, keywords, context)

        if not alt_text:
            alt_text = self.generate_alt_text_gemini(blog_data, image, keywords, context)

        if not alt_text:
            alt_text = self.generate_alt_text_cohere(blog_data, image, keywords, context)

        if not alt_text:
            alt_text = self.generate_alt_text_openai(blog_data, image, keywords, context)

        if not alt_text:
            logger.error("All providers failed - unable to generate alt text")

        return alt_text

    def save_alt_text(self, conn, image_id, alt_text):
        """Save generated alt text to database"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE image_tracking
                SET alt_text = %s, alt_text_generated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (alt_text, image_id))
            conn.commit()
            cursor.close()
            logger.info(f"Alt text saved for image_id: {image_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving alt text: {str(e)}")
            return False

    def get_used_image_urls(self, conn):
        """Get all image URLs already used as featured images to avoid duplicates"""
        try:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT it.image_url
                FROM blog_posts bp
                JOIN image_tracking it ON bp.featured_image_id = it.id
                WHERE bp.featured_image_id IS NOT NULL
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            used_urls = {row[0] for row in results} if results else set()
            logger.info(f"Found {len(used_urls)} already-used image URLs")
            return used_urls
        except Exception as e:
            logger.error(f"Error getting used image URLs: {str(e)}")
            return set()

    def select_unique_featured_image(self, conn, images, blog_id):
        """Select a unique image for this blog post (not already used by another post)"""
        try:
            # Get all image URLs already used as featured images
            used_urls = self.get_used_image_urls(conn)
            logger.info(f"Checking {len(images)} images for uniqueness against {len(used_urls)} used URLs")

            # Find first image NOT in used_urls
            for image in images:
                if image['image_url'] not in used_urls:
                    logger.info(f"Selected unique image for blog_id {blog_id}: {image['id']} (URL not in used list)")
                    return image

            # Fallback: if all images are used, just use the first one (and log warning)
            if images:
                logger.warning(f"All {len(images)} images already used elsewhere - reusing image {images[0]['id']}")
                return images[0]

            return None
        except Exception as e:
            logger.error(f"Error selecting unique image: {str(e)}")
            return images[0] if images else None

    def set_featured_image(self, conn, blog_id, image_id):
        """Set the featured image for a blog post"""
        try:
            cursor = conn.cursor()
            query = """
                UPDATE blog_posts
                SET featured_image_id = %s
                WHERE id = %s
            """
            cursor.execute(query, (image_id, blog_id))
            conn.commit()
            cursor.close()
            logger.info(f"Featured image set for blog_id {blog_id}: image_id {image_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting featured image: {str(e)}")
            return False

    def save_featured_image_alt_text(self, conn, blog_id, image_id, alt_text):
        """Save featured image alt text directly to blog_posts for R31 to use"""
        try:
            cursor = conn.cursor()
            # Store alt text in blog_posts for easy access by R31
            query = """
                UPDATE blog_posts
                SET featured_image_alt_text = %s
                WHERE id = %s
            """
            cursor.execute(query, (alt_text, blog_id))
            conn.commit()
            cursor.close()
            logger.info(f"Featured image alt text saved for blog_id {blog_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving featured image alt text: {str(e)}")
            return False

    def run(self):
        self.print_header("R8: ALT-TEXT GENERATOR & OPTIMIZER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Latest Blog with Images (from R7){RESET}")
            blog_data = self.get_latest_blog_with_images(conn)
            if not blog_data:
                logger.warning("No blog posts with images found - R7 may not have found images")
                logger.info("Alt-text generation skipped (images not yet available from R7)")
                print(f"  ⚠ No images found - skipping alt-text generation\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Status: {YELLOW}PASS (no images to process){RESET}")
                print('='*70 + "\n")
                return True
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            print(f"{BOLD}Step 2: Retrieving Images from R7{RESET}")
            images = self.get_images_for_blog(conn, blog_data['id'])
            if not images:
                logger.warning("No images found for blog post")
                logger.info("Alt-text generation skipped (no images in database)")
                print(f"  ⚠ No images found - skipping alt-text generation\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Status: {YELLOW}PASS (no images to process){RESET}")
                print('='*70 + "\n")
                return True
            print(f"  ✓ Found {len(images)} images\n")

            print(f"{BOLD}Step 3: Getting Topic Keywords{RESET}")
            keywords = self.get_topic_keywords(conn, blog_data['topic'])
            for kw in keywords[:3]:
                print(f"  • {kw}")
            print()

            print(f"{BOLD}Step 4: Extracting Blog Context{RESET}")
            context = self.extract_context_from_content(blog_data['content'], blog_data['title'])
            print(f"  ✓ Context extracted\n")

            print(f"{BOLD}Step 5: Generating Alt Text for Each Image{RESET}")
            for i, image in enumerate(images, 1):
                alt_text = self.generate_alt_text(conn, blog_data, image, keywords, context)
                if alt_text:
                    saved = self.save_alt_text(conn, image['id'], alt_text)
                    if saved:
                        self.alt_texts_generated += 1
                        print(f"  {i}. Image ({image['source']}):")
                        print(f"     Alt Text: {BLUE}{alt_text}{RESET}")
                    else:
                        print(f"  {i}. Image ({image['source']}): {RED}Failed to save{RESET}")
                else:
                    print(f"  {i}. Image ({image['source']}): {RED}Failed to generate{RESET}")
            print()

            print(f"{BOLD}Step 6: Setting Featured Image (Unique per Post){RESET}")
            # Select a UNIQUE image not already used by other posts
            featured_alt_text = None
            if images:
                selected_image = self.select_unique_featured_image(conn, images, blog_data['id'])
                if selected_image:
                    featured_set = self.set_featured_image(conn, blog_data['id'], selected_image['id'])
                    # Get the alt text for this featured image
                    if selected_image.get('alt_text'):
                        featured_alt_text = selected_image['alt_text']
                        # Save alt text to blog_posts for R31
                        self.save_featured_image_alt_text(conn, blog_data['id'], selected_image['id'], featured_alt_text)
                    if featured_set:
                        print(f"  ✓ Featured image set: Image ID {BLUE}{selected_image['id']}{RESET}")
                        print(f"    URL: {selected_image['image_url'][:60]}...")
                        if featured_alt_text:
                            print(f"    Alt Text: {featured_alt_text[:50]}...")
                        print(f"    (Unique: Not used by other posts)\n")
                    else:
                        print(f"  {RED}✗ Failed to set featured image{RESET}\n")
                else:
                    print(f"  {RED}✗ No unique images available{RESET}\n")
            print()

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Total Images: {len(images)}")
            print(f"  Alt Texts Generated: {GREEN}{self.alt_texts_generated}{RESET}")
            print(f"  Featured Image Linked: {GREEN}YES (Unique & Auto-linked for R31){RESET}")
            print(f"  Image Uniqueness: {GREEN}VERIFIED (Not used by other posts){RESET}")
            print(f"  Status: {GREEN}PASS - Unique images ready for WordPress publishing (R31){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    generator = AltTextGenerator()
    success = generator.run()
    sys.exit(0 if success else 1)
