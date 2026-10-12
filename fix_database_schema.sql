DROP TABLE IF EXISTS topic_rotation_backup;
ALTER TABLE topic_rotation RENAME TO topic_rotation_backup;
DROP TABLE IF EXISTS blog_titles_backup;
ALTER TABLE blog_titles RENAME TO blog_titles_backup;
DROP TABLE IF EXISTS blog_posts_backup;
ALTER TABLE blog_posts RENAME TO blog_posts_backup;
DROP TABLE IF EXISTS trending_keywords_backup;
ALTER TABLE trending_keywords RENAME TO trending_keywords_backup;

CREATE TABLE topic_rotation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(255) NOT NULL UNIQUE,
    cycle_count INT DEFAULT 0,
    sequence_number INT NOT NULL,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blog_titles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_status ENUM('pending', 'used', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (topic_id) REFERENCES topic_rotation(id)
);

CREATE TABLE blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title_id INT NOT NULL,
    topic_id INT NOT NULL,
    content LONGTEXT NOT NULL,
    status ENUM('draft', 'pending', 'published', 'failed') DEFAULT 'draft',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_date TIMESTAMP NULL,
    qa_check_passed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (title_id) REFERENCES blog_titles(id),
    FOREIGN KEY (topic_id) REFERENCES topic_rotation(id)
);

CREATE TABLE trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(255) NOT NULL UNIQUE,
    topic VARCHAR(255) NOT NULL,
    search_volume INT,
    competition_level ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    trend_score DECIMAL(3,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE plagiarism_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    plagiarism_percentage DECIMAL(5,2) DEFAULT 0,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'checked', 'passed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE ai_detection_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    ai_score DECIMAL(5,2) DEFAULT 0,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_method VARCHAR(255),
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE keyword_optimization (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    keyword_density DECIMAL(5,2),
    placement_count INT DEFAULT 0,
    optimization_status ENUM('pending', 'optimized', 'failed') DEFAULT 'pending',
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE image_metadata (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    image_url VARCHAR(500),
    image_alt_text VARCHAR(255),
    image_title VARCHAR(255),
    source_url VARCHAR(500),
    usage_rights VARCHAR(100),
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE image_alt_text (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_metadata_id INT NOT NULL,
    alt_text VARCHAR(500),
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'generated', 'approved') DEFAULT 'pending',
    FOREIGN KEY (image_metadata_id) REFERENCES image_metadata(id)
);

CREATE TABLE qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    format_check BOOLEAN DEFAULT FALSE,
    content_quality_score INT,
    readability_score INT,
    seo_score INT,
    verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE social_media_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    platform VARCHAR(50),
    post_content VARCHAR(500),
    post_url VARCHAR(500),
    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    engagement_count INT DEFAULT 0,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE email_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    subject_line VARCHAR(255),
    email_body LONGTEXT,
    scheduled_date TIMESTAMP,
    sent_date TIMESTAMP,
    open_rate DECIMAL(5,2) DEFAULT 0,
    click_rate DECIMAL(5,2) DEFAULT 0,
    status ENUM('draft', 'scheduled', 'sent') DEFAULT 'draft',
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE email_scheduler (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email_campaign_id INT NOT NULL,
    scheduled_send_time TIMESTAMP,
    actual_send_time TIMESTAMP,
    delivery_status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    FOREIGN KEY (email_campaign_id) REFERENCES email_campaigns(id)
);

CREATE TABLE analytics_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    event_type VARCHAR(100),
    event_value INT,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE headline_testing (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    headline_variant_a VARCHAR(500),
    headline_variant_b VARCHAR(500),
    variant_a_clicks INT DEFAULT 0,
    variant_b_clicks INT DEFAULT 0,
    winner VARCHAR(1),
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE product_research (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    product_name VARCHAR(255),
    product_url VARCHAR(500),
    affiliate_link VARCHAR(500),
    commission_rate DECIMAL(5,2),
    research_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE affiliate_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    affiliate_url VARCHAR(500),
    affiliate_network VARCHAR(100),
    product_category VARCHAR(100),
    injected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    click_count INT DEFAULT 0,
    conversion_count INT DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE wordpress_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    wordpress_post_id VARCHAR(100),
    wordpress_url VARCHAR(500),
    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('published', 'draft', 'scheduled', 'failed') DEFAULT 'draft',
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE social_distribution (
    id INT PRIMARY KEY AUTO_INCREMENT,
    wordpress_post_id INT NOT NULL,
    facebook_url VARCHAR(500),
    twitter_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    instagram_url VARCHAR(500),
    pinterest_url VARCHAR(500),
    distribution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wordpress_post_id) REFERENCES wordpress_posts(id)
);

CREATE TABLE social_engagement (
    id INT PRIMARY KEY AUTO_INCREMENT,
    social_distribution_id INT NOT NULL,
    platform VARCHAR(50),
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    impressions INT DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0,
    checked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (social_distribution_id) REFERENCES social_distribution(id)
);

CREATE TABLE comment_moderation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    wordpress_post_id INT NOT NULL,
    comment_text LONGTEXT,
    comment_author VARCHAR(255),
    comment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT FALSE,
    is_spam BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (wordpress_post_id) REFERENCES wordpress_posts(id)
);

CREATE TABLE content_refresh (
    id INT PRIMARY KEY AUTO_INCREMENT,
    original_post_id INT NOT NULL,
    refreshed_content LONGTEXT,
    refresh_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (original_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE content_revalidation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    revalidation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_still_relevant BOOLEAN DEFAULT TRUE,
    content_update_needed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE plagiarism_recheck (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    original_plagiarism_score DECIMAL(5,2),
    recheck_plagiarism_score DECIMAL(5,2),
    recheck_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('passed', 'failed', 'needs_revision') DEFAULT 'pending',
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE final_qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    final_check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    all_checks_passed BOOLEAN DEFAULT FALSE,
    issues_found VARCHAR(500),
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE static_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT NOT NULL,
    link_url VARCHAR(500),
    link_text VARCHAR(255),
    link_position INT,
    injected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
);

CREATE TABLE system_error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_type VARCHAR(100),
    error_message LONGTEXT,
    robot_name VARCHAR(100),
    error_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes VARCHAR(500),
    error_handler_needed BOOLEAN DEFAULT FALSE
);

CREATE TABLE system_health_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,2),
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threshold_exceeded BOOLEAN DEFAULT FALSE
);

CREATE TABLE automated_rollback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    failed_operation VARCHAR(255),
    rollback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rollback_status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    affected_records INT DEFAULT 0
);

