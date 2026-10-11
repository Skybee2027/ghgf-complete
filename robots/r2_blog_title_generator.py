#!/usr/bin/env python3
"""
R2: Blog Title Generator
Purpose: Generate 5 catchy, SEO-optimized blog titles using trending keywords and 18-topic rotation
Input: Trending keywords (from R13), current topic from rotation schedule
Output: 5 title variations (best selected for next phase)
Frequency: Every 6 hours
Dependencies: Requires R13 to populate trending_keywords table + topic_rotation table
"""

import os
import sys
import json
import mysql.connector
from datetime import datetime
from groq import Groq
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

class BlogTitleGenerator:
    def __init__(self):
        """Initialize title generator with database and API connections"""
        self.groq_key = os.getenv("GROQ_API_KEY")
        if not self.groq_key:
            logger.error("GROQ_API_KEY not set")
            sys.exit(1)

        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        self.titles_generated = 0
        self.current_topic = None
        self.trending_keywords = []

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*70}")
        print(f"{BOLD}{title}{RESET}")
        print('='*70)

    def connect_db(self):
        """Connect to database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            logger.info("Database connected successfully")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_current_topic(self, conn):
        """Get current active topic from 18-topic rotation"""
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM topic_rotation WHERE status = 'active' LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result:
                self.current_topic = result
                logger.info(f"Current topic: {result['topic_name']} (Cycle: {result['cycle_number']}, Seq: {result['topic_sequence']})")
                return result
            else:
                logger.warning("No active topic found. Setting to first topic...")
                query = "UPDATE topic_rotation SET status = 'active', start_date = CURDATE() WHERE cycle_number = 1 AND topic_sequence = 1"
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                cursor.close()
                return self.get_current_topic(conn)
        except Exception as e:
            logger.error(f"Error getting current topic: {str(e)}")
            return None

    def get_trending_keywords(self, conn, topic):
        """Get trending keywords for current topic from R13's cache"""
        try:
            cursor = conn.cursor(dictionary=True)
            # Get top 10 trending keywords for this topic
            query = """
                SELECT keyword, search_volume, competition_level
                FROM trending_keywords
                WHERE topic = %s
                ORDER BY search_volume DESC
                LIMIT 10
            """
            cursor.execute(query, (topic['topic_name'],))
            results = cursor.fetchall()
            cursor.close()

            if results:
                self.trending_keywords = results
                keywords_str = ", ".join([k['keyword'] for k in results])
                logger.info(f"Retrieved {len(results)} trending keywords: {keywords_str}")
                return results
            else:
                logger.warning(f"No trending keywords found for topic: {topic['topic_name']}")
                # Fallback: use topic name as keyword
                logger.info(f"Using topic name as fallback keyword")
                return [{'keyword': topic['topic_name'], 'search_volume': 0, 'competition_level': 'medium'}]
        except Exception as e:
            logger.error(f"Error getting trending keywords: {str(e)}")
            return []

    def generate_titles_with_groq(self, topic, keywords):
        """Generate 5 title variations using Groq"""
        try:
            client = Groq(api_key=self.groq_key)

            keywords_list = ", ".join([f"{k['keyword']}" for k in keywords[:5]])

            prompt = f"""Generate 5 catchy, engaging, SEO-optimized blog post titles about the topic: "{topic['topic_name']}"

Use these trending keywords naturally: {keywords_list}

Requirements:
- Each title should be 50-70 characters (good for Google SERP)
- Include at least one of the trending keywords
- Make it appealing to ALL age groups and genders
- Use power words (Top, Best, Complete, Guide, Essential, etc)
- Include numbers where relevant (10 Tips, 5 Ways, etc)
- Format: Title1 | Title2 | Title3 | Title4 | Title5
- Separate with |
- Return ONLY the titles, nothing else

Topic context: {topic['topic_name']}
Target audience: Adults of all ages and genders interested in health & fitness"""

            logger.info("Calling Groq API to generate titles...")
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8
            )

            if response.choices and response.choices[0].message.content:
                titles_raw = response.choices[0].message.content.strip()
                titles = [t.strip() for t in titles_raw.split('|')]
                titles = [t for t in titles if t]  # Remove empty

                self.titles_generated = len(titles)
                logger.info(f"Generated {self.titles_generated} titles")
                return titles[:5]  # Return max 5
            else:
                logger.error("Groq returned empty response")
                return None
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return None

    def score_titles(self, titles):
        """Score titles based on SEO and engagement factors"""
        scored_titles = []
        for i, title in enumerate(titles, 1):
            score = 0

            # Check length (50-70 chars is ideal)
            if 50 <= len(title) <= 70:
                score += 20
            elif 40 <= len(title) <= 80:
                score += 15
            else:
                score += 5

            # Check for power words
            power_words = ['best', 'top', 'essential', 'ultimate', 'complete', 'guide', 'tips', 'ways', 'secrets', 'proven']
            if any(word in title.lower() for word in power_words):
                score += 15

            # Check for numbers
            if any(char.isdigit() for char in title):
                score += 15

            # Check for trending keywords
            for keyword in self.trending_keywords[:3]:
                if keyword['keyword'].lower() in title.lower():
                    score += 20

            # Check for emotional triggers
            emotional_words = ['transform', 'discover', 'secret', 'proven', 'guaranteed', 'amazing', 'powerful']
            if any(word in title.lower() for word in emotional_words):
                score += 10

            scored_titles.append({
                'rank': i,
                'title': title,
                'length': len(title),
                'score': min(score, 100)
            })

        # Sort by score descending
        scored_titles.sort(key=lambda x: x['score'], reverse=True)
        return scored_titles

    def save_titles_to_db(self, conn, titles_data, topic):
        """Save generated titles to database"""
        try:
            cursor = conn.cursor()

            keywords_str = ",".join([k['keyword'] for k in self.trending_keywords[:5]])

            for title_data in titles_data:
                query = """
                    INSERT INTO blog_titles (title, topic, keywords, created_at, ctr_score)
                    VALUES (%s, %s, %s, NOW(), %s)
                """
                cursor.execute(query, (
                    title_data['title'],
                    topic['topic_name'],
                    keywords_str,
                    title_data['score'] / 100.0
                ))

            conn.commit()
            logger.info(f"Saved {len(titles_data)} titles to database")
            return True
        except Exception as e:
            logger.error(f"Error saving titles: {str(e)}")
            return False
        finally:
            cursor.close()

    def run(self):
        """Main execution flow"""
        self.print_header("R2: BLOG TITLE GENERATOR")
        print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Connect to database
        conn = self.connect_db()
        if not conn:
            logger.error("Cannot proceed without database connection")
            return False

        try:
            # Step 1: Get current active topic from 18-topic rotation
            print(f"{BOLD}Step 1: Getting Current Topic from Rotation Schedule{RESET}")
            topic = self.get_current_topic(conn)
            if not topic:
                logger.error("Failed to get current topic")
                return False
            print(f"  ✓ Topic: {BLUE}{topic['topic_name']}{RESET}\n")

            # Step 2: Get trending keywords for this topic (from R13 cache)
            print(f"{BOLD}Step 2: Retrieving Trending Keywords (from R13 cache){RESET}")
            keywords = self.get_trending_keywords(conn, topic)
            if not keywords:
                logger.warning("No keywords found, proceeding with topic name")
            for kw in keywords[:3]:
                print(f"  • {kw['keyword']} (Volume: {kw['search_volume']}, Competition: {kw['competition_level']})")
            print()

            # Step 3: Generate titles using Groq
            print(f"{BOLD}Step 3: Generating 5 Title Variations{RESET}")
            titles = self.generate_titles_with_groq(topic, keywords)
            if not titles:
                logger.error("Failed to generate titles")
                return False

            for i, title in enumerate(titles, 1):
                print(f"  {i}. {title}")
            print()

            # Step 4: Score and rank titles
            print(f"{BOLD}Step 4: Scoring & Ranking Titles{RESET}")
            scored_titles = self.score_titles(titles)
            for scored in scored_titles:
                print(f"  #{scored['rank']}: {YELLOW}{scored['title']}{RESET}")
                print(f"      Length: {scored['length']} chars | Score: {scored['score']}/100")
            print()

            # Step 5: Save to database
            print(f"{BOLD}Step 5: Saving to Database{RESET}")
            saved = self.save_titles_to_db(conn, scored_titles, topic)
            if saved:
                print(f"  ✓ {GREEN}Saved {len(scored_titles)} titles to blog_titles table{RESET}\n")

            # Summary
            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Topic: {BLUE}{topic['topic_name']}{RESET}")
            print(f"  Keywords: {len(keywords)} trending keywords available")
            print(f"  Titles Generated: {GREEN}{self.titles_generated}{RESET}")
            print(f"  Best Title: {BLUE}{scored_titles[0]['title']}{RESET} (Score: {scored_titles[0]['score']}/100)")
            print(f"  Status: {GREEN}SUCCESS{RESET}")
            print('='*70 + "\n")

            return True

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    generator = BlogTitleGenerator()
    success = generator.run()
    sys.exit(0 if success else 1)
