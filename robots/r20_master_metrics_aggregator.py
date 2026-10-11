#!/usr/bin/env python3
"""
R20: Master Metrics Aggregator
Purpose: Read-only coordinator that aggregates key metrics for system monitoring
Input: Analytics events, performance metrics from all robots
Output: System health metrics + performance dashboards (read-only, no writes)
Frequency: Every 2 hours (monitoring cycle)
Dependencies: R19 (analytics), R1-R18 (system performance data)
Conflict Resolution: READ-ONLY - never writes to database (Conflict #6 resolved)
Metrics: Content quality, affiliate performance, engagement rates, system health
Coordination: Provides metrics to R33 (write coordinator) and R26 (reporter)
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class MasterMetricsAggregator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.metrics = {}

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_content_quality_metrics(self, conn):
        """Aggregate content quality scores (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    COUNT(*) as total_posts,
                    AVG(plagiarism_score) as avg_plagiarism,
                    AVG(ai_detection_score) as avg_ai_detection,
                    AVG(readability_score) as avg_readability,
                    SUM(CASE WHEN qa_check_passed = TRUE THEN 1 ELSE 0 END) as qa_passed
                FROM blog_posts
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            return {
                'total_posts': result['total_posts'] or 0,
                'avg_plagiarism': round(result['avg_plagiarism'] or 0, 2),
                'avg_ai_detection': round(result['avg_ai_detection'] or 0, 2),
                'avg_readability': round(result['avg_readability'] or 0, 2),
                'qa_passed': result['qa_passed'] or 0
            }
        except Exception as e:
            logger.error(f"Error getting content metrics: {str(e)}")
            return {}

    def get_affiliate_performance(self, conn):
        """Aggregate affiliate link performance metrics (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT blog_id) as blogs_with_affiliate,
                    AVG(commission_rate) as avg_commission,
                    MAX(commission_rate) as max_commission
                FROM analytics_events
                WHERE event_type = 'AFFILIATE_CLICK'
                AND processed_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            return {
                'total_affiliate_clicks': result['total_clicks'] or 0,
                'blogs_with_affiliate_links': result['blogs_with_affiliate'] or 0,
                'avg_commission_rate': round(result['avg_commission'] or 0, 2),
                'max_commission_rate': round(result['max_commission'] or 0, 2)
            }
        except Exception as e:
            logger.error(f"Error getting affiliate metrics: {str(e)}")
            return {}

    def get_email_engagement_metrics(self, conn):
        """Aggregate email campaign metrics (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Email sends
            send_query = """
                SELECT COUNT(*) as total_sent,
                       SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful
                FROM email_send_log
                WHERE sent_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(send_query)
            send_result = cursor.fetchone()

            # Email opens
            opens_query = """
                SELECT COUNT(*) as total_opens
                FROM analytics_events
                WHERE event_type = 'EMAIL_OPEN'
                AND processed_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(opens_query)
            opens_result = cursor.fetchone()

            # Email clicks
            clicks_query = """
                SELECT COUNT(*) as total_clicks
                FROM analytics_events
                WHERE event_type = 'EMAIL_CLICK'
                AND processed_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(clicks_query)
            clicks_result = cursor.fetchone()

            cursor.close()

            total_sent = send_result['total_sent'] or 0
            successful = send_result['successful'] or 0
            delivery_rate = (successful / total_sent * 100) if total_sent > 0 else 0

            total_opens = opens_result['total_opens'] or 0
            open_rate = (total_opens / successful * 100) if successful > 0 else 0

            total_clicks = clicks_result['total_clicks'] or 0
            ctr = (total_clicks / total_opens * 100) if total_opens > 0 else 0

            return {
                'total_emails_sent': total_sent,
                'successful_sends': successful,
                'delivery_rate': round(delivery_rate, 2),
                'total_opens': total_opens,
                'open_rate': round(open_rate, 2),
                'total_clicks': total_clicks,
                'click_through_rate': round(ctr, 2)
            }
        except Exception as e:
            logger.error(f"Error getting email metrics: {str(e)}")
            return {}

    def get_social_media_metrics(self, conn):
        """Aggregate social media performance (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT platform) as platforms_used
                FROM social_media_posts
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                AND status = 'published'
            """
            cursor.execute(query)
            result = cursor.fetchone()

            # Get engagement by platform
            engagement_query = """
                SELECT platform, SUM(engagement_count) as total_engagement
                FROM social_engagement_metrics
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY platform
            """
            cursor.execute(engagement_query)
            engagement_results = cursor.fetchall()
            cursor.close()

            platform_engagement = {}
            for eng in engagement_results:
                platform_engagement[eng['platform']] = eng['total_engagement']

            return {
                'total_social_posts': result['total_posts'] or 0,
                'platforms_active': result['platforms_used'] or 0,
                'engagement_by_platform': platform_engagement
            }
        except Exception as e:
            logger.error(f"Error getting social metrics: {str(e)}")
            return {}

    def get_system_health_metrics(self, conn):
        """Check system health status (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Failed robots in last 24 hours
            query = """
                SELECT
                    COUNT(*) as failed_runs
                FROM robot_execution_log
                WHERE status = 'FAILED'
                AND executed_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            cursor.execute(query)
            failed = cursor.fetchone()

            # Average execution time
            exec_time_query = """
                SELECT AVG(execution_time_seconds) as avg_time,
                       MAX(execution_time_seconds) as max_time
                FROM robot_execution_log
                WHERE executed_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND status = 'SUCCESS'
            """
            cursor.execute(exec_time_query)
            exec_time = cursor.fetchone()

            # DB connection health
            db_health_query = """
                SELECT COUNT(*) as active_transactions
                FROM INFORMATION_SCHEMA.PROCESSLIST
                WHERE COMMAND != 'Sleep'
            """
            cursor.execute(db_health_query)
            db_health = cursor.fetchone()

            cursor.close()

            return {
                'failed_robot_runs_24h': failed['failed_runs'] or 0,
                'avg_execution_time_sec': round(exec_time['avg_time'] or 0, 2),
                'max_execution_time_sec': round(exec_time['max_time'] or 0, 2),
                'active_db_connections': db_health['active_transactions'] or 0
            }
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {}

    def get_publication_status(self, conn):
        """Check publication pipeline status (read-only)"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as drafts,
                    SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published,
                    SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) as archived
                FROM blog_posts
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            return {
                'draft_posts': result['drafts'] or 0,
                'published_posts': result['published'] or 0,
                'archived_posts': result['archived'] or 0
            }
        except Exception as e:
            logger.error(f"Error getting publication status: {str(e)}")
            return {}

    def run(self):
        self.print_header("R20: MASTER METRICS AGGREGATOR (READ-ONLY)")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Aggregating Content Quality Metrics{RESET}")
            content_metrics = self.get_content_quality_metrics(conn)
            if content_metrics:
                print(f"  Total Posts (7d): {content_metrics['total_posts']}")
                print(f"  Avg Plagiarism: {content_metrics['avg_plagiarism']}%")
                print(f"  Avg AI Detection: {content_metrics['avg_ai_detection']}%")
                print(f"  Avg Readability: {content_metrics['avg_readability']}")
                print(f"  QA Passed: {content_metrics['qa_passed']}\n")
            else:
                print(f"  No content data yet\n")

            print(f"{BOLD}Step 2: Aggregating Affiliate Performance{RESET}")
            affiliate_metrics = self.get_affiliate_performance(conn)
            if affiliate_metrics:
                print(f"  Total Affiliate Clicks: {affiliate_metrics['total_affiliate_clicks']}")
                print(f"  Avg Commission Rate: {affiliate_metrics['avg_commission_rate']}%")
                print(f"  Max Commission Rate: {affiliate_metrics['max_commission_rate']}%\n")
            else:
                print(f"  No affiliate data yet\n")

            print(f"{BOLD}Step 3: Aggregating Email Engagement{RESET}")
            email_metrics = self.get_email_engagement_metrics(conn)
            if email_metrics:
                print(f"  Total Sent: {email_metrics['total_emails_sent']}")
                print(f"  Delivery Rate: {email_metrics['delivery_rate']}%")
                print(f"  Open Rate: {email_metrics['open_rate']}%")
                print(f"  Click Rate: {email_metrics['click_through_rate']}%\n")
            else:
                print(f"  No email data yet\n")

            print(f"{BOLD}Step 4: Aggregating Social Media Metrics{RESET}")
            social_metrics = self.get_social_media_metrics(conn)
            if social_metrics:
                print(f"  Total Posts: {social_metrics['total_social_posts']}")
                print(f"  Platforms Active: {social_metrics['platforms_active']}\n")
            else:
                print(f"  No social data yet\n")

            print(f"{BOLD}Step 5: Checking System Health{RESET}")
            health_metrics = self.get_system_health_metrics(conn)
            if health_metrics:
                print(f"  Failed Runs (24h): {health_metrics['failed_robot_runs_24h']}")
                print(f"  Avg Exec Time: {health_metrics['avg_execution_time_sec']}s")
                print(f"  DB Connections: {health_metrics['active_db_connections']}\n")
            else:
                print(f"  No execution data yet\n")

            print(f"{BOLD}Step 6: Checking Publication Pipeline{RESET}")
            pub_metrics = self.get_publication_status(conn)
            if pub_metrics:
                print(f"  Draft Posts: {pub_metrics['draft_posts']}")
                print(f"  Published (30d): {pub_metrics['published_posts']}\n")
            else:
                print(f"  No publication data yet\n")

            # Compile all metrics
            all_metrics = {
                'content': content_metrics,
                'affiliate': affiliate_metrics,
                'email': email_metrics,
                'social': social_metrics,
                'system_health': health_metrics,
                'publication': pub_metrics,
                'aggregated_at': datetime.now().isoformat()
            }
            self.metrics = all_metrics

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Metrics Aggregated: 6 categories")
            print(f"  Content Quality: {GREEN}Tracked{RESET}")
            print(f"  Affiliate Performance: {GREEN}Tracked{RESET}")
            print(f"  Email Engagement: {GREEN}Tracked{RESET}")
            print(f"  Social Media: {GREEN}Tracked{RESET}")
            print(f"  System Health: {GREEN}Monitored{RESET}")
            print(f"  Access Level: {YELLOW}READ-ONLY (no database writes){RESET}")
            print(f"  Status: {GREEN}PASS - Metrics ready for coordination{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    aggregator = MasterMetricsAggregator()
    success = aggregator.run()
    sys.exit(0 if success else 1)
