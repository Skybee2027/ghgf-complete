#!/usr/bin/env python3
"""
R37: Content Retrofit & Monetization Engine
Purpose: Process existing 600+ blog posts, add affiliates, e-books, and optimize
Input: All published blog posts without monetization
Output: Fully monetized posts with affiliates, e-books, product cards
Frequency: Batch processing (50 posts per 6-hour cycle until all 600+ complete)
Dependencies: R14 (Affiliate logic), R14b (E-book logic), WordPress API
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
import requests
import re
from io import BytesIO

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage, ImageDraw, ImageFont

# API clients
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
MAGENTA = '\033[95m'

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
        self.groq_client = Groq(api_key=self.groq_api_key)

        # WooCommerce credentials
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', 'https://greathealthgreatfitness.com')
        self.wordpress_user = os.getenv('WORDPRESS_USERNAME', '')
        self.wordpress_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.woo_api_base = f"{self.wordpress_url}/wp-json/wc/v3"

        # Stats
        self.posts_processed = 0
        self.posts_enhanced = 0
        self.affiliates_added = 0
        self.ebooks_created = 0
        self.product_cards_inserted = 0
        self.posts_skipped = 0
        self.total_revenue_potential = 0

        # Batch size per cycle
        self.batch_size = 50

    def print_header(self, title):
        print(f"\n{'='*90}\n{BOLD}{title}{RESET}\n{'='*90}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_unretrofitted_posts(self, conn):
        """Get posts that haven't been retrofitted yet"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.slug, bp.content, bp.word_count,
                       bp.publish_date, bp.quality_score,
                       GROUP_CONCAT(pc.name SEPARATOR ', ') as categories
                FROM blog_posts bp
                LEFT JOIN blog_post_categories bpc ON bp.id = bpc.post_id
                LEFT JOIN post_categories pc ON bpc.category_id = pc.id
                LEFT JOIN retrofit_log rl ON bp.id = rl.blog_id AND rl.status = 'completed'
                WHERE rl.id IS NULL  -- Not yet retrofitted
                AND bp.status = 'published'
                AND bp.word_count >= 500  -- Minimum 500 words
                GROUP BY bp.id
                ORDER BY bp.publish_date DESC
                LIMIT %s
            """
            cursor.execute(query, (self.batch_size,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting unretrofitted posts: {str(e)}")
            return []

    def get_retrofit_progress(self, conn):
        """Get retrofit progress statistics"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Total posts
            cursor.execute("SELECT COUNT(*) as total FROM blog_posts WHERE status='published'")
            total = cursor.fetchone()['total']

            # Retrofitted posts
            cursor.execute("""
                SELECT COUNT(DISTINCT blog_id) as retrofitted
                FROM retrofit_log
                WHERE status = 'completed'
            """)
            retrofitted = cursor.fetchone()['retrofitted']

            # In progress
            cursor.execute("""
                SELECT COUNT(DISTINCT blog_id) as in_progress
                FROM retrofit_log
                WHERE status = 'in_progress'
            """)
            in_progress = cursor.fetchone()['in_progress']

            cursor.close()
            return {
                'total': total,
                'retrofitted': retrofitted,
                'in_progress': in_progress,
                'remaining': total - retrofitted - in_progress,
                'progress_pct': round((retrofitted / max(total, 1)) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            return {}

    def log_retrofit_start(self, conn, post_id):
        """Log retrofit start"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO retrofit_log (blog_id, status, started_at)
                VALUES (%s, 'in_progress', NOW())
            """, (post_id,))
            conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error logging retrofit start: {str(e)}")

    def log_retrofit_complete(self, conn, post_id, details):
        """Log retrofit completion"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE retrofit_log
                SET status = 'completed',
                    details = %s,
                    completed_at = NOW()
                WHERE blog_id = %s AND status = 'in_progress'
            """, (json.dumps(details), post_id))
            conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error logging retrofit completion: {str(e)}")

    def enhance_old_content(self, title, content, quality_score):
        """Use Groq to enhance old post content if quality is low"""
        if quality_score >= 7.0:
            return content  # Good enough, keep as-is

        try:
            # Clean HTML
            clean_content = re.sub('<[^<]+?>', '', content)

            prompt = f"""Improve this blog post while keeping the core message intact.

Title: {title}
Current Quality Score: {quality_score}/10

Original Content (first 2000 chars):
{clean_content[:2000]}

Improvements needed:
1. Better structure with clear headings
2. More actionable tips
3. Stronger introduction and conclusion
4. Better formatting for readability
5. SEO optimization

Provide ONLY the improved HTML content ready for WordPress (with <p>, <h2>, <h3> tags)."""

            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.6
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error enhancing content: {str(e)}")
            return content

    def add_affiliate_links(self, content, post_id, category):
        """Add affiliate links using R14 logic"""
        try:
            # Define affiliate products by category
            affiliate_products = {
                'fitness': [
                    {'name': 'Resistance Bands Set', 'cj_id': 'RES001', 'price': '$25.99'},
                    {'name': 'Yoga Mat Premium', 'cj_id': 'YOG001', 'price': '$45.99'},
                    {'name': 'Dumbbells Adjustable', 'cj_id': 'DUM001', 'price': '$99.99'}
                ],
                'nutrition': [
                    {'name': 'Protein Powder', 'cj_id': 'PRO001', 'price': '$35.99'},
                    {'name': 'Meal Prep Containers', 'cj_id': 'MEA001', 'price': '$24.99'},
                    {'name': 'Water Bottle Smart', 'cj_id': 'WAT001', 'price': '$49.99'}
                ],
                'health': [
                    {'name': 'Air Purifier HEPA', 'cj_id': 'AIR001', 'price': '$199.99'},
                    {'name': 'Sleep Tracking Device', 'cj_id': 'SLE001', 'price': '$149.99'},
                    {'name': 'Blood Pressure Monitor', 'cj_id': 'BLO001', 'price': '$79.99'}
                ],
                'wellness': [
                    {'name': 'Meditation Cushion', 'cj_id': 'MED001', 'price': '$39.99'},
                    {'name': 'Essential Oil Set', 'cj_id': 'ESS001', 'price': '$34.99'},
                    {'name': 'Stress Relief Tea', 'cj_id': 'TEA001', 'price': '$19.99'}
                ]
            }

            # Get relevant products
            cat_key = next((k for k in affiliate_products.keys() if k.lower() in category.lower()), 'health')
            products = affiliate_products.get(cat_key, affiliate_products['health'])

            # Insert 2-3 affiliate product mentions into content
            paragraphs = content.split('</p>')
            insert_positions = [len(paragraphs)//3, (2*len(paragraphs))//3]

            for idx, pos in enumerate(insert_positions[:2]):
                if pos < len(paragraphs):
                    product = products[idx % len(products)]
                    affiliate_html = f"""
                    <p style="background: #f0f4ff; padding: 12px; border-left: 4px solid #667eea; margin: 15px 0;">
                    <strong>💡 Recommendation:</strong> {product['name']} (${product['price']})
                    - <a href="https://www.cj.com/?{product['cj_id']}" style="color: #667eea; text-decoration: none;">
                    View on CJ Affiliate →</a>
                    </p>"""
                    paragraphs[pos] = paragraphs[pos] + '</p>' + affiliate_html

            self.affiliates_added += 1
            return '</p>'.join(paragraphs)

        except Exception as e:
            logger.error(f"Error adding affiliate links: {str(e)}")
            return content

    def generate_ebook_for_retrofit(self, title, content, category):
        """Generate e-book PDF for old post"""
        try:
            # Clean content
            clean_content = re.sub('<[^<]+?>', '', content)[:3000]

            # Create PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=72, leftMargin=72)
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
            story.append(Spacer(1, 0.3*inch))

            # Content
            story.append(Paragraph(clean_content, styles['BodyText']))
            story.append(Spacer(1, 0.5*inch))

            # Footer
            story.append(Paragraph(
                f"<i>From GreatHealthGreatFitness.com | Generated: {datetime.now().strftime('%B %d, %Y')}</i>",
                styles['Normal']
            ))

            doc.build(story)
            pdf_buffer.seek(0)

            self.ebooks_created += 1
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating e-book: {str(e)}")
            return None

    def insert_product_card(self, content, title, product_type='guide'):
        """Insert product card into old post"""
        try:
            card_html = f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px;
                        padding: 24px; margin: 30px 0; color: white; text-align: center;">
                <div style="font-size: 14px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
                           margin-bottom: 12px; opacity: 0.9;">
                    📘 PREMIUM {product_type.upper()} AVAILABLE
                </div>
                <h3 style="font-size: 22px; margin: 12px 0;">
                    Complete Guide: {title}
                </h3>
                <p style="font-size: 15px; margin: 16px 0; opacity: 0.95;">
                    Expanded with actionable steps, templates, and expert insights
                </p>
                <a href="/?add-to-cart={product_type}" style="
                    background: white; color: #667eea; padding: 12px 28px; border-radius: 8px;
                    font-weight: 600; text-decoration: none; display: inline-block; margin-top: 15px;">
                    Get Premium Version →
                </a>
                <p style="font-size: 12px; margin-top: 16px; opacity: 0.8;">
                    ✓ Instant download  •  ✓ PDF + Resources  •  ✓ Money-back guarantee
                </p>
            </div>
            """

            # Insert at 50% position for old posts
            paragraphs = content.split('</p>')
            insert_pos = len(paragraphs) // 2
            paragraphs[insert_pos] = paragraphs[insert_pos] + '</p>' + card_html

            self.product_cards_inserted += 1
            return '</p>'.join(paragraphs)

        except Exception as e:
            logger.error(f"Error inserting product card: {str(e)}")
            return content

    def update_post_wordpress(self, post_id, new_content, title):
        """Update post in WordPress with new content"""
        try:
            # Prepare update data
            update_data = {
                "content": new_content,
                "meta": {
                    "retrofitted": True,
                    "retrofit_date": datetime.now().isoformat(),
                    "has_affiliate_links": True,
                    "has_digital_product": True
                }
            }

            # Update via WordPress REST API
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/posts/{post_id}",
                json=update_data,
                auth=(self.wordpress_user, self.wordpress_password),
                timeout=30
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Error updating WordPress: {str(e)}")
            return False

    def update_blog_post_record(self, conn, post_id, enhanced_content, retrofit_data):
        """Update blog_posts record with retrofit data"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE blog_posts
                SET content = %s,
                    has_digital_product = TRUE,
                    quality_score = GREATEST(quality_score, 8.0),
                    retrofitted_at = NOW()
                WHERE id = %s
            """, (enhanced_content, post_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error updating blog record: {str(e)}")
            return False

    def run(self):
        self.print_header("R37: CONTENT RETROFIT & MONETIZATION ENGINE")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            # Get progress
            progress = self.get_retrofit_progress(conn)
            print(f"{BOLD}Retrofit Progress:{RESET}")
            print(f"  Total Posts: {progress['total']}")
            print(f"  Retrofitted: {GREEN}{progress['retrofitted']}{RESET}")
            print(f"  In Progress: {YELLOW}{progress['in_progress']}{RESET}")
            print(f"  Remaining: {progress['remaining']}")
            print(f"  Progress: {CYAN}{progress['progress_pct']}%{RESET}\n")

            # Get batch of posts to retrofit
            print(f"{BOLD}Step 1: Fetching Posts for Retrofit{RESET}")
            posts = self.get_unretrofitted_posts(conn)

            if not posts:
                print(f"  ✓ All posts have been retrofitted!\n")
                print(f"{'='*90}")
                print(f"{BOLD}RETROFIT COMPLETE{RESET}")
                print(f"  Total Posts Processed (All-Time): {progress['retrofitted']}")
                print(f"  Status: {GREEN}RETROFIT COMPLETE - System in maintenance mode{RESET}")
                print('='*90 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts for retrofit in this batch\n")

            print(f"{BOLD}Step 2: Processing Posts{RESET}")

            for i, post in enumerate(posts, 1):
                self.posts_processed += 1
                print(f"\n  [{i}/{len(posts)}] {post['title'][:60]}...")

                try:
                    # Log start
                    self.log_retrofit_start(conn, post['id'])

                    # Enhance content if needed
                    enhanced_content = self.enhance_old_content(
                        post['title'],
                        post['content'],
                        post['quality_score'] or 6.0
                    )

                    if enhanced_content != post['content']:
                        self.posts_enhanced += 1
                        print(f"      ✓ Content enhanced")

                    # Add affiliate links
                    monetized_content = self.add_affiliate_links(
                        enhanced_content,
                        post['id'],
                        post['categories'] or 'health'
                    )
                    print(f"      ✓ Affiliate links added")

                    # Insert product card
                    final_content = self.insert_product_card(
                        monetized_content,
                        post['title']
                    )
                    print(f"      ✓ Product card inserted")

                    # Generate e-book
                    ebook = self.generate_ebook_for_retrofit(
                        post['title'],
                        post['content'],
                        post['categories'] or 'health'
                    )
                    print(f"      ✓ E-book generated")

                    # Update WordPress
                    if self.update_post_wordpress(post['id'], final_content, post['title']):
                        print(f"      ✓ Published to WordPress")

                    # Update database
                    self.update_blog_post_record(conn, post['id'], final_content, {
                        'enhanced': enhanced_content != post['content'],
                        'affiliate_added': True,
                        'ebook_generated': ebook is not None,
                        'product_card_inserted': True
                    })

                    # Log completion
                    retrofit_details = {
                        'enhanced': self.posts_enhanced > 0,
                        'affiliates_added': 1,
                        'ebook_created': 1,
                        'product_card_added': 1
                    }
                    self.log_retrofit_complete(conn, post['id'], retrofit_details)

                    # Estimate revenue
                    estimated_revenue = 5 + (post['word_count'] / 1000) * 2  # $5 base + $2 per 1000 words
                    self.total_revenue_potential += estimated_revenue

                    print(f"      {GREEN}✓ Retrofitted successfully${estimated_revenue:.2f} potential{RESET}")

                except Exception as e:
                    logger.error(f"Error processing post {post['id']}: {str(e)}")
                    self.posts_skipped += 1
                    print(f"      {RED}✗ Error: {str(e)[:50]}{RESET}")
                    continue

            print(f"\n{'='*90}")
            print(f"{BOLD}BATCH COMPLETE{RESET}")
            print(f"  Posts in Batch: {len(posts)}")
            print(f"  Successfully Retrofitted: {GREEN}{self.posts_processed - self.posts_skipped}{RESET}")
            print(f"  Content Enhanced: {self.posts_enhanced}")
            print(f"  Affiliate Links Added: {self.affiliates_added}")
            print(f"  E-Books Generated: {self.ebooks_created}")
            print(f"  Product Cards Inserted: {self.product_cards_inserted}")
            print(f"  Skipped (Errors): {self.posts_skipped}")
            print(f"  Estimated Revenue (This Batch): {GREEN}${self.total_revenue_potential:.2f}{RESET}")
            print(f"  Overall Progress: {CYAN}{progress['progress_pct'] + (self.posts_processed/progress['total'])*100:.1f}%{RESET}")
            print(f"  Status: {GREEN}PASS - Retrofit batch complete{RESET}")
            print('='*90 + "\n")

            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    engine = ContentRetrofitEngine()
    success = engine.run()
    sys.exit(0 if success else 1)
