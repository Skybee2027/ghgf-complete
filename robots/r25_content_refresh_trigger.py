#!/usr/bin/env python3
"""
R25: Content Refresh Trigger
Purpose: Trigger weekly content refresh workflow (Monday/Wednesday/Friday)
Input: Previously published posts 30-90 days old
Output: Refresh tasks queued for R27 (revalidation) + R28 (plagiarism recheck)
Frequency: 3x weekly (Monday, Wednesday, Friday 9 AM UTC)
Dependencies: R13 (keyword updates), triggers R27, R28, R12
Conflict Resolution: Refreshed content re-runs R12, R27, R28 before re-publication (Conflict #4)
Refresh Strategy: Update with fresh keywords, new examples, latest data
Quality Threshold: Only refresh posts with >500 views in past month
Task Queuing: Batches 10-15 posts per refresh cycle
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class ContentRefreshTrigger:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.refresh_tasks_queued = 0
        self.posts_eligible = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def is_refresh_day(self):
        """Check if today is a refresh day (Monday, Wednesday, Friday)"""
        today = datetime.now().weekday()
        refresh_days = [0, 2, 4]  # Monday=0, Wednesday=2, Friday=4
        return today in refresh_days

    def get_eligible_posts_for_refresh(self, conn):
        """Get posts that meet refresh criteria"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Posts published 30-90 days ago with good engagement
            query = """
                SELECT bp.id, bp.title, bp.topic, bp.published_at,
                       COUNT(av.id) as view_count,
                       AVG(ae.event_type) as engagement_type
                FROM blog_posts bp
                LEFT JOIN analytics_page_views av ON bp.id = av.blog_id
                LEFT JOIN analytics_events ae ON bp.id = ae.blog_id
                WHERE bp.status = 'published'
                AND bp.published_at > DATE_SUB(NOW(), INTERVAL 90 DAY)
                AND bp.published_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
                AND bp.last_refreshed IS NULL OR bp.last_refreshed < DATE_SUB(NOW(), INTERVAL 60 DAY)
                GROUP BY bp.id
                HAVING view_count > 500
                ORDER BY view_count DESC
                LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting eligible posts: {str(e)}")
            return []

    def create_refresh_task(self, conn, blog_id, refresh_type='full'):
        """Create refresh task for a blog post"""
        try:
            cursor = conn.cursor()

            query = """
                INSERT INTO content_refresh_tasks
                (blog_id, refresh_type, status, created_at)
                VALUES (%s, %s, 'queued', NOW())
            """
            cursor.execute(query, (blog_id, refresh_type))

            task_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            logger.info(f"Created refresh task {task_id} for blog {blog_id}")
            return task_id
        except Exception as e:
            logger.error(f"Error creating refresh task: {str(e)}")
            return None

    def queue_refresh_workflow(self, conn, blog_id):
        """Queue the full refresh workflow (R12 → R27 → R28)"""
        try:
            cursor = conn.cursor()

            # Create workflow entry
            query = """
                INSERT INTO refresh_workflow_queue
                (blog_id, current_stage, workflow_sequence, created_at)
                VALUES (%s, 'R12_PRODUCT_RESEARCH', 'R12->R27->R28->REPUBLISH', NOW())
            """
            cursor.execute(query, (blog_id,))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error queuing refresh workflow: {str(e)}")
            return False

    def update_last_refreshed(self, conn, blog_id):
        """Update last_refreshed timestamp"""
        try:
            cursor = conn.cursor()
            query = "UPDATE blog_posts SET last_refreshed = NOW() WHERE id = %s"
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error updating last_refreshed: {str(e)}")
            return False

    def generate_refresh_report(self, conn):
        """Generate summary of refresh activities"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT refresh_type, COUNT(*) as count,
                       MAX(created_at) as latest
                FROM content_refresh_tasks
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY refresh_type
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return results
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return []

    def run(self):
        self.print_header("R25: CONTENT REFRESH TRIGGER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Check if today is refresh day
        if not self.is_refresh_day():
            today = datetime.now().strftime('%A')
            print(f"{YELLOW}Not a refresh day (today is {today}){RESET}")
            print(f"Refresh runs on: Monday, Wednesday, Friday\n")
            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Refresh Tasks Queued: 0")
            print(f"  Status: {YELLOW}SKIP - Not a scheduled refresh day{RESET}")
            print('='*70 + "\n")
            return True

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Checking Content Refresh Eligibility{RESET}")
            eligible_posts = self.get_eligible_posts_for_refresh(conn)
            self.posts_eligible = len(eligible_posts)

            if not eligible_posts:
                print(f"  No posts meet refresh criteria\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Refresh Tasks Queued: 0")
                print(f"  Status: {YELLOW}No eligible posts for refresh{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(eligible_posts)} posts eligible for refresh\n")

            print(f"{BOLD}Step 2: Creating Refresh Tasks{RESET}")
            refresh_by_topic = {}

            for post in eligible_posts[:15]:  # Limit to 15 per cycle
                task_id = self.create_refresh_task(conn, post['id'], 'full_refresh')

                if task_id:
                    self.refresh_tasks_queued += 1
                    topic = post['topic']
                    refresh_by_topic[topic] = refresh_by_topic.get(topic, 0) + 1

                    # Queue the workflow
                    self.queue_refresh_workflow(conn, post['id'])

                    print(f"  ✓ Queued: {post['title'][:50]}...")

            print()

            print(f"{BOLD}Step 3: Workflow Stage Preparation{RESET}")
            print(f"  Queued workflow: R12 (Products) → R27 (Revalidation) → R28 (Plagiarism)\n")

            print(f"{BOLD}Step 4: Generating Refresh Summary{RESET}")
            report = self.generate_refresh_report(conn)
            if report:
                for row in report:
                    print(f"  {row['refresh_type']:20} → {row['count']} tasks")
            print()

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Refresh Day: {datetime.now().strftime('%A')}")
            print(f"  Eligible Posts Found: {self.posts_eligible}")
            print(f"  Refresh Tasks Queued: {GREEN}{self.refresh_tasks_queued}{RESET}")
            for topic, count in refresh_by_topic.items():
                print(f"    {topic}: {count}")
            print(f"  Refresh Workflow: R12 → R27 → R28 → Re-publish")
            print(f"  Next Refresh: 3 days (after Monday/Wednesday/Friday schedule)")
            print(f"  Status: {GREEN}PASS - Content refresh cycle initiated{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    trigger = ContentRefreshTrigger()
    success = trigger.run()
    sys.exit(0 if success else 1)
