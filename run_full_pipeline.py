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

# Pipeline sequence - all 42 robots in execution order
PIPELINE = [
    # Content Generation Layer (R2-R3)
    ('r2_blog_title_generator.py', 'R2: Blog Title Generator'),
    ('r3_blog_content_generator.py', 'R3: Blog Content Generator'),
    
    # Initial QA Layer (R4-R6)
    ('r4_plagiarism_checker.py', 'R4: Plagiarism Checker'),
    ('r5_ai_detection_filter.py', 'R5: AI Detection Filter'),
    ('r6_keyword_optimizer.py', 'R6: Keyword Optimizer'),
    
    # Content Optimization (R7-R11)
    ('r7_image_finder.py', 'R7: Image Finder'),
    ('r8_alt_text_generator.py', 'R8: Alt Text Generator'),
    ('r9_qa_format_checker_first_pass.py', 'R9: QA Format Checker (1st Pass)'),
    ('r10_revalidation_second_pass.py', 'R10: Revalidation (2nd Pass)'),
    ('r11_headline_testing.py', 'R11: Headline Testing'),
    
    # Monetization Pipeline (R12-R18)
    ('r12_product_research.py', 'R12: Product Research'),
    ('r13_keywords_cache_refresh.py', 'R13: Keywords Cache Refresh'),
    ('r14_static_link_injector.py', 'R14: Static Link Injector'),
    ('r15_affiliate_link_injector.py', 'R15: Affiliate Link Injector'),
    ('r16_social_media_drafting.py', 'R16: Social Media Drafting'),
    ('r17_email_newsletter_builder.py', 'R17: Email Newsletter Builder'),
    ('r18_email_scheduler.py', 'R18: Email Scheduler'),
    
    # Infrastructure & Analytics (R19-R25)
    ('r19_analytics_event_tracker.py', 'R19: Analytics Event Tracker'),
    ('r20_master_metrics_aggregator.py', 'R20: Master Metrics Aggregator'),
    ('r21_social_media_publisher.py', 'R21: Social Media Publisher'),
    ('r22_wordpress_connector.py', 'R22: WordPress Connector'),
    ('r23_social_distributor.py', 'R23: Social Distributor'),
    ('r23_social_engagement_monitor.py', 'R23b: Social Engagement Monitor'),
    ('r24_comment_moderation.py', 'R24: Comment Moderation'),
    ('r25_content_refresh_trigger.py', 'R25: Content Refresh Trigger'),
    
    # Final Publishing Pipeline (R27-R32)
    ('r27_content_revalidation_refresh.py', 'R27: Content Revalidation'),
    ('r28_plagiarism_recheck_refresh.py', 'R28: Plagiarism Recheck'),
    ('r29_final_headline_confirmation.py', 'R29: Final Headline Confirmation'),
    ('r30_final_qa_verification.py', 'R30: Final QA Verification'),
    ('r31_wordpress_uploader_publisher.py', 'R31: WordPress Uploader/Publisher'),
    ('r32_post_publication_monitoring.py', 'R32: Post-Publication Monitoring'),
    
    # System Coordination (R33-R36)
    ('r33_master_control_coordinator.py', 'R33: Master Control Coordinator'),
    ('r34_error_handler_recovery.py', 'R34: Error Handler & Recovery'),
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
            timeout=300  # 5 minute timeout per robot
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {robot_name} - SUCCESS")
            return True
        else:
            logger.warning(f"⚠️  {robot_name} - Non-zero exit code: {result.returncode}")
            if result.stderr:
                logger.warning(f"   Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {robot_name} - TIMEOUT (>5 min)")
        return False
    except Exception as e:
        logger.error(f"✗ {robot_name} - EXCEPTION: {str(e)}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("GHGF 42-ROBOT AUTONOMOUS BLOGGING SYSTEM")
    logger.info("Starting Full Pipeline Cycle")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    successful = 0
    failed = 0
    skipped = 0
    
    for robot_file, robot_name in PIPELINE:
        success = run_robot(robot_file, robot_name)
        if success:
            successful += 1
        else:
            failed += 1
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info(f"Successful: {successful}/{len(PIPELINE)}")
    logger.info(f"Failed: {failed}/{len(PIPELINE)}")
    logger.info(f"Skipped: {skipped}/{len(PIPELINE)}")
    logger.info("=" * 80)
    
    if failed == 0:
        logger.info("✅ FULL PIPELINE COMPLETE - All robots executed successfully")
        return 0
    else:
        logger.warning(f"⚠️  PIPELINE COMPLETE WITH ERRORS - {failed} robots failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
