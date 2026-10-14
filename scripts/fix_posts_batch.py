#!/usr/bin/env python3
"""Fix blog posts in batch (5 posts per run) using Groq"""

import os
import sys
import re
import mysql.connector
from groq import Groq

BATCH_SIZE = 5
TARGET_WORDS = 1500

print("=" * 80)
print("PHASE 4: BATCH FIX - PROCESS 5 POSTS")
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

    # Find posts that need enhancement (word count < 1500)
    print(f"\nFinding posts with <{TARGET_WORDS} words...")
    cursor.execute(
        """SELECT id, title, content
           FROM blog_posts
           WHERE LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) < %s
           AND ready_for_wordpress = 0
           ORDER BY created_at ASC
           LIMIT %s""",
        (TARGET_WORDS, BATCH_SIZE)
    )
    posts = cursor.fetchall()

    if not posts:
        print(f"✅ No posts needing enhancement found (all have {TARGET_WORDS}+ words)")
        cursor.close()
        db.close()
        sys.exit(0)

    print(f"✅ Found {len(posts)} posts to enhance")

    # Initialize Groq client
    client = Groq(api_key=groq_key)

    enhanced_count = 0

    # Process each post
    for i, post in enumerate(posts, 1):
        post_id = post['id']
        title = post['title']
        current = post['content']
        curr_words = len(current.split())

        print(f"\n[{i}/{len(posts)}] Processing: {title}")
        print(f"  Current: {curr_words} words")

        try:
            # Enhance with Groq
            print(f"  Calling Groq API...")
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

            print(f"  Enhanced: {curr_words} → {new_words} words (+{improvement:.0f}%)")

            # Update database
            cursor.execute(
                "UPDATE blog_posts SET content = %s, ready_for_wordpress = 1 WHERE id = %s",
                (enhanced, post_id)
            )
            db.commit()
            print(f"  ✅ Database updated")
            enhanced_count += 1

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            continue

    cursor.close()
    db.close()

    print("\n" + "=" * 80)
    print(f"✅ BATCH COMPLETE: {enhanced_count}/{len(posts)} posts enhanced")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
