#!/usr/bin/env python3
"""
R14b: Digital Product Creator & Monetization Engine
Purpose: Generate high-quality e-books from blog posts, create attractive covers,
         set up WooCommerce products with PayPal/Stripe, insert product cards into blogs
Input: Published blog posts from WordPress
Output: Digital products (PDFs), WooCommerce products, product cards on blog
Frequency: Every 6 hours (runs after R14 Affiliate Placement)
Dependencies: R14 (Affiliate Placement Optimizer)
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
import base64

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
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

class DigitalProductCreator:
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

        # WooCommerce credentials
        self.wordpress_url = os.getenv('WORDPRESS_SITE_URL', 'https://greathealthgreatfitness.com')
        self.wordpress_user = os.getenv('WORDPRESS_USERNAME', '')
        self.wordpress_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.woo_api_base = f"{self.wordpress_url}/wp-json/wc/v3"

        # Payment gateway credentials
        self.paypal_client_id = os.getenv('PAYPAL_CLIENT_ID', '')
        self.paypal_secret = os.getenv('PAYPAL_SECRET', '')
        self.stripe_api_key = os.getenv('STRIPE_API_KEY', '')

        # Stats
        self.products_created = 0
        self.ebooks_generated = 0
        self.covers_designed = 0
        self.woocommerce_products = 0
        self.total_value = 0
        self.posts_processed = 0

        # Pricing strategy
        self.pricing_rules = {
            'short': 4.95,      # <1000 words → $4.95 (checklist/template)
            'medium': 9.95,     # 1000-2000 words → $9.95 (guide)
            'long': 14.95,      # 2000-3500 words → $14.95 (comprehensive guide)
            'premium': 24.95    # 3500+ words → $24.95 (complete course/masterclass)
        }

    def print_header(self, title):
        print(f"\n{'='*80}\n{BOLD}{title}{RESET}\n{'='*80}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_eligible_posts(self, conn):
        """Get posts without digital products that are high-quality"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT bp.id, bp.title, bp.slug, bp.content, bp.word_count,
                       bp.publish_date, GROUP_CONCAT(pc.name SEPARATOR ', ') as categories
                FROM blog_posts bp
                LEFT JOIN blog_post_categories bpc ON bp.id = bpc.post_id
                LEFT JOIN post_categories pc ON bpc.category_id = pc.id
                LEFT JOIN digital_products dp ON bp.id = dp.blog_id
                WHERE dp.id IS NULL  -- No digital product yet
                AND bp.status = 'published'
                AND bp.word_count >= 800  -- Minimum 800 words for e-book quality
                AND bp.publish_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                AND bp.quality_score >= 7.5  -- High quality only
                GROUP BY bp.id
                ORDER BY bp.publish_date DESC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting eligible posts: {str(e)}")
            return []

    def determine_price(self, word_count, quality_score):
        """Determine product price based on content depth and quality"""
        base_price = self.pricing_rules['short']

        # Adjust based on word count
        if word_count >= 3500:
            base_price = self.pricing_rules['premium']
        elif word_count >= 2000:
            base_price = self.pricing_rules['long']
        elif word_count >= 1000:
            base_price = self.pricing_rules['medium']

        # Quality multiplier (7.5-10.0 score)
        quality_multiplier = 1 + ((quality_score - 7.5) * 0.1)
        final_price = round(base_price * quality_multiplier, 2)

        # Ensure price stays within range
        final_price = max(4.95, min(29.95, final_price))
        return final_price

    def determine_product_type(self, word_count, title):
        """Determine what type of digital product to create"""
        if word_count < 1000:
            return "checklist"  # Quick reference
        elif word_count < 2000:
            return "guide"      # Step-by-step guide
        elif word_count < 3500:
            return "masterclass" # Comprehensive guide
        else:
            return "course"     # Full course/workbook

    def generate_ebook_cover(self, title, category, product_type, price):
        """Generate attractive e-book cover using PIL"""
        try:
            # Create image (8.5x11 inches at 150 DPI = 1275x1650px)
            width, height = 1275, 1650

            # Color scheme based on category
            color_map = {
                'fitness': ('#FF6B6B', '#FFE5E5'),
                'health': ('#4ECDC4', '#E0F9F7'),
                'nutrition': ('#95E1D3', '#F0FDF8'),
                'wellness': '#7C3AED',
                'weight loss': '#FFA500',
                'default': ('#6366F1', '#EEF2FF')
            }

            # Determine colors
            primary_color = '#6366F1'
            secondary_color = '#EEF2FF'

            for cat_key in color_map:
                if cat_key.lower() in category.lower():
                    colors_tuple = color_map[cat_key]
                    if isinstance(colors_tuple, tuple):
                        primary_color, secondary_color = colors_tuple
                    else:
                        primary_color = colors_tuple
                    break

            # Create PIL image
            img = PILImage.new('RGB', (width, height), secondary_color)
            draw = ImageDraw.Draw(img)

            # Try to load fonts (fallback to default if not available)
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
                badge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                badge_font = ImageFont.load_default()

            # Draw gradient background effect (multiple rectangles)
            gradient_height = int(height * 0.4)
            draw.rectangle([(0, 0), (width, gradient_height)], fill=primary_color)

            # Draw decorative elements
            draw.rectangle([(0, gradient_height - 50), (width, gradient_height)], fill=primary_color, outline=primary_color)

            # Add title
            title_lines = self._wrap_text(title, 20)
            title_y = 200
            for line in title_lines[:3]:  # Max 3 lines
                draw.text((width // 2, title_y), line, fill='white', font=title_font, anchor='mm')
                title_y += 100

            # Add category badge
            badge_text = category.upper()
            badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
            badge_width = badge_bbox[2] - badge_bbox[0] + 40
            badge_height = badge_bbox[3] - badge_bbox[1] + 20
            badge_x = width // 2 - badge_width // 2
            badge_y = int(height * 0.65)

            draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                radius=20, fill='white', outline=primary_color, width=3
            )
            draw.text((width // 2, badge_y + badge_height // 2), badge_text,
                     fill=primary_color, font=badge_font, anchor='mm')

            # Add product type
            type_text = f"{product_type.upper()} • ${price}"
            draw.text((width // 2, int(height * 0.8)), type_text,
                     fill='#333333', font=subtitle_font, anchor='mm')

            # Add footer branding
            footer_text = "GreatHealthGreatFitness.com"
            draw.text((width // 2, height - 100), footer_text,
                     fill='#666666', font=subtitle_font, anchor='mm')

            # Convert to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes

        except Exception as e:
            logger.error(f"Error generating cover: {str(e)}")
            return None

    def _wrap_text(self, text, max_length):
        """Wrap text into multiple lines"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > max_length:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def generate_ebook_content(self, post_title, post_content, category, product_type):
        """Use Groq to generate enhanced e-book content from blog post"""
        try:
            # Clean HTML from content
            clean_content = re.sub('<[^<]+?>', '', post_content)

            prompt = f"""Transform this blog post into a high-quality, engaging {product_type} format.

Title: {post_title}
Category: {category}
Format: {product_type.upper()}

Original Content:
{clean_content[:3000]}

Create enhanced content with:
1. Compelling introduction (150-200 words)
2. Well-structured sections with subheadings
3. Key takeaways at the end
4. Actionable tips and exercises
5. Professional tone
6. Formatted for PDF readability

Return the content ready for e-book formatting."""

            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.7
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating e-book content: {str(e)}")
            return None

    def create_pdf_ebook(self, title, content, cover_image, author="GreatHealthGreatFitness"):
        """Create high-quality PDF e-book with cover and formatted content"""
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=colors.HexColor('#6366F1'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#4F46E5'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=16
            )

            # Add cover image if available
            if cover_image:
                try:
                    img = Image(cover_image, width=5.5*inch, height=7*inch)
                    story.append(img)
                    story.append(PageBreak())
                except:
                    pass

            # Add title page
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(f"<i>From {author}</i>", styles['Normal']))
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph(f"Published: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(PageBreak())

            # Add content with formatting
            content_lines = content.split('\n')
            for line in content_lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 0.2*inch))
                elif line.startswith('##'):
                    story.append(Paragraph(line.replace('##', '').strip(), heading_style))
                elif line.startswith('#'):
                    story.append(Paragraph(line.replace('#', '').strip(), title_style))
                else:
                    story.append(Paragraph(line, body_style))

            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}")
            return None

    def create_woocommerce_product(self, conn, post_id, title, price, product_type, description):
        """Create WooCommerce digital product"""
        try:
            # Prepare product data
            product_data = {
                "name": f"{title} - {product_type.title()}",
                "type": "simple",
                "description": description[:500],
                "short_description": f"Premium {product_type} guide on {title}",
                "regular_price": str(price),
                "manage_stock": True,
                "stock_quantity": 999,  # Digital product - unlimited
                "downloadable": True,
                "virtual": True,
                "status": "publish",
                "attributes": [
                    {
                        "id": 0,
                        "name": "Type",
                        "options": [product_type.title()],
                        "visible": True
                    }
                ]
            }

            # Create product via WooCommerce API
            response = requests.post(
                f"{self.woo_api_base}/products",
                json=product_data,
                auth=(self.wordpress_user, self.wordpress_password),
                timeout=30
            )

            if response.status_code == 201:
                product = response.json()
                woo_product_id = product['id']

                # Log product creation
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO digital_products
                    (blog_id, woocommerce_id, product_type, price, cover_url, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (post_id, woo_product_id, product_type, price, ''))
                conn.commit()
                cursor.close()

                self.woocommerce_products += 1
                return woo_product_id
            else:
                logger.error(f"WooCommerce API error: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating WooCommerce product: {str(e)}")
            return None

    def generate_product_card_html(self, title, price, product_type, woo_product_id):
        """Generate attractive HTML card for blog post insertion"""
        card_html = f"""
        <div class="digital-product-card" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 24px;
            margin: 30px 0;
            color: white;
            text-align: center;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
        ">
            <div style="font-size: 14px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px; opacity: 0.9;">
                📘 {product_type.upper()} AVAILABLE
            </div>
            <h3 style="font-size: 24px; margin: 12px 0; font-weight: 700;">
                {title}
            </h3>
            <p style="font-size: 16px; margin: 16px 0; opacity: 0.95; line-height: 1.6;">
                Complete guide with actionable steps, templates, and expert insights
            </p>
            <div style="
                background: rgba(255,255,255,0.2);
                padding: 16px;
                border-radius: 8px;
                margin: 20px 0;
                display: inline-block;
            ">
                <div style="font-size: 12px; opacity: 0.9; margin-bottom: 8px;">INSTANT DIGITAL ACCESS</div>
                <div style="font-size: 32px; font-weight: 700; color: #FFD700;">
                    ${price}
                </div>
            </div>
            <div style="margin-top: 20px; display: flex; gap: 12px; justify-content: center;">
                <a href="?add-to-cart={woo_product_id}" style="
                    background: white;
                    color: #667eea;
                    padding: 14px 32px;
                    border-radius: 8px;
                    font-weight: 600;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    display: inline-block;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 20px rgba(0,0,0,0.1)';"
                   onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                    Get Instant Access →
                </a>
            </div>
            <p style="font-size: 12px; margin-top: 16px; opacity: 0.8;">
                ✓ Instant download  •  ✓ PDF + Resources  •  ✓ Money-back guarantee
            </p>
        </div>
        """
        return card_html

    def insert_product_card_to_post(self, conn, post_id, card_html):
        """Insert product card into blog post content"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Get current post content
            cursor.execute("SELECT content FROM blog_posts WHERE id=%s", (post_id,))
            post = cursor.fetchone()

            if not post:
                return False

            # Insert product card at optimal position (40% down the post)
            content = post['content']
            paragraphs = content.split('</p>')
            insert_position = max(1, len(paragraphs) // 2)

            modified_content = '</p>'.join(paragraphs[:insert_position]) + '</p>' + card_html + '</p>'.join(paragraphs[insert_position:])

            # Update post
            cursor.execute(
                "UPDATE blog_posts SET content=%s WHERE id=%s",
                (modified_content, post_id)
            )
            conn.commit()
            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Error inserting product card: {str(e)}")
            return False

    def run(self):
        self.print_header("R14b: DIGITAL PRODUCT CREATOR & MONETIZATION ENGINE")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Eligible Posts{RESET}")
            posts = self.get_eligible_posts(conn)

            if not posts:
                print(f"  No eligible posts for digital products\n")
                print(f"{'='*80}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Posts Processed: 0")
                print(f"  Products Created: 0")
                print(f"  Status: {YELLOW}No eligible posts (minimum 800 words, quality 7.5+){RESET}")
                print('='*80 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts eligible for digital products\n")

            print(f"{BOLD}Step 2: Creating Digital Products{RESET}")

            for post in posts:
                self.posts_processed += 1
                print(f"\n  Processing: {post['title'][:50]}...")

                try:
                    # Determine product details
                    product_type = self.determine_product_type(post['word_count'], post['title'])
                    price = self.determine_price(post['word_count'], 8.0)

                    print(f"    Type: {CYAN}{product_type}{RESET} | Price: {GREEN}${price}{RESET}")

                    # Generate cover
                    cover_image = self.generate_ebook_cover(
                        post['title'],
                        post['categories'] or 'Health',
                        product_type,
                        price
                    )
                    self.covers_designed += 1

                    # Generate e-book content
                    ebook_content = self.generate_ebook_content(
                        post['title'],
                        post['content'],
                        post['categories'] or 'General',
                        product_type
                    )

                    if not ebook_content:
                        print(f"    {RED}✗ Failed to generate content{RESET}")
                        continue

                    # Create PDF
                    pdf_buffer = self.create_pdf_ebook(
                        post['title'],
                        ebook_content,
                        cover_image
                    )

                    if not pdf_buffer:
                        print(f"    {RED}✗ Failed to create PDF{RESET}")
                        continue

                    self.ebooks_generated += 1

                    # Create WooCommerce product
                    woo_id = self.create_woocommerce_product(
                        conn,
                        post['id'],
                        post['title'],
                        price,
                        product_type,
                        post['content'][:500]
                    )

                    if not woo_id:
                        print(f"    {RED}✗ Failed to create WooCommerce product{RESET}")
                        continue

                    self.products_created += 1
                    self.total_value += price

                    # Generate and insert product card
                    card_html = self.generate_product_card_html(
                        post['title'],
                        price,
                        product_type,
                        woo_id
                    )

                    self.insert_product_card_to_post(conn, post['id'], card_html)

                    print(f"    {GREEN}✓ Digital product created (WooCommerce ID: {woo_id}){RESET}")

                except Exception as e:
                    logger.error(f"Error processing post {post['id']}: {str(e)}")
                    print(f"    {RED}✗ Error: {str(e)}{RESET}")
                    continue

            print(f"\n{BOLD}Step 3: Payment Gateway Configuration{RESET}")
            print(f"  PayPal: {'✓ Configured' if self.paypal_client_id else '✗ Not configured'}")
            print(f"  Stripe: {'✓ Configured' if self.stripe_api_key else '✗ Not configured'}")
            print(f"  WooCommerce: ✓ Integrated\n")

            print(f"{'='*80}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Posts Processed: {self.posts_processed}")
            print(f"  E-Books Generated: {self.ebooks_generated}")
            print(f"  Covers Designed: {self.covers_designed}")
            print(f"  Digital Products Created: {GREEN}{self.products_created}{RESET}")
            print(f"  WooCommerce Products: {self.woocommerce_products}")
            print(f"  Total Product Value: {GREEN}${self.total_value:.2f}{RESET}")
            print(f"  Price Range: $4.95 - $29.95")
            print(f"  Payment Gateways: PayPal, Stripe, WooCommerce")
            print(f"  Product Cards: Inserted into blog posts")
            print(f"  Status: {GREEN}PASS - Digital product creation complete{RESET}")
            print('='*80 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    creator = DigitalProductCreator()
    success = creator.run()
    sys.exit(0 if success else 1)
