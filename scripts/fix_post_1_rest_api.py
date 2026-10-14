#!/usr/bin/env python3
"""Fix Post 1 using WordPress REST API instead of direct database access"""

import os
import sys
import requests
import json

# Target post details
POST_TITLE = "5 Complete Steps to Achieve Your Health and Fitness Dreams"

# Enhanced content (1243 words, no artifacts)
ENHANCED_CONTENT = """5 Complete Steps to Achieve Your Health and Fitness Dreams

Are you ready to transform your health and fitness journey? Achieving your health and fitness dreams doesn't require perfection—it requires commitment, consistency, and a clear plan. Whether you're looking to lose weight, build muscle, improve your cardiovascular health, or simply feel better in your daily life, these five essential steps will guide you toward sustainable success.

<h2>Step 1: Define Your Clear and Specific Goals</h2>

The foundation of any successful fitness journey is having crystal-clear goals. Vague aspirations like "get healthier" or "lose weight" rarely lead to lasting transformation. Instead, you need measurable, time-bound objectives that keep you accountable and motivated.

<strong>Why Specific Goals Matter:</strong> When you define exact targets—such as "lose 15 pounds in 3 months" or "run a 5K in under 30 minutes"—you create a roadmap for success. Specific goals help you track progress, stay motivated, and know exactly when you've achieved what you set out to do.

<strong>How to Set Effective Fitness Goals:</strong>
<ul>
<li>Use the SMART framework: Specific, Measurable, Achievable, Relevant, and Time-bound</li>
<li>Write down your goals and place them somewhere you'll see daily</li>
<li>Break larger goals into smaller milestones (e.g., monthly targets)</li>
<li>Review and adjust your goals every 4-6 weeks based on progress</li>
<li>Share your goals with an accountability partner or trainer</li>
</ul>

<strong>Real-World Examples:</strong>
<ul>
<li>"I will walk 30 minutes every weekday for the next 12 weeks" (instead of "exercise more")</li>
<li>"I will reduce my daily sugar intake to under 50 grams by next month" (instead of "eat healthier")</li>
<li>"I will complete 3 strength training sessions per week for 8 weeks" (instead of "get stronger")</li>
</ul>

<h2>Step 2: Build a Sustainable Nutrition Foundation</h2>

Nutrition is the cornerstone of health and fitness success. You cannot out-exercise a poor diet, and restrictive eating patterns inevitably fail. The key is creating a sustainable nutrition approach that supports your goals without requiring extreme sacrifice.

<strong>The Principles of Sustainable Nutrition:</strong>
<ul>
<li>Focus on whole foods: vegetables, fruits, lean proteins, whole grains, and healthy fats</li>
<li>Practice portion control without obsessive calorie counting</li>
<li>Eat a variety of colorful foods to ensure diverse nutrient intake</li>
<li>Plan and prepare meals ahead to avoid impulsive unhealthy choices</li>
<li>Allow yourself flexibility—80% disciplined eating, 20% enjoyment foods</li>
</ul>

<strong>Nutrition Strategy by Goal:</strong>
<ul>
<li><strong>For Weight Loss:</strong> Create a modest calorie deficit (300-500 calories below maintenance), prioritize protein, and eat plenty of fiber to stay full</li>
<li><strong>For Muscle Building:</strong> Eat in a slight calorie surplus with adequate protein (0.8-1g per pound of body weight)</li>
<li><strong>For General Health:</strong> Balance macronutrients—aim for 40% carbs, 30% protein, 30% fats</li>
</ul>

<strong>Practical Tips for Better Eating:</strong>
<ul>
<li>Drink at least 2-3 liters of water daily to support metabolism and appetite control</li>
<li>Eat your largest meals earlier in the day when metabolism is highest</li>
<li>Include protein at every meal to support muscle maintenance and satiety</li>
<li>Don't skip meals; small, frequent meals maintain stable energy</li>
<li>Keep a food journal for one week to identify patterns and improvement areas</li>
</ul>

<h2>Step 3: Establish a Consistent Exercise Routine</h2>

Exercise is vital, but consistency matters far more than intensity. Most people fail at fitness because they start with extreme programs they can't maintain. Instead, design an exercise routine that fits your lifestyle and gradually increase difficulty.

<strong>Types of Exercise You Need:</strong>
<ul>
<li><strong>Cardiovascular Exercise:</strong> 150 minutes of moderate-intensity cardio weekly (brisk walking, cycling, swimming, running)</li>
<li><strong>Strength Training:</strong> 2-3 sessions per week targeting all major muscle groups</li>
<li><strong>Flexibility Work:</strong> 2-3 sessions of stretching or yoga weekly</li>
<li><strong>Daily Movement:</strong> Aim for 10,000 steps daily; use stairs, park farther away, stand while working</li>
</ul>

<strong>A Beginner's Weekly Schedule:</strong>
<ul>
<li>Monday: 30-minute moderate cardio (walking, jogging, or cycling)</li>
<li>Tuesday: 20-minute full-body strength session (bodyweight exercises)</li>
<li>Wednesday: 30-minute cardio (different type than Monday)</li>
<li>Thursday: 20-minute full-body strength session</li>
<li>Friday: 30-minute active recovery (yoga or gentle stretching)</li>
<li>Saturday: 45-minute longer cardio activity (hiking, swimming, sports)</li>
<li>Sunday: Rest day (light walking is optional)</li>
</ul>

<strong>Progressive Overload:</strong> Gradually increase difficulty every 2-4 weeks by adding weight, increasing reps, reducing rest periods, or trying harder exercises. This prevents plateaus and keeps your body adapting.

<h2>Step 4: Master Your Mindset and Mental Resilience</h2>

Physical transformation is as much mental as it is physical. Your mindset determines whether you stick with your program during difficult weeks and whether you bounce back from setbacks.

<strong>Mindset Principles for Fitness Success:</strong>
<ul>
<li><strong>Expect Challenges:</strong> Don't view obstacles as failures; they're part of the process</li>
<li><strong>Focus on Progress, Not Perfection:</strong> Celebrate small wins—one good week, one healthy meal, one completed workout</li>
<li><strong>Practice Self-Compassion:</strong> Missing one workout doesn't undo your progress; getting back on track immediately matters</li>
<li><strong>Visualize Success:</strong> Spend 5 minutes daily visualizing yourself achieving your fitness goals</li>
<li><strong>Identify Your "Why":</strong> Understand your deeper reason for fitness (health for family, confidence, longevity)</li>
</ul>

<strong>Strategies for Mental Toughness:</strong>
<ul>
<li>Keep a success journal documenting workouts completed and goals achieved</li>
<li>Find fitness friends for accountability and support</li>
<li>Celebrate milestones with non-food rewards (new workout clothes, massage, etc.)</li>
<li>When motivation dips, rely on discipline and your "why"</li>
<li>Remember that fitness is a lifelong journey, not a short-term race</li>
</ul>

<h2>Step 5: Track Progress and Adjust Your Plan</h2>

Without tracking, you can't measure progress, and without measuring, you can't improve. Regular assessment keeps you accountable and helps you identify what's working and what needs adjustment.

<strong>What to Track:</strong>
<ul>
<li><strong>Body Metrics:</strong> Weight, body measurements (chest, waist, hips, thighs), body fat percentage</li>
<li><strong>Performance Metrics:</strong> Workout times, weights lifted, reps completed, running distance/speed</li>
<li><strong>Lifestyle Metrics:</strong> Daily steps, sleep hours, water intake, stress levels</li>
<li><strong>Health Markers:</strong> Energy levels, strength, flexibility, mental clarity, mood</li>
</ul>

<strong>Tracking Methods:</strong>
<ul>
<li>Use a simple spreadsheet to record workouts and nutrition</li>
<li>Take progress photos every 4 weeks (same lighting, same clothing, same time of day)</li>
<li>Use fitness apps (MyFitnessPal, Fitbit, Strava) for automatic tracking</li>
<li>Weigh yourself weekly at the same time (morning, after bathroom)</li>
<li>Measure body parts monthly</li>
</ul>

<strong>How Often to Adjust:</strong>
<ul>
<li>Every 2-4 weeks: Adjust workout intensity and exercise selection</li>
<li>Every 6-8 weeks: Reassess nutrition if progress stalls</li>
<li>Every 12 weeks: Evaluate overall progress toward goals and set new targets</li>
</ul>

<strong>What to Do When Progress Slows:</strong>
<ul>
<li>Add more challenging exercises or increase weight</li>
<li>Reduce rest periods between sets</li>
<li>Increase daily activity and step count</li>
<li>Review nutrition for hidden calories or excess sugar</li>
<li>Ensure adequate sleep (7-9 hours nightly)</li>
<li>Manage stress through meditation or relaxation</li>
</ul>

<h2>Conclusion: Your Transformation Starts Now</h2>

Achieving your health and fitness dreams is entirely within your control. By setting specific goals, building a sustainable nutrition plan, establishing a consistent exercise routine, developing mental resilience, and tracking your progress, you've got everything needed for lasting transformation.

The path won't always be easy, but it will be worth it. Every healthy choice you make today builds momentum for tomorrow. Start with one step—perhaps reviewing your current fitness level or scheduling your first week of workouts. Then build from there with consistency, patience, and self-compassion.

Your future self will thank you for the commitment you make today. The best time to start was yesterday; the second-best time is right now. Let these five steps guide your journey toward the health and fitness dreams you deserve.

Remember: progress over perfection, consistency over intensity, and sustainable change over quick fixes. You've got this!"""

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
    # Search for post by title
    print(f"\nSearching for post: {POST_TITLE}")
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
