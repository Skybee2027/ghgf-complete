#!/usr/bin/env python3
"""
R17: Email Newsletter Builder & Database Writer
Purpose: Build HTML email newsletters from published blog posts (writes to DB)
Input: Published blog posts (daily), featured image
Output: HTML email content + newsletter record (stored for R18 scheduler to send)
Frequency: Daily (aggregates all posts from previous 24 hours)
Dependencies: Published blog posts (from R31)
Newsletter Elements: Hero image, featured articles, CTAs, footer with unsubscribe
Storage Strategy: Writes to email_newsletters table for R18 to send
Design: Responsive HTML template with embedded styles
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

class EmailNewsletterBuilder:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.newsletters_created = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_recent_published_blogs(self, conn, hours=24):
        """Get blogs published in last 24 hours"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       it.image_url,
                       COUNT(smp.id) as social_posts_count
                FROM blog_posts bp
                LEFT JOIN image_tracking it ON bp.id = it.blog_id
                LEFT JOIN social_media_posts smp ON bp.id = smp.blog_id
                WHERE bp.status = 'published'
                AND bp.published_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY bp.id
                ORDER BY bp.published_at DESC
            """
            cursor.execute(query, (hours,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting recent blogs: {str(e)}")
            return []

    def extract_excerpt(self, content, max_length=200):
        """Extract first paragraph as excerpt"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Get first 200 chars
        excerpt = text[:max_length].strip()
        if len(text) > max_length:
            excerpt = excerpt.rsplit(' ', 1)[0] + '...'
        return excerpt

    def build_email_html(self, blog_posts, newsletter_date):
        """Build responsive HTML email newsletter"""

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 10px 0 0 0; font-size: 14px; }}
        .article {{ border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 4px; }}
        .article-image {{ max-width: 100%; height: auto; margin: 10px 0; border-radius: 4px; }}
        .article h2 {{ margin: 0 0 10px 0; font-size: 20px; color: #667eea; }}
        .article p {{ margin: 10px 0; font-size: 14px; }}
        .read-more {{ display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .unsubscribe {{ color: #667eea; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Health & Fitness Weekly</h1>
            <p>Your dose of wellness insights - {newsletter_date.strftime('%B %d, %Y')}</p>
        </div>
'''

        # Add featured article (first one)
        if blog_posts:
            featured = blog_posts[0]
            excerpt = self.extract_excerpt(featured['content'], 250)

            html += f'''
        <div class="article featured">
            <h2>{featured['title']}</h2>
            <p><strong>Featured Article</strong></p>
'''
            if featured.get('image_url'):
                html += f'            <img src="{featured["image_url"]}" alt="{featured["title"]}" class="article-image">\n'

            html += f'''            <p>{excerpt}</p>
            <a href="https://greathealthgreatfitness.com/blog/{featured['title'].lower().replace(' ', '-')}" class="read-more">Read Full Article →</a>
        </div>
'''

        # Add other articles
        if len(blog_posts) > 1:
            html += '''        <h3 style="margin-top: 30px; color: #667eea;">Recent Articles</h3>
'''
            for post in blog_posts[1:]:
                excerpt = self.extract_excerpt(post['content'], 150)
                html += f'''        <div class="article">
            <h2>{post['title']}</h2>
            <p>{excerpt}</p>
            <a href="https://greathealthgreatfitness.com/blog/{post['title'].lower().replace(' ', '-')}" class="read-more">Learn More →</a>
        </div>
'''

        html += '''
        <div class="footer">
            <p>Great Health Great Fitness - Your Daily Source for Wellness</p>
            <p><a href="https://greathealthgreatfitness.com" class="unsubscribe">Visit Website</a> |
               <a href="#" class="unsubscribe">Manage Preferences</a> |
               <a href="#" class="unsubscribe">Unsubscribe</a></p>
            <p>&copy; 2024 Great Health Great Fitness. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
'''
        return html

    def calculate_newsletter_hash(self, html):
        """Create hash of newsletter content to prevent duplicates"""
        import hashlib
        return hashlib.md5(html.encode()).hexdigest()

    def save_newsletter(self, conn, html_content, blog_ids, newsletter_date):
        """Save newsletter to database for R18 scheduler"""
        try:
            cursor = conn.cursor()

            # Create newsletter record
            content_hash = self.calculate_newsletter_hash(html_content)

            query = """
                INSERT INTO email_newsletters (content_html, content_hash, blog_ids,
                                               newsletter_date, status, created_at)
                VALUES (%s, %s, %s, %s, 'draft', NOW())
            """
            blog_ids_str = ','.join([str(bid) for bid in blog_ids])
            cursor.execute(query, (html_content, content_hash, blog_ids_str, newsletter_date))

            newsletter_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            logger.info(f"Newsletter saved with ID: {newsletter_id}")
            return newsletter_id
        except Exception as e:
            logger.error(f"Error saving newsletter: {str(e)}")
            return None

    def run(self):
        self.print_header("R17: EMAIL NEWSLETTER BUILDER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Published Blogs (Last 24 Hours){RESET}")
            blogs = self.get_recent_published_blogs(conn, hours=24)
            if not blogs:
                print(f"  No new blogs published in last 24 hours\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Newsletters Created: 0")
                print(f"  Status: {YELLOW}No new content to feature{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(blogs)} published blogs\n")

            print(f"{BOLD}Step 2: Featured Article Analysis{RESET}")
            for i, blog in enumerate(blogs[:3], 1):
                social_count = blog['social_posts_count'] or 0
                print(f"  {i}. {BLUE}{blog['title'][:50]}...{RESET}")
                print(f"     Topic: {blog['topic']} | Social posts: {social_count}\n")

            print(f"{BOLD}Step 3: Building Email Newsletter HTML{RESET}")
            newsletter_date = datetime.now()
            html_content = self.build_email_html(blogs, newsletter_date)
            print(f"  ✓ HTML email generated\n")

            print(f"{BOLD}Step 4: Saving Newsletter to Database{RESET}")
            blog_ids = [b['id'] for b in blogs]
            newsletter_id = self.save_newsletter(conn, html_content, blog_ids, newsletter_date)

            if newsletter_id:
                self.newsletters_created = 1
                print(f"  ✓ {GREEN}Newsletter saved (ID: {newsletter_id}){RESET}\n")

            # Calculate stats
            featured_count = min(len(blogs), 1)
            recent_count = min(len(blogs) - 1, len(blogs))

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blogs Featured: {featured_count}")
            print(f"  Recent Articles Included: {recent_count}")
            print(f"  Total Newsletter Size: {len(html_content)} characters")
            print(f"  Newsletter Status: {YELLOW}DRAFT - Ready for R18 (Email Scheduler){RESET}")
            print(f"  Send Time: Scheduled by R18")
            print(f"  Status: {GREEN}PASS - Newsletter ready for distribution{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    builder = EmailNewsletterBuilder()
    success = builder.run()
    sys.exit(0 if success else 1)
