#!/usr/bin/env python3
"""Direct database cleanup for Post 1 - removes all artifacts and old content"""

import os
import sys
import mysql.connector
from mysql.connector import Error

# Enhanced content - Clean version
ENHANCED_CONTENT = """<p><span style="color: #0066cc;"><strong>Transform Your Health and Fitness Journey: The Complete Guide to Achieving Your Dreams</strong></span></p>

<p>Your health is your wealth. Yet for millions of people, the journey from aspiration to achievement remains frustratingly out of reach. If you're reading this, you've likely felt that gap—the distance between where you are and where you want to be. The good news? <span style="color: #d9534f;">That gap is completely bridgeable.</span> Thousands have successfully transformed their health and fitness through strategic planning, consistent execution, and the right guidance. This comprehensive guide reveals the exact framework that separates successful transformations from failed attempts. Whether you're starting from zero fitness experience, recovering from injury, or looking to break through a plateau, the principles in this guide apply to your unique situation.</p>

<h2><span style="color: #5cb85c;">Foundation Phase: Why Most People Fail (And How You Won't)</span></h2>

<p>Before diving into the five essential steps, understand this critical truth: <strong>88% of New Year's resolutions fail by mid-February</strong>. Why? People skip the foundation phase. They jump straight to action without clarity, strategy, or sustainable systems. This is why you'll notice our approach differs fundamentally from typical fitness guides—we build from the ground up.</p>

<p>The most successful transformations share one common element: <span style="color: #0066cc;"><strong>absolute clarity on the destination before taking a single step</strong></span>. Your mind, your body, and your circumstances all need alignment. When they are, transformation becomes inevitable rather than aspirational.</p>

<p>Research from Stanford University shows that people who establish a clear "why" are <strong>10 times more likely to achieve their fitness goals</strong> than those who don't. This foundation phase is where that "why" gets crystallized. Too many people focus exclusively on the "what" (lose 20 pounds) without understanding the "why" (so I can play with my kids without getting winded, or feel confident in my own skin). The difference is profound—when your motivation is rooted in genuine emotional desire rather than external pressure, consistency becomes natural.</p>

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

<p><strong>Example Goals That Work:</strong></p>
<ul>
<li>"Complete 3 strength training sessions per week for the next 16 weeks, with progressive weight increases every 2 weeks"</li>
<li>"Reduce body fat percentage from 32% to 26% in 16 weeks through consistent nutrition and training"</li>
<li>"Run a continuous 5K (3.1 miles) without stopping by week 12, then maintain that fitness level through week 16"</li>
</ul>

<p>Notice these goals aren't vague wishes—they're specific deliverables with measurement points. The brain responds to clarity. When it knows exactly what you're aiming for, it starts working behind the scenes (even while you sleep!) to move you toward that goal.</p>

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
The 80/20 rule works: 80% disciplined nutrition, 20% flexible indulgence. This maintains results while preventing the deprivation cycle that kills most diets. Plan your meals weekly. Prep on Sundays. This removes daily decision fatigue and supports consistency. The psychology here matters: when you allow yourself intentional, guilt-free indulgence 20% of the time, you're far less likely to binge on that other 80%. Your brain doesn't feel deprived, so willpower becomes easier to maintain.</p>

<p><strong>Practical Meal Prep Strategy:</strong> Dedicate 2-3 hours on Sunday to prepare protein, grains, and vegetables for the week. Store them in portion-controlled containers. When you arrive home hungry, grab a prepared meal instead of ordering takeout. Studies show meal preppers are 68% more likely to hit their nutrition targets compared to those who plan meals day-by-day.</p>

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
Never stay on the same program for more than 4 weeks. Every 2-4 weeks, increase difficulty by: adding weight, increasing reps, reducing rest periods, or advancing exercise variations. This prevents plateaus and keeps your body adapting. Your muscles adapt remarkably quickly—what feels challenging in week 1 feels routine by week 4. This is actually good news: it means your body is getting stronger. But it also means you must continually challenge it to see continued improvement.</p>

<p><strong>Example Progression Schedule:</strong></p>
<ul>
<li><strong>Weeks 1-2:</strong> Focus on form and consistency (3 sets of 8-12 reps per exercise)</li>
<li><strong>Weeks 3-4:</strong> Add 5-10% more weight to your lifts</li>
<li><strong>Weeks 5-6:</strong> Increase to 4 sets per exercise or reduce rest between sets</li>
<li><strong>Weeks 7-8:</strong> Advance exercise variations (barbell to dumbbell, or add single-leg variations)</li>
</ul>

<h3><span style="color: #ff7f50;"><strong>Foundation Four: Mental Resilience & Behavioral Mastery</strong></span></h3>

<p>Physical transformation is 40% physical and 60% mental. Your mindset determines whether you stick through difficult weeks, whether you bounce back from setbacks, and whether you eventually reach your destination.</p>

<p><strong>Mental Foundations That Work:</strong></p>
<ul>
<li><strong>Reframe Challenges:</strong> View obstacles as part of the process, not failures. Missing one workout doesn't undo your progress. Getting back on track immediately does. This is the difference between a temporary slip and a permanent derailment—your response to the slip determines which it becomes.</li>
<li><strong>Celebrate Small Wins:</strong> One completed workout, one healthy meal choice, one day of consistency—these compound into transformation. Your brain releases dopamine when you achieve small wins, which reinforces the behavior. You're literally rewiring your neural pathways toward health.</li>
<li><strong>Develop Your "Why":</strong> Understanding your deeper reason (health for family, confidence, longevity, performance) sustains motivation when initial enthusiasm fades. Write this down. When you face a difficult workout or a tempting food choice, that "why" becomes your north star.</li>
<li><strong>Visualization Practice:</strong> Spend 5 minutes daily visualizing yourself achieving your goals, feeling the emotions, imagining the benefits. This primes your subconscious for success. Olympic athletes and Navy SEALs use visualization routinely—it's not mystical, it's neuroscience.</li>
<li><strong>Build Accountability:</strong> Find a fitness partner, join a community, or hire a coach. External accountability increases follow-through by 65%. When someone else is counting on you (or vice versa), you're far more likely to show up.</li>
</ul>

<p><strong>The Self-Compassion Component:</strong> Be as kind to yourself during this journey as you'd be to a friend attempting the same transformation. Research shows that self-criticism actually undermines progress by increasing cortisol (stress hormone) and reducing motivation. Self-compassion, on the other hand, predicts long-term adherence better than any other single factor.</p>

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
Increase exercise difficulty. Reduce rest periods between sets. Increase daily movement. Review nutrition for hidden calories. Ensure adequate sleep. Manage stress through meditation. Progress slows naturally over time, but these adjustments restart forward movement. This phenomenon is called a "plateau," and it's actually a sign that your body has adapted to your stimulus—which means your program was working! The solution is simply to provide a new stimulus.</p>

<p><strong>Plateau-Breaking Strategies:</strong> If you've been doing the same routine for 6-8 weeks with no change in metrics, try one of these: (1) Change your exercise selection entirely (if you've been doing bench press, try incline press or dumbbells), (2) Increase volume by 20% (more total reps across all exercises), (3) Decrease rest periods by 30-50%, or (4) Take a deload week (40% lighter loads) to allow your nervous system to recover, then return stronger.</p>

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

<p><span style="color: #d9534f;"><strong>Your health is the one investment that pays dividends forever.</strong></span> Not just in the form of a better body, but in the form of more energy for your family, more confidence in yourself, more resilience during difficult times, and a longer, higher-quality life.</p>

<h2><span style="color: #5cb85c;">Bonus: Common Obstacles & How to Overcome Them</span></h2>

<p>Every person encounters obstacles on their fitness journey. Here's how to navigate the most common ones:</p>

<p><strong>"I don't have time to work out."</strong> Start with 20 minutes, 3 days per week. That's just 1 hour per week—roughly equivalent to one TV show. As consistency builds, you naturally find more time. But starting small removes the barrier to entry.</p>

<p><strong>"I've tried before and always fail."</strong> Previous attempts failed not because you lack willpower, but because you lacked a system. This framework provides the system. Follow it exactly for 16 weeks without modification, then assess results.</p>

<p><strong>"Healthy food is expensive."</strong> Whole foods (rice, beans, eggs, seasonal vegetables) are actually cheaper than processed foods when you buy in bulk and meal prep. A cost comparison: $3 fast food meal vs. $1.50 homemade meal with better nutrition.</p>

<p><strong>"I don't know how to exercise correctly."</strong> Start with bodyweight exercises or light weights, film yourself, watch tutorial videos, and adjust form. Perfection isn't required—consistency is. Your form improves naturally as you practice.</p>

<p><strong>"My metabolism is slow."</strong> Metabolism is partially genetic but largely controlled by muscle mass and activity level. Build muscle through strength training, and your metabolism increases. The process starts immediately.</p>

<h2><span style="color: #5cb85c;">Final Truth: You're Not Waiting for Motivation, You're Building Momentum</span></h2>

<p>Motivation is unreliable. It comes and goes like the weather. Discipline is unstoppable—it's a choice you make regardless of how you feel. The magic happens when discipline builds momentum, and momentum generates genuine motivation that feels effortless.</p>

<p>Start today with one action from each foundation. Tomorrow, add another. Within weeks, you'll have built unstoppable momentum. Within months, transformation becomes visible in the mirror and in how others respond to you. Within a year, you'll hardly recognize your former self—and more importantly, you won't recognize how much that transformation ripples into every other area of your life.</p>

<p>The best time to start was yesterday. The second-best time is today. Right now, this moment, you can choose progress over perfection, consistency over intensity, and sustainable change over quick fixes. That choice compounds.</p>

<p><strong><span style="color: #0066cc;">Your health and fitness dreams are not just possible—they're inevitable with the right system, consistency, and commitment. The framework in this guide works if you work it. Start now. Do the work. In 16 weeks, you'll have proof that transformation is real and that you're capable of it. The future version of you—stronger, healthier, more confident—will thank you for the decision you make today.</span></strong></p>"""

