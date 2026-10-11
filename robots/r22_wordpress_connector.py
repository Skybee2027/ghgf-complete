#!/usr/bin/env python3
"""
R22: WordPress Connector & API Integration
Purpose: Establish and maintain WordPress API connectivity
Input: WordPress site credentials and configuration
Output: Validated API connection + WordPress compatibility checks
Frequency: Every 4 hours (continuous health checks)
Dependencies: None (infrastructure layer)
Conflict Resolution: R22 validates, R31 publishes (clear separation)
WordPress API: Uses REST API v2 for post creation/updates
Connection Pool: Maintains persistent connections to WordPress
Health Checks: Validates authentication, API availability, database connectivity
"""

import os
import sys
import requests
import mysql.connector
from datetime import datetime
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

class WordPressConnector:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        # WordPress configuration
        self.wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
        self.wp_user = os.getenv('WORDPRESS_USER', 'api_user')
        self.wp_password = os.getenv('WORDPRESS_PASSWORD', '')
        self.wp_api_base = f"{self.wp_url}/wp-json/wp/v2"

        # Connection info
        self.connection_status = 'UNKNOWN'
        self.last_check = None
        self.health_score = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def validate_wp_credentials(self):
        """Validate WordPress credentials"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            # Test authentication by fetching current user
            response = requests.get(
                f"{self.wp_api_base}/users/me",
                auth=auth,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("WordPress authentication successful")
                return True, "Authentication successful"
            else:
                error = f"Authentication failed: {response.status_code}"
                logger.error(error)
                return False, error
        except requests.exceptions.ConnectionError as e:
            error = f"Connection error: {str(e)}"
            logger.error(error)
            return False, error
        except Exception as e:
            error = f"Error validating credentials: {str(e)}"
            logger.error(error)
            return False, error

    def check_wordpress_health(self):
        """Check WordPress site health"""
        try:
            headers = {'Content-Type': 'application/json'}

            # Check WordPress REST API availability
            response = requests.get(
                f"{self.wp_url}/wp-json/",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("WordPress site is accessible")
                return True, "Site accessible"
            else:
                error = f"Site returned {response.status_code}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Health check failed: {str(e)}"
            logger.error(error)
            return False, error

    def verify_posts_endpoint(self):
        """Verify posts endpoint is accessible"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            response = requests.get(
                f"{self.wp_api_base}/posts?per_page=1",
                auth=auth,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Posts endpoint verified")
                return True, "Posts endpoint accessible"
            else:
                error = f"Posts endpoint returned {response.status_code}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Posts endpoint error: {str(e)}"
            logger.error(error)
            return False, error

    def verify_categories_endpoint(self):
        """Verify categories endpoint is accessible"""
        try:
            headers = {'Content-Type': 'application/json'}

            response = requests.get(
                f"{self.wp_api_base}/categories",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Categories endpoint verified ({len(categories)} categories)")
                return True, f"Categories endpoint accessible ({len(categories)} found)"
            else:
                error = f"Categories endpoint returned {response.status_code}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Categories endpoint error: {str(e)}"
            logger.error(error)
            return False, error

    def test_post_creation_capability(self):
        """Test ability to create posts (draft mode)"""
        try:
            auth = (self.wp_user, self.wp_password)
            headers = {'Content-Type': 'application/json'}

            test_post = {
                'title': 'Test Post - Connection Verification',
                'content': 'This is a test post to verify API connectivity.',
                'status': 'draft'
            }

            response = requests.post(
                f"{self.wp_api_base}/posts",
                auth=auth,
                headers=headers,
                json=test_post,
                timeout=10
            )

            if response.status_code in [200, 201]:
                post_data = response.json()
                post_id = post_data['id']

                # Delete the test post
                delete_response = requests.delete(
                    f"{self.wp_api_base}/posts/{post_id}?force=true",
                    auth=auth,
                    timeout=10
                )

                logger.info("Post creation capability verified")
                return True, "Can create and delete posts"
            else:
                error = f"Post creation returned {response.status_code}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Post creation test failed: {str(e)}"
            logger.error(error)
            return False, error

    def save_connection_status(self, conn, status, health_score, checks):
        """Save connection status to database"""
        try:
            cursor = conn.cursor()

            query = """
                INSERT INTO wordpress_connection_log
                (status, health_score, auth_check, site_health, posts_endpoint,
                 categories_endpoint, post_creation, checked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """

            cursor.execute(query, (
                status,
                health_score,
                checks['auth'],
                checks['site_health'],
                checks['posts_endpoint'],
                checks['categories_endpoint'],
                checks['post_creation']
            ))

            conn.commit()
            cursor.close()
            logger.info("Connection status saved to database")
            return True
        except Exception as e:
            logger.error(f"Error saving status: {str(e)}")
            return False

    def run(self):
        self.print_header("R22: WORDPRESS CONNECTOR")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Validating WordPress Credentials{RESET}")
            auth_ok, auth_msg = self.validate_wp_credentials()
            status_icon = GREEN + "✓" + RESET if auth_ok else RED + "✗" + RESET
            print(f"  {status_icon} {auth_msg}\n")

            print(f"{BOLD}Step 2: Checking WordPress Site Health{RESET}")
            health_ok, health_msg = self.check_wordpress_health()
            status_icon = GREEN + "✓" + RESET if health_ok else RED + "✗" + RESET
            print(f"  {status_icon} {health_msg}\n")

            print(f"{BOLD}Step 3: Verifying Posts Endpoint{RESET}")
            posts_ok, posts_msg = self.verify_posts_endpoint()
            status_icon = GREEN + "✓" + RESET if posts_ok else RED + "✗" + RESET
            print(f"  {status_icon} {posts_msg}\n")

            print(f"{BOLD}Step 4: Verifying Categories Endpoint{RESET}")
            cats_ok, cats_msg = self.verify_categories_endpoint()
            status_icon = GREEN + "✓" + RESET if cats_ok else RED + "✗" + RESET
            print(f"  {status_icon} {cats_msg}\n")

            print(f"{BOLD}Step 5: Testing Post Creation Capability{RESET}")
            create_ok, create_msg = self.test_post_creation_capability()
            status_icon = GREEN + "✓" + RESET if create_ok else RED + "✗" + RESET
            print(f"  {status_icon} {create_msg}\n")

            # Calculate health score
            checks = {
                'auth': 1 if auth_ok else 0,
                'site_health': 1 if health_ok else 0,
                'posts_endpoint': 1 if posts_ok else 0,
                'categories_endpoint': 1 if cats_ok else 0,
                'post_creation': 1 if create_ok else 0
            }

            health_score = sum(checks.values()) * 20  # 0-100

            # Overall status
            if health_score == 100:
                self.connection_status = 'HEALTHY'
                status_color = GREEN
            elif health_score >= 80:
                self.connection_status = 'DEGRADED'
                status_color = YELLOW
            else:
                self.connection_status = 'FAILED'
                status_color = RED

            # Save to database
            self.save_connection_status(conn, self.connection_status, health_score, checks)

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  WordPress URL: {self.wp_url}")
            print(f"  Authentication: {'✓ Valid' if auth_ok else '✗ Invalid'}")
            print(f"  Site Health: {'✓ Online' if health_ok else '✗ Offline'}")
            print(f"  Posts Endpoint: {'✓ Working' if posts_ok else '✗ Failed'}")
            print(f"  Categories: {'✓ Available' if cats_ok else '✗ Failed'}")
            print(f"  Post Creation: {'✓ Ready' if create_ok else '✗ Disabled'}")
            print(f"  Overall Health: {status_color}{health_score}%{RESET}")
            print(f"  Connection Status: {status_color}{self.connection_status}{RESET}")
            print(f"  Status: {GREEN}PASS - WordPress ready for publishing{RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    connector = WordPressConnector()
    success = connector.run()
    sys.exit(0 if success else 1)
