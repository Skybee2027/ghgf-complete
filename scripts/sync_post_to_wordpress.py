#!/usr/bin/env python3
"""
SYNC DATABASE TO WORDPRESS
Updates an existing WordPress post with content from the database
This runs after database fixes to publish changes to WordPress
"""

import os
import sys
import requests
import mysql.connector
import json
import base64
from datetime import datetime

# Configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_HOST, DB_USER, DB_NAME]):
    print("❌ CRITICAL: DB_HOST, DB_USER, and DB_NAME environment variables must be set")
    sys.exit(1)

WORDPRESS_URL = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
WORDPRESS_USER = os.getenv('WORDPRESS_USER', 'api_user')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', '')

WP_API_BASE = f"{WORDPRESS_URL}/wp-json/wp/v2"

print("\n" + "="*80)
print("🔄 SYNC DATABASE CHANGES TO WORDPRESS")
print("="*80)
print(f"\nConfiguration:")
print(f"  Database: {DB_HOST}/{DB_NAME}")
print(f"  WordPress: {WORDPRESS_URL}")
print(f"  API Base: {WP_API_BASE}\n")

# Connect to database
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False
    )
    cursor = conn.cursor(dictionary=True)
    print("✅ Database connected")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Find the post
print("\n📖 Finding post in database...")
try:
    cursor.execute("SELECT * FROM blog_posts WHERE title LIKE %s LIMIT 1", ('%Health%Fitness%Trends%',))
    post = cursor.fetchone()

    if not post:
        print("❌ Post not found in database")
        sys.exit(1)

    print(f"✅ Found: {post['title']}")
    print(f"   ID: {post['id']}")
    print(f"   WordPress Post ID: {post.get('wordpress_post_id', 'Not set')}")

    post_id = post['id']
    wp_post_id = post.get('wordpress_post_id')

    if not wp_post_id:
        print("❌ No WordPress Post ID - post has not been published yet")
        sys.exit(1)

    content = post['content']
    title = post['title']
    meta_desc = post.get('meta_description', '')

except Exception as e:
    print(f"❌ Error finding post: {e}")
    sys.exit(1)

# Prepare WordPress credentials
print("\n🔐 Preparing WordPress authentication...")
auth_string = f"{WORDPRESS_USER}:{WORDPRESS_PASSWORD}"
auth_bytes = auth_string.encode('utf-8')
auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

if not WORDPRESS_PASSWORD:
    print("⚠️  WARNING: WORDPRESS_PASSWORD is empty!")
    print("   WordPress update will likely fail without credentials")

# Update post via WordPress REST API
print("\n📤 Updating post in WordPress...")
print("-"*80)

try:
    wp_endpoint = f"{WP_API_BASE}/posts/{wp_post_id}"

    update_data = {
        'title': title,
        'content': content,
        'meta': {
            'meta_description': meta_desc
        }
    }

    print(f"   Endpoint: {wp_endpoint}")
    print(f"   Title: {title[:50]}...")
    print(f"   Content length: {len(content)} characters")

    response = requests.post(
        wp_endpoint,
        headers=headers,
        json=update_data,
        timeout=30
    )

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ POST UPDATED IN WORDPRESS!")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Modified: {result.get('modified', 'N/A')}")
        print(f"   URL: {result.get('link', 'N/A')}")

    elif response.status_code == 401:
        print(f"❌ ERROR: Authentication failed (401)")
        print(f"   Check WORDPRESS_USER and WORDPRESS_PASSWORD")
        print(f"   Response: {response.text[:200]}")
        sys.exit(1)

    elif response.status_code == 404:
        print(f"❌ ERROR: WordPress post not found (404)")
        print(f"   Post ID {wp_post_id} may not exist in WordPress")
        sys.exit(1)

    else:
        print(f"❌ ERROR: Failed to update post (Status: {response.status_code})")
        print(f"   Response: {response.text[:500]}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error updating post: {e}")
    sys.exit(1)

# Verify update
print("\n✅ VERIFICATION")
print("-"*80)

try:
    # Check WordPress post
    get_response = requests.get(
        f"{WP_API_BASE}/posts/{wp_post_id}",
        headers=headers,
        timeout=10
    )

    if get_response.status_code == 200:
        wp_post = get_response.json()
        wp_content = wp_post.get('content', {}).get('rendered', '')

        # Check for specific fixes
        has_faq = 'FAQ' in wp_content and 'Q:' in wp_content
        has_ebook = 'eBook' in wp_content or 'Fitness Fundamentals' in wp_content
        has_sources = 'Sources' in wp_content or 'Harvard' in wp_content
        has_social = 'Share' in wp_content and ('Facebook' in wp_content or 'Twitter' in wp_content)
        has_no_placeholders = 'XYZ Probiotic' not in wp_content
        has_no_template_labels = '**Hook:**' not in wp_content and '**Pro tip:**' not in wp_content

        print(f"WordPress post title: {wp_post.get('title', {}).get('rendered', 'N/A')[:50]}")
        print(f"WordPress post status: {wp_post.get('status', 'N/A')}")
        print(f"Last modified: {wp_post.get('modified', 'N/A')}\n")

        print(f"Content checks:")
        print(f"  No code artifacts (```, **Hook:**, **Pro tip:**): {'✅' if has_no_placeholders and has_no_template_labels else '❌'}")
        print(f"  FAQ section: {'✅' if has_faq else '❌'}")
        print(f"  eBook link: {'✅' if has_ebook else '❌'}")
        print(f"  Sources section: {'✅' if has_sources else '❌'}")
        print(f"  Social sharing links: {'✅' if has_social else '❌'}")

        all_fixed = has_faq and has_ebook and has_sources and has_social and has_no_placeholders and has_no_template_labels

        if all_fixed:
            print(f"\n✅ ALL FIXES VERIFIED IN WORDPRESS!")
        else:
            print(f"\n⚠️  Some fixes may not be visible yet (WordPress caching?)")

    else:
        print(f"⚠️  Could not verify WordPress post (status: {get_response.status_code})")

except Exception as e:
    print(f"⚠️  Could not verify: {e}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ SYNC COMPLETE")
print("="*80)
print("\nNext Steps:")
print("1. Wait 30 seconds for cache to clear")
print("2. Visit the post on your website")
print("3. Refresh the page (Ctrl+F5 to hard refresh)")
print("4. Verify all fixes are visible")
print("\n")

sys.exit(0)
