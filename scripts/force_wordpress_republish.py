#!/usr/bin/env python3
"""
FORCE WORDPRESS REPUBLISH
Marks post as draft then back to published to force refresh
"""

import os
import sys
import requests
import mysql.connector
import time

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ghgf_blogging')

WORDPRESS_URL = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com')
WORDPRESS_USER = os.getenv('WORDPRESS_USER', 'api_user')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', '')

WP_API = f"{WORDPRESS_URL}/wp-json/wp/v2"

print("\n" + "="*80)
print("🔄 FORCE WORDPRESS REPUBLISH")
print("="*80)

auth = (WORDPRESS_USER, WORDPRESS_PASSWORD)
headers = {'Content-Type': 'application/json'}

try:
    # Get post from database
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

    wp_id = post['wordpress_post_id']
    content = post['content']
    title = post['title']

    print(f"\n📋 Post: {title}")
    print(f"   WordPress ID: {wp_id}")

    cursor.close()
    conn.close()

    # Step 1: Set to draft
    print(f"\n1️⃣  Setting post to DRAFT...")
    draft_response = requests.post(
        f"{WP_API}/posts/{wp_id}",
        auth=auth,
        headers=headers,
        json={'status': 'draft'},
        timeout=10
    )

    if draft_response.status_code not in [200, 201]:
        print(f"❌ Failed to set draft: {draft_response.status_code}")
        print(f"   {draft_response.text[:300]}")
        sys.exit(1)

    print(f"   ✅ Post set to draft")
    time.sleep(2)

    # Step 2: Update content while in draft
    print(f"\n2️⃣  Updating content...")
    content_response = requests.post(
        f"{WP_API}/posts/{wp_id}",
        auth=auth,
        headers=headers,
        json={'content': content},
        timeout=10
    )

    if content_response.status_code not in [200, 201]:
        print(f"❌ Failed to update content: {content_response.status_code}")
        print(f"   {content_response.text[:300]}")
        sys.exit(1)

    print(f"   ✅ Content updated")
    time.sleep(2)

    # Step 3: Publish (set back to published)
    print(f"\n3️⃣  Publishing post...")
    pub_response = requests.post(
        f"{WP_API}/posts/{wp_id}",
        auth=auth,
        headers=headers,
        json={'status': 'publish'},
        timeout=10
    )

    if pub_response.status_code not in [200, 201]:
        print(f"❌ Failed to publish: {pub_response.status_code}")
        print(f"   {pub_response.text[:300]}")
        sys.exit(1)

    updated = pub_response.json()
    print(f"   ✅ Post published!")
    print(f"   Status: {updated.get('status')}")
    print(f"   Modified: {updated.get('modified')}")
    print(f"   Link: {updated.get('link')}")

    # Verify
    print(f"\n✅ VERIFICATION")
    print("-"*80)

    time.sleep(3)

    verify = requests.get(
        f"{WP_API}/posts/{wp_id}",
        auth=auth,
        headers=headers,
        timeout=10
    ).json()

    wp_content = verify.get('content', {}).get('rendered', '')

    checks = {
        'No code markers (```)': '```' not in wp_content,
        'No XYZ Probiotic': 'XYZ Probiotic' not in wp_content,
        'No template labels': '**Hook:**' not in wp_content and '**Pro tip:**' not in wp_content,
        'Has FAQ': 'FAQ' in wp_content,
        'Has eBook': 'eBook' in wp_content or 'Fitness Fundamentals' in wp_content,
        'Has sources': 'Sources' in wp_content,
        'Has social sharing': 'Share' in wp_content,
        'Has author bio': 'About the Author' in wp_content,
    }

    all_passed = True
    for check, result in checks.items():
        status = '✅' if result else '❌'
        print(f"  {status} {check}")
        if not result:
            all_passed = False

    if all_passed:
        print(f"\n🎉 ALL CHECKS PASSED! Post is fixed and published!")
    else:
        print(f"\n⚠️  Some checks still failing - may be caching issue")
        print(f"   Try hard refreshing the page (Ctrl+F5)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80 + "\n")
