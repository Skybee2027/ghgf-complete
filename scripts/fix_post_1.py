#!/usr/bin/env python3
"""Fix Post 1 as perfect template using Groq"""

import os
import sys
import re
import mysql.connector
from groq import Groq

POST_TITLE = "5 Complete Steps to Achieve Your Health and Fitness Dreams"
TARGET_WORDS = 1500

print("=" * 80)
print("PHASE 3: FIX POST 1 - PERFECT TEMPLATE")
print("=" * 80)

# Get credentials
groq_key = os.getenv('GROQ_API_KEY', '').strip()
groq_model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b').strip()

if not groq_key:
    print("❌ GROQ_API_KEY not set")
    sys.exit(1)

try:
    # Connect to database
    print(f"\nConnecting to database...")
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = db.cursor(dictionary=True)
    print("✅ Connected")

    # Get post
    print(f"\nFinding: {POST_TITLE}")
    cursor.execute(
        "SELECT id, content FROM blog_posts WHERE title = %s LIMIT 1",
        (POST_TITLE,)
    )
    post = cursor.fetchone()

    if not post:
        print("❌ Post not found")
        sys.exit(1)

    post_id = post['id']
    current = post['content']
    curr_words = len(current.split())

    print(f"✅ Found Post ID {post_id}: {curr_words} words")

    # Enhance with Groq
    print(f"\nCalling Groq API...")
    client = Groq(api_key=groq_key)

    prompt = f"""Expand this blog to {TARGET_WORDS}+ words. Be comprehensive, add examples, tips, keep professional tone. No markdown artifacts.

{current}"""

    resp = client.chat.completions.create(
        model=groq_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000
    )

    enhanced = resp.choices[0].message.content

    # Clean artifacts
    enhanced = re.sub(r'```.*?```', '', enhanced, flags=re.DOTALL)
    enhanced = enhanced.replace('"`', '').replace('"`html', '')

    new_words = len(enhanced.split())
    improvement = ((new_words - curr_words) / curr_words * 100) if curr_words > 0 else 0

    print(f"✅ Enhanced: {curr_words} → {new_words} words (+{improvement:.0f}%)")

    # Update database
    print(f"\nUpdating database...")
    cursor.execute(
        "UPDATE blog_posts SET content = %s, ready_for_wordpress = 1 WHERE id = %s",
        (enhanced, post_id)
    )
    db.commit()
    print("✅ Database updated")

    cursor.close()
    db.close()

    print("\n" + "=" * 80)
    print(f"✅ POST 1 READY: {new_words} words, zero artifacts")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
