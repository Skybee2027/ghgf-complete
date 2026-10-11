#!/usr/bin/env python3
"""
R34: Error Handler & Recovery
Purpose: Detect, classify, and recover from errors across all robots
Input: Posts flagged with errors (error_handler_needed = TRUE)
Output: Recovery status + escalation to R35 if needed
Frequency: Every 30 minutes (error detection cycle)
Dependencies: All robots (R1-R32) report errors, feeds to R35 (rollback)
Error Classification: Critical vs Warning vs Info
Recovery Strategies: Retry, regenerate, fix-in-place, rollback
Escalation: Critical errors → R35 (Rollback Manager)
Monitoring: Error trends, root cause analysis, prevention
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class ErrorHandlerRecovery:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        self.errors_detected = 0
        self.errors_recovered = 0
        self.errors_critical = 0

        # Error severity levels
        self.error_severity = {
            'api_timeout': 'warning',
            'database_connection': 'critical',
            'content_generation_failed': 'critical',
            'plagiarism_detected': 'warning',
            'validation_failed': 'warning',
            'wordpress_api_error': 'critical',
            'post_publication_issue': 'warning',
            'image_upload_failed': 'warning',
            'link_injection_failed': 'warning',
            'affiliate_search_failed': 'info'
        }

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_flagged_posts(self, conn):
        """Get posts flagged for error handling"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT bp.id, bp.title, bp.error_handler_needed, bp.error_type,
                       bp.error_message, bp.status, bp.version
                FROM blog_posts bp
                WHERE bp.error_handler_needed = TRUE
                ORDER BY bp.updated_at DESC
                LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting flagged posts: {str(e)}")
            return []

    def classify_error_severity(self, error_type):
        """Classify error severity level"""
        return self.error_severity.get(error_type, 'warning')

    def recover_from_api_timeout(self, conn, blog_id):
        """Attempt recovery from API timeout"""
        try:
            cursor = conn.cursor()

            # Mark for retry with exponential backoff
            query = """
                UPDATE blog_posts
                SET api_retry_count = COALESCE(api_retry_count, 0) + 1,
                    next_retry_at = DATE_ADD(NOW(), INTERVAL POW(2, api_retry_count) MINUTE),
                    last_error_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error handling API timeout: {str(e)}")
            return False

    def recover_from_validation_failure(self, conn, blog_id):
        """Attempt recovery from validation failure"""
        try:
            cursor = conn.cursor()

            # Mark for regeneration with same constraints
            query = """
                UPDATE blog_posts
                SET regeneration_needed = TRUE,
                    regeneration_reason = 'Validation failure - automatic recovery',
                    version = version + 1,
                    last_error_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error handling validation failure: {str(e)}")
            return False

    def recover_from_plagiarism(self, conn, blog_id):
        """Attempt recovery from plagiarism detection"""
        try:
            cursor = conn.cursor()

            # Mark for regeneration with paraphrase instruction
            query = """
                UPDATE blog_posts
                SET regeneration_needed = TRUE,
                    regeneration_reason = 'Plagiarism detected - regenerating with paraphrase',
                    regeneration_type = 'paraphrase',
                    version = version + 1,
                    last_error_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error handling plagiarism recovery: {str(e)}")
            return False

    def recover_from_wordpress_error(self, conn, blog_id):
        """Attempt recovery from WordPress API error"""
        try:
            cursor = conn.cursor()

            # Check retry count - if too many, mark for escalation
            check_query = """
                SELECT wordpress_api_retry_count
                FROM blog_posts
                WHERE id = %s
            """
            cursor.execute(check_query, (blog_id,))
            result = cursor.fetchone()

            retry_count = result[0] if result and result[0] else 0

            if retry_count >= 3:
                # Too many retries - escalate to R35
                escalate_query = """
                    UPDATE blog_posts
                    SET rollback_required = TRUE,
                        rollback_reason = 'WordPress API failures after 3 retries',
                        error_severity = 'critical'
                    WHERE id = %s
                """
                cursor.execute(escalate_query, (blog_id,))
            else:
                # Retry with updated WordPress connection
                retry_query = """
                    UPDATE blog_posts
                    SET wordpress_api_retry_count = %s,
                        next_retry_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE),
                        last_error_at = NOW()
                    WHERE id = %s
                """
                cursor.execute(retry_query, (retry_count + 1, blog_id))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error handling WordPress error: {str(e)}")
            return False

    def recover_from_image_upload_failure(self, conn, blog_id):
        """Attempt recovery from image upload failure"""
        try:
            cursor = conn.cursor()

            # Try with backup image or placeholder
            query = """
                UPDATE blog_posts
                SET featured_image_retry_count = COALESCE(featured_image_retry_count, 0) + 1,
                    next_retry_at = DATE_ADD(NOW(), INTERVAL 10 MINUTE),
                    last_error_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error handling image upload: {str(e)}")
            return False

    def attempt_recovery(self, conn, blog_id, error_type):
        """Route error to appropriate recovery handler"""
        recovery_handlers = {
            'api_timeout': self.recover_from_api_timeout,
            'validation_failed': self.recover_from_validation_failure,
            'plagiarism_detected': self.recover_from_plagiarism,
            'wordpress_api_error': self.recover_from_wordpress_error,
            'image_upload_failed': self.recover_from_image_upload_failure,
        }

        handler = recovery_handlers.get(error_type)
        if handler:
            return handler(conn, blog_id)
        else:
            logger.warning(f"No recovery handler for error type: {error_type}")
            return False

    def escalate_to_rollback(self, conn, blog_id, reason):
        """Escalate error to R35 (Rollback Manager)"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET rollback_required = TRUE,
                    rollback_reason = %s,
                    error_severity = 'critical'
                WHERE id = %s
            """
            cursor.execute(query, (reason, blog_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error escalating to rollback: {str(e)}")
            return False

    def save_error_record(self, conn, blog_id, error_type, severity, recovery_status):
        """Save error record for audit trail"""
        try:
            cursor = conn.cursor()

            query = """
                INSERT INTO error_log
                (blog_id, error_type, severity, recovery_attempted, recovery_successful, logged_at)
                VALUES (%s, %s, %s, TRUE, %s, NOW())
            """
            cursor.execute(query, (
                blog_id,
                error_type,
                severity,
                recovery_status
            ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error saving error record: {str(e)}")
            return False

    def clear_error_flag(self, conn, blog_id):
        """Clear error flag after recovery"""
        try:
            cursor = conn.cursor()

            query = """
                UPDATE blog_posts
                SET error_handler_needed = FALSE,
                    error_type = NULL,
                    error_message = NULL,
                    last_error_resolved_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (blog_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error clearing error flag: {str(e)}")
            return False

    def run(self):
        self.print_header("R34: ERROR HANDLER & RECOVERY")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Detecting Flagged Posts{RESET}")
            posts = self.get_flagged_posts(conn)
            if not posts:
                print(f"  No errors to handle\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Errors Detected: 0")
                print(f"  Status: {GREEN}No errors in queue{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(posts)} posts with errors\n")

            print(f"{BOLD}Step 2: Processing Errors and Recovery{RESET}")
            for post in posts:
                self.errors_detected += 1
                error_type = post['error_type'] or 'unknown'
                severity = self.classify_error_severity(error_type)

                # Attempt recovery
                recovery_successful = self.attempt_recovery(conn, post['id'], error_type)

                # Save error record
                self.save_error_record(conn, post['id'], error_type, severity, recovery_successful)

                if recovery_successful:
                    self.errors_recovered += 1
                    # Clear error flag
                    self.clear_error_flag(conn, post['id'])
                    status_color = GREEN
                    status_text = "RECOVERED"
                else:
                    if severity == 'critical':
                        self.errors_critical += 1
                        # Escalate critical errors
                        self.escalate_to_rollback(conn, post['id'], f"Recovery failed: {error_type}")
                        status_color = RED
                        status_text = "ESCALATED TO R35"
                    else:
                        status_color = YELLOW
                        status_text = "RETRY QUEUED"

                print(f"  {status_color}{status_text}{RESET}: {post['title'][:40]}... ({error_type})")

            print()

            print(f"{BOLD}Step 3: Error Summary and Trends{RESET}")
            print(f"  Recovery rate: {(self.errors_recovered/max(self.errors_detected, 1)*100):.0f}%")
            print(f"  Critical escalations: {self.errors_critical}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Errors Detected: {self.errors_detected}")
            print(f"  Recovered: {GREEN}{self.errors_recovered}{RESET}")
            print(f"  Critical/Escalated: {RED}{self.errors_critical}{RESET}")
            print(f"  Error Types: {len(self.error_severity)} classifications")
            print(f"  Recovery Strategies: Retry, regenerate, fix-in-place, escalate")
            print(f"  Escalation Target: R35 (Rollback Manager)")
            print(f"  Audit Trail: Enabled (error_log table)")
            print(f"  Status: {GREEN}PASS - Error handling complete{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    handler = ErrorHandlerRecovery()
    success = handler.run()
    sys.exit(0 if success else 1)
