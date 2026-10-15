#!/usr/bin/env python3
"""
POST QUALITY FIX - PHASE 1
Fixes code artifacts, placeholders, template labels, and sources
Run via: python3 scripts/fix_post_quality_phase1.py
"""

import os
import mysql.connector
import re
import sys
from datetime import datetime

# Database config from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ghgf_blogging')

print("\n" + "="*80)
print("🔧 POST QUALITY REMEDIATION - PHASE 1")
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
    # Multiple search strategies
    queries = [
        ("blog_posts WHERE title LIKE '%Health%Fitness%Trends%'", "SELECT * FROM blog_posts WHERE title LIKE '%Health%Fitness%Trends%' LIMIT 1"),
        ("blog_posts WHERE slug LIKE '%health-fitness-trends%'", "SELECT * FROM blog_posts WHERE slug LIKE '%health-fitness-trends%' LIMIT 1"),
        ("blog_posts ORDER BY created_at DESC", "SELECT * FROM blog_posts ORDER BY created_at DESC LIMIT 1"),
    ]
    
    post = None
    for desc, query in queries:
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            post = result
            print(f"✅ Found post: {post['title']}")
            break
    
    if not post:
        print("❌ Post not found")
        sys.exit(1)
        
    post_id = post['id']
    original_content = post['content']
    
except Exception as e:
    print(f"❌ Error finding post: {e}")
    sys.exit(1)

# FIX #1: Remove code artifacts
print("\n" + "-"*80)
print("FIX #1: REMOVE CODE ARTIFACTS")
print("-"*80)

code_fences = len(re.findall(r'```', original_content))
html_tags = len(re.findall(r'<meta[^>]+>', original_content))

print(f"Found code artifacts:")
print(f"  - Backtick markers (```): {code_fences}")
print(f"  - HTML meta tags: {html_tags}")

fixed_content = original_content

# Remove code fences
fixed_content = re.sub(r'```html', '', fixed_content)
fixed_content = re.sub(r'```', '', fixed_content)

# Remove HTML meta tags
fixed_content = re.sub(r'<meta[^>]+>', '', fixed_content)

# Clean up extra whitespace
fixed_content = re.sub(r'\n{3,}', '\n\n', fixed_content)

print(f"✅ Removed {code_fences + html_tags} code artifacts")

# FIX #2: Replace placeholder products
print("\n" + "-"*80)
print("FIX #2: REPLACE PLACEHOLDER PRODUCTS")
print("-"*80)

# Replace XYZ Probiotic
if "XYZ Probiotic" in fixed_content:
    print("Found: 'XYZ Probiotic'")
    fixed_content = fixed_content.replace("XYZ Probiotic", "Garden of Life Raw Probiotics Women")
    print("✅ Replaced with: 'Garden of Life Raw Probiotics Women'")
else:
    print("ℹ️  'XYZ Probiotic' not found")

# FIX #3: Remove template labels
print("\n" + "-"*80)
print("FIX #3: REMOVE TEMPLATE LABELS")
print("-"*80)

template_labels = [
    r'\*\*Hook:\*\*',
    r'\*\*Pro tip:\*\*',
    r'\(\d+% Into the Post\)',
    r'\(0% Into the Post\)',
    r'\(25% Into the Post\)',
    r'\(50% Into the Post\)',
    r'\(75% Into the Post\)',
    r'\(100% Into the Post\)',
]

removed_labels = 0
for label_pattern in template_labels:
    matches = len(re.findall(label_pattern, fixed_content))
    if matches > 0:
        fixed_content = re.sub(label_pattern, '', fixed_content)
        removed_labels += matches
        print(f"✅ Removed {matches} occurrences of: {label_pattern}")

print(f"Total labels removed: {removed_labels}")

# FIX #4: Add sources for health claims (preparatory)
print("\n" + "-"*80)
print("FIX #4: MARK HEALTH CLAIMS FOR SOURCING")
print("-"*80)

# We don't fully implement this here - just mark that it needs to be done
health_claims = [
    "30%",
    "18%",
    "40%",
    "meta-analysis",
    "Harvard Health",
    "ACSM"
]

marked_claims = 0
for claim in health_claims:
    if claim.lower() in fixed_content.lower():
        marked_claims += 1

print(f"Found {marked_claims} health claims that need sourcing")
print("ℹ️  Health claims will be sourced in Phase 2")

# Update the post
print("\n" + "-"*80)
print("💾 SAVING CHANGES")
print("-"*80)

try:
    update_query = """
        UPDATE blog_posts 
        SET content = %s,
            updated_at = NOW()
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
    
    remaining_artifacts = len(re.findall(r'```', verified_content)) + len(re.findall(r'<meta[^>]+>', verified_content))
    
    print(f"Original size: {len(original_content)} chars")
    print(f"Fixed size: {len(fixed_content)} chars")
    print(f"Verified: {len(verified_content)} chars")
    print(f"Remaining artifacts: {remaining_artifacts}")
    print(f"\n✅ Phase 1 Complete!" if remaining_artifacts == 0 else "⚠️  Some artifacts may remain")
    
except Exception as e:
    print(f"⚠️  Could not verify: {e}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ PHASE 1 FIXES APPLIED")
print("="*80)
print("\nNext Steps:")
print("1. Check the post on your website")
print("2. Verify all fixes are correct")
print("3. Then run: python3 scripts/fix_post_quality_phase2.py")
print("\n")

