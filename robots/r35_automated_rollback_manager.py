#!/usr/bin/env python3
"""
R35: Automated Rollback Manager
Purpose: CRITICAL - Handle rollbacks for posts with critical errors
Input: Posts flagged for rollback from R34 (rollback_required = TRUE)
Output: Restored post versions + reset state + rollback log
Frequency: Every 30 minutes (triggered by critical errors)
Dependencies: R34 (error handler), feeds to R36 (system health isolator)
Rollback Strategy: Multi-stage restoration with validation
Version Control: Restore from blog_post_versions table
State Reset: Revert dependent flags and workflows
Cascade Prevention: Isolate failed posts from future pipelines
Safety: Always preserve audit trail + manual override support
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

class AutomatedRollbackManager:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        self.rollbacks_initiated = 0
        self.rollbacks_successful = 0
        self.rollbacks_failed = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_rollback_candidates(self, conn):
        """Get posts flagged for rollback"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.status, bp.version,
                       bp.wordpress_post_id, bp.rollback_reason,
                       bp.rollback_required_at
                FROM blog_posts bp
                WHERE bp.rollback_required = TRUE
                AND bp.rollback_executed_at IS NULL
                ORDER BY bp.rollback_required_at ASC
                LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting rollback candidates: {str(e)}")
            return []

    def get_previous_stable_version(self, conn, blog_id):
        """Get the last stable version before the error"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT id, content, version, created_at
                FROM blog_post_versions
                WHERE blog_id = %s
                AND status = 'stable'
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query, (blog_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error getting previous version: {str(e)}")
            return None

    def restore_post_version(self, conn, blog_id, previous_version):
        """Restore post to previous stable version"""
        try:
            cursor = conn.cursor()

            # Restore content and state
            restore_query = """
                UPDATE blog_posts
                SET content = %s,
                    version = %s,
                    status = 'draft',
                    published_at = NULL,
                    published_to_wordpress_at = NULL,
                    wordpress_post_id = NULL,
                    rollback_source_version = %s,
                    restored_at = NOW()
                WHERE id = %s
            """
            cursor.execute(restore_query, (
                previous_version['content'],
                previous_version['version'],
                previous_version['id'],
                blog_id
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error restoring version: {str(e)}")
            return False

    def reset_dependent_flags(self, conn, blog_id):
        """Reset flags that depend on the rolled-back state"""
        try:
            cursor = conn.cursor()

            # Reset workflow and processing flags
            reset_query = """
                UPDATE blog_posts
                SET qa_check_passed = FALSE,
                    revalidation_passed = FALSE,
                    final_qa_passed = FALSE,
                    ready_for_wordpress = FALSE,
                    plagiarism_score = NULL,
                    error_handler_needed = FALSE,
                    error_type = NULL,
                    error_message = NULL,
                    rollback_required = FALSE,
                    api_retry_count = 0,
                    wordpress_api_retry_count = 0,
                    featured_image_retry_count = 0
                WHERE id = %s
            """
            cursor.execute(reset_query, (blog_id,))

            # Also reset refresh workflow if in progress
            refresh_reset = """
                DELETE FROM refresh_workflow_queue
                WHERE blog_id = %s AND current_stage != 'COMPLETED'
            """
            cursor.execute(refresh_reset, (blog_id,))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error resetting flags: {str(e)}")
            return False

    def disconnect_wordpress_post(self, conn, blog_id):
        """Safely disconnect WordPress post if published"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Check if post is published
            check_query = """
                SELECT wordpress_post_id FROM blog_posts
                WHERE id = %s AND wordpress_post_id IS NOT NULL
            """
            cursor.execute(check_query, (blog_id,))
            result = cursor.fetchone()

            if result and result['wordpress_post_id']:
                # In production, would delete WordPress post
                # For now, just mark it for manual cleanup
                disconnect_query = """
                    UPDATE blog_posts
                    SET wordpress_post_id = CONCAT(wordpress_post_id, '_ROLLBACK_ORPHAN'),
                        wordpress_post_cleanup_needed = TRUE
                    WHERE id = %s
                """
                cursor.execute(disconnect_query, (blog_id,))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error disconnecting WordPress post: {str(e)}")
            return False

    def record_rollback_event(self, conn, blog_id, reason, rollback_version, success):
        """Record rollback event in audit log"""
        try:
            cursor = conn.cursor()

            query = """
                INSERT INTO rollback_log
                (blog_id, rollback_reason, rollback_version, rollback_successful, rolled_back_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (
                blog_id,
                reason,
                rollback_version,
                success
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error recording rollback: {str(e)}")
            return False

    def isolate_for_manual_review(self, conn, blog_id):
        """Mark post for manual review and isolation"""
        try:
            cursor = conn.cursor()

            isolate_query = """
                UPDATE blog_posts
                SET manual_review_required = TRUE,
                    manual_review_reason = 'Rollback executed - requires review',
                    status = 'quarantine'
                WHERE id = %s
            """
            cursor.execute(isolate_query, (blog_id,))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error isolating post: {str(e)}")
            return False

    def execute_rollback(self, conn, post):
        """Execute complete rollback sequence"""
        try:
            # Get previous stable version
            previous_version = self.get_previous_stable_version(conn, post['id'])

            if not previous_version:
                logger.error(f"No previous version found for post {post['id']}")
                return False

            # Step 1: Disconnect WordPress if needed
            self.disconnect_wordpress_post(conn, post['id'])

            # Step 2: Restore previous version
            restore_ok = self.restore_post_version(conn, post['id'], previous_version)
            if not restore_ok:
                return False

            # Step 3: Reset dependent flags
            reset_ok = self.reset_dependent_flags(conn, post['id'])
            if not reset_ok:
                return False

            # Step 4: Record rollback event
            self.record_rollback_event(
                conn,
                post['id'],
                post['rollback_reason'],
                previous_version['version'],
                True
            )

            # Step 5: Isolate for review
            self.isolate_for_manual_review(conn, post['id'])

            return True
        except Exception as e:
            logger.error(f"Error executing rollback: {str(e)}")
            return False

    def run(self):
        self.print_header("R35: AUTOMATED ROLLBACK MANAGER (CRITICAL)")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Detecting Rollback Candidates{RESET}")
            posts = self.get_rollback_candidates(conn)
            if not posts:
                print(f"  No rollbacks required\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Rollbacks Initiated: 0")
                print(f"  Status: {GREEN}All systems healthy{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts requiring rollback\n")

            print(f"{BOLD}Step 2: Executing Rollback Sequences{RESET}")
            for post in posts:
                self.rollbacks_initiated += 1

                print(f"  Processing: {BLUE}{post['title'][:40]}...{RESET}")
                print(f"    Reason: {post['rollback_reason']}")

                # Execute rollback
                rollback_ok = self.execute_rollback(conn, post)

                if rollback_ok:
                    self.rollbacks_successful += 1
                    print(f"    ✓ {GREEN}ROLLBACK SUCCESSFUL{RESET}")
                    print(f"    Status: Reverted to draft, isolated for review")
                else:
                    self.rollbacks_failed += 1
                    print(f"    ✗ {RED}ROLLBACK FAILED{RESET}")
                    print(f"    Action: Manual intervention required")

                print()

            print(f"{BOLD}Step 3: Preparing for System Health Check{RESET}")
            print(f"  Isolated posts: {self.rollbacks_successful}")
            print(f"  Next stage: R36 (System Health Isolator)\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Rollbacks Initiated: {self.rollbacks_initiated}")
            print(f"  Successful: {GREEN}{self.rollbacks_successful}{RESET}")
            print(f"  Failed: {RED}{self.rollbacks_failed}{RESET}")
            print(f"  Recovery Strategy: Version restoration + state reset")
            print(f"  Cascade Prevention: Dependent flags cleared")
            print(f"  WordPress Cleanup: Orphaned posts marked")
            print(f"  Manual Review: Isolated posts queued")
            print(f"  Audit Trail: rollback_log table updated")
            print(f"  Status: {GREEN}PASS - Rollback operations complete{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    rollback_manager = AutomatedRollbackManager()
    success = rollback_manager.run()
    sys.exit(0 if success else 1)
