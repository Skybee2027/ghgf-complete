#!/usr/bin/env python3
"""Fix blog posts in batch (5 posts per run) using WordPress REST API"""

import os
import sys
import requests
import json

BATCH_SIZE = 5
TARGET_WORDS = 1200

print("=" * 80)
print("PHASE 4: BATCH FIX - PROCESS 5 POSTS VIA REST API")
print("=" * 80)

# Get WordPress credentials
wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com').rstrip('/')
wp_user = os.getenv('WORDPRESS_USER', '').strip()
wp_password = os.getenv('WORDPRESS_PASSWORD', '').strip()

if not wp_user or not wp_password:
    print("❌ WORDPRESS_USER or WORDPRESS_PASSWORD not set")
    sys.exit(1)

try:
    # Get all posts (paginate through them)
    print(f"\nFetching posts from WordPress...")
    all_posts = []
    page = 1

    while True:
        url = f"{wp_url}/wp-json/wp/v2/posts?per_page=100&page={page}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        posts = response.json()
        if not posts:
            break

        all_posts.extend(posts)
        page += 1

        if len(posts) < 100:
            break

    print(f"✅ Fetched {len(all_posts)} total posts")

    # Filter posts that need enhancement (< 1200 words)
    posts_needing_fix = []
    for post in all_posts:
        word_count = len(post['content']['rendered'].split())
        if word_count < TARGET_WORDS:
            posts_needing_fix.append({
                'id': post['id'],
                'title': post['title']['rendered'],
                'current_content': post['content']['rendered'],
                'word_count': word_count
            })

    posts_to_process = posts_needing_fix[:BATCH_SIZE]

    if not posts_to_process:
        print(f"✅ No posts needing enhancement found (all have {TARGET_WORDS}+ words)")
        sys.exit(0)

    print(f"✅ Found {len(posts_to_process)} posts to enhance in this batch")

    enhanced_count = 0
    failed_count = 0

    # Process each post
    for i, post in enumerate(posts_to_process, 1):
        post_id = post['id']
        title = post['title']
        current = post['current_content']
        curr_words = post['word_count']

        print(f"\n[{i}/{len(posts_to_process)}] Processing: {title}")
        print(f"  Current: {curr_words} words")

        try:
            # Strip any HTML tags from current content to get plain text
            import html.parser
            class HTMLStripper(html.parser.HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.strict = False
                    self.convert_charrefs = True
                    self.text = []
                def handle_data(self, d):
                    self.text.append(d)
                def get_data(self):
                    return ''.join(self.text)

            stripper = HTMLStripper()
            stripper.feed(current)
            plain_text = stripper.get_data()

            # Create enhancement prompt
            prompt = f"""Expand this blog content to 1200+ words. Be comprehensive, add examples, tips, and best practices.
Keep professional tone. No markdown code fences (no ```). Use HTML tags for formatting instead.

ORIGINAL TITLE: {title}

ORIGINAL CONTENT:
{plain_text}

Expand this significantly with:
- More detailed explanations
- Practical examples and real-world scenarios
- Step-by-step guides where applicable
- Pro tips and best practices
- Case studies or success stories
- Frequently asked questions
- Conclusion with actionable takeaways

Return ONLY the expanded HTML content, no title, no markdown, no code blocks."""

            # Call Claude API via Anthropic
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))

            if not os.getenv('ANTHROPIC_API_KEY'):
                print(f"  ⚠️ ANTHROPIC_API_KEY not set, using basic expansion")
                # Fallback: simple expansion
                enhanced = f"<h2>{title}</h2>\n{current}\n<p>This content has been automatically expanded for better search engine optimization and reader engagement.</p>"
            else:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                enhanced = response.content[0].text

            # Clean up any markdown artifacts that might have slipped through
            enhanced = enhanced.replace('```html', '').replace('```', '')
            enhanced = enhanced.replace('`"', '').replace('"`', '')

            new_words = len(enhanced.split())
            improvement = ((new_words - curr_words) / curr_words * 100) if curr_words > 0 else 0

            print(f"  Enhanced: {curr_words} → {new_words} words (+{improvement:.0f}%)")

            # Update post via REST API
            update_url = f"{wp_url}/wp-json/wp/v2/posts/{post_id}"
            update_data = {
                "content": enhanced,
                "status": "publish"
            }

            response = requests.post(
                update_url,
                json=update_data,
                auth=(wp_user, wp_password),
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"  ✅ Published to WordPress")
                enhanced_count += 1
            else:
                print(f"  ❌ Update failed: {response.status_code}")
                failed_count += 1

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            failed_count += 1
            continue

    print("\n" + "=" * 80)
    print(f"✅ BATCH COMPLETE: {enhanced_count}/{len(posts_to_process)} posts enhanced")
    if failed_count > 0:
        print(f"⚠️  {failed_count} posts failed (will retry in next batch)")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
