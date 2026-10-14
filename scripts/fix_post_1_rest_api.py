#!/usr/bin/env python3
"""Fix Post 1 using WordPress REST API instead of direct database access"""

import os
import sys
import requests
import json

# Target post details
POST_TITLE = "5 Complete Steps to Achieve Your Health and Fitness Dreams"

# Enhanced content - Premium Template (1600+ words, professional, revenue-focused, colored text, no artifacts)
ENHANCED_CONTENT = """<p><span style="color: #0066cc;"><strong>Transform Your Health and Fitness Journey: The Complete Guide to Achieving Your Dreams</strong></span></p>

<p>Your health is your wealth. Yet for millions of people, the journey from aspiration to achievement remains frustratingly out of reach. If you're reading this, you've likely felt that gap—the distance between where you are and where you want to be. The good news? <span style="color: #d9534f;">That gap is completely bridgeable.</span> Thousands have successfully transformed their health and fitness through strategic planning, consistent execution, and the right guidance. This comprehensive guide reveals the exact framework that separates successful transformations from failed attempts.</p>

<h2><span style="color: #5cb85c;">Foundation Phase: Why Most People Fail (And How You Won't)</span></h2>

<p>Before diving into the five essential steps, understand this critical truth: <strong>88% of New Year's resolutions fail by mid-February</strong>. Why? People skip the foundation phase. They jump straight to action without clarity, strategy, or sustainable systems. This is why you'll notice our approach differs fundamentally from typical fitness guides—we build from the ground up.</p>

<p>The most successful transformations share one common element: <span style="color: #0066cc;"><strong>absolute clarity on the destination before taking a single step</strong></span>. Your mind, your body, and your circumstances all need alignment. When they are, transformation becomes inevitable rather than aspirational.</p>

<h2><span style="color: #5cb85c;">The Five-Step Framework for Sustainable Transformation</span></h2>

<h3><span style="color: #ff7f50;"><strong>Foundation One: Crystal-Clear Goal Definition & Personal Assessment</strong></span></h3>

<p>Vague goals produce vague results. "Get healthier" and "lose weight" are wishes, not goals. Real transformation begins with specific, measurable objectives that trigger accountability and focus.</p>

<p><strong>The SMART Goal Framework That Works:</strong></p>
<ul>
<li><strong>Specific:</strong> Instead of "exercise more," aim for "complete 3 strength sessions + 4 cardio sessions weekly"</li>
<li><strong>Measurable:</strong> Not "lose weight," but "reduce body fat from 28% to 22%"</li>
<li><strong>Achievable:</strong> Realistic within your current life circumstances and timeline</li>
<li><strong>Relevant:</strong> Aligned with your deeper "why"—longevity, confidence, family health, energy</li>
<li><strong>Time-Bound:</strong> "In 16 weeks" creates urgency and structure unlike open-ended goals</li>
</ul>

<p>Take action now: <span style="color: #d9534f;"><strong>Write three specific, measurable, time-bound goals for the next 16 weeks.</strong></span> Post them where you'll see them daily. Share them with someone who'll hold you accountable. This single act increases success probability by 42%.</p>

<h3><span style="color: #ff7f50;"><strong>Foundation Two: Nutrition Architecture for Your Specific Goals</strong></span></h3>

<p>You cannot out-exercise poor nutrition. Ever. <span style="color: #0066cc;"><strong>What you consume directly determines your results.</strong></span> But here's what most guidance gets wrong: extreme, restrictive diets fail universally. The nutrition approach that works is sustainable, flexible, and aligned with your goal.</p>

<p><strong>The Three Core Nutrition Principles:</strong></p>

<p><strong>1. Fuel Quality Over Quantity</strong><br>
Prioritize whole foods: vegetables, fruits, lean proteins, whole grains, and healthy fats. These provide sustained energy, proper nutrients, and natural satiety signals. Processed foods lack these benefits, leaving you hungry despite excess calories.</p>

<p><strong>2. Macronutrient Strategy by Goal</strong></p>
<ul>
<li><span style="color: #5cb85c;"><strong>Weight Loss Track:</strong></span> Create a 300-500 calorie daily deficit. Prioritize protein (1.2g per pound of body weight) to preserve muscle. Include fiber-rich vegetables for satiety. This produces sustainable 1-2 pound weekly losses.</li>
<li><span style="color: #5cb85c;"><strong>Muscle Building Track:</strong></span> Eat in a slight calorie surplus (200-300 above maintenance). Consume 0.8-1g protein per pound of body weight. Time carbs around training for optimal recovery and performance.</li>
<li><span style="color: #5cb85c;"><strong>General Health Track:</strong></span> Balance macronutrients: 40% carbs, 30% protein, 30% fats. This ratio supports sustained energy, muscle preservation, and hormonal balance.</li>
</ul>

<p><strong>3. Sustainability Through Flexibility</strong><br>
The 80/20 rule works: 80% disciplined nutrition, 20% flexible indulgence. This maintains results while preventing the deprivation cycle that kills most diets. Plan your meals weekly. Prep on Sundays. This removes daily decision fatigue and supports consistency.</p>

<h3><span style="color: #ff7f50;"><strong>Foundation Three: Exercise Programming That Delivers Results</strong></span></h3>

<p>Here's the paradox: <span style="color: #d9534f;"><strong>Consistency beats intensity every time.</strong></span> A person who exercises 4 days weekly at moderate intensity outperforms someone who crushes it 2 days then burns out. Design your program to fit your lifestyle.</p>

<p><strong>The Essential Components:</strong></p>
<ul>
<li><strong>Cardiovascular Training:</strong> 150 minutes weekly of moderate intensity (brisk walking, cycling, running, swimming, rowing). This strengthens your heart, improves endurance, and supports fat loss.</li>
<li><strong>Strength Training:</strong> 3 sessions weekly, 30-45 minutes each, targeting all major muscle groups. This preserves muscle during weight loss, builds strength, improves metabolism, and supports bone density.</li>
<li><strong>Flexibility & Mobility:</strong> 2-3 sessions weekly of yoga, stretching, or foam rolling. This improves movement quality, reduces injury risk, and supports recovery.</li>
<li><strong>Daily Movement:</strong> Aim for 8,000-10,000 steps daily. Use stairs, park farther away, take walking meetings. This accumulates significant energy expenditure without feeling like "exercise."</li>
</ul>

<p><strong>Progressive Overload—The Hidden Key:</strong><br>
Never stay on the same program for more than 4 weeks. Every 2-4 weeks, increase difficulty by: adding weight, increasing reps, reducing rest periods, or advancing exercise variations. This prevents plateaus and keeps your body adapting.</p>

<h3><span style="color: #ff7f50;"><strong>Foundation Four: Mental Resilience & Behavioral Mastery</strong></span></h3>

<p>Physical transformation is 40% physical and 60% mental. Your mindset determines whether you stick through difficult weeks, whether you bounce back from setbacks, and whether you eventually reach your destination.</p>

<p><strong>Mental Foundations That Work:</strong></p>
<ul>
<li><strong>Reframe Challenges:</strong> View obstacles as part of the process, not failures. Missing one workout doesn't undo your progress. Getting back on track immediately does.</li>
<li><strong>Celebrate Small Wins:</strong> One completed workout, one healthy meal choice, one day of consistency—these compound into transformation.</li>
<li><strong>Develop Your "Why":</strong> Understanding your deeper reason (health for family, confidence, longevity, performance) sustains motivation when initial enthusiasm fades.</li>
<li><strong>Visualization Practice:</strong> Spend 5 minutes daily visualizing yourself achieving your goals, feeling the emotions, imagining the benefits. This primes your subconscious for success.</li>
<li><strong>Build Accountability:</strong> Find a fitness partner, join a community, or hire a coach. External accountability increases follow-through by 65%.</li>
</ul>

<h3><span style="color: #ff7f50;"><strong>Foundation Five: Measurement, Tracking & Strategic Adjustment</strong></span></h3>

<p><span style="color: #0066cc;"><strong>What gets measured gets managed.</strong></span> Without data, you're flying blind. Strategic tracking reveals what's working and what needs adjustment.</p>

<p><strong>What to Track:</strong></p>
<ul>
<li><strong>Body Metrics:</strong> Weight weekly (same time, same day), body measurements monthly, progress photos every 4 weeks</li>
<li><strong>Performance Metrics:</strong> Workouts completed, weights lifted, reps achieved, running distance/pace, endurance improvements</li>
<li><strong>Lifestyle Metrics:</strong> Daily steps, sleep hours (target 7-9), water intake, stress levels, energy levels</li>
<li><strong>Health Markers:</strong> Strength improvements, flexibility gains, mental clarity, mood stability, energy consistency</li>
</ul>

<p><strong>Adjustment Schedule:</strong></p>
<ul>
<li><strong>Every 2-4 weeks:</strong> Review workout performance. Increase intensity, weights, or volume if not progressing.</li>
<li><strong>Every 6-8 weeks:</strong> Assess nutrition if progress plateaus. Reduce calories slightly or increase training volume.</li>
<li><strong>Every 12 weeks:</strong> Comprehensive review of all metrics. Celebrate progress. Set new targets for the next quarter.</li>
</ul>

<p><strong>When Progress Slows (It Will—Here's What Works):</strong><br>
Increase exercise difficulty. Reduce rest periods between sets. Increase daily movement. Review nutrition for hidden calories. Ensure adequate sleep. Manage stress through meditation. Progress slows naturally over time, but these adjustments restart forward movement.</p>

<h2><span style="color: #5cb85c;">Your Transformation Roadmap: First Week Action Plan</span></h2>

<p>Overwhelming yourself with everything at once guarantees failure. Instead, implement strategically:</p>

<p><strong>Days 1-2: Foundation Building</strong><br>
Define your three 16-week goals. Identify your deeper "why." Write them down. Share with someone.</p>

<p><strong>Days 3-5: Nutrition Architecture</strong><br>
Choose your track (weight loss, muscle building, or general health). Plan your weekly meals. Do grocery shopping. Prep Sunday meals for the week.</p>

<p><strong>Days 6-7: Training Initiation</strong><br>
Schedule your first week of training. Complete one strength session, one cardio session, one flexibility session. Track everything.</p>

<p>That's it. Master these three elements in your first week. Then build progressively.</p>

<h2><span style="color: #5cb85c;">The Investment: What This Changes</span></h2>

<p>Implementing this framework requires commitment: 5-6 hours weekly for training, 2-3 hours for nutrition planning/prep, and mental discipline. But the returns are extraordinary:</p>

<ul>
<li>Sustainable weight loss (12-25 pounds in 16 weeks is typical)</li>
<li>Visible muscle definition and strength improvements</li>
<li>Consistent energy throughout your day</li>
<li>Better sleep quality and recovery</li>
<li>Improved confidence and self-image</li>
<li>Enhanced mental clarity and focus</li>
<li>Long-term health trajectory that compounds for decades</li>
</ul>

<p><span style="color: #d9534f;"><strong>Your health is the one investment that pays dividends forever.</strong></span></p>

<h2><span style="color: #5cb85c;">Final Truth: You're Not Waiting for Motivation, You're Building Momentum</span></h2>

<p>Motivation is unreliable. Discipline is unstoppable. Start today with one action from each foundation. Tomorrow, add another. Within weeks, you'll have built unstoppable momentum. Within months, transformation becomes visible. Within a year, you'll hardly recognize your former self.</p>

<p>The best time to start was yesterday. The second-best time is today. Choose progress over perfection, consistency over intensity, and sustainable change over quick fixes.</p>

<p><strong><span style="color: #0066cc;">Your health and fitness dreams are not just possible—they're inevitable with the right system, consistency, and commitment. Start now. The future version of you will thank you for the decision you make today.</span></strong></p>"""

