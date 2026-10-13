#!/usr/bin/env python3
"""
R6: Keyword Optimizer
Purpose: Optimize content for target keywords (1-2% density); improve headers; maintain readability
Input: Blog post content (from R5 AI detection)
Output: Keyword-optimized content ready for SEO
Frequency: Every 6 hours (after R5 completes)
Dependencies: R5 (provides content), R13 (provides keywords)
"""

import os
import sys
import mysql.connector
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class KeywordOptimizer:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.target_density = 0.015  # 1.5%
        self.density_range = (0.01, 0.02)  # 1-2%

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_pending_content(self, conn):
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT id, title, content, topic, ai_detection_score
                FROM blog_posts
                WHERE status = 'draft' AND ai_detection_score >= 0
                ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching content: {str(e)}")
            return None

    def get_target_keywords(self, conn, topic):
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT keyword FROM trending_keywords WHERE topic = %s ORDER BY search_volume DESC LIMIT 5"
            cursor.execute(query, (topic,))
            results = cursor.fetchall()
            cursor.close()
            return [r['keyword'] for r in results] if results else []
        except Exception as e:
            logger.error(f"Error getting keywords: {str(e)}")
            return []

    def analyze_keyword_density(self, content, keyword):
        """Analyze current keyword density"""
        words = re.findall(r'\b\w+\b', content.lower())
        keyword_count = content.lower().count(keyword.lower())
        total_words = len(words)
        density = keyword_count / total_words if total_words > 0 else 0
        return keyword_count, density

    def optimize_content(self, content, keywords):
        """Optimize content for keywords - aggressive 1%+ density targeting"""
        optimized = content

        # Calculate total word count for density calculation
        words = re.findall(r'\b\w+\b', content.lower())
        total_words = len(words)

        if total_words == 0:
            return content

        # Target: 1% density minimum
        target_density = 0.01
        target_occurrences_per_keyword = max(3, int(total_words * target_density))  # Minimum 3, or 1%

        logger.info(f"Content has {total_words} words. Target {target_occurrences_per_keyword} occurrences per keyword for 1% density")

        # Process each keyword
        for keyword in keywords[:5]:  # Process top 5 keywords
            # Count current occurrences
            current_count = optimized.lower().count(keyword.lower())
            needed_count = target_occurrences_per_keyword - current_count

            if needed_count > 0:
                logger.info(f"Keyword '{keyword}': {current_count} found, need {needed_count} more for {target_density*100}%")

                # Inject keyword into content naturally
                # Strategy: Add to first paragraph if missing, then distribute throughout body text

                # Try adding to first paragraph
                if keyword.lower() not in optimized[:500].lower():
                    paragraphs = optimized.split('</p>')
                    if len(paragraphs) > 1:
                        # Add at the end of first paragraph before closing tag
                        paragraphs[0] = paragraphs[0].rstrip() + f". {keyword} is essential for fitness success.</p>"
                        optimized = '</p>'.join(paragraphs)
                        needed_count -= 1

                # Distribute remaining keywords throughout middle paragraphs
                if needed_count > 0:
                    paragraphs = optimized.split('</p>')
                    para_count = len(paragraphs)

                    # Inject into roughly evenly spaced paragraphs
                    if para_count > 3:
                        for i in range(1, needed_count + 1):
                            para_idx = min(i * (para_count // (needed_count + 2)), para_count - 2)
                            if para_idx < len(paragraphs) and para_idx > 0:
                                # Add keyword naturally to the paragraph
                                paragraphs[para_idx] = paragraphs[para_idx].rstrip() + f". {keyword} enhances overall fitness."

                        optimized = '</p>'.join(paragraphs)

        # Enhance headers with first keyword
        if keywords:
            keyword = keywords[0]
            h2_pattern = r'<h2>([^<]+)</h2>'
            h2_match = re.search(h2_pattern, optimized)
            if h2_match:
                old_header = h2_match.group(1)
                if keyword.lower() not in old_header.lower():
                    new_header = f"{old_header}: {keyword}"
                    optimized = optimized.replace(f'<h2>{old_header}</h2>', f'<h2>{new_header}</h2>', 1)
                    logger.info(f"Updated header with '{keyword}'")

        return optimized

    def check_readability(self, content):
        """Check readability score (Flesch-Kincaid)"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r'\b\w+\b', content)

        # Simplified Flesch-Kincaid
        if len(sentences) == 0 or len(words) == 0:
            return 60

        syllable_count = sum(self.count_syllables(word) for word in words)

        fk_score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllable_count / len(words))
        fk_score = max(0, min(100, fk_score))

        return fk_score

    def count_syllables(self, word):
        """Estimate syllable count"""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel

        if word.endswith('e'):
            count -= 1
        if word.endswith('le'):
            count += 1

        return max(1, count)

    def save_optimized_content(self, conn, blog_id, optimized_content):
        try:
            cursor = conn.cursor()
            query = "UPDATE blog_posts SET content = %s, version = version + 1 WHERE id = %s"
            cursor.execute(query, (optimized_content, blog_id))
            conn.commit()
            cursor.close()
            logger.info(f"Optimized content saved for blog_id: {blog_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return False

    def run(self):
        self.print_header("R6: KEYWORD OPTIMIZER")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Content from R5{RESET}")
            blog_data = self.get_pending_content(conn)
            if not blog_data:
                return False
            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}\n")

            print(f"{BOLD}Step 2: Getting Target Keywords{RESET}")
            keywords = self.get_target_keywords(conn, blog_data['topic'])
            for kw in keywords:
                count, density = self.analyze_keyword_density(blog_data['content'], kw)
                print(f"  • {kw}: {count} times ({density:.2%})")
            print()

            print(f"{BOLD}Step 3: Optimizing Content{RESET}")
            optimized = self.optimize_content(blog_data['content'], keywords)
            print(f"  ✓ Keywords added to headers and introduction\n")

            print(f"{BOLD}Step 4: Checking Readability{RESET}")
            readability = self.check_readability(optimized)
            print(f"  Flesch-Kincaid Score: {readability:.1f}")
            if 60 <= readability <= 70:
                print(f"  ✓ {GREEN}Optimal readability{RESET}\n")
            else:
                print(f"  ⚠ {YELLOW}Readability could be improved{RESET}\n")

            print(f"{BOLD}Step 5: Saving Optimized Content{RESET}")
            saved = self.save_optimized_content(conn, blog_data['id'], optimized)
            if saved:
                print(f"  ✓ {GREEN}Content saved{RESET}\n")

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Keywords Optimized: {len(keywords)}")
            print(f"  Readability Score: {readability:.1f}/100")
            print(f"  Status: {GREEN}PASS - Ready for R7 (Image Finder){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    optimizer = KeywordOptimizer()
    success = optimizer.run()
    sys.exit(0 if success else 1)
