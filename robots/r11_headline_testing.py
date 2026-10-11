#!/usr/bin/env python3
"""
R11: Headline Testing & Selection
Purpose: A/B test headline variations and select best performer for publication
Input: Blog post with headline CTR scores (from R2)
Output: Selected headline with predicted best performance
Frequency: Every 6 hours (before R12 product research)
Dependencies: R2 (provides headline variations with CTR scores)
Testing Method: Rank by CTR score, length, keyword inclusion, emotional triggers
Selection: Highest-scoring headline + fallback options
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

class HeadlineTester:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }
        self.power_words = [
            'Ultimate', 'Best', 'Top', 'Proven', 'Secret', 'Hidden',
            'Guaranteed', 'Amazing', 'Incredible', 'Surprising', 'Shocking',
            'Essential', 'Critical', 'Powerful', 'Effective', 'Advanced',
            'Complete', 'Definitive', 'Essential', 'Must', 'Do', 'Never',
            'Always', 'Simple', 'Easy', 'Quick', 'Fast', 'Faster'
        ]
        self.emotional_triggers = [
            'you', 'your', 'health', 'fitness', 'lose', 'gain', 'boost',
            'improve', 'increase', 'decrease', 'protect', 'prevent', 'cure',
            'beat', 'fight', 'win', 'success', 'results', 'transform'
        ]
        self.selected_headline = None
        self.test_results = []

    def print_header(self, title):
        print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

    def connect_db(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_blog_and_headlines(self, conn):
        """Get latest blog with its headline variations from R2"""
        try:
            cursor = conn.cursor(dictionary=True)

            # Get latest draft blog
            blog_query = """
                SELECT id, title, topic
                FROM blog_posts
                WHERE status = 'draft'
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(blog_query)
            blog = cursor.fetchone()

            if not blog:
                cursor.close()
                return None, []

            # Get headline variations for this blog topic
            headlines_query = """
                SELECT id, title, topic, ctr_score, used
                FROM blog_titles
                WHERE topic = %s AND used = FALSE
                ORDER BY ctr_score DESC
                LIMIT 10
            """
            cursor.execute(headlines_query, (blog['topic'],))
            headlines = cursor.fetchall()
            cursor.close()

            return blog, headlines
        except Exception as e:
            logger.error(f"Error getting blog and headlines: {str(e)}")
            return None, []

    def analyze_headline_quality(self, headline):
        """Score headline on multiple quality factors"""
        score = 0
        details = []

        # 1. Length check (optimal 50-70 characters)
        length = len(headline)
        if 50 <= length <= 70:
            score += 25
            details.append(f"Length optimal: {length} chars (+25)")
        elif 40 <= length <= 80:
            score += 15
            details.append(f"Length acceptable: {length} chars (+15)")
        else:
            score += 5
            details.append(f"Length poor: {length} chars (+5)")

        # 2. Power word inclusion
        power_words_found = sum(1 for word in self.power_words if word.lower() in headline.lower())
        score += min(power_words_found * 10, 25)
        details.append(f"Power words: {power_words_found} found (+{min(power_words_found * 10, 25)})")

        # 3. Emotional triggers
        emotional_found = sum(1 for word in self.emotional_triggers if word.lower() in headline.lower())
        score += min(emotional_found * 8, 25)
        details.append(f"Emotional triggers: {emotional_found} found (+{min(emotional_found * 8, 25)})")

        # 4. Numbers in headline (usually performs better)
        if re.search(r'\d+', headline):
            score += 15
            details.append("Contains number (+15)")

        # 5. Question format (high engagement)
        if headline.endswith('?'):
            score += 15
            details.append("Question format (+15)")

        # 6. Keyword inclusion
        if any(keyword in headline.lower() for keyword in ['how', 'why', 'what', 'best', 'top']):
            score += 10
            details.append("Engagement keywords (+10)")

        return min(score, 100), details

    def evaluate_headlines(self, headlines):
        """Evaluate all headline variations and rank them"""
        evaluations = []

        for headline in headlines:
            quality_score, quality_details = self.analyze_headline_quality(headline['title'])

            # Combine quality score with CTR score from R2
            ctr_score = headline['ctr_score'] if headline['ctr_score'] else 0

            # Weighted combination: 60% CTR (R2's testing), 40% quality analysis
            combined_score = (ctr_score * 0.6) + (quality_score * 0.4)

            evaluations.append({
                'headline_id': headline['id'],
                'headline': headline['title'],
                'ctr_score': ctr_score,
                'quality_score': quality_score,
                'combined_score': combined_score,
                'details': quality_details
            })

        # Sort by combined score
        evaluations.sort(key=lambda x: x['combined_score'], reverse=True)
        return evaluations

    def get_keyword_match_bonus(self, headline, keywords):
        """Give bonus points if headline includes topic keywords"""
        bonus = 0
        matched_keywords = []

        for keyword in keywords[:5]:
            if keyword.lower() in headline.lower():
                bonus += 5
                matched_keywords.append(keyword)

        return bonus, matched_keywords

    def select_best_headline(self, conn, blog_id, evaluations, topic):
        """Select best headline and get keyword bonus"""
        try:
            # Get topic keywords
            cursor = conn.cursor(dictionary=True)
            kw_query = """
                SELECT keyword FROM trending_keywords
                WHERE topic = %s
                ORDER BY search_volume DESC
                LIMIT 5
            """
            cursor.execute(kw_query, (topic,))
            keywords = [r['keyword'] for r in cursor.fetchall()]
            cursor.close()

            best_evaluation = evaluations[0]
            keyword_bonus, matched_keywords = self.get_keyword_match_bonus(best_evaluation['headline'], keywords)
            best_evaluation['combined_score'] += keyword_bonus
            best_evaluation['matched_keywords'] = matched_keywords

            return best_evaluation
        except Exception as e:
            logger.error(f"Error selecting best headline: {str(e)}")
            return evaluations[0] if evaluations else None

    def save_headline_selection(self, conn, blog_id, headline_id, selected_headline, test_results):
        """Save selected headline and test results to database"""
        try:
            cursor = conn.cursor()

            # Update blog_posts with selected headline
            blog_update = """
                UPDATE blog_posts
                SET title = %s, selected_headline_id = %s,
                    headline_testing_passed = TRUE, headline_tested_at = NOW()
                WHERE id = %s
            """
            cursor.execute(blog_update, (selected_headline, headline_id, blog_id))

            # Save test results to database (store as JSON/text)
            results_json = str(test_results)
            results_update = """
                UPDATE blog_posts
                SET headline_test_results = %s
                WHERE id = %s
            """
            cursor.execute(results_update, (results_json, blog_id))

            # Mark title as used in blog_titles
            title_update = """
                UPDATE blog_titles
                SET used = TRUE, used_at = NOW()
                WHERE id = %s
            """
            cursor.execute(title_update, (headline_id,))

            conn.commit()
            cursor.close()
            logger.info(f"Headline selection saved: {selected_headline}")
            return True
        except Exception as e:
            logger.error(f"Error saving headline selection: {str(e)}")
            return False

    def run(self):
        self.print_header("R11: HEADLINE TESTING & SELECTION")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        conn = self.connect_db()
        if not conn:
            return False

        try:
            print(f"{BOLD}Step 1: Fetching Blog and Headline Variations{RESET}")
            blog_data, headlines = self.get_blog_and_headlines(conn)
            if not blog_data:
                logger.error("No draft blog found")
                return False

            if not headlines:
                logger.error("No headline variations found from R2")
                return False

            print(f"  ✓ Blog ID: {BLUE}{blog_data['id']}{RESET}")
            print(f"  ✓ Current Title: {blog_data['title']}")
            print(f"  ✓ Headlines to test: {len(headlines)}\n")

            print(f"{BOLD}Step 2: Evaluating Headline Quality{RESET}")
            evaluations = self.evaluate_headlines(headlines)

            for i, eval_result in enumerate(evaluations[:3], 1):
                print(f"  {i}. {eval_result['headline'][:60]}...")
                print(f"     CTR Score: {eval_result['ctr_score']:.2f}")
                print(f"     Quality Score: {eval_result['quality_score']:.0f}/100")
                print(f"     Combined Score: {GREEN}{eval_result['combined_score']:.2f}{RESET}\n")

            print(f"{BOLD}Step 3: Selecting Best Performing Headline{RESET}")
            best_headline = self.select_best_headline(conn, blog_data['id'], evaluations, blog_data['topic'])

            if best_headline:
                print(f"  ✓ Selected Headline: {BLUE}{best_headline['headline']}{RESET}")
                print(f"    Final Score: {best_headline['combined_score']:.2f}")
                if best_headline.get('matched_keywords'):
                    print(f"    Keywords matched: {', '.join(best_headline['matched_keywords'])}\n")
                else:
                    print()
            else:
                logger.error("Failed to select headline")
                return False

            print(f"{BOLD}Step 4: Saving Selected Headline to Database{RESET}")
            saved = self.save_headline_selection(
                conn, blog_data['id'], best_headline['headline_id'],
                best_headline['headline'], evaluations
            )

            if not saved:
                logger.error("Failed to save headline selection")
                return False

            print(f"  ✓ {GREEN}Headline saved and title updated{RESET}\n")

            print(f"{BOLD}Step 5: Alternative Headlines (Backup Options){RESET}")
            for i, eval_result in enumerate(evaluations[1:4], 1):
                print(f"  {i}. {eval_result['headline'][:60]}... (Score: {eval_result['combined_score']:.2f})")
            print()

            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Blog ID: {blog_data['id']}")
            print(f"  Headlines Tested: {len(headlines)}")
            print(f"  Selected Headline: {BLUE}{best_headline['headline']}{RESET}")
            print(f"  Confidence Score: {GREEN}{best_headline['combined_score']:.2f}/100{RESET}")
            print(f"  Status: {GREEN}PASS - Headline optimized, ready for R12 (Product Research){RESET}")
            print('='*70 + "\n")
            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    tester = HeadlineTester()
    success = tester.run()
    sys.exit(0 if success else 1)
