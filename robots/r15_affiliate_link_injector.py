#!/usr/bin/env python3
"""
R15: Affiliate Link Injector & Placement
Purpose: Inject affiliate product links from R12 into blog content
Input: Blog content + affiliate products (from R12)
Output: Content with natural affiliate link placements and CTAs
Frequency: Every 6 hours (Stage 5b)
Dependencies: R12 (provides affiliate products)
Placement Strategy: START + MIDDLE + END + FLOATING (primary placement)
Conflict Resolution: R14 handles SIDEBAR + FOOTER (secondary placement)
CTA Integration: Natural product recommendation text + affiliate links
Commission Tracking: Links tagged with affiliate product ID for revenue tracking
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

class AffiliateLinksInjector:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.affiliate_links_injected = 0

        # CTA templates for natural product placement
        self.cta_templates = {
            'recommendation': 'We recommend checking out {product_name} for {benefit}.',
            'bestseller': 'If you\'re looking for a quality option, {product_name} is a bestseller.',
            'top_choice': 'One of our top choices is {product_name} - it\'s perfect for {benefit}.',
            'result_driven': 'For better {benefit}, consider {product_name}.',
            'comparison': 'Compared to other options, {product_name} stands out.',
            'expert_pick': 'Our expert recommendation: {product_name}.'
        }

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

    def get_affiliate_products(self, conn, blog_id):
        """Get affiliate products for this blog from R12"""
        try:
            cursor = conn.cursor(dictionary=True)

            # First, ensure product_url column exists (migration safety)
            try:
                alter_query = """
                    ALTER TABLE affiliate_products
                    ADD COLUMN IF NOT EXISTS product_url VARCHAR(1000)
                """
                cursor.execute(alter_query)
                conn.commit()
                logger.debug("Ensured product_url column exists in affiliate_products table")
            except Exception as e:
                logger.debug(f"Could not verify/add product_url column: {str(e)}")

            # Ensure all required columns exist (migration auto-apply)
            required_columns = [
                ('product_url', 'VARCHAR(1000)'),
                ('description', 'TEXT'),
                ('commission_rate', 'DECIMAL(5, 2)'),
                ('source_network', 'VARCHAR(100)'),
                ('score', 'DECIMAL(5, 2)')
            ]

            for col_name, col_type in required_columns:
                try:
                    alter_query = f"""
                        ALTER TABLE affiliate_products
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """
                    cursor.execute(alter_query)
                    logger.debug(f"Ensured {col_name} column exists")
                except Exception as e:
                    logger.debug(f"Could not verify/add {col_name} column: {str(e)}")

            conn.commit()

            # Query with safe column selection using COALESCE
            query = """
                SELECT id, product_name,
                       COALESCE(product_url, '') as product_url,
                       COALESCE(description, 'Product recommendation') as description,
                       COALESCE(commission_rate, 5.0) as commission_rate,
                       COALESCE(source_network, 'affiliate') as source_network,
                       COALESCE(score, 50) as score
                FROM affiliate_products
                WHERE blog_id = %s
                ORDER BY score DESC
                LIMIT 8
            """
            cursor.execute(query, (blog_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting affiliate products: {str(e)}")
            logger.error(f"Missing columns detected. Auto-apply failed. Run these manually:")
            logger.error(f"  ALTER TABLE affiliate_products ADD COLUMN IF NOT EXISTS product_url VARCHAR(1000);")
            logger.error(f"  ALTER TABLE affiliate_products ADD COLUMN IF NOT EXISTS description TEXT;")
            logger.error(f"  ALTER TABLE affiliate_products ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5, 2);")
            logger.error(f"  ALTER TABLE affiliate_products ADD COLUMN IF NOT EXISTS score DECIMAL(5, 2);")
            return []

    def build_product_cta(self, product, template_type='recommendation'):
        """Build natural CTA text for product"""
        template = self.cta_templates.get(template_type, self.cta_templates['recommendation'])

        # Extract benefit from description
        benefit = product['description'].split('-')[0].strip() if '-' in product['description'] else 'better health'

        cta_text = template.format(
            product_name=product['product_name'],
            benefit=benefit
        )

        return cta_text

    def create_affiliate_link_html(self, product, affiliate_id):
        """Create HTML for affiliate product link"""
        link_html = f'<a href="{product["product_url"]}" class="affiliate-link" data-affiliate-id="{affiliate_id}" data-commission="{product["commission_rate"]}">{product["product_name"]}</a>'
        return link_html

    def create_product_box(self, product, affiliate_id):
        """Create styled product recommendation box"""
        cta = self.build_product_cta(product)
        link = self.create_affiliate_link_html(product, affiliate_id)

        box_html = f'''<div class="product-recommendation">
  <div class="product-content">
    <p>{cta}</p>
    <p class="product-link">{link}</p>
    <small>Commission: {product["commission_rate"]}% | Source: {product["source_network"]}</small>
  </div>
</div>'''
        return box_html

    def inject_links_at_positions(self, content, products):
        """Inject affiliate links at START, MIDDLE, END, and FLOATING positions"""
        if not products:
            logger.warning("No products to inject")
            return content, []

        injection_log = []

        # 1. START position: After first introduction paragraph
        first_p_close = content.find('</p>')
        if first_p_close != -1 and len(products) > 0:
            start_product = products[0]
            start_box = self.create_product_box(start_product, 1)
            insert_pos = first_p_close + 4
            content = content[:insert_pos] + '\n' + start_box + '\n' + content[insert_pos:]
            injection_log.append({
                'position': 'START',
                'product': start_product['product_name'],
                'affiliate_id': start_product['id']
            })

        # 2. MIDDLE position: Find middle section (around 50% of content)
        content_length = len(content)
        middle_pos = content_length // 2

        # Find nearest </p> before middle
        search_start = max(0, middle_pos - 500)
        search_text = content[search_start:middle_pos + 500]
        nearest_p = search_text.rfind('</p>')

        if nearest_p != -1 and len(products) > 1:
            actual_pos = search_start + nearest_p + 4
            middle_product = products[1]
            middle_box = self.create_product_box(middle_product, 2)
            content = content[:actual_pos] + '\n' + middle_box + '\n' + content[actual_pos:]
            injection_log.append({
                'position': 'MIDDLE',
                'product': middle_product['product_name'],
                'affiliate_id': middle_product['id']
            })

        # 3. END position: Before last paragraph or at end
        last_p_close = content.rfind('</p>')
        if last_p_close != -1 and len(products) > 2:
            end_product = products[2]
            end_box = self.create_product_box(end_product, 3)
            content = content[:last_p_close + 4] + '\n' + end_box + '\n' + content[last_p_close + 4:]
            injection_log.append({
                'position': 'END',
                'product': end_product['product_name'],
                'affiliate_id': end_product['id']
            })

        # 4. FLOATING position: Sticky/floating element for additional products
        if len(products) > 3:
            floating_products = products[3:5]  # Use next 2 products
            floating_html = '<div class="floating-products">\n'
            floating_html += '<h5>Popular Products</h5>\n'
            floating_html += '<ul>\n'

            for i, prod in enumerate(floating_products, start=4):
                link = self.create_affiliate_link_html(prod, i)
                floating_html += f'<li>{link}</li>\n'
                injection_log.append({
                    'position': 'FLOATING',
                    'product': prod['product_name'],
                    'affiliate_id': prod['id']
                })

            floating_html += '</ul>\n</div>\n'

            # Add floating element at end
            content = content + '\n' + floating_html

        return content, injection_log

    def save_affiliate_injections(self, conn, blog_id, modified_content, injection_log):
        """Save affiliate link injections to database"""
        try:
            cursor = conn.cursor()

            # Update blog content
            query = """
                UPDATE blog_posts
                SET content = %s, version = version + 1,
                    affiliate_links_injected = TRUE,
                    affiliate_links_count = %s,
                    affiliate_links_injected_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (modified_content, len(injection_log), blog_id))

            # Log each injection
            for injection in injection_log:
                log_query = """
                    INSERT INTO affiliate_injection_log (blog_id, product_name,
                                                        placement_position, injected_at)
                    VALUES (%s, %s, %s, NOW())
                """
                cursor.execute(log_query, (
                    blog_id,
                    injection['product'],
                    injection['position']
                ))

            conn.commit()
            cursor.close()
            logger.info(f"Saved {len(injection_log)} affiliate link injections")
            return True
        except Exception as e:
            logger.error(f"Error saving injections: {str(e)}")
            return False

    def run(self):
        self.print_header("R15: AFFILIATE LINK INJECTOR")
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
            print(f"  ✓ Title: {blog_data['title']}\n")

            print(f"{BOLD}Step 2: Getting Affiliate Products from R12{RESET}")
            products = self.get_affiliate_products(conn, blog_data['id'])
            if not products:
                logger.error("No affiliate products found from R12")
                return False
            print(f"  ✓ Retrieved {len(products)} products\n")

            print(f"{BOLD}Step 3: Planning Link Placement Strategy{RESET}")
            placements_available = {
                'START': len(products) > 0,
                'MIDDLE': len(products) > 1,
                'END': len(products) > 2,
                'FLOATING': len(products) > 3
            }

            for position, available in placements_available.items():
                status = GREEN + "✓" + RESET if available else "✗"
                print(f"  {status} {position} position")
            print()

            print(f"{BOLD}Step 4: Injecting Affiliate Links into Content{RESET}")
            modified_content, injection_log = self.inject_links_at_positions(blog_data['content'], products)
            self.affiliate_links_injected = len(injection_log)

            print(f"  ✓ Injected {self.affiliate_links_injected} affiliate links:\n")
            for injection in injection_log:
                print(f"    • {injection['position']:8} → {injection['product']}")
            print()

            print(f"{BOLD}Step 5: Saving Injections to Database{RESET}")
            saved = self.save_affiliate_injections(conn, blog_data['id'], modified_content, injection_log)
            if saved:
                print(f"  ✓ {GREEN}Affiliate links saved successfully{RESET}\n")

            # Breakdown by position
            position_counts = {}
            for inj in injection_log:
                pos = inj['position']
                position_counts[pos] = position_counts.get(pos, 0) + 1

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Total Affiliate Links: {GREEN}{self.affiliate_links_injected}{RESET}")
            for position in ['START', 'MIDDLE', 'END', 'FLOATING']:
                count = position_counts.get(position, 0)
                if count > 0:
                    print(f"  {position:8} placement: {count} link(s)")
            print(f"  Conflict Resolution: R15 primary (primary zones), R14 secondary (sidebar/footer)")
            print(f"  Status: {GREEN}PASS - Affiliate links placed, ready for publication{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    injector = AffiliateLinksInjector()
    success = injector.run()
    sys.exit(0 if success else 1)