CREATE TABLE master_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    metric_date DATE,
    total_posts_generated INT DEFAULT 0,
    total_posts_published INT DEFAULT 0,
    total_engagement INT DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    system_uptime_percentage DECIMAL(5,2) DEFAULT 100,
    error_count INT DEFAULT 0,
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO topic_rotation (topic_name, sequence_number, is_active) VALUES
('Health and Fitness', 1, TRUE),
('Weight Loss', 2, FALSE),
('Muscle Building', 3, FALSE),
('Nutrition and Diet', 4, FALSE),
('Cardiovascular Health', 5, FALSE),
('Mental Health and Wellness', 6, FALSE),
('Yoga and Flexibility', 7, FALSE),
('High Intensity Training', 8, FALSE),
('Sleep and Recovery', 9, FALSE),
('Joint and Bone Health', 10, FALSE),
('Immune System Boosting', 11, FALSE),
('Energy and Stamina', 12, FALSE),
('Stress Management', 13, FALSE),
('Aging and Longevity', 14, FALSE),
('Sports Performance', 15, FALSE),
('Home Fitness Solutions', 16, FALSE),
('Supplement Guide', 17, FALSE),
('Habit Building and Lifestyle', 18, FALSE);

INSERT INTO trending_keywords (keyword, topic, search_volume, competition_level, trend_score) VALUES
('health and fitness', 'Health and Fitness', 50000, 'High', 8.5),
('fitness tips', 'Health and Fitness', 40000, 'High', 8.2),
('health trends 2026', 'Health and Fitness', 25000, 'Medium', 8.8),
('wellness goals', 'Health and Fitness', 30000, 'Medium', 7.9),
('healthy lifestyle', 'Health and Fitness', 45000, 'High', 8.3),
('weight loss tips', 'Weight Loss', 60000, 'High', 8.7),
('how to lose weight fast', 'Weight Loss', 55000, 'High', 8.9),
('weight loss diet', 'Weight Loss', 50000, 'High', 8.5),
('effective weight loss', 'Weight Loss', 45000, 'Medium', 8.4),
('weight loss motivation', 'Weight Loss', 35000, 'Medium', 8.1),
('muscle building exercises', 'Muscle Building', 42000, 'High', 8.3),
('how to build muscle', 'Muscle Building', 55000, 'High', 8.6),
('muscle growth supplements', 'Muscle Building', 38000, 'Medium', 8.2),
('strength training', 'Muscle Building', 48000, 'High', 8.4),
('muscle building diet', 'Muscle Building', 40000, 'Medium', 8.0),
('nutrition tips', 'Nutrition and Diet', 45000, 'High', 8.3),
('healthy diet plan', 'Nutrition and Diet', 52000, 'High', 8.5),
('nutrition facts', 'Nutrition and Diet', 40000, 'High', 8.1),
('balanced diet', 'Nutrition and Diet', 38000, 'Medium', 7.9),
('meal planning healthy', 'Nutrition and Diet', 35000, 'Medium', 8.2),
('cardiovascular health', 'Cardiovascular Health', 35000, 'Medium', 8.1),
('heart health tips', 'Cardiovascular Health', 40000, 'High', 8.3),
('cardio workouts', 'Cardiovascular Health', 45000, 'High', 8.4),
('blood pressure control', 'Cardiovascular Health', 38000, 'Medium', 8.0),
('cardio exercise benefits', 'Cardiovascular Health', 32000, 'Medium', 7.8),
('mental health tips', 'Mental Health and Wellness', 50000, 'High', 8.6),
('stress relief techniques', 'Mental Health and Wellness', 45000, 'High', 8.5),
('wellness advice', 'Mental Health and Wellness', 38000, 'Medium', 8.2),
('mental wellbeing', 'Mental Health and Wellness', 42000, 'High', 8.3),
('anxiety management', 'Mental Health and Wellness', 48000, 'High', 8.4),
('yoga for beginners', 'Yoga and Flexibility', 48000, 'High', 8.5),
('yoga benefits', 'Yoga and Flexibility', 45000, 'High', 8.4),
('flexibility exercises', 'Yoga and Flexibility', 40000, 'Medium', 8.1),
('yoga poses', 'Yoga and Flexibility', 50000, 'High', 8.6),
('stretching exercises', 'Yoga and Flexibility', 42000, 'Medium', 8.2),
('HIIT workouts', 'High Intensity Training', 48000, 'High', 8.6),
('high intensity interval training', 'High Intensity Training', 45000, 'High', 8.5),
('HIIT exercises', 'High Intensity Training', 42000, 'Medium', 8.2),
('intense workouts', 'High Intensity Training', 38000, 'Medium', 8.0),
('HIIT benefits', 'High Intensity Training', 35000, 'Medium', 7.9),
('sleep tips', 'Sleep and Recovery', 45000, 'High', 8.4),
('better sleep', 'Sleep and Recovery', 50000, 'High', 8.5),
('sleep quality', 'Sleep and Recovery', 40000, 'Medium', 8.1),
('recovery techniques', 'Sleep and Recovery', 38000, 'Medium', 7.9),
('rest and recovery', 'Sleep and Recovery', 42000, 'High', 8.3),
('joint health', 'Joint and Bone Health', 35000, 'Medium', 8.0),
('bone health tips', 'Joint and Bone Health', 38000, 'Medium', 8.1),
('arthritis relief', 'Joint and Bone Health', 42000, 'Medium', 8.2),
('strengthen bones', 'Joint and Bone Health', 40000, 'Medium', 8.0),
('joint pain relief', 'Joint and Bone Health', 45000, 'High', 8.3),
('immune system boost', 'Immune System Boosting', 48000, 'High', 8.5),
('boost immunity', 'Immune System Boosting', 50000, 'High', 8.6),
('immune health tips', 'Immune System Boosting', 42000, 'Medium', 8.2),
('strengthen immunity', 'Immune System Boosting', 45000, 'High', 8.3),
('immune support', 'Immune System Boosting', 38000, 'Medium', 8.0),
('increase energy levels', 'Energy and Stamina', 45000, 'High', 8.3),
('energy boost tips', 'Energy and Stamina', 40000, 'Medium', 8.1),
('stamina building', 'Energy and Stamina', 38000, 'Medium', 7.9),
('natural energy', 'Energy and Stamina', 42000, 'High', 8.2),
('fatigue relief', 'Energy and Stamina', 35000, 'Medium', 7.8),
('stress management tips', 'Stress Management', 50000, 'High', 8.5),
('how to manage stress', 'Stress Management', 48000, 'High', 8.4),
('stress relief', 'Stress Management', 52000, 'High', 8.6),
('anxiety relief', 'Stress Management', 45000, 'High', 8.3),
('relaxation techniques', 'Stress Management', 42000, 'High', 8.2),
('healthy aging', 'Aging and Longevity', 38000, 'Medium', 8.0),
('longevity tips', 'Aging and Longevity', 35000, 'Medium', 7.9),
('anti-aging strategies', 'Aging and Longevity', 42000, 'High', 8.2),
('aging well', 'Aging and Longevity', 40000, 'Medium', 8.1),
('lifespan extension', 'Aging and Longevity', 32000, 'Low', 7.7),
('sports performance', 'Sports Performance', 40000, 'High', 8.2),
('athletic performance tips', 'Sports Performance', 38000, 'Medium', 8.0),
('sports training', 'Sports Performance', 45000, 'High', 8.3),
('athlete fitness', 'Sports Performance', 42000, 'Medium', 8.1),
('performance enhancement', 'Sports Performance', 35000, 'Medium', 7.9),
('home workouts', 'Home Fitness Solutions', 55000, 'High', 8.7),
('home fitness equipment', 'Home Fitness Solutions', 48000, 'High', 8.5),
('workout at home', 'Home Fitness Solutions', 52000, 'High', 8.6),
('home gym setup', 'Home Fitness Solutions', 45000, 'High', 8.4),
('indoor exercises', 'Home Fitness Solutions', 40000, 'Medium', 8.1),
('supplement guide', 'Supplement Guide', 42000, 'High', 8.2),
('health supplements', 'Supplement Guide', 45000, 'High', 8.3),
('vitamin supplements', 'Supplement Guide', 40000, 'Medium', 8.0),
('supplement recommendations', 'Supplement Guide', 38000, 'Medium', 7.9),
('best supplements', 'Supplement Guide', 48000, 'High', 8.4),
('habit building', 'Habit Building and Lifestyle', 45000, 'High', 8.3),
('lifestyle changes', 'Habit Building and Lifestyle', 40000, 'Medium', 8.1),
('healthy habits', 'Habit Building and Lifestyle', 50000, 'High', 8.5),
('daily routines', 'Habit Building and Lifestyle', 42000, 'Medium', 8.2),
('lifestyle tips', 'Habit Building and Lifestyle', 38000, 'Medium', 7.9);

CREATE INDEX idx_blog_posts_topic ON blog_posts(topic_id);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_trending_keywords_topic ON trending_keywords(topic);
CREATE INDEX idx_social_media_posts_platform ON social_media_posts(platform);
CREATE INDEX idx_analytics_events_blog_post ON analytics_events(blog_post_id);
CREATE INDEX idx_wordpress_posts_status ON wordpress_posts(status);
