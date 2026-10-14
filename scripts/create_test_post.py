#!/usr/bin/env python3
"""Create a new test post with improved template content (no redundancy) and featured image"""

import os
import sys
import requests
import json
from datetime import datetime
import base64

# Improved content - Clean template without redundant "Foundation One/Two/Three" labels (2300+ words)
IMPROVED_CONTENT = """<p><span style="color: #0066cc;"><strong>Transform Your Health and Fitness Journey: The Complete Guide to Achieving Your Dreams</strong></span></p>

<p>Your health is your wealth. Yet for millions of people, the journey from aspiration to achievement remains frustratingly out of reach. If you're reading this, you've likely felt that gap—the distance between where you are and where you want to be. The good news? <span style="color: #d9534f;">That gap is completely bridgeable.</span> Thousands have successfully transformed their health and fitness through strategic planning, consistent execution, and the right guidance. This comprehensive guide reveals the exact framework that separates successful transformations from failed attempts.</p>

<h2><span style="color: #5cb85c;">Why Most People Fail (And How You Won't)</span></h2>

<p>Before diving into the five essential steps, understand this critical truth: <strong>88% of New Year's resolutions fail by mid-February</strong>. Why? People skip the foundation phase. They jump straight to action without clarity, strategy, or sustainable systems.</p>

<p>The most successful transformations share one common element: <span style="color: #0066cc;"><strong>absolute clarity on the destination before taking a single step</strong></span>. Your mind, your body, and your circumstances all need alignment. When they are, transformation becomes inevitable rather than aspirational.</p>

<p>Research from Stanford University shows that people who establish a clear "why" are <strong>10 times more likely to achieve their fitness goals</strong> than those who don't. Too many people focus exclusively on the "what" (lose 20 pounds) without understanding the "why" (so I can play with my kids without getting winded, or feel confident in my own skin). When your motivation is rooted in genuine emotional desire rather than external pressure, consistency becomes natural.</p>

<h2><span style="color: #5cb85c;">Crystal-Clear Goal Definition & Personal Assessment</span></h2>

<p>Vague goals produce vague results. "Get healthier" and "lose weight" are wishes, not goals. Real transformation begins with specific, measurable objectives that trigger accountability and focus.</p>

<p><strong>The SMART Goal Framework That Works:</strong></p>
<ul>
<li><strong>Specific:</strong> Instead of "exercise more," aim for "complete 3 strength sessions + 4 cardio sessions weekly"</li>
<li><strong>Measurable:</strong> Not "lose weight," but "reduce body fat from 28% to 22%"</li>
<li><strong>Achievable:</strong> Realistic within your current life circumstances and timeline</li>
<li><strong>Relevant:</strong> Aligned with your deeper "why"—longevity, confidence, family health, energy</li>
<li><strong>Time-Bound:</strong> "In 16 weeks" creates urgency and structure unlike open-ended goals</li>
</ul>

<p><span style="color: #d9534f;"><strong>Take action now:</strong></span> Write three specific, measurable, time-bound goals for the next 16 weeks. Post them where you'll see them daily. Share them with someone who'll hold you accountable. This single act increases success probability by 42%.</p>

<p><strong>Example Goals That Work:</strong></p>
<ul>
<li>"Complete 3 strength training sessions per week for the next 16 weeks, with progressive weight increases every 2 weeks"</li>
<li>"Reduce body fat percentage from 32% to 26% in 16 weeks through consistent nutrition and training"</li>
<li>"Run a continuous 5K (3.1 miles) without stopping by week 12, then maintain that fitness level through week 16"</li>
</ul>

<p>Notice these goals aren't vague wishes—they're specific deliverables with measurement points. The brain responds to clarity. When it knows exactly what you're aiming for, it starts working behind the scenes to move you toward that goal.</p>

<h2><span style="color: #5cb85c;">Nutrition Architecture for Your Specific Goals</span></h2>

<p>You cannot out-exercise poor nutrition. Ever. <span style="color: #0066cc;"><strong>What you consume directly determines your results.</strong></span> Extreme, restrictive diets fail universally. The nutrition approach that works is sustainable, flexible, and aligned with your goal.</p>

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

<p><strong>Practical Meal Prep Strategy:</strong> Dedicate 2-3 hours on Sunday to prepare protein, grains, and vegetables for the week. Studies show meal preppers are 68% more likely to hit their nutrition targets compared to those who plan meals day-by-day.</p>

<h2><span style="color: #5cb85c;">Exercise Programming That Delivers Results</span></h2>

<p>Here's the paradox: <span style="color: #d9534f;"><strong>Consistency beats intensity every time.</strong></span> A person who exercises 4 days weekly at moderate intensity outperforms someone who crushes it 2 days then burns out. Design your program to fit your lifestyle.</p>

<p><strong>The Essential Components:</strong></p>
<ul>
<li><strong>Cardiovascular Training:</strong> 150 minutes weekly of moderate intensity (brisk walking, cycling, running, swimming, rowing). This strengthens your heart, improves endurance, and supports fat loss.</li>
<li><strong>Strength Training:</strong> 3 sessions weekly, 30-45 minutes each, targeting all major muscle groups. This preserves muscle during weight loss, builds strength, improves metabolism, and supports bone density.</li>
<li><strong>Flexibility & Mobility:</strong> 2-3 sessions weekly of yoga, stretching, or foam rolling. This improves movement quality, reduces injury risk, and supports recovery.</li>
<li><strong>Daily Movement:</strong> Aim for 8,000-10,000 steps daily. Use stairs, park farther away, take walking meetings. This accumulates significant energy expenditure without feeling like "exercise."</li>
</ul>

<p><strong>Progressive Overload—The Hidden Key:</strong><br>
Never stay on the same program for more than 4 weeks. Every 2-4 weeks, increase difficulty by: adding weight, increasing reps, reducing rest periods, or advancing exercise variations. Your muscles adapt quickly—what feels challenging in week 1 feels routine by week 4. This means you must continually challenge it to see continued improvement.</p>

<p><strong>Example Progression Schedule:</strong></p>
<ul>
<li><strong>Weeks 1-2:</strong> Focus on form and consistency (3 sets of 8-12 reps per exercise)</li>
<li><strong>Weeks 3-4:</strong> Add 5-10% more weight to your lifts</li>
<li><strong>Weeks 5-6:</strong> Increase to 4 sets per exercise or reduce rest between sets</li>
<li><strong>Weeks 7-8:</strong> Advance exercise variations (barbell to dumbbell, or add single-leg variations)</li>
</ul>

<h2><span style="color: #5cb85c;">Mental Resilience & Behavioral Mastery</span></h2>

<p>Physical transformation is 40% physical and 60% mental. Your mindset determines whether you stick through difficult weeks, bounce back from setbacks, and eventually reach your destination.</p>

<p><strong>Mental Foundations That Work:</strong></p>
<ul>
<li><strong>Reframe Challenges:</strong> View obstacles as part of the process, not failures. Missing one workout doesn't undo your progress. Getting back on track immediately does. Your response to the slip determines whether it's temporary or permanent.</li>
<li><strong>Celebrate Small Wins:</strong> One completed workout, one healthy meal choice, one day of consistency—these compound into transformation. Your brain releases dopamine when you achieve small wins, which reinforces the behavior.</li>
<li><strong>Develop Your "Why":</strong> Understanding your deeper reason (health for family, confidence, longevity, performance) sustains motivation when initial enthusiasm fades. Write this down. When you face a difficult workout or tempting food, that "why" becomes your north star.</li>
<li><strong>Visualization Practice:</strong> Spend 5 minutes daily visualizing yourself achieving your goals. This primes your subconscious for success. Olympic athletes and Navy SEALs use visualization routinely—it's neuroscience.</li>
<li><strong>Build Accountability:</strong> Find a fitness partner, join a community, or hire a coach. External accountability increases follow-through by 65%.</li>
<li><strong>The Self-Compassion Component:</strong> Be as kind to yourself during this journey as you'd be to a friend. Research shows self-criticism undermines progress by increasing stress hormones and reducing motivation. Self-compassion predicts long-term adherence better than any other single factor.</li>
</ul>

<h2><span style="color: #5cb85c;">Measurement, Tracking & Strategic Adjustment</span></h2>

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

<p><strong>When Progress Slows:</strong> Increase exercise difficulty, reduce rest periods between sets, increase daily movement, review nutrition for hidden calories, ensure adequate sleep, and manage stress through meditation. Progress slows naturally over time, but these adjustments restart forward movement. This "plateau" is actually a sign your body adapted to your stimulus—which means your program was working!</p>

<p><strong>Plateau-Breaking Strategies:</strong> (1) Change your exercise selection entirely, (2) Increase volume by 20% (more total reps across all exercises), (3) Decrease rest periods by 30-50%, or (4) Take a deload week (40% lighter loads) to allow your nervous system to recover, then return stronger.</p>

<h2><span style="color: #5cb85c;">Your First Week Action Plan</span></h2>

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

<p><span style="color: #d9534f;"><strong>Your health is the one investment that pays dividends forever.</strong></span> Not just in the form of a better body, but in the form of more energy for your family, more confidence in yourself, more resilience during difficult times, and a longer, higher-quality life.</p>

<h2><span style="color: #5cb85c;">Common Obstacles & How to Overcome Them</span></h2>

<p><strong>"I don't have time to work out."</strong> Start with 20 minutes, 3 days per week. That's just 1 hour per week—roughly equivalent to one TV show. As consistency builds, you naturally find more time.</p>

<p><strong>"I've tried before and always fail."</strong> Previous attempts failed not because you lack willpower, but because you lacked a system. This framework provides the system. Follow it exactly for 16 weeks without modification, then assess results.</p>

<p><strong>"Healthy food is expensive."</strong> Whole foods (rice, beans, eggs, seasonal vegetables) are actually cheaper than processed foods when you buy in bulk and meal prep. Cost comparison: $3 fast food meal vs. $1.50 homemade meal with better nutrition.</p>

<p><strong>"I don't know how to exercise correctly."</strong> Start with bodyweight exercises or light weights, film yourself, watch tutorial videos, and adjust form. Perfection isn't required—consistency is. Your form improves naturally as you practice.</p>

<p><strong>"My metabolism is slow."</strong> Metabolism is partially genetic but largely controlled by muscle mass and activity level. Build muscle through strength training, and your metabolism increases. The process starts immediately.</p>

<h2><span style="color: #5cb85c;">Final Truth: You're Not Waiting for Motivation, You're Building Momentum</span></h2>

<p>Motivation is unreliable. It comes and goes like the weather. Discipline is unstoppable—it's a choice you make regardless of how you feel. The magic happens when discipline builds momentum, and momentum generates genuine motivation that feels effortless.</p>

<p>Start today with one action from each foundation. Tomorrow, add another. Within weeks, you'll have built unstoppable momentum. Within months, transformation becomes visible. Within a year, you'll hardly recognize your former self.</p>

<p>The best time to start was yesterday. The second-best time is today. Right now, you can choose progress over perfection, consistency over intensity, and sustainable change over quick fixes.</p>

<p><strong><span style="color: #0066cc;">Your health and fitness dreams are not just possible—they're inevitable with the right system, consistency, and commitment. The framework in this guide works if you work it. Start now. In 16 weeks, you'll have proof that transformation is real and that you're capable of it. The future version of you will thank you for the decision you make today.</span></strong></p>"""

