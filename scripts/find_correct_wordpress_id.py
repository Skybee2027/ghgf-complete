#!/usr/bin/env python3
"""
Find the correct WordPress post ID by searching for the post by slug
Then update database with correct ID if different
"""

import os
import sys
import requests
import mysql.connector

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ghgf_blogging')

WORDPRESS_URL = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
WORDPRESS_USER = os.getenv('WORDPRESS_USER', 'api_user')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', '')

WP_API = f"{WORDPRESS_URL}/wp-json/wp/v2"

print("\n" + "="*80)
print("🔎 FIND CORRECT WORDPRESS POST ID")
print("="*80)

# Get post slug from database
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title, slug, wordpress_post_id FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1")
    post = cursor.fetchone()

    if not post:
        print("❌ Post not found in database")
        sys.exit(1)

    db_id = post['id']
    title = post['title']
    slug = post['slug']
    stored_wp_id = post['wordpress_post_id']

    print(f"\n📋 Database info:")
    print(f"   DB ID: {db_id}")
    print(f"   Title: {title}")
    print(f"   Slug: {slug}")
    print(f"   Stored WordPress ID: {stored_wp_id}")

    cursor.close()

except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

# Search WordPress by slug
print(f"\n🔍 Searching WordPress for post with slug: {slug}")
print("-"*80)

auth = (WORDPRESS_USER, WORDPRESS_PASSWORD)

try:
    # Search by slug
    response = requests.get(
        f"{WP_API}/posts",
        auth=auth,
        params={'slug': slug, 'per_page': 100},
        timeout=10
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        print(f"   Trying without auth...")

        response = requests.get(
            f"{WP_API}/posts",
            params={'slug': slug, 'per_page': 100},
            timeout=10
        )

    posts = response.json() if isinstance(response.json(), list) else [response.json()]

    if not posts or (isinstance(posts, list) and len(posts) == 0):
        print(f"❌ No posts found with slug: {slug}")

        # Try searching by title
        print(f"\nTrying to search by keywords in title...")
        response = requests.get(
            f"{WP_API}/posts",
            auth=auth,
            params={'search': 'health fitness trends', 'per_page': 100},
            timeout=10
        )

        posts = response.json() if isinstance(response.json(), list) else [response.json()]

        if posts:
            print(f"Found {len(posts)} posts matching keywords:")
            for p in posts[:5]:
                print(f"  ID {p.get('id')}: {p.get('title', {}).get('rendered', 'N/A')[:50]}")
        else:
            print(f"❌ No posts found at all")
            sys.exit(1)
    else:
        print(f"✅ Found {len(posts)} post(s) with that slug:")

        actual_post = None
        if len(posts) == 1:
            actual_post = posts[0]
        elif isinstance(posts, list):
            # Get first post
            actual_post = posts[0]

        if actual_post:
            actual_wp_id = actual_post.get('id')
            actual_title = actual_post.get('title', {}).get('rendered', 'N/A')

            print(f"\n   ID: {actual_wp_id}")
            print(f"   Title: {actual_title[:60]}")
            print(f"   Status: {actual_post.get('status')}")
            print(f"   Link: {actual_post.get('link')}")
            print(f"   Modified: {actual_post.get('modified')}")

            # Check if IDs match
            if stored_wp_id and int(stored_wp_id) == int(actual_wp_id):
                print(f"\n✅ IDs MATCH! Stored ID {stored_wp_id} is correct.")
            else:
                print(f"\n⚠️  ID MISMATCH!")
                print(f"   Stored in DB: {stored_wp_id}")
                print(f"   Actual in WordPress: {actual_wp_id}")
                print(f"\n   Updating database with correct ID...")

                # Update database with correct ID
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE blog_posts SET wordpress_post_id = %s WHERE id = %s",
                        (actual_wp_id, db_id)
                    )
                    conn.commit()
                    print(f"   ✅ Database updated!")
                    print(f"      {db_id}: {stored_wp_id} → {actual_wp_id}")
                    cursor.close()
                except Exception as e:
                    print(f"   ❌ Failed to update: {e}")
                    sys.exit(1)

            # Now try to update the post with correct content
            print(f"\n📤 Attempting to update WordPress post {actual_wp_id}...")

            # Get fresh content from database
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT content FROM blog_posts WHERE id = %s", (db_id,))
            fresh_post = cursor.fetchone()
            cursor.close()

            if not fresh_post:
                print(f"❌ Could not reload post content from database")
                sys.exit(1)

            fresh_content = fresh_post['content']

            # Update WordPress
            update_response = requests.post(
                f"{WP_API}/posts/{actual_wp_id}",
                auth=auth,
                headers={'Content-Type': 'application/json'},
                json={'content': fresh_content},
                timeout=10
            )

            if update_response.status_code in [200, 201]:
                print(f"✅ POST UPDATED SUCCESSFULLY!")
                updated = update_response.json()
                print(f"   Content length: {len(updated.get('content', {}).get('rendered', ''))} chars")
                print(f"   Modified: {updated.get('modified')}")
            else:
                print(f"❌ Update failed: {update_response.status_code}")
                print(f"   {update_response.text[:300]}")
                sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

conn.close()
print("\n" + "="*80 + "\n")
