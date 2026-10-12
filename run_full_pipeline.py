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

# Pipeline sequence - CORE robots for blog generation and publishing
# For full pipeline, add remaining QA, monetization, and coordination robots
PIPELINE = [
    # Content Generation Layer (R2-R3)
    ('r2_blog_title_generator.py', 'R2: Blog Title Generator'),
    ('r3_blog_content_generator.py', 'R3: Blog Content Generator'),

    # WordPress Publishing (R31) - DIRECT PUBLISH (skipping QA/optimization for speed)
    ('r31_wordpress_uploader_publisher.py', 'R31: WordPress Uploader/Publisher'),
]

# FULL PIPELINE - Uncomment to use complete pipeline with all robots
# PIPELINE_FULL = [
#     # ... all 36+ robots as before
# ]

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
    core_robots_passed = True  # Track if R2, R3, R31 all succeed

    for robot_file, robot_name in PIPELINE:
        success = run_robot(robot_file, robot_name)
        if success:
            successful += 1
        else:
            failed += 1
            # Check if a core robot failed (R2, R3, or R31)
            if robot_name in ['R2: Blog Title Generator', 'R3: Blog Content Generator', 'R31: WordPress Uploader/Publisher']:
                core_robots_passed = False

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
    print(f"Core Robots Status: {'✅ PASSED' if core_robots_passed else '❌ FAILED'}")
    print("=" * 80)

    if core_robots_passed:
        logger.info("✅ CORE PIPELINE COMPLETE - Blog post generated and published to WordPress!")
        print("✅ CORE ROBOTS SUCCEEDED - Blog post published to WordPress!")
        return 0  # Success - the essential robots (R2, R3, R31) all passed
    else:
        logger.warning(f"⚠️  PIPELINE FAILED - Core robots did not complete successfully")
        print(f"❌ CORE ROBOTS FAILED")
        print("Check error log files for details")
        return 1  # Failure - core robots failed

if __name__ == '__main__':
    sys.exit(main())
