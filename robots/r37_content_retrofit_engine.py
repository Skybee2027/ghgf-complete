#!/usr/bin/env python3
"""
R37: Content Retrofit & Monetization Engine
Purpose: Batch process 600+ existing blog posts, enhance old content,
         add affiliate links and digital product cards
Input: Published blog posts from WordPress
Output: Enhanced posts with monetization elements
Frequency: Every 6 hours (batch processes 50 posts per cycle)
Timeline: Process all 600+ posts in 3-5 days
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
import requests
import re
from groq import Groq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'

class ContentRetrofitEngine:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        # API Keys
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')

        # *** CHANGE #1: Fixed Groq client initialization with error handling ***
        try:
            self.groq_client = Groq(api_key=self.groq_api_key)
        except TypeError as e:
            # Handle version compatibility - use simpler initialization
            if 'proxies' in str(e):
                import httpx
                self.groq_client = Groq(
                    api_key=self.groq_api_key,
                    http_client=httpx.Client()
                )
            else:
                raise

        # WordPress credentials
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', 'https://greathealthgreatfitness.com')
        self.wordpress_user = os.getenv('WORDPRESS_USERNAME', '')
        self.wordpress_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.wp_api_base = f"{self.wordpress_url}/wp-json/wp/v2"

        # Affiliate credentials
        self.cj_api_key = os.getenv('CJ_AFFILIATE_API', '')
        self.sharesale_api = os.getenv('SHARESALE_API', '')

        # Stats
        self.batch_number = 0
        self.posts_processed = 0
        self.posts_enhanced = 0
        self.affiliates_added = 0
        self.products_inserted = 0
        self.total_revenue_potential = 0.0

        # Batch configuration
        self.batch_size = 50  # Process 50 posts per 6-hour cycle
        self.max_retries = 3

    def print_header(self, title):
        print(f"\n{'='*80}\n{BOLD}{title}{RESET}\n{'='*80}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_unretrofitted_posts(self, conn, limit=50):
        """Get posts that haven't been retrofitted yet"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.slug, bp.content, bp.word_count,
                       bp.publish_date, bp.status
                FROM blog_posts bp
                LEFT JOIN retrofit_log rl ON bp.id = rl.blog_id AND rl.status = 'completed'
                WHERE rl.id IS NULL  -- Not yet retrofitted
                AND bp.status = 'published'
                AND bp.word_count >= 500  -- Minimum 500 words
                AND bp.publish_date < DATE_SUB(NOW(), INTERVAL 1 DAY)
                ORDER BY bp.publish_date DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting unretrofitted posts: {str(e)}")
            return []

    def enhance_content_with_groq(self, title, content, word_count):
        """Use Groq to enhance old blog content"""
        try:
            # Clean HTML
            clean_content = re.sub('<[^<]+?>', '', content)

            prompt = f"""Enhance this blog post to make it more valuable and engaging.

Title: {title}
Word Count: {word_count}

Original Content:
{clean_content[:2000]}

Enhance by:
1. Adding more actionable insights
2. Including data/statistics if relevant
3. Adding a clear call-to-action section
4. Improving formatting with subheadings
5. Adding internal linking suggestions [LINK_HERE tags]
6. Keeping the original tone and meaning

Return ONLY the enhanced content, ready for insertion."""

            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.5
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error enhancing content: {str(e)}")
            return None

    def identify_affiliate_opportunities(self, content, category):
        """Identify where affiliate links should be placed"""
        try:
            # Simple keyword matching for affiliate opportunities
            opportunities = []

            # Product references
            product_keywords = {
                'fitness equipment': ['dumbbells', 'resistance bands', 'yoga mat', 'kettlebell'],
                'supplements': ['protein', 'vitamin', 'supplement', 'creatine'],
                'books': ['guide', 'book', 'workbook', 'training program'],
                'apps': ['app', 'software', 'tracking', 'monitor']
            }

            for category_type, keywords in product_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        opportunities.append({
                            'type': category_type,
                            'keyword': keyword,
                            'affiliate_program': 'cj' if category_type != 'books' else 'sharesale'
                        })

            return opportunities
        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")
            return []

    def insert_affiliate_links(self, conn, post_id, content, opportunities):
        """Insert affiliate links into post content"""
        try:
            if not opportunities:
                return content

            # Example affiliate links (would be dynamic from API)
            affiliate_links = {
                'dumbbells': 'https://shareasale.com/r.cfm?b=1234&u=567&m=890&urllink=product',
                'resistance bands': 'https://shareasale.com/r.cfm?b=1234&u=567&m=890&urllink=product',
                'protein': 'https://cj.com/products/protein-powder',
            }

            modified_content = content
            for opportunity in opportunities[:3]:  # Max 3 affiliate links per post
                keyword = opportunity['keyword']
                if keyword in affiliate_links:
                    link = affiliate_links[keyword]
                    # Simple keyword linking (would be more sophisticated)
                    modified_content = modified_content.replace(
                        keyword,
                        f'<a href="{link}" target="_blank">{keyword}</a>',
                        1
                    )

            return modified_content
        except Exception as e:
            logger.error(f"Error inserting affiliate links: {str(e)}")
            return content

    def insert_product_promotion(self, content, post_id):
        """Insert digital product promotion card"""
        try:
            product_card = f"""
            <div class="retrofit-product-card" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 30px 0;
                color: white;
                text-align: center;
            ">
                <h3>📘 Premium Guide Available</h3>
                <p>Get the complete digital version of this guide with templates, checklists, and more.</p>
                <a href="/shop/" style="
                    background: white;
                    color: #667eea;
                    padding: 10px 20px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 600;
                ">View Digital Products →</a>
            </div>
            """

            # Insert at end of content
            modified_content = content + product_card
            return modified_content
        except Exception as e:
            logger.error(f"Error inserting product promotion: {str(e)}")
            return content

    def update_post_in_wordpress(self, post_id, enhanced_content):
        """Update post in WordPress via REST API"""
        try:
            update_data = {
                "content": enhanced_content,
                "status": "publish"
            }

            response = requests.post(
                f"{self.wp_api_base}/posts/{post_id}",
                json=update_data,
                auth=(self.wordpress_user, self.wordpress_password),
                timeout=30
            )

            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"WordPress update failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating WordPress post: {str(e)}")
            return False

    def log_retrofit(self, conn, post_id, status, details):
        """Log retrofit operation in database"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO retrofit_log
                (blog_id, status, started_at, completed_at, details, created_at)
                VALUES (%s, %s, NOW(), NOW(), %s, NOW())
            """, (post_id, status, json.dumps(details)))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error logging retrofit: {str(e)}")
            return False

    def run(self):
        self.print_header("R37: CONTENT RETROFIT & MONETIZATION ENGINE")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            print(f"{RED}✗ Database connection failed{RESET}")
            return False

        try:
            # Get current batch number
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT MAX(batch_number) as max_batch FROM retrofit_batches")
            result = cursor.fetchone()
            self.batch_number = (result['max_batch'] or 0) + 1
            cursor.close()

            print(f"{BOLD}Batch #{self.batch_number} - Processing up to {self.batch_size} posts{RESET}\n")

            # Get eligible posts
            posts = self.get_unretrofitted_posts(conn, self.batch_size)

            if not posts:
                print(f"  {YELLOW}No eligible posts for retrofit{RESET}\n")
                print(f"{'='*80}")
                print(f"{BOLD}BATCH SUMMARY{RESET}")
                print(f"  Batch #: {self.batch_number}")
                print(f"  Posts Processed: 0")
                print(f"  Status: {YELLOW}COMPLETE - No unretrofitted posts available{RESET}")
                print('='*80 + "\n")
                return True

            print(f"{BOLD}Step 1: Enhancing Content{RESET}")
            print(f"  Found {len(posts)} posts to process\n")

            for post in posts:
                self.posts_processed += 1
                print(f"  [{self.posts_processed}/{len(posts)}] {post['title'][:40]}...", end=" ")

                try:
                    # Enhance content with Groq
                    enhanced_content = self.enhance_content_with_groq(
                        post['title'],
                        post['content'],
                        post['word_count']
                    )

                    if not enhanced_content:
                        print(f"{RED}✗ Enhancement failed{RESET}")
                        self.log_retrofit(conn, post['id'], 'failed', {'reason': 'groq_enhancement_failed'})
                        continue

                    self.posts_enhanced += 1

                    # Find affiliate opportunities
                    opportunities = self.identify_affiliate_opportunities(
                        enhanced_content,
                        'general'
                    )

                    # Insert affiliate links
                    if opportunities:
                        enhanced_content = self.insert_affiliate_links(
                            conn,
                            post['id'],
                            enhanced_content,
                            opportunities
                        )
                        self.affiliates_added += len(opportunities)

                    # Insert product promotion
                    enhanced_content = self.insert_product_promotion(
                        enhanced_content,
                        post['id']
                    )
                    self.products_inserted += 1

                    # Update in WordPress
                    if self.update_post_in_wordpress(post['id'], enhanced_content):
                        # Log success
                        self.log_retrofit(conn, post['id'], 'completed', {
                            'enhanced': True,
                            'affiliate_links': len(opportunities),
                            'product_card': True
                        })
                        print(f"{GREEN}✓{RESET}")
                    else:
                        print(f"{RED}✗ Update failed{RESET}")
                        self.log_retrofit(conn, post['id'], 'failed', {'reason': 'wordpress_update_failed'})

                except Exception as e:
                    logger.error(f"Error processing post {post['id']}: {str(e)}")
                    print(f"{RED}✗{RESET}")
                    self.log_retrofit(conn, post['id'], 'failed', {'reason': str(e)})
                    continue

            # Record batch completion
            print(f"\n{BOLD}Step 2: Recording Batch Completion{RESET}")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO retrofit_batches
                (batch_number, batch_size, posts_processed, posts_successful, posts_failed,
                 status, notes, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, 'completed', %s, NOW(), NOW())
            """, (
                self.batch_number,
                self.batch_size,
                self.posts_processed,
                self.posts_enhanced,
                self.posts_processed - self.posts_enhanced,
                f"Batch {self.batch_number} complete"
            ))
            conn.commit()
            cursor.close()

            print(f"  ✓ Batch #{self.batch_number} recorded\n")

            print(f"{'='*80}")
            print(f"{BOLD}BATCH SUMMARY{RESET}")
            print(f"  Batch #: {self.batch_number}")
            print(f"  Posts Processed: {self.posts_processed}")
            print(f"  Posts Enhanced: {GREEN}{self.posts_enhanced}{RESET}")
            print(f"  Affiliate Links Added: {GREEN}{self.affiliates_added}{RESET}")
            print(f"  Product Cards Inserted: {GREEN}{self.products_inserted}{RESET}")
            print(f"  Success Rate: {CYAN}{round((self.posts_enhanced/max(1,self.posts_processed)*100), 1)}%{RESET}")
            print(f"  Processing Rate: ~50 posts per 6 hours")
            print(f"  Estimated Completion: ~3-5 days for 600+ posts")
            print(f"  Status: {GREEN}PASS - Batch processing complete{RESET}")
            print('='*80 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"{RED}✗ Error: {str(e)}{RESET}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    engine = ContentRetrofitEngine()
    success = engine.run()
    sys.exit(0 if success else 1)
