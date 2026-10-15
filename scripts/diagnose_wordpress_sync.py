#!/usr/bin/env python3
"""Diagnose why WordPress sync is not working"""

import os
import sys
import mysql.connector
import requests
import base64

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ghgf_blogging')

WORDPRESS_URL = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
WORDPRESS_USER = os.getenv('WORDPRESS_USER', 'api_user')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', '')

print("\n" + "="*80)
print("🔍 WORDPRESS SYNC DIAGNOSTIC")
print("="*80)

# 1. Check database
print("\n1️⃣  CHECKING DATABASE")
print("-"*80)

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title, wordpress_post_id, status, ready_for_wordpress, final_qa_passed FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1")
    post = cursor.fetchone()

    if post:
        print(f"Post found in database:")
        print(f"  DB ID: {post['id']}")
        print(f"  Title: {post['title']}")
        print(f"  WordPress Post ID: {post['wordpress_post_id']}")
        print(f"  Status: {post['status']}")
        print(f"  Ready for WordPress: {post['ready_for_wordpress']}")
        print(f"  Final QA Passed: {post['final_qa_passed']}")

        wp_post_id = post['wordpress_post_id']
    else:
        print("❌ Post not found in database!")
        sys.exit(1)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

# 2. Check WordPress REST API
print("\n2️⃣  CHECKING WORDPRESS REST API")
print("-"*80)

WP_API = f"{WORDPRESS_URL}/wp-json/wp/v2"

if not WORDPRESS_PASSWORD:
    print("⚠️  WORDPRESS_PASSWORD is empty!")
    print("   Cannot authenticate with WordPress")

    # Try unauthenticated
    try:
        print(f"\nTrying unauthenticated request...")
        response = requests.get(f"{WP_API}/posts/{wp_post_id}", timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            post_data = response.json()
            print(f"  ✅ Found post in WordPress: {post_data.get('title', {}).get('rendered', 'N/A')[:50]}")
            print(f"     Status: {post_data.get('status')}")
            print(f"     Link: {post_data.get('link')}")
    except Exception as e:
        print(f"  Error: {e}")
else:
    # Authenticate
    auth_string = f"{WORDPRESS_USER}:{WORDPRESS_PASSWORD}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {auth_b64}'}

    try:
        print(f"WordPress Post ID: {wp_post_id}")
        print(f"API Endpoint: {WP_API}/posts/{wp_post_id}")

        response = requests.get(f"{WP_API}/posts/{wp_post_id}", headers=headers, timeout=10)

        print(f"\nResponse Status: {response.status_code}")

        if response.status_code == 200:
            post_data = response.json()
            print(f"✅ Post found in WordPress!")
            print(f"  Title: {post_data.get('title', {}).get('rendered', 'N/A')[:50]}")
            print(f"  Status: {post_data.get('status')}")
            print(f"  Link: {post_data.get('link')}")
            print(f"  Modified: {post_data.get('modified')}")

            content = post_data.get('content', {}).get('rendered', '')
            print(f"  Content length: {len(content)} chars")

            # Check for fixes
            print(f"\n  Content checks:")
            print(f"    Has code markers: {'YES ❌' if '```' in content else 'NO ✅'}")
            print(f"    Has XYZ Probiotic: {'YES ❌' if 'XYZ Probiotic' in content else 'NO ✅'}")
            print(f"    Has FAQ: {'YES ✅' if 'FAQ' in content else 'NO ❌'}")
            print(f"    Has eBook: {'YES ✅' if 'eBook' in content or 'Fitness Fundamentals' in content else 'NO ❌'}")
            print(f"    Has sources: {'YES ✅' if 'Sources' in content else 'NO ❌'}")

        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"   Check WORDPRESS_USER and WORDPRESS_PASSWORD")
        elif response.status_code == 404:
            print(f"❌ Post not found in WordPress (404)")
            print(f"   WordPress Post ID {wp_post_id} does not exist")
            print(f"   This might be the problem - the stored ID doesn't match!")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error: {e}")

# 3. Try to find the post by slug
print("\n3️⃣  SEARCHING FOR POST BY SLUG IN WORDPRESS")
print("-"*80)

try:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT slug FROM blog_posts WHERE id = (SELECT id FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1)")
    result = cursor.fetchone()
    slug = result['slug'] if result else 'complete-guide-to-health-and-fitness-trends-to-watch-in-2026'
    cursor.close()

    print(f"Post slug: {slug}")

    # Try searching by slug
    search_url = f"{WP_API}/posts?slug={slug}"
    print(f"Searching: {search_url}")

    response = requests.get(search_url, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        results = response.json()
        if results:
            found_post = results[0]
            print(f"✅ Found post by slug!")
            print(f"  WordPress ID: {found_post.get('id')}")
            print(f"  Title: {found_post.get('title', {}).get('rendered', 'N/A')[:50]}")
            print(f"  Status: {found_post.get('status')}")

            if int(found_post.get('id')) != int(wp_post_id):
                print(f"\n⚠️  MISMATCH!")
                print(f"  Database has ID: {wp_post_id}")
                print(f"  WordPress actual ID: {found_post.get('id')}")
                print(f"  You may need to update the database with the correct ID!")
        else:
            print(f"❌ No posts found with slug: {slug}")

except Exception as e:
    print(f"Error searching by slug: {e}")

print("\n" + "="*80 + "\n")
