#!/usr/bin/env python3
"""
Master Orchestration Script for GHGF 42-Robot Autonomous Blogging System
Runs the complete content pipeline: Generation → QA → Monetization → Publishing → Monitoring
Executes one full cycle producing 1 post every 6 hours
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROBOTS_DIR = os.path.join(os.path.dirname(__file__), 'robots')

# Pipeline sequence - COMPLETE 42-ROBOT PIPELINE
# All robots must execute in order for proper QA verification before publishing
PIPELINE = [
    # Content Generation Layer (R2-R3)
    ('r2_blog_title_generator.py', 'R2: Blog Title Generator'),
    ('r3_blog_content_generator.py', 'R3: Blog Content Generator'),

    # Quality & Safety Checks (R4-R5)
    ('r4_plagiarism_checker.py', 'R4: Plagiarism Checker'),
    ('r5_ai_detection_filter.py', 'R5: AI Detection Filter'),

    # Content Enhancement (R6-R8)
    ('r6_keyword_optimizer.py', 'R6: Keyword Optimizer'),
    ('r7_image_finder.py', 'R7: Image Finder'),
    ('r8_alt_text_generator.py', 'R8: Alt Text Generator'),

    # QA Format Verification (R9-R10)
    ('r9_qa_format_checker_first_pass.py', 'R9: QA Format Checker - First Pass'),
    ('r10_revalidation_second_pass.py', 'R10: Revalidation Second Pass'),

    # Deep Editorial Quality Review (R9.5) - NEW: AI-powered editorial quality check
    ('r9_5_deep_content_reviewer.py', 'R9.5: Deep Content Reviewer'),

    # Enhancement & Validation (R11-R15)
    ('r11_headline_testing.py', 'R11: Headline Testing'),
    ('r12_product_research.py', 'R12: Product Research'),
    ('r13_keywords_cache_refresh.py', 'R13: Keywords Cache Refresh'),
    ('r14_static_link_injector.py', 'R14: Static Link Injector'),
    ('r14b_digital_product_creator.py', 'R14b: Digital Product Creator'),
    ('r15_affiliate_link_injector.py', 'R15: Affiliate Link Injector'),

    # Distribution & Monitoring (R16-R28)
    ('r16_social_media_drafting.py', 'R16: Social Media Drafting'),
    ('r17_email_newsletter_builder.py', 'R17: Email Newsletter Builder'),
    ('r18_email_scheduler.py', 'R18: Email Scheduler'),
    ('r19_analytics_event_tracker.py', 'R19: Analytics Event Tracker'),
    ('r20_master_metrics_aggregator.py', 'R20: Master Metrics Aggregator'),
    ('r21_social_media_publisher.py', 'R21: Social Media Publisher'),
    ('r23_social_distributor.py', 'R23: Social Distributor'),
    ('r24_social_engagement_monitor.py', 'R24: Social Engagement Monitor'),
    ('r25_content_refresh_trigger.py', 'R25: Content Refresh Trigger'),
    ('r26_dashboard_reporter.py', 'R26: Dashboard Reporter'),
    ('r27_content_revalidation_refresh.py', 'R27: Content Revalidation Refresh'),
    ('r28_plagiarism_recheck_refresh.py', 'R28: Plagiarism Recheck Refresh'),

    # Final Verification & Publication (R29-R31)
    ('r29_final_headline_confirmation.py', 'R29: Final Headline Confirmation'),
    ('r30_final_qa_verification.py', 'R30: Final QA Verification'),
    ('r31_wordpress_uploader_publisher.py', 'R31: WordPress Uploader/Publisher'),

    # Post-Publication Monitoring (R32-R36)
    ('r32_post_publication_monitoring.py', 'R32: Post Publication Monitoring'),
    ('r33_master_control_coordinator.py', 'R33: Master Control Coordinator'),
    ('r34_error_handler_recovery.py', 'R34: Error Handler/Recovery'),
    ('r35_automated_rollback_manager.py', 'R35: Automated Rollback Manager'),
    ('r36_system_health_isolator.py', 'R36: System Health Isolator'),
]

def run_robot(robot_file, robot_name):
    """Execute a single robot and return success status"""
    robot_path = os.path.join(ROBOTS_DIR, robot_file)

    if not os.path.exists(robot_path):
        logger.error(f"✗ {robot_name} - File not found: {robot_path}")
        return False

    try:
        logger.info(f"▶ Running {robot_name}...")
        result = subprocess.run(
            ['python3', robot_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per robot
            env=os.environ  # Explicitly pass environment variables (API keys, DB config, etc)
        )

        if result.returncode == 0:
            logger.info(f"✅ {robot_name} - SUCCESS")
            return True
        else:
            logger.warning(f"⚠️  {robot_name} - Non-zero exit code: {result.returncode}")

            # Log FULL error output (not truncated!)
            if result.stderr:
                logger.warning(f"   STDERR Output:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.warning(f"      {line}")

            if result.stdout:
                logger.warning(f"   STDOUT Output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.warning(f"      {line}")

            # Also write to error log file for debugging
            error_log_file = f"error_log_{robot_name.replace(': ', '_').replace(' ', '_')}.txt"
            with open(error_log_file, 'w') as f:
                f.write(f"Robot: {robot_name}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("=== STDERR ===\n")
                f.write(result.stderr)
                f.write("\n\n=== STDOUT ===\n")
                f.write(result.stdout)

            logger.warning(f"   Full error logged to: {error_log_file}")

            return False

    except subprocess.TimeoutExpired:
        logger.error(f"✗ {robot_name} - TIMEOUT (>5 min)")
        return False
    except Exception as e:
        logger.error(f"✗ {robot_name} - EXCEPTION: {str(e)}")
        return False

def verify_database():
    """Verify database connectivity before running robots"""
    try:
        import mysql.connector
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging'),
            'connection_timeout': 5
        }

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check for critical tables
        critical_tables = ['blog_posts', 'topics', 'topic_rotation', 'trending_keywords']
        for table in critical_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                logger.error(f"✗ CRITICAL: Table '{table}' not found in database")
                cursor.close()
                conn.close()
                return False

        cursor.close()
        conn.close()
        logger.info("✓ Database verification passed - all critical tables exist")
        return True
    except Exception as e:
        logger.error(f"✗ Database verification failed: {str(e)}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("GHGF 42-ROBOT AUTONOMOUS BLOGGING SYSTEM")
    logger.info("Starting Full Pipeline Cycle")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # Verify database before running robots
    if not verify_database():
        logger.error("✗ Database verification failed - aborting pipeline")
        print("\n❌ PIPELINE FAILED: Database verification failed")
        return 1

    successful = 0
    failed = 0
    skipped = 0
    critical_robots_passed = True  # Track if critical path robots succeed

    for robot_file, robot_name in PIPELINE:
        success = run_robot(robot_file, robot_name)
        if success:
            successful += 1
        else:
            failed += 1
            # Check if a critical path robot failed (R2, R3, R30, or R31)
            # R30 = Final QA verification (CRITICAL for proper QA)
            # R31 = WordPress publisher (final step)
            if robot_name in [
                'R2: Blog Title Generator',
                'R3: Blog Content Generator',
                'R30: Final QA Verification',
                'R31: WordPress Uploader/Publisher'
            ]:
                critical_robots_passed = False

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info(f"Successful: {successful}/{len(PIPELINE)}")
    logger.info(f"Failed: {failed}/{len(PIPELINE)}")
    logger.info(f"Skipped: {skipped}/{len(PIPELINE)}")
    logger.info("=" * 80)

    # PRINT to stdout for workflow visibility
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION RESULT")
    print(f"Robots Run: {len(PIPELINE)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Critical Path Status: {'✅ PASSED' if critical_robots_passed else '❌ FAILED'}")
    if failed == 0:
        print(f"Overall Status: {'✅ ALL ROBOTS SUCCESSFUL' if failed == 0 else f'⚠️  {failed} robots failed'}")
    print("=" * 80)

    if critical_robots_passed and failed == 0:
        logger.info("✅ COMPLETE PIPELINE SUCCESS - Blog post generated, verified, and published to WordPress!")
        print("✅ ALL ROBOTS SUCCEEDED - Blog post published to WordPress!")
        return 0  # Success - all robots passed
    elif critical_robots_passed and failed > 0:
        logger.warning(f"⚠️  PIPELINE COMPLETED WITH ISSUES - {failed} non-critical robots failed")
        print(f"⚠️  {failed} non-critical robots failed, but critical path succeeded")
        return 0  # Partial success - critical path passed
    else:
        logger.error(f"❌ PIPELINE FAILED - Critical robots did not complete successfully")
        print(f"❌ CRITICAL PATH FAILED")
        print("Check error log files for details")
        return 1  # Failure - critical path failed

if __name__ == '__main__':
    sys.exit(main())
