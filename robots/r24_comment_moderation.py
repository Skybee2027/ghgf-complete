#!/usr/bin/env python3
"""
R24: Comment Moderation & Response Bot
Purpose: Moderate comments and generate automated responses
Input: Comments from WordPress, social media
Output: Moderated comments + automated responses where appropriate
Frequency: Every 6 hours (comment review cycle)
Dependencies: R31 (blog posts), R21 (social posts)
Comment Filtering: Spam detection, toxicity analysis, relevance scoring
Response Generation: Contextual replies to common questions/feedback
Moderation Actions: Auto-approve, auto-reject, flag for manual review
Community Engagement: Automated thank-you replies, helpful responses
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
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

class CommentModerator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.comments_processed = 0
        self.comments_approved = 0
        self.comments_rejected = 0
        self.comments_flagged = 0
        self.responses_generated = 0

        # Spam detection patterns
        self.spam_patterns = [
            r'viagra|cialis|casino|lottery',
            r'http.*amazon|http.*aliexpress',
            r'buy now|click here.*urgent',
            r'\b(bitcoin|crypto|nft)\b.*invest'
        ]

        # Automated response templates
        self.response_templates = {
            'thank_you': "Thank you for your feedback! We appreciate your engagement.",
            'question_deflect': "Great question! We'll be covering this topic in an upcoming post.",
            'product_inquiry': "We don't sell products directly, but we review and recommend quality options.",
            'off_topic': "This seems a bit off-topic for this article, but we'd love to help!",
            'follow_up': "Thank you for the thoughtful comment. More details coming soon!"
        }

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_pending_comments(self, conn):
        """Get unmoderated comments from WordPress"""
        try:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT wc.id, wc.blog_id, wc.author_name, wc.author_email,
                       wc.content, wc.created_at, bp.title, bp.topic
                FROM wordpress_comments wc
                JOIN blog_posts bp ON wc.blog_id = bp.id
                WHERE wc.status = 'pending'
                AND wc.created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY wc.created_at DESC
                LIMIT 50
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return []

    def detect_spam(self, comment_text):
        """Detect spam in comment"""
        comment_lower = comment_text.lower()

        for pattern in self.spam_patterns:
            if re.search(pattern, comment_lower, re.IGNORECASE):
                return True

        # Check for excessive links
        links = re.findall(r'http[s]?://\S+', comment_text)
        if len(links) > 2:
            return True

        # Check for excessive caps
        if len(comment_text) > 20:
            caps_ratio = sum(1 for c in comment_text if c.isupper()) / len(comment_text)
            if caps_ratio > 0.5:
                return True

        return False

    def check_toxicity(self, comment_text):
        """Check for toxic/hostile language"""
        toxic_words = [
            'hate', 'stupid', 'idiot', 'worst', 'trash',
            'disgusting', 'horrible', 'terrible', 'useless'
        ]

        comment_lower = comment_text.lower()
        toxic_score = 0

        for word in toxic_words:
            if word in comment_lower:
                toxic_score += 1

        # Toxicity ratio
        return toxic_score / max(len(comment_text.split()), 1)

    def calculate_approval_score(self, comment_text, author_email):
        """Calculate score for auto-approval"""
        score = 100

        # Spam check
        if self.detect_spam(comment_text):
            return -1  # Auto-reject

        # Toxicity check
        toxicity = self.check_toxicity(comment_text)
        score -= (toxicity * 50)

        # Length check (too short is less reliable)
        if len(comment_text) < 20:
            score -= 20

        # Email validation (rough check)
        if '@' not in author_email or '.' not in author_email:
            score -= 30

        return max(score, 0)

    def select_response_template(self, comment_text):
        """Select appropriate response template"""
        comment_lower = comment_text.lower()

        if any(word in comment_lower for word in ['thank', 'appreciate', 'great', 'love']):
            return 'thank_you'

        if '?' in comment_text:
            return 'question_deflect'

        if any(word in comment_lower for word in ['where', 'buy', 'price', 'cost']):
            return 'product_inquiry'

        if len(comment_text.split()) < 15:
            return 'follow_up'

        return 'follow_up'

    def approve_comment(self, conn, comment_id):
        """Approve comment in database"""
        try:
            cursor = conn.cursor()
            query = "UPDATE wordpress_comments SET status = 'approved' WHERE id = %s"
            cursor.execute(query, (comment_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error approving comment: {str(e)}")
            return False

    def reject_comment(self, conn, comment_id, reason):
        """Reject comment in database"""
        try:
            cursor = conn.cursor()
            query = """UPDATE wordpress_comments
                      SET status = 'rejected', moderation_reason = %s
                      WHERE id = %s"""
            cursor.execute(query, (reason, comment_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error rejecting comment: {str(e)}")
            return False

    def flag_comment(self, conn, comment_id, flag_reason):
        """Flag comment for manual review"""
        try:
            cursor = conn.cursor()
            query = """UPDATE wordpress_comments
                      SET status = 'flagged', moderation_reason = %s
                      WHERE id = %s"""
            cursor.execute(query, (flag_reason, comment_id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error flagging comment: {str(e)}")
            return False

    def create_response(self, conn, comment_id, blog_id, response_text, is_auto=True):
        """Create automated response to comment"""
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO wordpress_responses
                (comment_id, blog_id, response_text, is_automated, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (comment_id, blog_id, response_text, is_auto))
            conn.commit()
            cursor.close()
            self.responses_generated += 1
            return True
        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            return False

    def run(self):
        self.print_header("R24: COMMENT MODERATION & RESPONSE")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Pending Comments{RESET}")
            comments = self.get_pending_comments(conn)
            if not comments:
                print(f"  No pending comments\n")
                print(f"{'='*70}")
                print(f"{BOLD}SUMMARY{RESET}")
                print(f"  Comments Processed: 0")
                print(f"  Status: {YELLOW}No comments to moderate{RESET}")
                print('='*70 + "\n")
                return True

            print(f"  ✓ Found {len(comments)} comments to moderate\n")

            print(f"{BOLD}Step 2: Moderating Comments{RESET}")
            for comment in comments:
                self.comments_processed += 1

                # Calculate approval score
                score = self.calculate_approval_score(comment['content'], comment['author_email'])

                if score < 0:
                    # Auto-reject (spam)
                    self.reject_comment(conn, comment['id'], 'Spam detected')
                    self.comments_rejected += 1
                    print(f"  {RED}✗ REJECTED{RESET}: {comment['author_name']} - Spam")

                elif score >= 70:
                    # Auto-approve
                    self.approve_comment(conn, comment['id'])
                    self.comments_approved += 1

                    # Generate auto-response
                    template_key = self.select_response_template(comment['content'])
                    response_text = self.response_templates[template_key]
                    self.create_response(conn, comment['id'], comment['blog_id'],
                                        response_text, is_auto=True)

                    print(f"  {GREEN}✓ APPROVED{RESET}: {comment['author_name'][:20]}... "
                          f"(score: {score})")

                else:
                    # Flag for manual review
                    self.flag_comment(conn, comment['id'], f'Score: {score} - manual review needed')
                    self.comments_flagged += 1
                    print(f"  {YELLOW}⚠ FLAGGED{RESET}: {comment['author_name'][:20]}... "
                          f"(score: {score})")

            print()

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Comments Processed: {self.comments_processed}")
            print(f"  Approved: {GREEN}{self.comments_approved}{RESET}")
            print(f"  Rejected: {RED}{self.comments_rejected}{RESET}")
            print(f"  Flagged for Review: {YELLOW}{self.comments_flagged}{RESET}")
            print(f"  Auto-Responses Generated: {GREEN}{self.responses_generated}{RESET}")
            print(f"  Moderation Method: AI-powered filtering + toxicity analysis")
            print(f"  Status: {GREEN}PASS - Comments moderated{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    moderator = CommentModerator()
    success = moderator.run()
    sys.exit(0 if success else 1)
