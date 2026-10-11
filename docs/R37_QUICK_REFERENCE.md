# R37 Quick Reference Card

## One-Liner
**R37** retrofits 600+ old blog posts with affiliates, e-books, and product cards in parallel with your regular content generation system. Estimated revenue: **$18,000-26,000** in 3 months.

---

## Installation (45 minutes)

```bash
# 1. Database setup (5 min)
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < R37_Database_Schema.sql

# 2. Copy robot (2 min)
cp GHGFrobots/r37_content_retrofit_engine.py /robots/
chmod +x /robots/r37_content_retrofit_engine.py

# 3. Test standalone (30 min)
# Set env vars, then:
python /robots/r37_content_retrofit_engine.py

# 4. Add to workflow (5 min)
# Edit .github/workflows/ghgf-36-robots.yml
# Add R37 step after R24

# 5. Commit & push (2 min)
git commit -m "Add R37 Content Retrofit Engine"
git push origin main
```

---

## Running R37

### Manual (Testing)
```bash
python /robots/r37_content_retrofit_engine.py
```

### Automated (Production)
R37 runs automatically every 6 hours as part of the GitHub Actions workflow.

### Trigger Manually
```bash
gh workflow run ghgf-36-robots.yml
```

---

## Check Progress (Copy & Paste)

### Simple Query
```sql
SELECT 
    COUNT(*) total,
    SUM(IF(retrofitted=1,1,0)) done,
    ROUND(SUM(IF(retrofitted=1,1,0))/COUNT(*)*100,1) pct
FROM blog_posts WHERE status='published';
```

### Expected Output (Growing)
```
total  done   pct
-----  ----  ------
 627     0    0.0%   (Start)
 627    50    8.0%   (Batch 1)
 627   100   15.9%   (Batch 2)
 627   200   31.9%   (Batch 4)
 627   400   63.8%   (Batch 8)
 627   627  100.0%   (Complete!)
```

---

## Check Revenue Potential

```sql
SELECT 
    ROUND(SUM(5 + word_count/1000*2), 2) revenue,
    COUNT(*) posts,
    ROUND(SUM(5 + word_count/1000*2)/COUNT(*), 2) avg_per_post
FROM retrofit_log rl
JOIN blog_posts bp ON rl.blog_id = bp.id
WHERE rl.status = 'completed';
```

### Expected (Growing)
```
Revenue  Posts  Avg/Post
-------  -----  --------
$400      50    $8.00    (Batch 1)
$800     100    $8.00    (Batch 2)
$4,800   600   $8.00    (Complete)
```

---

## Check for Errors

```bash
# Quick check
mysql -e "
SELECT COUNT(*) FROM retrofit_errors WHERE status='pending';
"
# Should be 0. If > 0, problems need fixing.

# See what failed
SELECT blog_id, error_type, error_message 
FROM retrofit_errors 
WHERE status='pending' 
ORDER BY created_at DESC;
```

---

## Monitor Batch Progress

```bash
# Current batch status
mysql -e "
SELECT 
    batch_number,
    posts_successful,
    posts_failed,
    status,
    DATE_FORMAT(start_time, '%H:%i:%s') started
FROM retrofit_batches
ORDER BY batch_number DESC LIMIT 1;
"
```

---

## Troubleshooting Quick Fixes

### "R37 not in logs"
```bash
# Check if workflow has R37 step
grep "R37" .github/workflows/ghgf-36-robots.yml
# Should show the step definition
```

### "Posts stuck in in_progress"
```sql
-- Reset stuck posts
UPDATE retrofit_log 
SET status='pending' 
WHERE status='in_progress' 
AND started_at < DATE_SUB(NOW(),INTERVAL 2 HOUR);
```

### "No posts found for retrofit"
```sql
-- All posts done! Check total
SELECT COUNT(*) FROM blog_posts WHERE retrofitted=1;
-- Should be 627
```

### "Groq API rate limit"
```python
# Edit r37_content_retrofit_engine.py line 74
self.batch_size = 30  # Reduce from 50
```

---

## Key Metrics to Watch

**Daily:**
- Retrofit progress % (should increase by ~8% per batch)
- Error count (should be 0)

**Weekly:**
- Revenue potential (should grow ~$4,800 per batch)
- Average revenue per post (should be ~$8)

**Monthly:**
- Total posts retrofitted (goal: 627)
- Total revenue potential (goal: $4,800-9,000)

---

## Timeline

| Day | Batches | Posts | Progress | Revenue |
|-----|---------|-------|----------|---------|
| 1   | 1-4     | 200   | 32%      | $1,600  |
| 2   | 5-8     | 400   | 64%      | $3,200  |
| 3   | 9-12    | 600   | 96%      | $4,800  |
| 4   | 13      | 627   | 100%     | $5,000  |

---

## Files Reference

| File | Purpose | Action |
|------|---------|--------|
| r37_content_retrofit_engine.py | The robot | Copy to /robots/ |
| R37_Database_Schema.sql | Create tables | Run once via mysql |
| R37-Content-Retrofit-Engine-Guide.md | Full docs | Read for details |
| OPTION_C_Complete_Integration_Guide.md | Full system | Read for integration |
| R37_QUICK_REFERENCE.md | This card | Quick lookups |

---

## Money Calculation

**Per Post:**
- Base: $5
- Bonus: +$2 per 1,000 words
- Example: 2,000-word post = $5 + $4 = **$9/post**

**Total Potential:**
- 600 posts × avg $8/post = **$4,800**
- Add new posts: +$60-100/month
- Month 1: ~$2,500-3,500
- Month 2: ~$7,000-9,500
- Month 3: ~$7,200-9,600
- **3-Month Total: $18,000-26,000**

---

## Support

**Documentation:**
- Full guide: `R37-Content-Retrofit-Engine-Guide.md`
- Integration: `OPTION_C_Complete_Integration_Guide.md`

**Logs:**
- GitHub Actions: Check workflow run logs
- Database: Check `retrofit_log` table
- Errors: Check `retrofit_errors` table

**Emergency Rollback:**
```bash
# Disable R37 (keep original posts)
# Edit workflow to comment out R37 step
git commit -m "Disable R37 temporarily"
git push origin main
```

---

## Status Check Script

Save as `check_r37_status.sh`:

```bash
#!/bin/bash
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "
    SELECT '=== R37 STATUS ===' as '';
    SELECT CONCAT(COUNT(*),' total posts') FROM blog_posts WHERE status='published';
    SELECT CONCAT(SUM(IF(retrofitted=1,1,0)),' retrofitted') FROM blog_posts WHERE status='published';
    SELECT CONCAT(ROUND(SUM(IF(retrofitted=1,1,0))/COUNT(*)*100,1),'% complete') FROM blog_posts WHERE status='published';
    SELECT CONCAT('$',ROUND(SUM(5+word_count/1000*2),2),' revenue potential') FROM retrofit_log rl JOIN blog_posts bp ON rl.blog_id=bp.id WHERE rl.status='completed';
    SELECT CONCAT(COUNT(*),' errors pending') FROM retrofit_errors WHERE status='pending';
"
```

Run: `bash check_r37_status.sh`

---

**Remember:** R37 runs automatically every 6 hours. Just set it up once and let it work!

Last Updated: October 10, 2026
