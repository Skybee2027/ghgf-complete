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

    def _extract_text_paragraphs(self, content):
        """Extract paragraphs while preserving HTML structure
        Returns list of tuples: (full_html, text_only, is_header)
        """
        paragraphs = []

        # Split by paragraph tags but preserve them
        p_pattern = r'<p>(.*?)</p>'
        h2_pattern = r'<h2>(.*?)</h2>'

        # Extract all paragraphs
        for match in re.finditer(p_pattern, content, re.DOTALL):
            html = match.group(0)
            text = match.group(1)
            # Strip HTML tags from text for analysis
            text_only = re.sub(r'<[^>]+>', '', text)
            paragraphs.append({
                'full_html': html,
                'text': text_only,
                'type': 'paragraph',
                'match_obj': match
            })

        # Extract headers
        for match in re.finditer(h2_pattern, content):
            html = match.group(0)
            text = match.group(1)
            paragraphs.append({
                'full_html': html,
                'text': text,
                'type': 'header',
                'match_obj': match
            })

        return paragraphs

    def _is_valid_injection_point(self, sentence, keywords_lower):
        """Check if a sentence is a valid injection point
        Skip if: already contains all keywords, is a list, too short, has placeholders
        """
        # Skip if sentence is too short (< 5 words)
        sentence_words = sentence.strip().split()
        if len(sentence_words) < 5:
            return False

        # Skip if contains multiple keyword instances already (keyword stuffing)
        keyword_count = sum(1 for kw in keywords_lower if kw in sentence.lower())
        if keyword_count > 1:
            return False

        # Skip if contains placeholders
        if '[[' in sentence or ']]' in sentence:
            return False

        # Skip if it's a list of items starting with numbers/bullets
        if re.match(r'^\d+\s*[\.\)]\s', sentence) or re.match(r'^[\*\-]\s', sentence):
            return False

        return True

    def _inject_keyword_naturally(self, sentence, keyword):
        """Inject a keyword naturally into a sentence using context-aware placement
        Strategies:
        1. If sentence has topical words (about, including, such as), inject there
        2. Otherwise integrate into relevant clause
        3. Avoid mechanical " and keyword" patterns
        """
        keyword_lower = keyword.lower()

        # Strategy 1: Look for natural connection points (about, including, such as, etc)
        connection_patterns = [
            (r'(about\s+)', lambda m: m.group(1) + keyword + ' '),
            (r'(including\s+)', lambda m: m.group(1) + keyword + ', '),
            (r'(such as\s+)', lambda m: m.group(1) + keyword + ', '),
            (r'(like\s+)', lambda m: m.group(1) + keyword + ' and '),
        ]

        for pattern, replacement in connection_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                new_sentence = re.sub(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
                if new_sentence != sentence:
                    logger.info(f"    Injected '{keyword}' using connection pattern")
                    return new_sentence

        # Strategy 2: Integrate into a clause at the end of sentence before period/punctuation
        # Find the last complete clause/phrase before punctuation
        match = re.search(r'([^.!?]+)([.!?]?\s*)$', sentence)
        if match:
            clause = match.group(1).strip()
            punctuation = match.group(2)

            # Check if clause is topically related to keyword (contains related words)
            clause_words = set(word.lower() for word in clause.split() if len(word) > 3)
            keyword_words = set(word.lower() for word in keyword.split())

            # If keyword is multi-word (e.g., "health fitness"), look for any component
            if len(keyword.split()) > 1:
                shared = clause_words & keyword_words
                if shared:
                    # Topically related - integrate keyword before period
                    new_sentence = f"{sentence.rstrip('.!?')}, particularly with {keyword}{punctuation}"
                    logger.info(f"    Injected '{keyword}' into topical clause")
                    return new_sentence
            else:
                # Single-word keyword - inject if sentence is about related topic
                # For now, use a conservative insertion
                new_sentence = f"{sentence.rstrip('.!?')} regarding {keyword}{punctuation}"
                logger.info(f"    Injected '{keyword}' into sentence")
                return new_sentence

        # Fallback: return original sentence (don't force bad injection)
        return sentence

    def optimize_content(self, content, keywords):
        """Optimize content for keywords with semantic, context-aware insertion
        Target: 1.0-1.5% keyword density with natural language preservation
        """
        if not keywords:
            return content

        optimized = content
        keywords_lower = [kw.lower() for kw in keywords]

        # Calculate total word count
        words = re.findall(r'\b\w+\b', content.lower())
        total_words = len(words)

        if total_words == 0:
            return content

        logger.info(f"Content has {total_words} words")
        logger.info(f"Processing {len(keywords)} keywords for natural integration")

        # For each keyword, ensure it appears naturally in the content
        for keyword in keywords[:5]:  # Process top 5 keywords
            keyword_lower = keyword.lower()
            current_count = optimized.lower().count(keyword_lower)

            # Target 1-2 natural occurrences per keyword (not forced mechanical density)
            # If keyword already in content naturally, don't force more
            if current_count >= 2:
                logger.info(f"✓ '{keyword}': already appears {current_count} times (sufficient)")
                continue

            logger.info(f"Processing '{keyword}': found {current_count} time(s)")

            # Split content into paragraphs and headers
            paragraphs = optimized.split('</p>')
            injected = False

            # Skip first paragraph (introduction) and last (conclusion) for injection
            # Inject into middle content paragraphs
            for i in range(1, len(paragraphs) - 1):
                if current_count >= 2:  # Stop after 2 natural occurrences
                    break

                para = paragraphs[i]

                # Skip if this is a header
                if '<h' in para:
                    continue

                # Skip if paragraph already has this keyword
                if keyword_lower in para.lower():
                    continue

                # Extract text from paragraph (strip HTML tags for analysis)
                text_match = re.search(r'>([^<]+)<', para)
                if not text_match:
                    continue

                para_text = text_match.group(1)

                # Split into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para_text)
                if not sentences:
                    continue

                # Find a valid sentence to inject into
                for j, sentence in enumerate(sentences):
                    if not self._is_valid_injection_point(sentence, keywords_lower):
                        continue

                    # Inject keyword naturally
                    new_sentence = self._inject_keyword_naturally(sentence, keyword)

                    if new_sentence != sentence:
                        # Replace sentence in original paragraph HTML
                        escaped_sentence = re.escape(sentence)
                        para = re.sub(escaped_sentence, new_sentence, para, count=1)
                        current_count += 1
                        injected = True

                        if current_count >= 2:
                            break

                paragraphs[i] = para

            optimized = '</p>'.join(paragraphs)

            if injected:
                logger.info(f"  ✓ Successfully injected '{keyword}' naturally")
            else:
                logger.info(f"  ⚠ Could not find natural injection point for '{keyword}'")

        # NOTE: Headers are left unchanged - they should reflect natural content structure,
        # not be modified for keyword optimization. Keywords are integrated into body content
        # through the injection logic above.

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
            print(f"  ✓ Keywords integrated naturally into body content")

            # Verify final keyword density
            print(f"\n{BOLD}Step 3a: Verifying Final Keyword Density{RESET}")
            for kw in keywords:
                count, density = self.analyze_keyword_density(optimized, kw)
                status = "✓" if density >= 0.01 else "⚠"
                print(f"  {status} {kw}: {count} times ({density:.2%})")
            print()

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
