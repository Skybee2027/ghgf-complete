#!/usr/bin/env python3
"""
POST QUALITY FIX - PHASE 3
Adds social media links and navigation links
Run via: python3 scripts/fix_post_quality_phase3.py
"""

import os
import mysql.connector
import re
import sys

# Database config from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ghgf_blogging')

print("\n" + "="*80)
print("🔧 POST QUALITY REMEDIATION - PHASE 3")
print("="*80)
print(f"\nDatabase: {DB_HOST}/{DB_NAME}")

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
print("\n📖 Finding post: 'Health and Fitness Trends 2026'...")

try:
    cursor.execute("SELECT * FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1")
    post = cursor.fetchone()

    if not post:
        print("❌ Post not found")
        sys.exit(1)

    print(f"✅ Found post: {post['title']}")

    post_id = post['id']
    original_content = post['content']

except Exception as e:
    print(f"❌ Error finding post: {e}")
    sys.exit(1)

fixed_content = original_content

# FIX #8: Add social media sharing links
print("\n" + "-"*80)
print("FIX #8: ADD SOCIAL MEDIA LINKS")
print("-"*80)

social_links_section = """---

## Share This Article

Help others discover these fitness trends! Share this guide with your community:

- [Share on Facebook](https://www.facebook.com/sharer/sharer.php?u=https://greathealthgreatfitness.com/index.php/2026/10/14/complete-guide-to-health-and-fitness-trends-to-watch-in-2026/)
- [Share on Twitter](https://twitter.com/intent/tweet?text=Check%20out%20this%20complete%20guide%20to%20health%20and%20fitness%20trends%20for%202026&url=https://greathealthgreatfitness.com/index.php/2026/10/14/complete-guide-to-health-and-fitness-trends-to-watch-in-2026/)
- [Share on LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https://greathealthgreatfitness.com/index.php/2026/10/14/complete-guide-to-health-and-fitness-trends-to-watch-in-2026/)
- [Share via Email](mailto:?subject=Check%20out:%20Complete%20Guide%20to%20Health%20and%20Fitness%20Trends&body=I%20found%20this%20helpful%20fitness%20guide:%20https://greathealthgreatfitness.com/index.php/2026/10/14/complete-guide-to-health-and-fitness-trends-to-watch-in-2026/)

---"""

if "Share" not in fixed_content and "social" not in fixed_content.lower():
    # Add before sources
    if "## Sources" in fixed_content:
        fixed_content = fixed_content.replace("## Sources", social_links_section + "\n\n## Sources")
    else:
        fixed_content = fixed_content.rstrip() + "\n\n" + social_links_section
    print("✅ Social media links added")
else:
    print("ℹ️  Social sharing section already present")

# FIX #9: Add related articles navigation
print("\n" + "-"*80)
print("FIX #9: ADD RELATED ARTICLES NAVIGATION")
print("-"*80)

related_articles_section = """---

## Related Reading

Deepen your fitness knowledge with these complementary guides:

- [Complete Guide to Home Workouts for Beginners](https://greathealthgreatfitness.com/home-workout-guide)
- [Nutrition Fundamentals for Fitness Success](https://greathealthgreatfitness.com/nutrition-fitness-guide)
- [Mental Health and Fitness: The Mind-Body Connection](https://greathealthgreatfitness.com/mental-health-fitness)
- [Recovery Strategies for Peak Performance](https://greathealthgreatfitness.com/recovery-guide)

---"""

if "Related" not in fixed_content and "similar" not in fixed_content.lower():
    # Add after social section
    if "Share This Article" in fixed_content:
        fixed_content = fixed_content.replace("Share This Article", "Share This Article\n\n---\n\n## Related Reading\n\nDeepen your fitness knowledge with these complementary guides:\n\n- [Complete Guide to Home Workouts for Beginners](https://greathealthgreatfitness.com/home-workout-guide)\n- [Nutrition Fundamentals for Fitness Success](https://greathealthgreatfitness.com/nutrition-fitness-guide)\n- [Mental Health and Fitness: The Mind-Body Connection](https://greathealthgreatfitness.com/mental-health-fitness)\n- [Recovery Strategies for Peak Performance](https://greathealthgreatfitness.com/recovery-guide)")
    else:
        fixed_content = fixed_content.rstrip() + "\n\n" + related_articles_section
    print("✅ Related articles section added")
else:
    print("ℹ️  Related articles section already present")

# Update the post
print("\n" + "-"*80)
print("💾 SAVING CHANGES")
print("-"*80)

try:
    update_query = """
        UPDATE blog_posts
        SET content = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (fixed_content, post_id))
    conn.commit()
    print(f"✅ Post updated successfully (ID: {post_id})")

except Exception as e:
    conn.rollback()
    print(f"❌ Error updating post: {e}")
    sys.exit(1)

# Verify changes
print("\n" + "-"*80)
print("✅ VERIFICATION")
print("-"*80)

try:
    cursor.execute("SELECT content FROM blog_posts WHERE id = %s", (post_id,))
    verified = cursor.fetchone()
    verified_content = verified['content']

    social_present = "Share on Facebook" in verified_content or "social" in verified_content.lower()
    related_present = "Related Reading" in verified_content or "related" in verified_content.lower()

    print(f"Social media links present: {'✅' if social_present else '❌'}")
    print(f"Related articles section present: {'✅' if related_present else '❌'}")

    if social_present and related_present:
        print(f"\n✅ Phase 3 Complete!")
    else:
        print(f"\n⚠️  Some items may be incomplete")

except Exception as e:
    print(f"⚠️  Could not verify: {e}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ PHASE 3 FIXES APPLIED")
print("="*80)
print("\nNext Steps:")
print("1. Check the post on your website")
print("2. Verify social media and related article links are present")
print("3. Then run: python3 scripts/fix_post_quality_phase4.py")
print("\n")
