#!/usr/bin/env python3
"""
GHGF WordPress Blogging Robot - Fully Automatic with Image Upload
Generates and publishes blog posts using AI APIs
- Content generation: Groq/Google/OpenAI/Cohere
- Images: Unsplash/Pixabay → WordPress media library
- Affiliate links: CJ Affiliate
- Publishing: WordPress REST API with featured images
"""

import os
import sys
import json
import requests
import random
from datetime import datetime
from urllib.parse import urljoin

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'

class BloggingRobot:
    def __init__(self):
        self.site_url = os.getenv("WORDPRESS_SITE_URL", "").rstrip('/')
        self.wp_username = os.getenv("WORDPRESS_USERNAME")
        self.wp_password = os.getenv("WORDPRESS_PASSWORD")
        self.posts_created = 0

        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.cohere_key = os.getenv("COHERE_API_KEY")
        self.unsplash_key = os.getenv("UNSPLASH_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        self.cj_key = os.getenv("CJ_API_KEY")

        self.topics = [
            "fitness", "health", "nutrition", "workout", "diet",
            "exercise", "wellness", "healthy living", "gym tips", "weight loss"
        ]

    def print_header(self, title):
        print(f"\n{'='*70}")
        print(f"{BOLD}{title}{RESET}")
        print('='*70)

    def generate_blog_title(self):
        """Generate an engaging blog post title"""
        title_templates = [
            "10 {topic} Tips You Need to Know Today",
            "The Complete Guide to {topic} Success",
            "Why {topic} is More Important Than You Think",
            "{topic}: Everything You Should Know",
            "Transform Your Life With These {topic} Secrets",
            "The Ultimate {topic} Checklist",
            "How to Master {topic} in 30 Days",
            "Top 5 {topic} Hacks That Actually Work",
            "Your Complete {topic} Roadmap",
            "Breaking: The Truth About {topic}"
        ]
        topic = random.choice(self.topics).capitalize()
        template = random.choice(title_templates)
        return template.format(topic=topic)

    def generate_content_groq(self, title):
        """Generate blog content using Groq"""
        if not self.groq_key:
            return None

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)

            models_to_try = [
                "mixtral-8x7b-32768",
                "llama-3.1-70b-versatile",
                "llama2-70b-4096",
                "qwen-3.8-27b"
            ]

            for model in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{
                            "role": "user",
                            "content": f"""Write a detailed, engaging blog post about: {title}

                            Include:
                            - 2-3 paragraph introduction
                            - 4-5 main sections with headers
                            - Practical tips and actionable advice
                            - Conclusion with call-to-action

                            Write in HTML format with <h2>, <h3>, <p>, <ul>, <li> tags."""
                        }],
                        max_tokens=1500,
                        temperature=0.7,
                        timeout=30
                    )

                    if response.choices and response.choices[0].message.content:
                        return response.choices[0].message.content
                except:
                    continue

            return None
        except Exception as e:
            print(f"⚠️  Groq generation failed: {str(e)[:60]}")
            return None

    def generate_content_openai(self, title):
        """Generate blog content using OpenAI"""
        if not self.openai_key:
            return None

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"""Write a detailed, engaging blog post about: {title}

                    Include:
                    - 2-3 paragraph introduction
                    - 4-5 main sections with headers
                    - Practical tips and actionable advice
                    - Conclusion with call-to-action

                    Write in HTML format with <h2>, <h3>, <p>, <ul>, <li> tags."""
                }],
                max_tokens=1500,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            return None
        except Exception as e:
            print(f"⚠️  OpenAI generation failed: {str(e)[:60]}")
            return None

    def generate_content_cohere(self, title):
        """Generate blog content using Cohere"""
        if not self.cohere_key:
            return None

        try:
            import cohere
            client = cohere.Client(api_key=self.cohere_key)

            response = client.chat(
                message=f"""Write a detailed, engaging blog post about: {title}

                Include:
                - 2-3 paragraph introduction
                - 4-5 main sections with headers
                - Practical tips and actionable advice
                - Conclusion with call-to-action

                Write in HTML format with <h2>, <h3>, <p>, <ul>, <li> tags.""",
                max_tokens=1500
            )

            if response.text:
                return response.text
            return None
        except Exception as e:
            print(f"⚠️  Cohere generation failed: {str(e)[:60]}")
            return None

    def generate_blog_content(self, title):
        """Generate blog content using available APIs"""
        generators = [
            ("Groq", self.generate_content_groq),
            ("OpenAI", self.generate_content_openai),
            ("Cohere", self.generate_content_cohere),
        ]

        random.shuffle(generators)

        for name, generator in generators:
            print(f"📝 Generating content with {name}...", end=" ")
            content = generator(title)
            if content:
                print(f"{GREEN}✅{RESET}")
                return content
            print(f"{RED}✗{RESET}")

        return None

    def get_image_unsplash(self, query):
        """Get random image from Unsplash"""
        if not self.unsplash_key:
            return None

        try:
            response = requests.get(
                "https://api.unsplash.com/photos/random",
                headers={"Authorization": f"Client-ID {self.unsplash_key}"},
                params={"query": query, "count": 1},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data[0].get('urls', {}).get('regular')
                return data.get('urls', {}).get('regular')
            return None
        except Exception as e:
            print(f"⚠️  Unsplash fetch failed: {str(e)[:60]}")
            return None

    def get_image_pixabay(self, query):
        """Get image from Pixabay"""
        if not self.pixabay_key:
            return None

        try:
            response = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "per_page": 1,
                    "image_type": "photo"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('hits'):
                    return data['hits'][0].get('largeImageURL')
            return None
        except Exception as e:
            print(f"⚠️  Pixabay fetch failed: {str(e)[:60]}")
            return None

    def get_blog_image(self, topic):
        """Get featured image for blog post"""
        print(f"🖼️  Fetching image for '{topic}'...", end=" ")

        image_url = self.get_image_unsplash(topic)
        if image_url:
            print(f"{GREEN}✅ Unsplash{RESET}")
            return image_url

        image_url = self.get_image_pixabay(topic)
        if image_url:
            print(f"{GREEN}✅ Pixabay{RESET}")
            return image_url

        print(f"{RED}✗{RESET}")
        return None

    def add_affiliate_links(self, content, topic):
        """Add CJ Affiliate links to content"""
        if not self.cj_key or not content:
            return content

        affiliate_section = f"""
        <hr>
        <p><strong>Recommended Products:</strong></p>
        <p>Looking for quality {topic} products? Check out our <a href="https://www.cj.com" rel="nofollow">recommended {topic} gear and supplements</a> on CJ Affiliate.</p>
        """

        return content + affiliate_section

    def upload_image_to_wordpress(self, image_url):
        """Download image and upload to WordPress media library"""
        if not image_url or not self.site_url:
            return None

        try:
            auth = (self.wp_username, self.wp_password)

            # Download image
            img_response = requests.get(image_url, timeout=15)
            if img_response.status_code != 200:
                return None

            # Get filename from URL
            filename = image_url.split('/')[-1].split('?')[0]
            if not filename or '.' not in filename:
                filename = "blog-image.jpg"

            # Upload to WordPress
            media_url = urljoin(self.site_url, '/wp-json/wp/v2/media')
            files = {'file': (filename, img_response.content)}

            response = requests.post(
                media_url,
                auth=auth,
                files=files,
                timeout=30
            )

            if response.status_code in [200, 201]:
                media_id = response.json().get('id')
                return media_id

            return None
        except Exception as e:
            print(f"⚠️  Image upload failed: {str(e)[:60]}")
            return None

    def create_wordpress_post(self, title, content, image_url, slug=None):
        """Create and publish post to WordPress with featured image"""
        if not self.site_url or not self.wp_username or not self.wp_password:
            print(f"{RED}❌ WordPress credentials missing{RESET}")
            return False

        try:
            wp_api = urljoin(self.site_url, '/wp-json/wp/v2/posts')
            auth = (self.wp_username, self.wp_password)

            # Upload image and get media ID
            featured_media = 0
            if image_url:
                print(f"   📤 Uploading image to WordPress...", end=" ")
                media_id = self.upload_image_to_wordpress(image_url)
                if media_id:
                    featured_media = media_id
                    print(f"{GREEN}✅{RESET}")
                else:
                    print(f"{RED}✗{RESET}")

            post_data = {
                "title": title,
                "content": content,
                "status": "publish",
                "type": "post",
                "categories": [1],  # Default category
            }

            # Add featured image if available
            if featured_media > 0:
                post_data["featured_media"] = featured_media

            # Add slug if provided
            if slug:
                post_data["slug"] = slug

            print(f"📤 Publishing to WordPress...", end=" ")

            response = requests.post(
                wp_api,
                auth=auth,
                json=post_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                post_id = response.json().get('id')
                post_url = response.json().get('link')
                print(f"{GREEN}✅{RESET}")
                print(f"   Post ID: {post_id}")
                print(f"   URL: {post_url}")
                return True
            elif response.status_code == 401:
                print(f"{RED}❌ Authentication failed{RESET}")
                print(f"   Check WordPress username/password")
                return False
            else:
                error = response.json().get('message', response.text)
                print(f"{RED}❌ HTTP {response.status_code}{RESET}")
                print(f"   Error: {error[:100]}")
                return False

        except Exception as e:
            print(f"{RED}❌ Error: {str(e)[:60]}{RESET}")
            return False

    def create_blog_post(self):
        """Create one complete blog post"""
        print(f"\n{BOLD}Creating Blog Post...{RESET}")
        print("-" * 70)

        # Generate title
        title = self.generate_blog_title()
        print(f"📰 Title: {title}")

        # Generate content
        content = self.generate_blog_content(title)
        if not content:
            print(f"{RED}❌ Failed to generate content{RESET}")
            return False

        # Get image
        topic = random.choice(self.topics)
        image_url = self.get_blog_image(topic)

        # Add affiliate links
        content = self.add_affiliate_links(content, topic)

        # Create WordPress post
        slug = title.lower().replace(' ', '-')[:50]
        success = self.create_wordpress_post(title, content, image_url, slug)

        if success:
            self.posts_created += 1

        return success

    def run(self):
        """Run blogging robot"""
        self.print_header("GHGF BLOGGING ROBOT - AUTOMATIC WITH IMAGES")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Validate WordPress
        if not self.site_url:
            print(f"{RED}❌ WORDPRESS_SITE_URL not configured{RESET}")
            return False

        if not self.wp_username or not self.wp_password:
            print(f"{RED}❌ WordPress credentials missing{RESET}")
            return False

        print(f"🌐 WordPress Site: {self.site_url}")
        print(f"👤 Username: {self.wp_username}\n")

        # Check which APIs are available
        print(f"{BOLD}Available APIs:{RESET}")
        apis = []
        if self.groq_key: apis.append("✅ Groq")
        if self.openai_key: apis.append("✅ OpenAI")
        if self.cohere_key: apis.append("✅ Cohere")
        if self.unsplash_key: apis.append("✅ Unsplash")
        if self.pixabay_key: apis.append("✅ Pixabay")
        if self.cj_key: apis.append("✅ CJ Affiliate")

        if apis:
            for api in apis:
                print(f"  {api}")
        else:
            print(f"  {RED}❌ No APIs configured{RESET}")
            return False

        print()

        # Generate multiple blog posts (default 3)
        posts_to_create = 3
        print(f"🤖 Generating {posts_to_create} blog posts with featured images...\n")

        for i in range(posts_to_create):
            print(f"{YELLOW}Post {i+1}/{posts_to_create}{RESET}")
            success = self.create_blog_post()
            if not success:
                print(f"⚠️  Post creation failed, continuing...")

        # Summary
        print(f"\n{'='*70}")
        print(f"{BOLD}SUMMARY{RESET}")
        print(f"Posts created: {self.posts_created}/{posts_to_create}")

        if self.posts_created > 0:
            print(f"{GREEN}✅ Blogging robot completed successfully!{RESET}")
            print("="*70 + "\n")
            return True
        else:
            print(f"{RED}❌ No posts were created{RESET}")
            print("="*70 + "\n")
            return False

if __name__ == "__main__":
    robot = BloggingRobot()
    success = robot.run()
    sys.exit(0 if success else 1)
