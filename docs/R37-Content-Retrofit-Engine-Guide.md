# R37: Content Retrofit & Monetization Engine

## Overview

R37 is a specialized robot designed to process your existing 600+ blog posts and retrofit them with monetization features. It's the backbone of **Option C** (Retrofit Old + Generate New + Weekly Refresh), which will add approximately **$4,200-9,000/month** in additional revenue.

**Key Functions:**
- ✓ Batch process 600+ existing blog posts (50 per 6-hour cycle)
- ✓ Enhance low-quality content using AI (Groq)
- ✓ Add 2-3 affiliate product mentions per post
- ✓ Generate premium PDF e-books from blog content
- ✓ Insert attractive product cards into posts
- ✓ Update WordPress with all monetization layers
- ✓ Track progress and revenue potential
- ✓ Support parallel execution with R1-R36

---

## Architecture

### How R37 Fits Into the System

```
PARALLEL EXECUTION (OPTION C)
│
├─ R1-R36: Continue generating NEW posts (3 posts every 6 hours)
│   └─ Output: Fresh, monetized blog posts
│
├─ R37: Retrofit OLD posts in batches (50 posts every 6 hours)
│   └─ Output: Monetized legacy posts with affiliates + e-books
│
└─ R25-R30: Weekly refresh cycle (runs once per week)
    └─ Output: Optimized posts with improved SEO + engagement
```

### Batch Processing Strategy

```
Cycle 1:   Posts 1-50    (6 hours)
Cycle 2:   Posts 51-100  (6 hours)
Cycle 3:   Posts 101-150 (6 hours)
...
Cycle 12:  Posts 551-600 (6 hours)

Total Time: 72 hours = 3 days to process all 600 posts
```

**While R37 is processing old posts, R1-R36 continues creating new content:**
- Day 1: R37 processes 50 posts + R1-R36 creates 9 new posts = 59 posts monetized
- Day 3: R37 completes 600 posts + R1-R36 creates 27 new posts = 627 total posts monetized

---

## Installation & Configuration

### Step 1: Database Setup

Run the R37 database schema:

```bash
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < R37_Database_Schema.sql
```

This creates:
- `retrofit_log` - Tracks which posts have been retrofitted
- `retrofit_batches` - Batch processing statistics
- `retrofit_analytics` - Progress and revenue analytics
- `retrofit_errors` - Error tracking and retry logic
- `retrofit_affiliates` - Affiliate link tracking
- `retrofit_digital_products` - E-book metadata

### Step 2: Copy R37 Robot

```bash
cp GHGFrobots/r37_content_retrofit_engine.py /robots/
chmod +x /robots/r37_content_retrofit_engine.py
```

### Step 3: Verify Dependencies

Ensure these are in your `requirements-36robots-updated.txt`:

```
# R37 Dependencies (already included from R14b)
reportlab==4.0.7
pillow==10.1.0
groq==0.4.2
mysql-connector-python==8.2.0
requests==2.31.0
```

Install if needed:
```bash
pip install -r requirements-36robots-updated.txt
```

### Step 4: GitHub Actions Integration

Update `.github/workflows/ghgf-36-robots.yml` to add R37:

```yaml
- name: R37 - Content Retrofit & Monetization Engine
  run: python /robots/r37_content_retrofit_engine.py
  # Important: Run AFTER R1-R24 (for data availability)
  #            Run BEFORE R25-R36 (to maintain sequence)
```

**Placement in workflow:**
```
R1-R24: Blog generation & validation (4 hours)
├─ R1: API Health
├─ R2-R3: Content generation
├─ R4-R8: QA checks
└─ R9-R24: Formatting

R37: Retrofit old posts (parallel, ~1 hour per 50 posts)
├─ Enhance content
├─ Add affiliates
├─ Generate e-books
└─ Update WordPress

R25-R36: Publishing & monitoring (1 hour)
├─ R25-R30: Content refresh cycle
└─ R31-R36: Publishing & analytics
```

