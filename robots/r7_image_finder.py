#!/usr/bin/env python3
"""
R7: Image Finder & Matcher
Purpose: Find 3-5 relevant images matching blog topic; avoid 90-day repetition
Input: Blog topic, keywords
Output: 3-5 image URLs + metadata
Frequency: Every 6 hours (parallel with R8)
Dependencies: R6 (provides topic)
APIs: Unsplash, Pexels (free alternatives)
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class ImageFinder:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.unsplash_key = os.getenv("UNSPLASH_API_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        self.repetition_days = 90
        self.images_found = 0

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_current_blog_topic(self, conn):
        try:
            cursor = conn.cursor(dictionary=True)
            # Try to get topic name from topics table if topic_id is stored
            query = """
                SELECT COALESCE(bp.topic, t.name) as topic
                FROM blog_posts bp
                LEFT JOIN topics t ON bp.topic_id = t.id
                WHERE bp.status = 'draft'
                ORDER BY bp.created_at DESC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result['topic'] if result else None
        except Exception as e:
            logger.error(f"Error getting topic: {str(e)}")
            return None

    def get_recently_used_images(self, conn, topic):
        """Get images used in last 90 days for this topic"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT image_url
                FROM image_tracking
                WHERE topic = %s
                AND used_date > DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            cursor.execute(query, (topic, self.repetition_days))
            results = cursor.fetchall()
            cursor.close()
            return [r['image_url'] for r in results]
        except Exception as e:
            logger.error(f"Error getting recent images: {str(e)}")
            return []

    def search_unsplash(self, query, exclude_urls=None):
        """Search Unsplash for images"""
        if not self.unsplash_key:
            return []

        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': query,
                'per_page': 10,
                'client_id': self.unsplash_key,
                'orientation': 'landscape'
            }

            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get('results', [])
                images = []
                for img in results[:5]:
                    img_url = img['urls']['regular']
                    if exclude_urls and img_url in exclude_urls:
                        continue
                    images.append({
                        'url': img_url,
                        'source': 'unsplash',
                        'title': img.get('description', 'Image'),
                        'credit': img['user']['name']
                    })
                return images
            return []
        except Exception as e:
            logger.error(f"Unsplash search error: {str(e)}")
            return []

    def search_pexels(self, query, exclude_urls=None):
        """Search Pexels for images"""
        if not self.pexels_key:
            return []

        try:
            url = "https://api.pexels.com/v1/search"
            headers = {'Authorization': self.pexels_key}
            params = {'query': query, 'per_page': 10}

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get('photos', [])
                images = []
                for img in results[:5]:
                    img_url = img['src']['large']
                    if exclude_urls and img_url in exclude_urls:
                        continue
                    images.append({
                        'url': img_url,
                        'source': 'pexels',
                        'title': f"Photo by {img['photographer']}",
                        'credit': img['photographer']
                    })
                return images
            return []
        except Exception as e:
            logger.error(f"Pexels search error: {str(e)}")
            return []

    def rank_images(self, images):
        """Rank images by quality signals"""
        ranked = []
        for i, img in enumerate(images):
            score = 100 - (i * 5)  # Earlier results score higher
            ranked.append({**img, 'score': score})
        return sorted(ranked, key=lambda x: x['score'], reverse=True)

    def save_images(self, conn, images, blog_id, topic):
        """Save selected images to database"""
        try:
            cursor = conn.cursor()
            for img in images:
                query = """
                    INSERT INTO image_tracking (image_url, topic, used_date, blog_id, expires_date)
                    VALUES (%s, %s, CURDATE(), %s, DATE_ADD(CURDATE(), INTERVAL %s DAY))
                """
                expires = datetime.now() + timedelta(days=self.repetition_days)
                cursor.execute(query, (img['url'], topic, blog_id, self.repetition_days))
            conn.commit()
            cursor.close()
            logger.info(f"Saved {len(images)} images to database")
            return True
        except Exception as e:
            logger.error(f"Error saving images: {str(e)}")
            return False

    def run(self):
        self.print_header("R7: IMAGE FINDER & MATCHER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Getting Blog Topic{RESET}")
            topic = self.get_current_blog_topic(conn)
            if not topic:
                logger.error("No topic found")
                return False
            print(f"  ✓ Topic: {BLUE}{topic}{RESET}\n")

            print(f"{BOLD}Step 2: Checking Recently Used Images (90-day rule){RESET}")
            used_images = self.get_recently_used_images(conn, topic)
            print(f"  Found {len(used_images)} recently used images - will avoid these\n")

            print(f"{BOLD}Step 3: Searching for Images (Unsplash + Pexels){RESET}")
            unsplash_results = self.search_unsplash(topic, used_images)
            pexels_results = self.search_pexels(topic, used_images)

            all_images = unsplash_results + pexels_results
            print(f"  Found {len(unsplash_results)} from Unsplash")
            print(f"  Found {len(pexels_results)} from Pexels")
            print(f"  Total: {len(all_images)} images\n")

            print(f"{BOLD}Step 4: Ranking & Selecting Best 3-5{RESET}")
            ranked = self.rank_images(all_images)
            selected = ranked[:5]
            self.images_found = len(selected)

            for i, img in enumerate(selected, 1):
                print(f"  {i}. {img['title']} ({img['source']}) - Score: {img['score']}")
            print()

            print(f"{BOLD}Step 5: Saving Image URLs to Database{RESET}")
            # Get current blog ID
            cursor = conn.cursor(dictionary=True)
            query = "SELECT id FROM blog_posts WHERE status = 'draft' ORDER BY created_at DESC LIMIT 1"
            cursor.execute(query)
            blog = cursor.fetchone()
            cursor.close()

            if blog and self.save_images(conn, selected, blog['id'], topic):
                print(f"  ✓ {GREEN}Saved {self.images_found} images{RESET}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Topic: {topic}")
            print(f"  Images Found: {GREEN}{self.images_found}{RESET}")
            print(f"  Status: {GREEN}PASS - Running in parallel with R8 (Alt-Text){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    finder = ImageFinder()
    success = finder.run()
    sys.exit(0 if success else 1)