print("=" * 80)
print("DIRECT DATABASE CLEANUP - POST 1")
print("=" * 80)

# Get database credentials
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', '')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', '')

if not db_user:
    print("❌ Database credentials not set (DB_USER, DB_PASSWORD, DB_NAME)")
    sys.exit(1)

try:
    # Connect to database
    print(f"\nConnecting to database: {db_host}/{db_name}...")
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    if connection.is_connected():
        db_info = connection.get_server_info()
        print(f"✅ Connected to MySQL Server version {db_info}")

        cursor = connection.cursor()

        # Find the post by slug
        post_slug = "5-complete-steps-to-achieve-your-health-and-fitness-dreams"
        query = f"SELECT ID, post_title, post_content FROM wp_posts WHERE post_name = %s AND post_type = 'post'"
        cursor.execute(query, (post_slug,))
        post = cursor.fetchone()

        if post:
            post_id, post_title, old_content = post
            old_words = len(old_content.split())

            print(f"✅ Found Post ID {post_id}")
            print(f"   Title: {post_title}")
            print(f"   Current words: {old_words}")

            # Update with clean content
            print(f"\n🔄 Updating post content (removing all artifacts)...")
            update_query = "UPDATE wp_posts SET post_content = %s WHERE ID = %s"
            cursor.execute(update_query, (ENHANCED_CONTENT, post_id))
            connection.commit()

            # Verify update
            cursor.execute("SELECT post_content FROM wp_posts WHERE ID = %s", (post_id,))
            result = cursor.fetchone()

            if result:
                new_content = result[0]
                new_words = len(new_content.split())
                has_artifacts = '`html' in new_content or '```' in new_content

                print(f"\n✅ Update complete!")
                print(f"   Old: {old_words} words")
                print(f"   New: {new_words} words")
                print(f"   Artifacts: {'❌ DETECTED' if has_artifacts else '✅ CLEAN'}")

                if not has_artifacts:
                    print(f"\n✅ POST 1 CLEANED: {new_words} words, zero artifacts, ready for WordPress")
                else:
                    print(f"\n⚠️ WARNING: Still has artifacts after database update")
        else:
            print(f"❌ Post not found with slug: {post_slug}")
            sys.exit(1)

        cursor.close()

except Error as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

finally:
    if connection.is_connected():
        connection.close()
        print("\n✅ Database connection closed")