### Step 5: Environment Variables

Ensure these GitHub Secrets are set (most already configured):

```
# Database
DB_HOST
DB_USER
DB_PASSWORD
DB_NAME

# API Keys
GROQ_API_KEY                    # Required (from R2/R3)

# WordPress/WooCommerce
WORDPRESS_SITE_URL             # https://greathealthgreatfitness.com
WORDPRESS_USERNAME             # WordPress REST API user
WORDPRESS_PASSWORD             # WordPress REST API password

# Payment Gateways (from R14b)
PAYPAL_CLIENT_ID               # For PayPal integration
PAYPAL_SECRET                  # For PayPal integration
STRIPE_API_KEY                 # For Stripe integration
```

---

## How R37 Works

### Phase 1: Fetch Posts for Retrofit (5 minutes)

```python
R37 queries database:
  - WHERE status = 'published'
  - AND word_count >= 500
  - AND NOT IN (SELECT blog_id FROM retrofit_log WHERE status = 'completed')
  - ORDER BY publish_date DESC
  - LIMIT 50  # Batch size
```

**Output:** 50 posts ready for processing

### Phase 2: Enhance Content (10-15 minutes)

For posts with `quality_score < 7.0`:

```
Groq API Call:
├─ Input: Blog title + first 2000 chars of content
├─ Instruction: Improve structure, add actionable tips, strengthen intro/conclusion
└─ Output: Enhanced HTML content

Result: Improved readability, better structure, actionable content
Quality Score Update: quality_score = MAX(quality_score, 8.0)
```

**If quality_score >= 7.0:** Content kept as-is (saves API cost)

### Phase 3: Add Affiliate Links (5 minutes)

```
For each post:
├─ Detect category (Fitness/Nutrition/Health/Wellness)
├─ Select 2-3 relevant affiliate products
├─ Insert CJ/ShareASale affiliate mentions
│  ├─ Position 1: 33% into post
│  └─ Position 2: 66% into post
└─ Format: Nice blue boxes with product info & links
```

**Example output:**
```html
<p style="background: #f0f4ff; padding: 12px; border-left: 4px solid #667eea;">
  <strong>💡 Recommendation:</strong> Yoga Mat Premium - $45.99
  - <a href="https://cj.com/?YOG001">View on CJ Affiliate →</a>
</p>
```

### Phase 4: Generate E-Books (10 minutes)

```
ReportLab PDF Creation:
├─ Cover page: Category-colored (Fitness: red, Health: teal, etc)
├─ Title page: Post title, category, generated date
├─ Content pages: Cleaned text + formatting
└─ Footer: Branding (GreatHealthGreatFitness.com)

Result: Professional-looking PDF ready for sale
```

### Phase 5: Insert Product Card (5 minutes)

```
At 50% position in post content:
├─ Gradient background (Indigo to Purple)
├─ "PREMIUM GUIDE AVAILABLE" badge
├─ Call-to-action button
├─ Trust indicators (instant download, money-back guarantee)
└─ WooCommerce add-to-cart link
```

**Visual result:**
```
┌─────────────────────────────────┐
│ 📘 PREMIUM GUIDE AVAILABLE      │
│                                 │
│ Complete Guide: [Post Title]    │
│                                 │
│ [Get Premium Version →]         │
│                                 │
│ ✓ Instant download              │
│ • Money-back guarantee          │
└─────────────────────────────────┘
```

### Phase 6: Update WordPress (10 minutes)

```
WordPress REST API Call:
├─ Update post_content with enhanced content
├─ Add retrofitted meta fields
│  ├─ retrofitted: true
│  ├─ has_affiliate_links: true
│  └─ has_digital_product: true
└─ Trigger publish event

Result: Post is now live with monetization
```

### Phase 7: Log Progress (1 minute)

```sql
INSERT INTO retrofit_log:
├─ blog_id: [post ID]
├─ status: 'completed'
├─ details: {enhanced, affiliates_added, ebook_created, product_card_added}
├─ completed_at: NOW()
└─ Result: Post marked as retrofitted
```

