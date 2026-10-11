#!/usr/bin/env python3
"""
R14: Static Link Injector
Purpose: Inject internal links to existing blog posts (sidebar/footer only)
Input: Blog content with internal link placeholders
Output: Content with resolved internal links to relevant published posts
Frequency: Every 6 hours (Stage 5a)
Dependencies: R3 (provides content with placeholders)
Placement Strategy: RIGHT SIDEBAR + FOOTER ONLY (secondary placement)
Conflict Resolution: R15 handles primary placement (start/middle/end/floating)
Link Types: Related posts, topic-relevant posts, category links
"""

import os
import sys
import mysql.connector
from datetime import datetime
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

class StaticLinkInjector:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.links_injected = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_latest_draft_blog(self, conn):
        """Get latest draft blog post"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, content, topic
                FROM blog_posts
                WHERE status = 'draft'
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting blog: {str(e)}")
            return None

    def find_related_published_posts(self, conn, topic, blog_id, limit=5):
        """Find related published posts for this topic"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, slug, topic
                FROM blog_posts
                WHERE status = 'published'
                AND topic = %s
                AND id != %s
                ORDER BY published_at DESC
                LIMIT %s
            """
            cursor.execute(query, (topic, blog_id, limit))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error finding related posts: {str(e)}")
            return []

    def find_all_published_by_topic(self, conn, exclude_id, limit=3):
        """Find published posts across different topics"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, slug, topic
                FROM blog_posts
                WHERE status = 'published'
                AND id != %s
                ORDER BY published_at DESC
                LIMIT %s
            """
            cursor.execute(query, (exclude_id, limit))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error finding published posts: {str(e)}")
            return []

    def create_internal_link(self, post):
        """Create HTML link for internal post"""
        slug = post['slug'] if post.get('slug') else post['title'].lower().replace(' ', '-')
        url = f"/blog/{slug}"
        return {
            'url': url,
            'title': post['title'],
            'topic': post['topic'],
            'html': f'<a href="{url}" class="internal-link">{post["title"]}</a>'
        }

    def build_sidebar_links(self, related_posts, other_posts):
        """Build sidebar section with related posts"""
        sidebar_html = '<div class="blog-sidebar">\n'
        sidebar_html += '<h3>Related Posts</h3>\n'
        sidebar_html += '<ul class="related-posts">\n'

        # Add related posts first
        for post in related_posts[:3]:
            link = self.create_internal_link(post)
            sidebar_html += f'<li>{link["html"]}</li>\n'

        # Add other posts if space
        for post in other_posts[:2]:
            if len(related_posts) + len(other_posts) <= 5:
                link = self.create_internal_link(post)
                sidebar_html += f'<li>{link["html"]}</li>\n'

        sidebar_html += '</ul>\n'
        sidebar_html += '</div>\n'

        return sidebar_html

    def build_footer_links(self, related_posts):
        """Build footer section with related topic links"""
        footer_html = '<div class="blog-footer-links">\n'
        footer_html += '<h4>More on this topic:</h4>\n'
        footer_html += '<ul class="footer-related">\n'

        for post in related_posts[:4]:
            link = self.create_internal_link(post)
            footer_html += f'<li>{link["html"]}</li>\n'

        footer_html += '</ul>\n'
        footer_html += '</div>\n'

        return footer_html

    def inject_links_into_content(self, content, sidebar_html, footer_html):
        """Inject sidebar and footer links into content"""
        # Add sidebar after first section (after first </h2>)
        first_h2_close = content.find('</h2>')
        if first_h2_close != -1:
            insert_pos = content.find('</p>', first_h2_close) + 4
            if insert_pos > first_h2_close:
                content = content[:insert_pos] + '\n' + sidebar_html + '\n' + content[insert_pos:]
        else:
            # No H2 found, add after first paragraph
            first_p_close = content.find('</p>')
            if first_p_close != -1:
                content = content[:first_p_close + 4] + '\n' + sidebar_html + '\n' + content[first_p_close + 4:]

        # Add footer at end (before closing </article> if present)
        article_close = content.rfind('</article>')
        if article_close != -1:
            content = content[:article_close] + '\n' + footer_html + '\n' + content[article_close:]
        else:
            # No article tag, add at very end
            content = content + '\n' + footer_html

        return content

    def count_injected_links(self, sidebar_html, footer_html):
        """Count total links injected"""
        sidebar_links = len(re.findall(r'<a href=', sidebar_html))
        footer_links = len(re.findall(r'<a href=', footer_html))
        return sidebar_links + footer_links

    def save_links_to_db(self, conn, blog_id, modified_content, link_data):
        """Save links and modified content to database"""
        try:
            cursor = conn.cursor()

            # Update content with injected links
            query = """
                UPDATE blog_posts
                SET content = %s, version = version + 1,
                    static_links_injected = TRUE,
                    static_links_count = %s,
                    static_links_injected_at = NOW()
                WHERE id = %s
            """
            link_count = len(link_data)
            cursor.execute(query, (modified_content, link_count, blog_id))

            # Store link injection record
            record_query = """
                INSERT INTO link_injection_log (blog_id, injection_type, links_count,
                                               placement_zone, injected_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(record_query, (blog_id, 'static_internal', link_count, 'sidebar_footer'))

            conn.commit()
            cursor.close()
            logger.info(f"Saved {link_count} links to database")
            return True
        except Exception as e:
            logger.error(f"Error saving links: {str(e)}")
            return False

    def run(self):
        self.print_header("R14: STATIC LINK INJECTOR")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Latest Draft Blog{RESET}")
            blog_data = self.get_latest_draft_blog(conn)
            if not blog_data:
                logger.error("No draft blog found")
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Topic: {blog_data['topic']}")
            print(f"  ✓ Title: {blog_data['title']}\n")

            print(f"{BOLD}Step 2: Finding Related Published Posts{RESET}")
            related_posts = self.find_related_published_posts(conn, blog_data['topic'], blog_data['id'], 5)
            print(f"  ✓ Found {len(related_posts)} posts on topic '{blog_data['topic']}'\n")

            print(f"{BOLD}Step 3: Finding Additional Posts (Other Topics){RESET}")
            other_posts = self.find_all_published_by_topic(conn, blog_data['id'], 3)
            print(f"  ✓ Found {len(other_posts)} additional posts\n")

            if not related_posts and not other_posts:
                print(f"  ⚠ {YELLOW}No published posts available for linking yet{RESET}\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Blog ID: {blog_data['id']}")
                print(f"  Links Injected: 0 (no published posts available yet)")
                print(f"  Status: {YELLOW}SKIP - First blog, will work on future posts{RESET}")
                print('='*70 + "\n")
                return True

            print(f"{BOLD}Step 4: Building Sidebar Links (Right Sidebar){RESET}")
            sidebar_html = self.build_sidebar_links(related_posts, other_posts)
            sidebar_count = len(re.findall(r'<a href=', sidebar_html))
            print(f"  ✓ Built sidebar with {sidebar_count} links\n")

            print(f"{BOLD}Step 5: Building Footer Links{RESET}")
            footer_html = self.build_footer_links(related_posts)
            footer_count = len(re.findall(r'<a href=', footer_html))
            print(f"  ✓ Built footer with {footer_count} links\n")

            print(f"{BOLD}Step 6: Injecting Links into Content{RESET}")
            modified_content = self.inject_links_into_content(
                blog_data['content'],
                sidebar_html,
                footer_html
            )
            self.links_injected = sidebar_count + footer_count
            print(f"  ✓ {GREEN}Injected {self.links_injected} total links{RESET}\n")

            print(f"{BOLD}Step 7: Saving to Database{RESET}")
            link_data = []
            for post in related_posts + other_posts:
                link = self.create_internal_link(post)
                link_data.append(link)

            saved = self.save_links_to_db(conn, blog_data['id'], modified_content, link_data)
            if saved:
                print(f"  ✓ {GREEN}Links saved successfully{RESET}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Sidebar Links: {sidebar_count}")
            print(f"  Footer Links: {footer_count}")
            print(f"  Total Injected: {GREEN}{self.links_injected}{RESET}")
            print(f"  Placement: Right Sidebar + Footer (Secondary)")
            print(f"  Conflict Resolution: R15 handles primary placement")
            print(f"  Status: {GREEN}PASS - Ready for R15 (Affiliate Placement){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    injector = StaticLinkInjector()
    success = injector.run()
    sys.exit(0 if success else 1)
