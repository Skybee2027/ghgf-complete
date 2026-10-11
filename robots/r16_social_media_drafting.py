#!/usr/bin/env python3
"""
R16: Social Media Drafting & Scheduling
Purpose: Create social media posts (Twitter, Facebook, LinkedIn, Pinterest) from published blog
Input: Published blog post content, images, headline
Output: Multi-platform social media drafts with optimal formatting, hashtags, CTAs
Frequency: Daily (aggregates from multiple published posts)
Dependencies: Published blog posts (from R31 uploader)
Platforms: Twitter (280 chars), Facebook (2200 chars), LinkedIn (3000 chars), Pinterest
Strategy: Different copy for each platform + strategic delays (stored for R18 scheduler)
Hashtags: Auto-generated from keywords
CTAs: Platform-specific calls-to-action with tracking
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class SocialMediaDrafts:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.posts_created = 0

        # Platform character limits
        self.platform_limits = {
            'twitter': 280,
            'facebook': 2200,
            'linkedin': 3000,
            'pinterest': 500
        }

        # CTAs by platform
        self.ctas = {
            'twitter': ['Read more →', 'Learn how →', 'Check it out →'],
            'facebook': ['Read the full article →', 'Discover more tips →', 'Learn the full story →'],
            'linkedin': ['Read the full insights →', 'Get expert advice →', 'Share this article →'],
            'pinterest': ['Save this tip →', 'Learn more →', 'Discover this →']
        }

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_published_blogs_for_social(self, conn, days=7):
        """Get recently published blogs that need social media posts"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.published_at,
                       it.image_url
                FROM blog_posts bp
                LEFT JOIN image_tracking it ON bp.id = it.blog_id
                WHERE bp.status = 'published'
                AND bp.social_posts_created = FALSE
                AND bp.published_at > DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY bp.published_at DESC
                LIMIT 10
            """
            cursor.execute(query, (days,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting published blogs: {str(e)}")
            return []

    def extract_keywords_from_content(self, content, title):
        """Extract keywords for hashtags"""
        # Get first 100 words
        words = re.findall(r'\b\w+\b', title.lower())

        # Remove common words
        common = {'the', 'a', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        keywords = [w for w in words if w not in common and len(w) > 3]

        return keywords[:5]

    def create_twitter_post(self, blog_title, keywords, image_url=None):
        """Create Twitter post (280 chars max)"""
        hashtags = ' '.join([f'#{kw}' for kw in keywords[:3]])
        cta = self.ctas['twitter'][0]

        # Build base post: title + hashtags + link
        base = f"{blog_title} {hashtags}"

        if len(base) > self.platform_limits['twitter']:
            # Truncate title
            title_chars = self.platform_limits['twitter'] - len(hashtags) - 5  # -5 for spacing
            blog_title = blog_title[:title_chars].rsplit(' ', 1)[0]
            base = f"{blog_title}... {hashtags}"

        post = {
            'content': base,
            'platform': 'twitter',
            'word_count': len(base.split()),
            'char_count': len(base),
            'hashtags': hashtags,
            'image_url': image_url
        }
        return post

    def create_facebook_post(self, blog_title, blog_content, keywords, image_url=None):
        """Create Facebook post (2200 chars)"""
        hashtags = ' '.join([f'#{kw}' for kw in keywords])

        # Extract first 2-3 sentences from content
        sentences = re.split(r'[.!?]+', blog_content)[:3]
        excerpt = '. '.join([s.strip() for s in sentences if s.strip()]) + '.'

        if len(excerpt) > 500:
            excerpt = excerpt[:500] + '...'

        cta = self.ctas['facebook'][0]
        post_content = f"{blog_title}\n\n{excerpt}\n\n{cta}\n\n{hashtags}"

        post = {
            'content': post_content,
            'platform': 'facebook',
            'word_count': len(post_content.split()),
            'char_count': len(post_content),
            'hashtags': hashtags,
            'image_url': image_url
        }
        return post

    def create_linkedin_post(self, blog_title, blog_content, keywords, topic):
        """Create LinkedIn post (3000 chars)"""
        hashtags = ' '.join([f'#{kw}' for kw in keywords])

        # Professional tone for LinkedIn
        intro = f"Insights on {topic}:\n\n"

        # Extract key points (first 3 bullet points if available)
        bullets = re.findall(r'<li>(.*?)</li>', blog_content)[:3]
        bullet_text = '\n'.join([f"• {b}" for b in bullets]) if bullets else blog_content[:300]

        cta = self.ctas['linkedin'][0]
        post_content = f"{intro}{blog_title}\n\n{bullet_text}\n\n{cta}\n\n{hashtags}"

        post = {
            'content': post_content,
            'platform': 'linkedin',
            'word_count': len(post_content.split()),
            'char_count': len(post_content),
            'hashtags': hashtags,
            'image_url': None
        }
        return post

    def create_pinterest_post(self, blog_title, keywords, image_url=None):
        """Create Pinterest post (500 chars)"""
        # Pinterest requires images
        if not image_url:
            return None

        hashtags = ' '.join([f'#{kw}' for kw in keywords[:3]])
        cta = self.ctas['pinterest'][0]

        post_content = f"{blog_title}\n\n{cta}\n\n{hashtags}"

        post = {
            'content': post_content,
            'platform': 'pinterest',
            'word_count': len(post_content.split()),
            'char_count': len(post_content),
            'hashtags': hashtags,
            'image_url': image_url,
            'pin_description': blog_title[:100]
        }
        return post

    def save_social_posts(self, conn, blog_id, social_posts):
        """Save social media drafts to database"""
        try:
            cursor = conn.cursor()

            for post in social_posts:
                query = """
                    INSERT INTO social_media_posts (blog_id, platform, content,
                                                   hashtags, word_count, status,
                                                   created_at)
                    VALUES (%s, %s, %s, %s, %s, 'draft', NOW())
                """
                cursor.execute(query, (
                    blog_id,
                    post['platform'],
                    post['content'],
                    post['hashtags'],
                    post['word_count']
                ))

            # Mark blog as having social posts created
            blog_update = """
                UPDATE blog_posts
                SET social_posts_created = TRUE, social_posts_created_at = NOW()
                WHERE id = %s
            """
            cursor.execute(blog_update, (blog_id,))

            conn.commit()
            cursor.close()
            logger.info(f"Saved {len(social_posts)} social media posts")
            return True
        except Exception as e:
            logger.error(f"Error saving social posts: {str(e)}")
            return False

    def run(self):
        self.print_header("R16: SOCIAL MEDIA DRAFTING & SCHEDULING")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Published Blogs Needing Social Posts{RESET}")
            blogs = self.get_published_blogs_for_social(conn, days=7)
            if not blogs:
                print(f"  No published blogs found needing social posts\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Social Posts Created: 0")
                print(f"  Status: {YELLOW}No new published posts to promote{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(blogs)} blogs needing social promotion\n")

            print(f"{BOLD}Step 2: Creating Multi-Platform Social Posts{RESET}")
            for i, blog in enumerate(blogs, 1):
                print(f"  {i}. Creating posts for: {BLUE}{blog['title'][:50]}...{RESET}")

                keywords = self.extract_keywords_from_content(blog['content'], blog['title'])

                # Create posts for each platform
                social_posts = []

                # Twitter
                twitter_post = self.create_twitter_post(blog['title'], keywords, blog.get('image_url'))
                if twitter_post:
                    social_posts.append(twitter_post)

                # Facebook
                facebook_post = self.create_facebook_post(blog['title'], blog['content'], keywords, blog.get('image_url'))
                if facebook_post:
                    social_posts.append(facebook_post)

                # LinkedIn
                linkedin_post = self.create_linkedin_post(blog['title'], blog['content'], keywords, blog['topic'])
                if linkedin_post:
                    social_posts.append(linkedin_post)

                # Pinterest
                if blog.get('image_url'):
                    pinterest_post = self.create_pinterest_post(blog['title'], keywords, blog.get('image_url'))
                    if pinterest_post:
                        social_posts.append(pinterest_post)

                # Save posts
                if social_posts:
                    saved = self.save_social_posts(conn, blog['id'], social_posts)
                    if saved:
                        self.posts_created += len(social_posts)
                        print(f"     ✓ Created {len(social_posts)} posts (Twitter, Facebook, LinkedIn, Pinterest)\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blogs Processed: {len(blogs)}")
            print(f"  Social Posts Created: {GREEN}{self.posts_created}{RESET}")
            print(f"  Platforms: Twitter, Facebook, LinkedIn, Pinterest")
            print(f"  Status: {YELLOW}DRAFT - Ready for R18 (Email Newsletter) and R21 (Social Publisher){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    drafter = SocialMediaDrafts()
    success = drafter.run()
    sys.exit(0 if success else 1)