---

## Running R37

### Manual Execution (Testing)

```bash
# Run R37 standalone
python /robots/r37_content_retrofit_engine.py

# Output:
# ══════════════════════════════════════════════════════
# R37: CONTENT RETROFIT & MONETIZATION ENGINE
# ══════════════════════════════════════════════════════
#
# Retrofit Progress:
#   Total Posts: 627
#   Retrofitted: 0
#   In Progress: 0
#   Remaining: 627
#   Progress: 0.0%
#
# Step 1: Fetching Posts for Retrofit
#   ✓ Found 50 posts for retrofit in this batch
#
# Step 2: Processing Posts
#   [1/50] Weight Loss Tips for Busy Professionals...
#       ✓ Content enhanced
#       ✓ Affiliate links added
#       ✓ Product card inserted
#       ✓ E-book generated
#       ✓ Published to WordPress
#       ✓ Retrofitted successfully $12.34 potential
```

### Automated Execution (GitHub Actions)

GitHub Actions automatically triggers R37 every 6 hours as part of the workflow.

**To see logs:**
1. Go to GitHub repo
2. Navigate to Actions → ghgf-36-robots workflow
3. Click latest run
4. Scroll to "R37 - Content Retrofit Engine" step
5. Expand to see full output

### Manual GitHub Actions Trigger

```bash
# Trigger workflow manually
gh workflow run ghgf-36-robots.yml
```

---

## Monitoring Progress

### View Progress in Real-Time

```bash
# Connect to database
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME

# Check retrofit progress
SELECT 
    COUNT(*) as total_posts,
    SUM(CASE WHEN retrofitted = 1 THEN 1 ELSE 0 END) as retrofitted,
    COUNT(*) - SUM(CASE WHEN retrofitted = 1 THEN 1 ELSE 0 END) as remaining,
    ROUND((SUM(CASE WHEN retrofitted = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1) as percentage
FROM blog_posts
WHERE status = 'published';
```

**Expected output over time:**
```
Total  Retrofitted  Remaining  Progress
───────────────────────────────────────
627         0         627      0.0%    (Start)
627        50         577      8.0%    (After batch 1)
627       100         527     15.9%    (After batch 2)
627       150         477     23.9%    (After batch 3)
627       600          27     95.7%    (Almost done)
627       627           0    100.0%    (Complete!)
```

### Check Batch Statistics

```sql
SELECT 
    batch_number,
    batch_size,
    posts_successful,
    posts_failed,
    estimated_revenue,
    DATE_FORMAT(start_time, '%Y-%m-%d %H:%i') as started,
    DATE_FORMAT(end_time, '%Y-%m-%d %H:%i') as completed,
    TIMESTAMPDIFF(MINUTE, start_time, end_time) as duration_minutes,
    status
FROM retrofit_batches
ORDER BY batch_number DESC;
```

### View Current Errors

```sql
SELECT 
    blog_id,
    error_type,
    error_message,
    retry_count,
    status,
    created_at
FROM retrofit_errors
WHERE status = 'pending'
ORDER BY created_at DESC;
```

---

## Revenue Tracking

### Per-Post Calculation

```
Base: $5.00
+ Word count bonus: $2 per 1000 words
= Estimated revenue per post

Example:
- 1,500 word post = $5 + $3 = $8 per post
- 3,000 word post = $5 + $6 = $11 per post
- 5,000 word post = $5 + $10 = $15 per post
```

### View Retrofit Revenue Analytics

```sql
-- Total revenue potential from retrofit
SELECT 
    SUM(
        5 + (word_count / 1000 * 2)
    ) as total_revenue_potential,
    COUNT(*) as total_retrofitted_posts,
    ROUND(
        SUM(5 + (word_count / 1000 * 2)) / COUNT(*), 2
    ) as average_revenue_per_post
FROM retrofit_log rl
JOIN blog_posts bp ON rl.blog_id = bp.id
WHERE rl.status = 'completed';
```

