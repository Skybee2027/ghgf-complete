#!/usr/bin/env python3
"""
R2: Blog Title Generator (Multi-Provider Fallback)
Purpose: Generate 5 catchy, SEO-optimized blog titles using trending keywords and 18-topic rotation
Input: Trending keywords (from R13), current topic from rotation schedule
Output: 5 title variations (best selected for next phase)
Frequency: Every 6 hours
Dependencies: Requires R13 to populate trending_keywords table + topic_rotation table

Provider Chain: Groq → Gemini → OpenAI
This implementation removes all hardcoded model assumptions and automatically falls back
through providers based on actual availability and successful API calls.
"""

import os
import sys
import json
import traceback
import mysql.connector
from datetime import datetime
import logging

# Setup logging with more verbosity
logging.basicConfig(
    level=logging.DEBUG,
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
        """Initialize title generator with database and multi-provider API connections"""
        logger.info("=" * 70)
        logger.info("Initializing R2: Blog Title Generator (Multi-Provider)")
        logger.info("=" * 70)

        # Check available API keys - all are optional since we have a fallback chain
        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.cohere_key = os.getenv("COHERE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # Model names - fully configurable with intelligent defaults
        # User can override with environment variables, otherwise sensible defaults are used
        # Defaults chosen for broad availability across free/trial accounts:
        # Using 'or' operator to handle empty strings from GitHub Secrets
        self.groq_model = os.getenv("GROQ_MODEL") or "mixtral-8x7b-32768"
        self.gemini_model = os.getenv("GEMINI_MODEL") or "gemini-pro"
        self.cohere_model = os.getenv("COHERE_MODEL") or "command-r"
        self.openai_model = os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo"

        logger.debug(f"Model configuration:")
        logger.debug(f"  GROQ_MODEL={self.groq_model} (default: mixtral-8x7b-32768)")
        logger.debug(f"  GEMINI_MODEL={self.gemini_model} (default: gemini-pro)")
        logger.debug(f"  COHERE_MODEL={self.cohere_model} (default: command-r)")
        logger.debug(f"  OPENAI_MODEL={self.openai_model} (default: gpt-3.5-turbo)")

        if not any([self.groq_key, self.gemini_key, self.cohere_key, self.openai_key]):
            logger.error("CRITICAL: No API keys found!")
            logger.error("At least one of these must be set:")
            logger.error("  - GROQ_API_KEY")
            logger.error("  - GEMINI_API_KEY")
            logger.error("  - COHERE_API_KEY")
            logger.error("  - OPENAI_API_KEY")
            sys.exit(1)

        if self.groq_key:
            logger.info("✓ GROQ_API_KEY is set")
        else:
            logger.warning("⚠ GROQ_API_KEY not set - will skip Groq provider")

        if self.gemini_key:
            logger.info("✓ GEMINI_API_KEY is set")
        else:
            logger.warning("⚠ GEMINI_API_KEY not set - will skip Gemini provider")

        if self.cohere_key:
            logger.info("✓ COHERE_API_KEY is set")
        else:
            logger.warning("⚠ COHERE_API_KEY not set - will skip Cohere provider")

        if self.openai_key:
            logger.info("✓ OPENAI_API_KEY is set")
        else:
            logger.warning("⚠ OPENAI_API_KEY not set - will skip OpenAI provider")

        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ghgf_blogging')
        }

        logger.info(f"Database config: host={self.db_config['host']}, db={self.db_config['database']}, user={self.db_config['user']}")

        self.titles_generated = 0
        self.current_topic = None
        self.trending_keywords = []
        self.provider_used = None

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*70}")
        print(f"{BOLD}{title}{RESET}")
        print('='*70)

    def connect_db(self):
        """Connect to database"""
        try:
            logger.info("Attempting database connection...")
            conn = mysql.connector.connect(**self.db_config)
            logger.info("✓ Database connected successfully")

            # Verify database has required tables
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'topic_rotation'")
            if not cursor.fetchone():
                logger.error("CRITICAL: topic_rotation table does not exist!")
            else:
                logger.info("✓ topic_rotation table exists")

            cursor.execute("SHOW TABLES LIKE 'trending_keywords'")
            if not cursor.fetchone():
                logger.error("CRITICAL: trending_keywords table does not exist!")
            else:
                logger.info("✓ trending_keywords table exists")

            cursor.execute("SHOW TABLES LIKE 'blog_titles'")
            if not cursor.fetchone():
                logger.error("CRITICAL: blog_titles table does not exist!")
            else:
                logger.info("✓ blog_titles table exists")

            cursor.close()
            return conn
        except mysql.connector.Error as e:
            logger.error(f"Database connection failed - MySQL Error {e.errno}: {e.msg}")
            logger.error(f"Full error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_current_topic(self, conn):
        """Get current active topic from 18-topic rotation"""
        try:
            logger.info("Fetching current active topic...")
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM topic_rotation WHERE status = 'active' LIMIT 1"
            logger.debug(f"Query: {query}")
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result:
                self.current_topic = result
                logger.info(f"✓ Current topic: {result['topic_name']}")
                logger.debug(f"  Topic details: {json.dumps(result, indent=2, default=str)}")
                logger.info(f"  Cycle: {result.get('cycle_number', 'N/A')}, Sequence: {result.get('topic_sequence', 'N/A')}")
                return result
            else:
                logger.warning("No active topic found. Attempting to set first topic to active...")
                query = "UPDATE topic_rotation SET status = 'active', start_date = CURDATE() WHERE cycle_number = 1 AND topic_sequence = 1"
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                logger.info(f"Updated {cursor.rowcount} rows to active")
                cursor.close()
                return self.get_current_topic(conn)
        except Exception as e:
            logger.error(f"Error getting current topic: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_trending_keywords(self, conn, topic):
        """Get trending keywords for current topic from R13's cache"""
        try:
            logger.info(f"Fetching trending keywords for topic: {topic['topic_name']}...")
            cursor = conn.cursor(dictionary=True)
            # Get top 10 trending keywords for this topic
            query = """
                SELECT keyword, search_volume, competition_level
                FROM trending_keywords
                WHERE topic = %s
                ORDER BY search_volume DESC
                LIMIT 10
            """
            logger.debug(f"Query: {query}")
            logger.debug(f"Parameter: {topic['topic_name']}")
            cursor.execute(query, (topic['topic_name'],))
            results = cursor.fetchall()
            cursor.close()

            if results:
                self.trending_keywords = results
                keywords_str = ", ".join([k['keyword'] for k in results])
                logger.info(f"✓ Retrieved {len(results)} trending keywords")
                logger.debug(f"  Keywords: {keywords_str}")
                return results
            else:
                logger.warning(f"No trending keywords found for topic: {topic['topic_name']}")
                logger.info(f"Using topic name as fallback keyword")
                return [{'keyword': topic['topic_name'], 'search_volume': 0, 'competition_level': 'Medium'}]
        except Exception as e:
            logger.error(f"Error getting trending keywords: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def generate_titles_with_groq(self, topic, keywords):
        """Generate 5 title variations using Groq"""
        if not self.groq_key:
            logger.debug("Groq API key not available, skipping Groq provider")
            return None

        try:
            from groq import Groq

            logger.info("=" * 70)
            logger.info("ATTEMPTING GROQ PROVIDER")
            logger.info("=" * 70)

            logger.info("Step 1: Initializing Groq client...")
            client = Groq(api_key=self.groq_key)
            logger.info("✓ Groq client initialized successfully")

            keywords_list = ", ".join([f"{k['keyword']}" for k in keywords[:5]])
            logger.debug(f"Keywords for prompt: {keywords_list}")

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

            logger.info("Step 2: Building API request...")
            logger.debug(f"  Model: {self.groq_model}")
            logger.debug(f"  Max tokens: 300")
            logger.debug(f"  Temperature: 0.8")
            logger.debug(f"  Prompt length: {len(prompt)} characters")

            logger.info("Step 3: Calling Groq API...")
            try:
                # Groq API requires model parameter - always include it (guaranteed to have value from defaults)
                response = client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.8
                )
                logger.info("✓ Groq API call succeeded")
            except Exception as api_error:
                logger.error(f"GROQ API CALL FAILED:")
                logger.error(f"  Error Type: {type(api_error).__name__}")
                logger.error(f"  Error Message: {str(api_error)}")
                return None

            logger.info("Step 4: Processing response...")
            if not response.choices:
                logger.error("Groq returned empty response (no choices)")
                return None

            first_choice = response.choices[0]
            if not first_choice.message or not first_choice.message.content:
                logger.error("Groq returned empty message content")
                return None

            titles_raw = first_choice.message.content.strip()
            logger.info(f"✓ Received response content: {len(titles_raw)} characters")
            logger.debug(f"  Raw content: {titles_raw}")

            titles = [t.strip() for t in titles_raw.split('|')]
            titles = [t for t in titles if t]  # Remove empty

            logger.info(f"✓ Parsed {len(titles)} titles from Groq response")
            for i, t in enumerate(titles[:5], 1):
                logger.debug(f"  Title {i}: {t}")

            self.titles_generated = len(titles)
            self.provider_used = "Groq"
            return titles[:5]

        except ImportError:
            logger.warning("Groq library not installed, skipping Groq provider")
            return None
        except Exception as e:
            logger.error(f"GROQ PROVIDER FAILED:")
            logger.error(f"  Error Type: {type(e).__name__}")
            logger.error(f"  Error Message: {str(e)}")
            return None

    def generate_titles_with_gemini(self, topic, keywords):
        """Generate 5 title variations using Google Gemini"""
        if not self.gemini_key:
            logger.debug("Gemini API key not available, skipping Gemini provider")
            return None

        try:
            import google.generativeai as genai

            logger.info("=" * 70)
            logger.info("ATTEMPTING GEMINI PROVIDER")
            logger.info("=" * 70)

            logger.info("Step 1: Initializing Gemini client...")
            genai.configure(api_key=self.gemini_key)
            logger.info("✓ Gemini client initialized successfully")

            keywords_list = ", ".join([f"{k['keyword']}" for k in keywords[:5]])
            logger.debug(f"Keywords for prompt: {keywords_list}")

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

            logger.info("Step 2: Building API request...")
            logger.debug(f"  Model: {self.gemini_model}")
            logger.debug(f"  Prompt length: {len(prompt)} characters")

            logger.info("Step 3: Calling Gemini API...")
            try:
                model = genai.GenerativeModel(self.gemini_model)
                response = model.generate_content(prompt)
                logger.info("✓ Gemini API call succeeded")
            except Exception as api_error:
                logger.error(f"GEMINI API CALL FAILED:")
                logger.error(f"  Error Type: {type(api_error).__name__}")
                logger.error(f"  Error Message: {str(api_error)}")
                return None

            logger.info("Step 4: Processing response...")
            if not response or not response.text:
                logger.error("Gemini returned empty response")
                return None

            titles_raw = response.text.strip()
            logger.info(f"✓ Received response content: {len(titles_raw)} characters")
            logger.debug(f"  Raw content: {titles_raw}")

            titles = [t.strip() for t in titles_raw.split('|')]
            titles = [t for t in titles if t]  # Remove empty

            logger.info(f"✓ Parsed {len(titles)} titles from Gemini response")
            for i, t in enumerate(titles[:5], 1):
                logger.debug(f"  Title {i}: {t}")

            self.titles_generated = len(titles)
            self.provider_used = "Gemini"
            return titles[:5]

        except ImportError:
            logger.warning("Google Generative AI library not installed, skipping Gemini provider")
            return None
        except Exception as e:
            logger.error(f"GEMINI PROVIDER FAILED:")
            logger.error(f"  Error Type: {type(e).__name__}")
            logger.error(f"  Error Message: {str(e)}")
            return None

    def generate_titles_with_cohere(self, topic, keywords):
        """Generate 5 title variations using Cohere"""
        if not self.cohere_key:
            logger.debug("Cohere API key not available, skipping Cohere provider")
            return None

        try:
            import cohere

            logger.info("=" * 70)
            logger.info("ATTEMPTING COHERE PROVIDER")
            logger.info("=" * 70)

            logger.info("Step 1: Initializing Cohere client...")
            client = cohere.ClientV2(api_key=self.cohere_key)
            logger.info("✓ Cohere client initialized successfully")

            keywords_list = ", ".join([f"{k['keyword']}" for k in keywords[:5]])
            logger.debug(f"Keywords for prompt: {keywords_list}")

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

            logger.info("Step 2: Building API request...")
            logger.debug(f"  Model: {self.cohere_model}")
            logger.debug(f"  Max tokens: 300")
            logger.debug(f"  Prompt length: {len(prompt)} characters")

            logger.info("Step 3: Calling Cohere API...")
            try:
                response = client.chat(
                    model=self.cohere_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                logger.info("✓ Cohere API call succeeded")
            except Exception as api_error:
                logger.error(f"COHERE API CALL FAILED:")
                logger.error(f"  Error Type: {type(api_error).__name__}")
                logger.error(f"  Error Message: {str(api_error)}")
                return None

            logger.info("Step 4: Processing response...")
            if not response or not response.message or not response.message.content:
                logger.error("Cohere returned empty response")
                return None

            titles_raw = response.message.content[0].text.strip()
            logger.info(f"✓ Received response content: {len(titles_raw)} characters")
            logger.debug(f"  Raw content: {titles_raw}")

            titles = [t.strip() for t in titles_raw.split('|')]
            titles = [t for t in titles if t]  # Remove empty

            logger.info(f"✓ Parsed {len(titles)} titles from Cohere response")
            for i, t in enumerate(titles[:5], 1):
                logger.debug(f"  Title {i}: {t}")

            self.titles_generated = len(titles)
            self.provider_used = "Cohere"
            return titles[:5]

        except ImportError:
            logger.warning("Cohere library not installed, skipping Cohere provider")
            return None
        except Exception as e:
            logger.error(f"COHERE PROVIDER FAILED:")
            logger.error(f"  Error Type: {type(e).__name__}")
            logger.error(f"  Error Message: {str(e)}")
            return None

    def generate_titles_with_openai(self, topic, keywords):
        """Generate 5 title variations using OpenAI"""
        if not self.openai_key:
            logger.debug("OpenAI API key not available, skipping OpenAI provider")
            return None

        try:
            from openai import OpenAI

            logger.info("=" * 70)
            logger.info("ATTEMPTING OPENAI PROVIDER")
            logger.info("=" * 70)

            logger.info("Step 1: Initializing OpenAI client...")
            client = OpenAI(api_key=self.openai_key)
            logger.info("✓ OpenAI client initialized successfully")

            keywords_list = ", ".join([f"{k['keyword']}" for k in keywords[:5]])
            logger.debug(f"Keywords for prompt: {keywords_list}")

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

            logger.info("Step 2: Building API request...")
            logger.debug(f"  Model: {self.openai_model}")
            logger.debug(f"  Max tokens: 300")
            logger.debug(f"  Temperature: 0.8")
            logger.debug(f"  Prompt length: {len(prompt)} characters")

            logger.info("Step 3: Calling OpenAI API...")
            try:
                response = client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.8
                )
                logger.info("✓ OpenAI API call succeeded")
            except Exception as api_error:
                logger.error(f"OPENAI API CALL FAILED:")
                logger.error(f"  Error Type: {type(api_error).__name__}")
                logger.error(f"  Error Message: {str(api_error)}")
                return None

            logger.info("Step 4: Processing response...")
            if not response.choices:
                logger.error("OpenAI returned empty response (no choices)")
                return None

            first_choice = response.choices[0]
            if not first_choice.message or not first_choice.message.content:
                logger.error("OpenAI returned empty message content")
                return None

            titles_raw = first_choice.message.content.strip()
            logger.info(f"✓ Received response content: {len(titles_raw)} characters")
            logger.debug(f"  Raw content: {titles_raw}")

            titles = [t.strip() for t in titles_raw.split('|')]
            titles = [t for t in titles if t]  # Remove empty

            logger.info(f"✓ Parsed {len(titles)} titles from OpenAI response")
            for i, t in enumerate(titles[:5], 1):
                logger.debug(f"  Title {i}: {t}")

            self.titles_generated = len(titles)
            self.provider_used = "OpenAI"
            return titles[:5]

        except ImportError:
            logger.warning("OpenAI library not installed, skipping OpenAI provider")
            return None
        except Exception as e:
            logger.error(f"OPENAI PROVIDER FAILED:")
            logger.error(f"  Error Type: {type(e).__name__}")
            logger.error(f"  Error Message: {str(e)}")
            return None

    def generate_titles_with_fallback(self, topic, keywords):
        """Generate titles using provider fallback chain: Groq → Gemini → Cohere → OpenAI"""
        logger.info("=" * 70)
        logger.info("TITLE GENERATION - MULTI-PROVIDER FALLBACK")
        logger.info("=" * 70)

        # Try Groq first
        logger.info("\n[1/4] Trying Groq provider...")
        titles = self.generate_titles_with_groq(topic, keywords)
        if titles:
            logger.info(f"✓ Successfully generated titles using {self.provider_used}")
            return titles

        # Try Gemini second
        logger.info("\n[2/4] Groq failed, trying Gemini provider...")
        titles = self.generate_titles_with_gemini(topic, keywords)
        if titles:
            logger.info(f"✓ Successfully generated titles using {self.provider_used}")
            return titles

        # Try Cohere third
        logger.info("\n[3/4] Gemini failed, trying Cohere provider...")
        titles = self.generate_titles_with_cohere(topic, keywords)
        if titles:
            logger.info(f"✓ Successfully generated titles using {self.provider_used}")
            return titles

        # Try OpenAI fourth
        logger.info("\n[4/4] Cohere failed, trying OpenAI provider...")
        titles = self.generate_titles_with_openai(topic, keywords)
        if titles:
            logger.info(f"✓ Successfully generated titles using {self.provider_used}")
            return titles

        # All providers failed
        logger.error("=" * 70)
        logger.error("❌ ALL PROVIDERS FAILED")
        logger.error("=" * 70)
        logger.error("Could not generate titles from any provider:")
        logger.error("  1. Groq - Failed or no API key")
        logger.error("  2. Gemini - Failed or no API key")
        logger.error("  3. Cohere - Failed or no API key")
        logger.error("  4. OpenAI - Failed or no API key")
        logger.error("\nEnsure at least one API key is configured:")
        logger.error("  - GROQ_API_KEY")
        logger.error("  - GEMINI_API_KEY")
        logger.error("  - COHERE_API_KEY")
        logger.error("  - OPENAI_API_KEY")
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
                    INSERT INTO blog_titles (title, topic, keywords, created_at, ctr_score, provider)
                    VALUES (%s, %s, %s, NOW(), %s, %s)
                """
                cursor.execute(query, (
                    title_data['title'],
                    topic['topic_name'],
                    keywords_str,
                    title_data['score'] / 100.0,
                    self.provider_used
                ))

            conn.commit()
            logger.info(f"Saved {len(titles_data)} titles to database (Provider: {self.provider_used})")
            return True
        except Exception as e:
            logger.error(f"Error saving titles: {str(e)}")
            return False
        finally:
            cursor.close()

    def run(self):
        """Main execution flow"""
        self.print_header("R2: BLOG TITLE GENERATOR (MULTI-PROVIDER)")
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

            # Step 3: Generate titles using multi-provider fallback
            print(f"{BOLD}Step 3: Generating 5 Title Variations (Multi-Provider Fallback){RESET}")
            titles = self.generate_titles_with_fallback(topic, keywords)
            if not titles:
                logger.error("Failed to generate titles from any provider")
                print(f"  {RED}✗ Failed to generate titles{RESET}\n")
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
                print(f"  ✓ {GREEN}Saved {len(scored_titles)} titles to blog_titles table (Provider: {self.provider_used}){RESET}\n")

            # Summary
            print(f"{'='*70}")
            print(f"{BOLD}SUMMARY{RESET}")
            print(f"  Topic: {BLUE}{topic['topic_name']}{RESET}")
            print(f"  Keywords: {len(keywords)} trending keywords available")
            print(f"  Titles Generated: {GREEN}{self.titles_generated}{RESET}")
            print(f"  Provider Used: {GREEN}{self.provider_used}{RESET}")
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
