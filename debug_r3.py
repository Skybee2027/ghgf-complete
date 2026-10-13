#!/usr/bin/env python3
"""
Debug R3: Test content generation locally
Helps identify what's going wrong with LLM API calls
"""

import os
import sys
import mysql.connector
from datetime import datetime
import logging

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

def check_api_keys():
    """Check which API keys are configured"""
    print(f"\n{BOLD}STEP 1: Checking API Keys{RESET}")
    print("=" * 70)

    keys = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'COHERE_API_KEY': os.getenv('COHERE_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }

    for key_name, key_value in keys.items():
        if key_value:
            # Show first 10 chars of key for verification
            display = key_value[:10] + "..." if len(key_value) > 10 else key_value
            print(f"  ✓ {key_name}: {GREEN}{display}{RESET}")
        else:
            print(f"  ✗ {key_name}: {RED}NOT SET{RESET}")

    if not any(keys.values()):
        print(f"\n{RED}ERROR: No API keys configured!{RESET}")
        return False

    return True

def check_models():
    """Check which models are configured"""
    print(f"\n{BOLD}STEP 2: Checking Models{RESET}")
    print("=" * 70)

    models = {
        'GROQ_MODEL': os.getenv('GROQ_MODEL'),
        'GEMINI_MODEL': os.getenv('GEMINI_MODEL'),
        'COHERE_MODEL': os.getenv('COHERE_MODEL'),
        'OPENAI_MODEL': os.getenv('OPENAI_MODEL')
    }

    for model_name, model_value in models.items():
        if model_value:
            print(f"  ✓ {model_name}: {BLUE}{model_value}{RESET}")
        else:
            print(f"  ⚠ {model_name}: {YELLOW}NOT SET (will use default){RESET}")

    return True

def check_database():
    """Check database connectivity and data availability"""
    print(f"\n{BOLD}STEP 3: Checking Database{RESET}")
    print("=" * 70)

    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'ghgf_blogging')
    }

    print(f"  DB_HOST: {BLUE}{db_config['host']}{RESET}")
    print(f"  DB_USER: {BLUE}{db_config['user']}{RESET}")
    print(f"  DB_NAME: {BLUE}{db_config['database']}{RESET}")

    try:
        conn = mysql.connector.connect(**db_config)
        print(f"  ✓ {GREEN}Database connected{RESET}")
        cursor = conn.cursor(dictionary=True)

        # Check blog_titles
        cursor.execute("SELECT COUNT(*) as count FROM blog_titles WHERE used = FALSE")
        result = cursor.fetchone()
        available_titles = result['count'] if result else 0
        print(f"\n  ✓ Available titles (unused): {BLUE}{available_titles}{RESET}")

        # Get a sample title
        cursor.execute("""
            SELECT id, title, topic, keywords, ctr_score
            FROM blog_titles
            WHERE used = FALSE
            ORDER BY ctr_score DESC
            LIMIT 1
        """)
        title_sample = cursor.fetchone()

        if title_sample:
            print(f"    Sample title: {title_sample['title']}")
            print(f"    Topic: {title_sample['topic']}")
            print(f"    CTR Score: {title_sample['ctr_score']}")
        else:
            print(f"  {RED}✗ No available titles in blog_titles table!{RESET}")

        # Check trending_keywords
        if title_sample:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM trending_keywords
                WHERE topic = %s
            """, (title_sample['topic'],))
            result = cursor.fetchone()
            available_keywords = result['count'] if result else 0
            print(f"\n  ✓ Keywords for topic '{title_sample['topic']}': {BLUE}{available_keywords}{RESET}")

            if available_keywords > 0:
                cursor.execute("""
                    SELECT keyword, search_volume
                    FROM trending_keywords
                    WHERE topic = %s
                    ORDER BY search_volume DESC
                    LIMIT 5
                """, (title_sample['topic'],))
                keywords = cursor.fetchall()
                for kw in keywords:
                    print(f"    - {kw['keyword']} (volume: {kw['search_volume']})")
            else:
                print(f"  {RED}✗ No keywords found for topic!{RESET}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  {RED}✗ Database error: {str(e)}{RESET}")
        return False

def test_groq_directly():
    """Test Groq API directly with minimal prompt"""
    print(f"\n{BOLD}STEP 4: Testing Groq API{RESET}")
    print("=" * 70)

    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL')

    if not api_key:
        print(f"  {RED}✗ GROQ_API_KEY not set{RESET}")
        return None

    if not model:
        print(f"  {YELLOW}⚠ GROQ_MODEL not set, using default{RESET}")
        model = 'openai/gpt-oss-120b'

    try:
        from groq import Groq

        print(f"  Testing with model: {BLUE}{model}{RESET}")
        client = Groq(api_key=api_key)

        # Test 1: Simple request
        print(f"\n  Test 1: Simple 50-word request")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Write 50 words about fitness. Just the content, no explanation."}],
            max_tokens=100,
            temperature=0.7
        )

        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            print(f"  ✓ Response received: {len(content)} characters")
            print(f"    Content preview: {content[:100]}...")
        else:
            print(f"  {RED}✗ Empty response from Groq{RESET}")
            return None

        # Test 2: Longer request (like R3 does)
        print(f"\n  Test 2: 800-1500 word request (like R3)")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Write a 1000-word blog post about 'Best Fitness Exercises'. Include HTML tags. Return ONLY the content."}],
            max_tokens=2000,
            temperature=0.7
        )

        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            word_count = len(content.split())
            print(f"  ✓ Response received: {len(content)} characters, ~{word_count} words")
            print(f"    Content preview: {content[:150]}...")

            if word_count < 500:
                print(f"  {YELLOW}⚠ WARNING: Response shorter than expected!{RESET}")
                print(f"     Expected: ~800-1500 words, Got: ~{word_count} words")

            return word_count
        else:
            print(f"  {RED}✗ Empty response from Groq{RESET}")
            return None

    except ImportError:
        print(f"  {RED}✗ Groq library not installed: pip install groq{RESET}")
        return None
    except Exception as e:
        print(f"  {RED}✗ Groq API error: {type(e).__name__}: {str(e)}{RESET}")
        logger.debug(f"Full error: {repr(e)}")
        return None

def test_gemini_directly():
    """Test Gemini API directly"""
    print(f"\n{BOLD}STEP 5: Testing Gemini API{RESET}")
    print("=" * 70)

    api_key = os.getenv('GEMINI_API_KEY')
    model = os.getenv('GEMINI_MODEL')

    if not api_key:
        print(f"  {RED}✗ GEMINI_API_KEY not set{RESET}")
        return None

    if not model:
        print(f"  {YELLOW}⚠ GEMINI_MODEL not set, using default{RESET}")
        model = 'gemini-1.5-flash'

    try:
        import google.generativeai as genai

        print(f"  Testing with model: {BLUE}{model}{RESET}")
        genai.configure(api_key=api_key)

        print(f"\n  Test: 800-1500 word request")
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(
            "Write a 1000-word blog post about 'Best Fitness Exercises'. Include HTML tags. Return ONLY the content."
        )

        if response.text:
            content = response.text
            word_count = len(content.split())
            print(f"  ✓ Response received: {len(content)} characters, ~{word_count} words")
            print(f"    Content preview: {content[:150]}...")

            if word_count < 500:
                print(f"  {YELLOW}⚠ WARNING: Response shorter than expected!{RESET}")
                print(f"     Expected: ~800-1500 words, Got: ~{word_count} words")

            return word_count
        else:
            print(f"  {RED}✗ Empty response from Gemini{RESET}")
            return None

    except ImportError:
        print(f"  {RED}✗ Google Generative AI library not installed: pip install google-generativeai{RESET}")
        return None
    except Exception as e:
        print(f"  {RED}✗ Gemini API error: {type(e).__name__}: {str(e)}{RESET}")
        logger.debug(f"Full error: {repr(e)}")
        return None

def main():
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}R3 DEBUGGING TOOL - Content Generation Diagnostics{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run checks
    keys_ok = check_api_keys()
    check_models()
    db_ok = check_database()

    if not keys_ok:
        print(f"\n{RED}CRITICAL: No API keys configured. Cannot test content generation.{RESET}")
        sys.exit(1)

    if not db_ok:
        print(f"\n{RED}CRITICAL: Database connection failed.{RESET}")
        sys.exit(1)

    # Test APIs
    groq_words = test_groq_directly()
    gemini_words = test_gemini_directly()

    # Summary
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}SUMMARY{RESET}")
    print(f"{'='*70}{RESET}")

    if groq_words is not None and groq_words >= 500:
        print(f"  {GREEN}✓ Groq API working: {groq_words} words generated{RESET}")
    elif groq_words is not None:
        print(f"  {YELLOW}⚠ Groq API responding but output too short: {groq_words} words{RESET}")
    else:
        print(f"  {RED}✗ Groq API not working{RESET}")

    if gemini_words is not None and gemini_words >= 500:
        print(f"  {GREEN}✓ Gemini API working: {gemini_words} words generated{RESET}")
    elif gemini_words is not None:
        print(f"  {YELLOW}⚠ Gemini API responding but output too short: {gemini_words} words{RESET}")
    else:
        print(f"  {RED}✗ Gemini API not working{RESET}")

    print(f"\n{BOLD}NEXT STEPS:{RESET}")
    if not groq_words and not gemini_words:
        print(f"  1. Check API keys are correct and have valid credentials")
        print(f"  2. Verify models are correct for each provider")
        print(f"  3. Check API rate limits and account status")
        print(f"  4. Run with: GROQ_API_KEY=xxx python debug_r3.py")
    else:
        print(f"  1. Check if R3 is using the correct prompt")
        print(f"  2. Run R3 with enhanced logging to see actual responses")
        print(f"  3. Verify database data (titles and keywords)")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