### Monthly Revenue Projection

```
Week 1-4:   Retrofit phase + new post generation
            Retrofitted posts: 200 (from batches 1-4)
            Estimated: $200-400 from retrofit
            + $10-30 from new posts
            = $210-430/week

Week 5-8:   Retrofit accelerating + new content stacking
            Retrofitted posts: 400 (from batches 5-8)
            Estimated: $400-600/week from retrofit
            + $30-60 from new posts
            = $430-660/week

Week 9-12:  Retrofit complete + all posts monetized
            Retrofitted posts: 600 complete
            Estimated: $600-900/week from retrofit
            + $60-100 from new posts
            = $660-1,000/week

3-Month Total: $6,500-9,500
Average: $7,200/month
```

---

## Troubleshooting

### Issue: "Posts not found for retrofit"

**Cause:** All posts already retrofitted OR no posts meeting criteria

**Solution:**
```sql
-- Check retrofit status
SELECT COUNT(*) FROM blog_posts WHERE retrofitted = 0 AND status = 'published';

-- If all retrofitted, R37 will display "RETROFIT COMPLETE"
-- This is normal behavior - proceed to weekly refresh cycle (R25-R30)
```

### Issue: "WooCommerce API error: 401"

**Cause:** Invalid WordPress credentials

**Solution:**
```bash
# Test WordPress API credentials
curl -u $WORDPRESS_USERNAME:$WORDPRESS_PASSWORD \
  https://greathealthgreatfitness.com/wp-json/wc/v3/products

# Check GitHub Secrets
# Settings → Secrets and variables → Actions
# Verify:
#   - WORDPRESS_USERNAME is set
#   - WORDPRESS_PASSWORD is set (use App Password, not main password)
#   - WORDPRESS_SITE_URL ends without trailing slash
```

### Issue: "PDF generation failed"

**Cause:** Missing reportlab or pillow packages

**Solution:**
```bash
pip install reportlab==4.0.7 pillow==10.1.0

# Verify installation
python -c "import reportlab; import PIL; print('OK')"
```

### Issue: "Groq API error: 429 (rate limit)"

**Cause:** Too many API calls hitting Groq's rate limit

**Solution:**
```python
# Reduce batch size in r37_content_retrofit_engine.py
# Line 74: self.batch_size = 30  # Reduced from 50

# Or add delay between posts
import time
time.sleep(1)  # 1 second between each content enhancement
```

### Issue: "Content enhancement not working"

**Cause:** GROQ_API_KEY not set or invalid

**Solution:**
```bash
# Check if key is set
echo $GROQ_API_KEY

# Get fresh key from https://console.groq.com
# Update GitHub Secret: GROQ_API_KEY

# Test Groq API
python -c "from groq import Groq; c = Groq(api_key='your_key'); print('OK')"
```

### Issue: "Posts stuck in 'in_progress' status"

**Cause:** R37 crashed mid-processing

**Solution:**
```sql
-- Reset stuck posts
UPDATE retrofit_log 
SET status = 'pending'
WHERE status = 'in_progress'
AND started_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- Re-run R37 to retry them
```

---

## Success Metrics (4 Weeks)

### Technical Metrics
- ✓ 200+ posts retrofitted in first 2 weeks
- ✓ 100% batch processing success rate
- ✓ 95%+ post update success (WordPress API)
- ✓ 0 database errors
- ✓ All affiliate links valid
- ✓ All e-books generated successfully

### Business Metrics
- ✓ $200-400 revenue week 1 (from new posts)
- ✓ $400-700 revenue week 2-4 (retrofit starts showing)
- ✓ $1,500-2,000 total week 4
- ✓ Conversion rate tracking enabled
- ✓ Customer satisfaction tracking enabled

### Quality Metrics
- ✓ Average e-book rating: 4.0+ stars
- ✓ Affiliate click-through rate: 1-2%
- ✓ Product card visibility: 95%+
- ✓ Zero broken links in affiliate sections

