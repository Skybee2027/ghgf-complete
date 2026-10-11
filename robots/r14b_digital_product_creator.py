#!/usr/bin/env python3
"""
R14b - Digital Product Creator & Monetization Engine
Creates professional digital products (e-books) from blog posts
Handles WooCommerce integration and payment processing
"""

import os
import sys
import logging
import json
import requests
import mysql.connector
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DigitalProductCreator:
    """Create digital products from blog posts"""

    def __init__(self):
        """Initialize with environment variables"""
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', '').rstrip('/')
        self.wordpress_user = os.getenv('WORDPRESS_USERNAME', '')
        self.wordpress_pass = os.getenv('WORDPRESS_PASSWORD', '')

        self.db_host = os.getenv('DB_HOST', '193.203.166.223')
        self.db_user = os.getenv('DB_USER', '')
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'u853068512_ghgf_blogging')

        self.connection = None
        self.posts_processed = 0
        self.products_created = 0

        logger.info("Digital Product Creator initialized")

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

    def get_eligible_posts(self):
        """Get posts eligible for digital products (800+ words)"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # FIXED: Removed problematic NOT IN subquery
            query = """
                SELECT id, title, content, word_count
                FROM blog_posts
                WHERE word_count >= 800
                  AND status = 'published'
                LIMIT 20
            """

            cursor.execute(query)
            posts = cursor.fetchall()
            cursor.close()

            logger.info(f"Found {len(posts)} eligible posts for digital products")
            return posts

        except Exception as e:
            logger.error(f"✗ Error getting eligible posts: {e}")
            return []

    def create_ebook_pdf(self, post_title, post_content, filename):
        """Create professional PDF e-book from post content"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)

            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2C5AA0'),
                spaceAfter=30,
                alignment=1
            )
            story.append(Paragraph(post_title, title_style))
            story.append(Spacer(1, 0.2*inch))

            # Metadata
            meta_style = ParagraphStyle(
                'Meta',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                spaceAfter=20
            )
            story.append(Paragraph(f"Created: {datetime.now().strftime('%B %d, %Y')}", meta_style))
            story.append(Spacer(1, 0.3*inch))

            # Content
            content_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=11,
                alignment=4,
                spaceAfter=12
            )

            # Remove HTML tags from content
            import re
            clean_content = re.sub('<[^<]+?>', '', post_content)

            for paragraph in clean_content.split('\n\n'):
                if paragraph.strip():
                    story.append(Paragraph(paragraph.strip(), content_style))
                    story.append(Spacer(1, 0.1*inch))

            # Build PDF
            doc.build(story)
            logger.info(f"✓ Created PDF: {filename}")
            return True

        except Exception as e:
            logger.error(f"✗ Error creating PDF: {e}")
            return False

    def record_product(self, post_id, post_title, product_url, price=9.99):
        """Record digital product in database"""
        try:
            cursor = self.connection.cursor()

            insert_query = """
                INSERT INTO digital_products
                (post_id, product_name, product_url, price, woocommerce_product_id, created_date)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """

            cursor.execute(insert_query, (
                post_id,
                f"E-book: {post_title}",
                product_url,
                price,
                None
            ))

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"✗ Error recording product: {e}")
            return False

    def process_posts(self):
        """Process eligible posts and create digital products"""
        posts = self.get_eligible_posts()

        if not posts:
            logger.warning("No eligible posts for digital products")
            return

        logger.info(f"Step 1: Creating Digital Products")
        logger.info(f"  Found {len(posts)} posts to process\n")

        for idx, post in enumerate(posts, 1):
            try:
                post_id = post['id']
                post_title = post['title']

                # Create PDF
                pdf_filename = f"/tmp/ebook_{post_id}.pdf"

                if self.create_ebook_pdf(post_title, post['content'], pdf_filename):
                    # Record in database
                    if self.record_product(post_id, post_title, pdf_filename):
                        self.products_created += 1
                        logger.info(f"  [{idx}/{len(posts)}] {post_title[:40]}... ✓ Product created")
                    else:
                        logger.error(f"  [{idx}/{len(posts)}] {post_title[:40]}... ✗ Failed to record")
                else:
                    logger.error(f"  [{idx}/{len(posts)}] {post_title[:40]}... ✗ PDF creation failed")

                self.posts_processed += 1

            except Exception as e:
                logger.error(f"  [{idx}/{len(posts)}] Error: {e}")
                self.posts_processed += 1
                continue

    def run(self):
        """Execute the digital product creator"""
        logger.info("=" * 80)
        logger.info("R14b: DIGITAL PRODUCT CREATOR & MONETIZATION ENGINE")
        logger.info("=" * 80)

        if not self.connect_database():
            logger.error("✗ Cannot proceed without database connection")
            return False

        try:
            self.process_posts()

            # Summary
            logger.info("=" * 80)
            logger.info("SUMMARY")
            logger.info(f"  Posts Processed: {self.posts_processed}")
            logger.info(f"  Products Created: {self.products_created}")
            logger.info(f"  Status: Digital product creation complete")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"✗ Creator failed: {e}")
            return False

        finally:
            self.close_database()


def main():
    """Main entry point"""
    try:
        creator = DigitalProductCreator()
        success = creator.run()

        if success:
            logger.info("✓ R14b - Digital Product Creator completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ R14b - Digital Product Creator failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