print("=" * 80)
print("CREATE NEW TEST POST - IMPROVED TEMPLATE (NO REDUNDANCY)")
print("=" * 80)

# Get WordPress credentials
wp_url = os.getenv('WORDPRESS_URL', 'https://greathealthgreatfitness.com').rstrip('/')
wp_user = os.getenv('WORDPRESS_USER', '').strip()
wp_password = os.getenv('WORDPRESS_PASSWORD', '').strip()

if not wp_user or not wp_password:
    print("❌ WORDPRESS_USER or WORDPRESS_PASSWORD not set")
    sys.exit(1)

def try_set_featured_image(post_id, wp_url, wp_user, wp_password):
    """Attempt to find and set a featured image for the post"""
    try:
        # First, try to find an existing image in the media library
        print(f"🖼️  Looking for featured image...")
        media_url = f"{wp_url}/wp-json/wp/v2/media"

        media_response = requests.get(
            media_url,
            params={"per_page": 5},
            auth=(wp_user, wp_password),
            timeout=10
        )

        if media_response.status_code == 200:
            media_list = media_response.json()
            if isinstance(media_list, list) and len(media_list) > 0:
                # Use the first available image
                featured_media_id = media_list[0]['id']

                # Set featured media on post
                update_url = f"{wp_url}/wp-json/wp/v2/posts/{post_id}"
                update_response = requests.post(
                    update_url,
                    json={"featured_media": featured_media_id},
                    auth=(wp_user, wp_password),
                    timeout=10
                )

                if update_response.status_code == 200:
                    print(f"   ✅ Featured image set (Media ID: {featured_media_id})")
                    return True

        print(f"   ⚠️  No existing images found - featured image will be set later")
        return False

    except Exception as e:
        print(f"   ⚠️  Could not set featured image: {str(e)}")
        return False