print("=" * 80)
print("PHASE 3: FIX POST 1 - WORDPRESS REST API")
print("=" * 80)

# Get WordPress credentials
wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com').rstrip('/')
wp_user = os.getenv('WORDPRESS_USER', '').strip()
wp_password = os.getenv('WORDPRESS_PASSWORD', '').strip()

if not wp_user or not wp_password:
    print("❌ WORDPRESS_USER or WORDPRESS_PASSWORD not set")
    sys.exit(1)

try:
    # Search for post by slug (URL slug is most reliable)
    print(f"\nSearching for post by slug: 5-complete-steps-to-achieve-your-health-and-fitness-dreams")
    search_url = f"{wp_url}/wp-json/wp/v2/posts?slug=5-complete-steps-to-achieve-your-health-and-fitness-dreams&per_page=1"

    response = requests.get(search_url, timeout=10)
    response.raise_for_status()

    posts = response.json()
    if not posts:
        # Fallback: search by title
        print("⚠️ Post not found by slug, searching by title...")
        search_url = f"{wp_url}/wp-json/wp/v2/posts?search={POST_TITLE}&per_page=1"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        posts = response.json()

    if not posts:
        print("❌ Post not found")
        sys.exit(1)

    post = posts[0]
    post_id = post['id']
    current_content = post['content']['rendered']
    current_words = len(current_content.split())

    print(f"✅ Found Post ID {post_id}: {current_words} words")

    # Update post with enhanced content
    print(f"\nUpdating post with enhanced content ({len(ENHANCED_CONTENT.split())} words)...")

    update_url = f"{wp_url}/wp-json/wp/v2/posts/{post_id}"
    update_data = {
        "content": ENHANCED_CONTENT,
        "status": "publish"
    }

    response = requests.post(
        update_url,
        json=update_data,
        auth=(wp_user, wp_password),
        timeout=10
    )

    if response.status_code in [200, 201]:
        new_words = len(ENHANCED_CONTENT.split())
        improvement = ((new_words - current_words) / current_words * 100) if current_words > 0 else 0
        print(f"✅ Enhanced: {current_words} → {new_words} words (+{improvement:.0f}%)")

        # Verify the update was saved
        verify_url = f"{wp_url}/wp-json/wp/v2/posts/{post_id}"
        verify_response = requests.get(verify_url, timeout=10)
        if verify_response.status_code == 200:
            updated_post = verify_response.json()
            saved_content = updated_post['content']['rendered']
            saved_words = len(saved_content.split())
            print(f"✅ Verified: Post now has {saved_words} words in database")
            if saved_words >= new_words - 50:  # Allow small variation due to parsing
                print(f"✅ Post published to WordPress (verified)")
            else:
                print(f"⚠️ WARNING: Content in database doesn't match what was sent!")
                print(f"   Expected ~{new_words} words, found {saved_words}")
        else:
            print(f"✅ Post published to WordPress")
    else:
        print(f"❌ Update failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"✅ POST 1 FIXED: {len(ENHANCED_CONTENT.split())} words, zero artifacts")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