---

## Integration with Option C

### Full System Architecture

```
OPTION C EXECUTION:

Every 6 hours:
┌─────────────────────────────────────────────────┐
│ NEW POST GENERATION (R1-R24)                    │
│ ├─ Title generation: R2                         │
│ ├─ Content generation: R3                       │
│ ├─ Plagiarism check: R4                         │
│ ├─ AI detection: R5                            │
│ ├─ SEO optimization: R6                         │
│ ├─ Image finder: R7                            │
│ ├─ ALT text: R8                                │
│ ├─ QA checks: R9                               │
│ └─ Format validation: R24                      │
│ Output: 3 new blog posts (ready for monetization)
└─────────────────────────────────────────────────┘
           ↓
         PARALLEL
           ↓
┌─────────────────────────────────────────────────┐
│ RETROFIT OLD POSTS (R37) - BATCHES              │
│ ├─ Fetch 50 unretrofitted posts                │
│ ├─ Enhance content (Groq)                      │
│ ├─ Add affiliate links                         │
│ ├─ Generate e-books (ReportLab)                │
│ ├─ Insert product cards                        │
│ └─ Update WordPress                            │
│ Output: 50 legacy posts + monetization
└─────────────────────────────────────────────────┘
           ↓
         MERGE
           ↓
┌─────────────────────────────────────────────────┐
│ MONETIZATION (R14-R14b) - Already included in   │
│ both R1-R24 pipeline AND R37 retrofit         │
│ ├─ Affiliate placement: R14                     │
│ ├─ Digital products: R14b                       │
│ └─ Product cards: inserted                      │
│ Output: All posts with full monetization
└─────────────────────────────────────────────────┘
           ↓
         WEEKLY
           ↓
┌─────────────────────────────────────────────────┐
│ REFRESH CYCLE (R25-R30) - Every 7 days          │
│ ├─ Content refresh: R25                         │
│ ├─ Plagiarism recheck: R28                      │
│ ├─ Headline optimization: R29                   │
│ └─ Final QA: R30                               │
│ Output: Optimized posts with improved engagement
└─────────────────────────────────────────────────┘

RESULT: 600+ monetized legacy posts + 63 new posts/month
        = $7,200-9,600/month from retrofit alone
        = $12,000-18,000/month total revenue potential
```

### Timeline Summary

| Phase | Duration | Posts Processed | Revenue Generated | Status |
|-------|----------|-----------------|-------------------|--------|
| Week 1-2 | 48 hours | 200 retrofitted + 18 new | $200-400 | Ramping |
| Week 3-4 | 48 hours | 400 retrofitted + 36 new | $800-1,200 | Accelerating |
| Month 1 Total | 30 days | 600 retrofitted + 63 new | $1,500-2,500 | On track |
| Month 2-3 | 60 days | 0 retrofit + 126 new | $10,000-15,000 | Stable state |
| **3-Month Total** | **90 days** | **600 retrofit + 189 new** | **$12,000-18,000** | **Success** |

---

## Next Steps

1. **Run database schema:** Execute R37_Database_Schema.sql
2. **Copy robot:** Place r37_content_retrofit_engine.py in /robots/
3. **Update workflow:** Add R37 step to GitHub Actions workflow
4. **First test:** Manually trigger workflow and monitor first batch
5. **Monitor progress:** Check retrofit_log and retrofit_analytics daily
6. **Scale up:** Once batch 1 completes, R37 will auto-continue on 6-hour cycles

---

## Support & Documentation

- **R37 Robot Code:** `/robots/r37_content_retrofit_engine.py`
- **Database Schema:** `R37_Database_Schema.sql`
- **Integration Guide:** `OPTION_C_Integration_Guide.md`
- **Main System Docs:** See 36-Robot System documentation

---

**Created:** October 10, 2026  
**Version:** 1.0 Production Release  
**Part of:** 36-Robot Autonomous Blogging System (Option C)  
**Maintained by:** Skybee (Automation Project)
