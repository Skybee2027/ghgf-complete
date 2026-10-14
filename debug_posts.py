#!/usr/bin/env python3
"""Debug script to find and inspect posts"""

import os
import requests
import base64
import json

wordpress_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com').rstrip('/')
wordpress_user = os.getenv('WORDPRESS_USER', '')
wordpress_password = os.getenv('WORDPRESS_PASSWORD', '')

# Setup auth
if wordpress_user and wordpress_password:
    credentials = base64.b64encode(f"{wordpress_user}:{wordpress_password}".encode()).decode()
    auth_header = f"Basic {credentials}"
else:
    print("ERROR: WordPress credentials not found")
    exit(1)

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Debug/1.0',
    'Authorization': auth_header
}

api_base = f"{wordpress_url}/wp-json/wp/v2"

# Search for posts with keywords
keywords = ["5 Complete Steps", "Top 7", "Health", "Fitness", "Dreams", "Innovations"]

print("="*80)
print("WORDPRESS POST SEARCH - DEBUG")
print("="*80)

for keyword in keywords:
    print(f"\nSearching for: '{keyword}'")
    url = f"{api_base}/posts"
    params = {
        'search': keyword,
        'per_page': 20,
        'orderby': 'relevance'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        posts = response.json()

        print(f"  Found {len(posts)} posts:")
        for post in posts:
            title = post.get('title', {}).get('rendered', 'UNKNOWN')
            post_id = post.get('id', 'UNKNOWN')
            content = post.get('content', {}).get('rendered', '')
            word_count = len(content.split())

            print(f"\n    ID: {post_id}")
            print(f"    Title: {title[:80]}")
            print(f"    Word Count: {word_count}")

    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*80)
print("TARGET POST TITLES TO FIND:")
print("="*80)
targets = [
    "5 Complete Steps to Achieve Your Health and Fitness Dreams",
    "Top 7 Health and Fitness Innovations to Watch in 2026"
]

for target in targets:
    print(f"\nSearching for EXACT: '{target}'")
    url = f"{api_base}/posts"
    params = {
        'search': target,
        'per_page': 20
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        posts = response.json()

        found = False
        for post in posts:
            title = post.get('title', {}).get('rendered', '')
            if title == target:
                print(f"  ✓ FOUND EXACT MATCH!")
                print(f"    ID: {post.get('id')}")
                print(f"    Word Count: {len(post.get('content', {}).get('rendered', '').split())}")
                found = True
                break

        if not found:
            print(f"  ✗ NO EXACT MATCH FOUND")
            print(f"    But search returned {len(posts)} close matches:")
            for post in posts[:3]:
                title = post.get('title', {}).get('rendered', '')
                print(f"      - {title[:70]}")

    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*80)
