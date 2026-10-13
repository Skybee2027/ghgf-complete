#!/usr/bin/env python3
"""
R29: Final Headline Confirmation
Purpose: Finalize and confirm headline before publication
Input: Blog post with selected headline from R11
Output: Confirmed headline + search product list for R15 final affiliate placement
Frequency: Every 6 hours (final check before publishing)
Dependencies: R11 (headline testing), triggers R15 (final affiliate placement)
Conflict Resolution: R29 finalizes BEFORE R21 posts, R15 places matching products (Conflict #10)
Headline Analysis: Final SEO review, readability check, emotional triggers
Product Matching: Generate product search terms from final headline
Status: Locked for publication (cannot change headline after R29)
"""

import os
import sys
import mysql.connector
from datetime import datetime
import logging
import re
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class FinalHeadlineConfirmation:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.headlines_confirmed = 0
        self.affiliate_triggers = 0

        # Headline quality indicators
        self.power_words = [
            'ultimate', 'essential', 'proven', 'exclusive', 'breakthrough',
            'amazing', 'incredible', 'powerful', 'secret', 'guaranteed',
            'natural', 'effective', 'complete', 'simple', 'quick'
        ]

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_posts_for_final_confirmation(self, conn):
        """Get posts ready for final headline confirmation"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Changed from timestamp-based to flag-based detection
            # This prevents race conditions where R29 runs before R10 completes
            # Now processes posts where headline_locked is NULL or FALSE
            query = """
                SELECT bp.id, bp.title, bp.content, bp.topic,
                       bp.qa_check_passed, bp.version
                FROM blog_posts bp
                WHERE bp.status = 'draft'
                AND bp.qa_check_passed = TRUE
                AND (bp.headline_locked IS NULL OR bp.headline_locked = FALSE)
                ORDER BY bp.created_at DESC
                LIMIT 30
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []

    def analyze_headline_quality(self, headline):
        """Analyze final headline quality"""
        analysis = {
            'length': len(headline),
            'word_count': len(headline.split()),
            'has_number': bool(re.search(r'\d+', headline)),
            'has_question': headline.endswith('?'),
            'has_power_word': False,
            'power_word': None,
            'readability_score': 0
        }

        # Check for power words
        headline_lower = headline.lower()
        for word in self.power_words:
            if word in headline_lower:
                analysis['has_power_word'] = True
                analysis['power_word'] = word
                break

        # Readability: length check (50-70 chars optimal)
        if 50 <= analysis['length'] <= 70:
            analysis['readability_score'] = 95
        elif 40 <= analysis['length'] <= 80:
            analysis['readability_score'] = 85
        elif 30 <= analysis['length'] <= 100:
            analysis['readability_score'] = 70
        else:
            analysis['readability_score'] = 50

        # Emotional trigger analysis
        emotional_words = ['how to', 'why', 'never', 'best', 'worst', 'dangerous']
        has_emotional = any(word in headline_lower for word in emotional_words)

        if has_emotional:
            analysis['readability_score'] += 10

        return analysis

    def extract_product_keywords_from_headline(self, headline, topic):
        """Extract keywords for product research from headline"""
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'of', 'for', 'to', 'your'}

        # Extract main terms
        words = headline.lower().split()
        keywords = [w for w in words if w not in common_words and len(w) > 3]

        # Combine with topic for product search terms
        product_searches = []

        # Primary: headline keywords + topic
        for keyword in keywords[:3]:
            search_term = f"{topic} {keyword}".strip()
            product_searches.append(search_term)

        # Secondary: just topic + top keyword
        if keywords:
            product_searches.append(f"{topic} {keywords[0]}")

        return product_searches

    def confirm_headline(self, conn, blog_id, headline, analysis):
        """Confirm headline and lock for publication"""
        try:
            cursor = conn.cursor()

            # Update blog post
            query = """
                UPDATE blog_posts
                SET headline_confirmed_at = NOW(),
                    headline_final_score = %s,
                    headline_locked = TRUE
                WHERE id = %s
            """
            cursor.execute(query, (analysis['readability_score'], blog_id))

            # Create headline confirmation record
            confirmation_query = """
                INSERT INTO headline_confirmations
                (blog_id, headline_text, headline_analysis, confirmed_at)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(confirmation_query, (
                blog_id,
                headline,
                json.dumps(analysis)
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error confirming headline: {str(e)}")
            return False

    def trigger_affiliate_product_search(self, conn, blog_id, topic, search_terms):
        """Trigger R15 to search for affiliate products based on final headline"""
        try:
            cursor = conn.cursor()

            # Create product search task
            query = """
                INSERT INTO affiliate_search_queue
                (blog_id, topic, search_terms, triggered_by, created_at)
                VALUES (%s, %s, %s, 'R29_FINAL_HEADLINE', NOW())
            """
            cursor.execute(query, (
                blog_id,
                topic,
                json.dumps(search_terms)
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error triggering affiliate search: {str(e)}")
            return False

    def run(self):
        self.print_header("R29: FINAL HEADLINE CONFIRMATION")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Finding Posts Ready for Confirmation{RESET}")
            posts = self.get_posts_for_final_confirmation(conn)
            if not posts:
                print(f"  No posts ready for headline confirmation\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Headlines Confirmed: 0")
                print(f"  Status: {YELLOW}No posts in confirmation queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts ready for confirmation\n")

            print(f"{BOLD}Step 2: Analyzing and Confirming Headlines{RESET}")
            for post in posts:
                # Analyze headline
                analysis = self.analyze_headline_quality(post['title'])

                # Confirm
                confirmed = self.confirm_headline(conn, post['id'], post['title'], analysis)

                if confirmed:
                    self.headlines_confirmed += 1

                    # Extract product keywords
                    search_terms = self.extract_product_keywords_from_headline(
                        post['title'],
                        post['topic']
                    )

                    # Trigger affiliate product search
                    triggered = self.trigger_affiliate_product_search(
                        conn,
                        post['id'],
                        post['topic'],
                        search_terms
                    )

                    if triggered:
                        self.affiliate_triggers += 1

                    # Print summary
                    quality_indicator = '⭐' * int(analysis['readability_score'] / 20)
                    print(f"  ✓ CONFIRMED: {post['title'][:45]}...")
                    print(f"    Quality: {quality_indicator} ({analysis['readability_score']}%)")
                    print(f"    Search terms: {', '.join(search_terms[:2])}")
                    print()

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Headlines Confirmed: {GREEN}{self.headlines_confirmed}{RESET}")
            print(f"  Affiliate Searches Triggered: {GREEN}{self.affiliate_triggers}{RESET}")
            print(f"  Confirmation Method: Automated + keyword analysis")
            print(f"  Quality Check: SEO, readability, power words")
            print(f"  Headline Locked: TRUE (cannot change after R29)")
            print(f"  Next Stage: R15 (Affiliate product placement) → R21 (Social posting)")
            print(f"  Status: {GREEN}PASS - Headlines confirmed and locked{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    confirmer = FinalHeadlineConfirmation()
    success = confirmer.run()
    sys.exit(0 if success else 1)