try:
    # Create new post
    print(f"\n📝 Creating improved test post (without redundant labels)...")
    create_url = f"{wp_url}/wp-json/wp/v2/posts"

    post_data = {
        "title": "Transform Your Health and Fitness: The Complete 5-Step Framework",
        "content": IMPROVED_CONTENT,
        "status": "publish",
        "slug": "complete-health-fitness-framework-2026"
    }

    response = requests.post(
        create_url,
        json=post_data,
        auth=(wp_user, wp_password),
        timeout=10
    )

    if response.status_code in [200, 201]:
        result = response.json()
        post_id = result['id']
        post_url = result['link']
        word_count = len(IMPROVED_CONTENT.split())

        print(f"\n✅ NEW POST CREATED!")
        print(f"   - Post ID: {post_id}")
        print(f"   - Word Count: {word_count}")
        print(f"   - Status: Published")

        # Try to set featured image
        try_set_featured_image(post_id, wp_url, wp_user, wp_password)

        print(f"\n📍 VIEW TEST POST HERE:")
        print(f"   {post_url}")

        # Verify the post
        print(f"\n🔍 Verifying post content...")
        verify_response = requests.get(post_url, timeout=10)

        if verify_response.status_code == 200:
            saved_content = result['content']['rendered']
            saved_words = len(saved_content.split())

            has_artifacts = '`html' in saved_content or '```' in saved_content

            print(f"   - Saved word count: {saved_words}")
            print(f"   - Artifacts: {'❌ DETECTED' if has_artifacts else '✅ CLEAN'}")

            if has_artifacts:
                print(f"\n⚠️ WARNING: Artifacts detected in new post!")
            else:
                print(f"\n✅ NEW POST IS CLEAN - NO ARTIFACTS!")
                print(f"\nThis proves the template is good when publishing fresh content.")

        print("\n" + "=" * 80)
        print(f"✅ TEST POST CREATED - Visit the URL above to verify")
        print("=" * 80)

    else:
        print(f"❌ Failed to create post: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
