#!/usr/bin/env python3
"""
DIRECT WORDPRESS POST UPDATE
Uses simple requests.auth instead of Base64 headers
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

WP_API_BASE = f"{WORDPRESS_URL}/wp-json/wp/v2"

print("\n" + "="*80)
print("📝 DIRECT WORDPRESS POST UPDATE")
print("="*80)

# Get database content
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1")
    post = cursor.fetchone()

    if not post:
        print("❌ Post not found in database")
        sys.exit(1)

    print(f"\n✅ Found post in database:")
    print(f"   Title: {post['title']}")
    print(f"   WordPress ID: {post.get('wordpress_post_id')}")
    print(f"   Content length: {len(post['content'])} chars\n")

    content = post['content']
    title = post['title']
    wp_post_id = post.get('wordpress_post_id')

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

# Update WordPress
print(f"📤 Updating WordPress post ID {wp_post_id}...")
print("-"*80)

auth = (WORDPRESS_USER, WORDPRESS_PASSWORD)
headers = {'Content-Type': 'application/json'}

try:
    # First, fetch the current post
    print(f"Fetching current post from WordPress...")
    get_response = requests.get(
        f"{WP_API_BASE}/posts/{wp_post_id}",
        auth=auth,
        headers=headers,
        timeout=10
    )

    if get_response.status_code != 200:
        print(f"❌ Failed to fetch post: {get_response.status_code}")
        print(f"   Response: {get_response.text[:500]}")
        sys.exit(1)

    wp_post = get_response.json()
    print(f"✅ Current post retrieved")
    print(f"   Status: {wp_post.get('status')}")
    print(f"   Current content length: {len(wp_post.get('content', {}).get('rendered', ''))} chars")

    # Update with new content
    print(f"\nSending updated content...")
    update_response = requests.post(
        f"{WP_API_BASE}/posts/{wp_post_id}",
        auth=auth,
        headers=headers,
        json={'content': content},
        timeout=10
    )

    if update_response.status_code not in [200, 201]:
        print(f"❌ Update failed: {update_response.status_code}")
        print(f"   Response: {update_response.text[:500]}")
        sys.exit(1)

    print(f"✅ POST UPDATED!")
    updated = update_response.json()
    print(f"   New content length: {len(updated.get('content', {}).get('rendered', ''))} chars")
    print(f"   Modified: {updated.get('modified')}")
    print(f"   Link: {updated.get('link')}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Verify
print(f"\n✅ VERIFICATION")
print("-"*80)

try:
    verify = requests.get(
        f"{WP_API_BASE}/posts/{wp_post_id}",
        auth=auth,
        headers=headers,
        timeout=10
    ).json()

    content_now = verify.get('content', {}).get('rendered', '')

    checks = [
        ('No code markers', '```' not in content_now),
        ('No XYZ Probiotic', 'XYZ Probiotic' not in content_now),
        ('FAQ section', 'FAQ' in content_now),
        ('eBook link', 'eBook' in content_now),
        ('Sources section', 'Sources' in content_now),
        ('Social sharing', 'Share' in content_now),
        ('Author bio', 'About the Author' in content_now),
        ('Copyright', 'Copyright' in content_now),
    ]

    all_good = True
    for check_name, result in checks:
        status = '✅' if result else '❌'
        print(f"  {status} {check_name}")
        if not result:
            all_good = False

    if all_good:
        print(f"\n✅ ALL CHECKS PASSED!")
    else:
        print(f"\n⚠️  Some checks failed")

except Exception as e:
    print(f"⚠️  Verification error: {e}")

print("\n" + "="*80 + "\n")
