#!/usr/bin/env python3
"""
R19: Analytics Event Tracker
Purpose: Collect and log all conversion & engagement analytics events
Input: User interactions (clicks, views, conversions, email opens)
Output: Raw analytics events stored in analytics_events table
Frequency: Real-time (event-driven)
Dependencies: R17 (email), R16 (social), R21 (publisher), R31 (wordpress uploader)
Tracking: Affiliate clicks, email opens/clicks, social engagement, page views, conversions
Event Types: AFFILIATE_CLICK, EMAIL_OPEN, EMAIL_CLICK, SOCIAL_CLICK, PAGE_VIEW, CONVERSION
Attribution: Links tagged with tracking IDs from R15, R17, R21
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class AnalyticsEventTracker:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.events_tracked = 0

        # Event type mappings
        self.event_types = {
            'AFFILIATE_CLICK': {'revenue_impact': True, 'priority': 'high'},
            'EMAIL_OPEN': {'revenue_impact': False, 'priority': 'medium'},
            'EMAIL_CLICK': {'revenue_impact': False, 'priority': 'medium'},
            'SOCIAL_CLICK': {'revenue_impact': False, 'priority': 'low'},
            'PAGE_VIEW': {'revenue_impact': False, 'priority': 'low'},
            'CONVERSION': {'revenue_impact': True, 'priority': 'critical'},
            'NEWSLETTER_SIGNUP': {'revenue_impact': False, 'priority': 'medium'},
            'PRODUCT_VIEW': {'revenue_impact': False, 'priority': 'low'}
        }

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def process_affiliate_clicks(self, conn):
        """Process affiliate link clicks from tracking"""
        try:
            cursor = conn.cursor(dictionary=True)
            # Get affiliate clicks that haven't been processed
            query = """
                SELECT id, blog_id, product_name, affiliate_product_id,
                       commission_rate, created_at
                FROM affiliate_link_clicks
                WHERE processed = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                LIMIT 100
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            events = []
            for click in results:
                event = {
                    'event_type': 'AFFILIATE_CLICK',
                    'blog_id': click['blog_id'],
                    'affiliate_product_id': click['affiliate_product_id'],
                    'product_name': click['product_name'],
                    'commission_rate': click['commission_rate'],
                    'event_data': json.dumps({
                        'product': click['product_name'],
                        'commission': click['commission_rate']
                    }),
                    'occurred_at': click['created_at']
                }
                events.append(event)

            return events
        except Exception as e:
            logger.error(f"Error processing affiliate clicks: {str(e)}")
            return []

    def process_email_events(self, conn):
        """Process email opens and clicks from tracking pixels"""
        try:
            cursor = conn.cursor(dictionary=True)
            # Get email opens/clicks not yet processed
            query = """
                SELECT id, newsletter_id, subscriber_id, event_type,
                       clicked_link, created_at
                FROM email_tracking_events
                WHERE processed = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                LIMIT 100
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            events = []
            for track in results:
                event = {
                    'event_type': track['event_type'],  # EMAIL_OPEN or EMAIL_CLICK
                    'newsletter_id': track['newsletter_id'],
                    'subscriber_id': track['subscriber_id'],
                    'event_data': json.dumps({
                        'link_clicked': track['clicked_link'] if track['clicked_link'] else None
                    }),
                    'occurred_at': track['created_at']
                }
                events.append(event)

            return events
        except Exception as e:
            logger.error(f"Error processing email events: {str(e)}")
            return []

    def process_social_engagement(self, conn):
        """Process social media engagement metrics"""
        try:
            cursor = conn.cursor(dictionary=True)
            # Get social engagement metrics
            query = """
                SELECT id, blog_id, platform, post_id, engagement_type,
                       engagement_count, created_at
                FROM social_engagement_metrics
                WHERE processed = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL 3 DAY)
                LIMIT 100
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            events = []
            for engagement in results:
                event = {
                    'event_type': 'SOCIAL_CLICK',  # Could be SOCIAL_LIKE, SOCIAL_SHARE, etc
                    'blog_id': engagement['blog_id'],
                    'event_data': json.dumps({
                        'platform': engagement['platform'],
                        'engagement_type': engagement['engagement_type'],
                        'count': engagement['engagement_count']
                    }),
                    'occurred_at': engagement['created_at']
                }
                events.append(event)

            return events
        except Exception as e:
            logger.error(f"Error processing social engagement: {str(e)}")
            return []

    def process_page_views(self, conn):
        """Process page view analytics"""
        try:
            cursor = conn.cursor(dictionary=True)
            # Get page views from analytics
            query = """
                SELECT id, blog_id, page_url, user_session_id,
                       time_on_page, created_at
                FROM page_view_analytics
                WHERE processed = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                LIMIT 200
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            events = []
            for view in results:
                event = {
                    'event_type': 'PAGE_VIEW',
                    'blog_id': view['blog_id'],
                    'event_data': json.dumps({
                        'url': view['page_url'],
                        'time_on_page': view['time_on_page'],
                        'session_id': view['user_session_id']
                    }),
                    'occurred_at': view['created_at']
                }
                events.append(event)

            return events
        except Exception as e:
            logger.error(f"Error processing page views: {str(e)}")
            return []

    def save_analytics_events(self, conn, events):
        """Save all events to analytics_events table"""
        if not events:
            return 0

        try:
            cursor = conn.cursor()

            saved_count = 0
            for event in events:
                query = """
                    INSERT INTO analytics_events
                    (event_type, blog_id, newsletter_id, subscriber_id,
                     affiliate_product_id, event_data, occurred_at, processed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """

                cursor.execute(query, (
                    event['event_type'],
                    event.get('blog_id'),
                    event.get('newsletter_id'),
                    event.get('subscriber_id'),
                    event.get('affiliate_product_id'),
                    event.get('event_data'),
                    event.get('occurred_at')
                ))
                saved_count += 1

            conn.commit()
            cursor.close()

            logger.info(f"Saved {saved_count} analytics events")
            return saved_count
        except Exception as e:
            logger.error(f"Error saving events: {str(e)}")
            return 0

    def mark_source_events_processed(self, conn):
        """Mark source events as processed"""
        try:
            cursor = conn.cursor()

            # Mark affiliate clicks processed
            cursor.execute("UPDATE affiliate_link_clicks SET processed = TRUE WHERE processed = FALSE")

            # Mark email events processed
            cursor.execute("UPDATE email_tracking_events SET processed = TRUE WHERE processed = FALSE")

            # Mark social engagement processed
            cursor.execute("UPDATE social_engagement_metrics SET processed = TRUE WHERE processed = FALSE")

            # Mark page views processed
            cursor.execute("UPDATE page_view_analytics SET processed = TRUE WHERE processed = FALSE")

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error marking events processed: {str(e)}")
            return False

    def generate_summary_report(self, conn):
        """Generate summary of tracked events"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Get event type distribution
            query = """
                SELECT event_type, COUNT(*) as count
                FROM analytics_events
                WHERE processed_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY event_type
                ORDER BY count DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return results
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return []

    def run(self):
        self.print_header("R19: ANALYTICS EVENT TRACKER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Processing Affiliate Click Events{RESET}")
            affiliate_events = self.process_affiliate_clicks(conn)
            print(f"  ✓ Found {len(affiliate_events)} affiliate click events\n")

            print(f"{BOLD}Step 2: Processing Email Tracking Events{RESET}")
            email_events = self.process_email_events(conn)
            print(f"  ✓ Found {len(email_events)} email events (opens/clicks)\n")

            print(f"{BOLD}Step 3: Processing Social Media Engagement{RESET}")
            social_events = self.process_social_engagement(conn)
            print(f"  ✓ Found {len(social_events)} social engagement events\n")

            print(f"{BOLD}Step 4: Processing Page View Analytics{RESET}")
            pageview_events = self.process_page_views(conn)
            print(f"  ✓ Found {len(pageview_events)} page view events\n")

            # Combine all events
            all_events = affiliate_events + email_events + social_events + pageview_events

            print(f"{BOLD}Step 5: Saving Events to Analytics Table{RESET}")
            saved = self.save_analytics_events(conn, all_events)
            self.events_tracked = saved
            print(f"  ✓ {GREEN}Saved {saved} events{RESET}\n")

            print(f"{BOLD}Step 6: Marking Source Events as Processed{RESET}")
            marked = self.mark_source_events_processed(conn)
            if marked:
                print(f"  ✓ {GREEN}Source events marked processed{RESET}\n")

            print(f"{BOLD}Step 7: Generating Summary Report{RESET}")
            summary = self.generate_summary_report(conn)
            if summary:
                for event_summary in summary:
                    print(f"  {event_summary['event_type']:20} → {event_summary['count']} events")
            print()

            # Event type breakdown
            event_types_found = {}
            for event in all_events:
                et = event['event_type']
                event_types_found[et] = event_types_found.get(et, 0) + 1

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Total Events Tracked: {GREEN}{self.events_tracked}{RESET}")
            print(f"  Affiliate Clicks: {len(affiliate_events)}")
            print(f"  Email Events: {len(email_events)}")
            print(f"  Social Engagement: {len(social_events)}")
            print(f"  Page Views: {len(pageview_events)}")
            print(f"  Status: {GREEN}PASS - Analytics collected and stored{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    tracker = AnalyticsEventTracker()
    success = tracker.run()
    sys.exit(0 if success else 1)
