SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE IF NOT EXISTS topic_rotation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(255) NOT NULL UNIQUE
);

ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS cycle_number INT DEFAULT 1;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS topic_sequence INT;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS start_date DATE;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS cycle_day INT;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS current_topic VARCHAR(255);
ALTER TABLE topic_rotation ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS trending_keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(255) NOT NULL UNIQUE,
    topic VARCHAR(255) NOT NULL
);

ALTER TABLE trending_keywords ADD COLUMN IF NOT EXISTS search_volume INT;
ALTER TABLE trending_keywords ADD COLUMN IF NOT EXISTS competition_level ENUM('Low', 'Medium', 'High') DEFAULT 'Medium';
ALTER TABLE trending_keywords ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE trending_keywords ADD COLUMN IF NOT EXISTS trend_direction VARCHAR(50);
ALTER TABLE trending_keywords ADD COLUMN IF NOT EXISTS trend_score DECIMAL(3,1);

CREATE TABLE IF NOT EXISTS blog_titles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL
);

ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS topic VARCHAR(255);
ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS keywords VARCHAR(500);
ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS ctr_score DECIMAL(5,2) DEFAULT 0;
ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS used BOOLEAN DEFAULT FALSE;
ALTER TABLE blog_titles ADD COLUMN IF NOT EXISTS used_at TIMESTAMP NULL;

CREATE TABLE IF NOT EXISTS blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500),
    topic VARCHAR(255),
    content LONGTEXT
);

ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS status ENUM('draft', 'pending', 'published', 'failed') DEFAULT 'draft';
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS plagiarism_score DECIMAL(5,2) DEFAULT 0;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS ai_detection_score DECIMAL(5,2) DEFAULT 0;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS published_at TIMESTAMP NULL;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS published_to_wordpress_at TIMESTAMP NULL;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS qa_check_passed BOOLEAN DEFAULT FALSE;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS qa_check_report LONGTEXT;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS rollback_reason VARCHAR(500);
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS rollback_required_at TIMESTAMP NULL;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS slug VARCHAR(500);
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS wordpress_post_id VARCHAR(100);
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS word_count INT DEFAULT 0;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS publish_date DATE;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS error_handler_needed BOOLEAN DEFAULT FALSE;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS error_message LONGTEXT;
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);

CREATE TABLE IF NOT EXISTS version_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    version INT,
    content LONGTEXT,
    robot_modified_by VARCHAR(100),
    change_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plagiarism_check_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    plagiarism_score DECIMAL(5,2),
    check_type VARCHAR(100),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_plagiarized BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS ai_detection_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    ai_score DECIMAL(5,2) DEFAULT 0,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_method VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS keyword_optimization (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    keyword VARCHAR(255),
    keyword_density DECIMAL(5,2),
    placement_count INT DEFAULT 0,
    optimization_status ENUM('pending', 'optimized', 'failed') DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS image_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    image_url VARCHAR(500),
    alt_text VARCHAR(500),
    title VARCHAR(255),
    topic VARCHAR(255),
    source VARCHAR(255),
    used_date TIMESTAMP NULL,
    expires_date DATE
);

CREATE TABLE IF NOT EXISTS image_alt_text (
    id INT PRIMARY KEY AUTO_INCREMENT,
    image_metadata_id INT,
    alt_text VARCHAR(500),
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'generated', 'approved') DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    format_check BOOLEAN DEFAULT FALSE,
    content_quality_score INT,
    readability_score INT,
    seo_score INT,
    verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS final_qa_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    all_checks_passed BOOLEAN DEFAULT FALSE,
    qa_data LONGTEXT,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_media_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    content VARCHAR(500),
    status VARCHAR(50),
    hashtags VARCHAR(500),
    word_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_engagement_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    post_id VARCHAR(100),
    engagement_type VARCHAR(100),
    engagement_count INT DEFAULT 0,
    metrics_json LONGTEXT,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_engagement_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_ids VARCHAR(500),
    content_html LONGTEXT,
    content_hash VARCHAR(255),
    status ENUM('draft', 'scheduled', 'sent') DEFAULT 'draft',
    newsletter_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_scheduler (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email_campaign_id INT,
    scheduled_send_time TIMESTAMP NULL,
    actual_send_time TIMESTAMP NULL,
    delivery_status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    retry_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS email_send_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    newsletter_id INT,
    subscriber_id VARCHAR(100),
    status VARCHAR(50),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_tracking_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    newsletter_id INT,
    subscriber_id VARCHAR(100),
    event_type VARCHAR(100),
    clicked_link VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    event_type VARCHAR(100),
    event_value INT,
    event_data LONGTEXT,
    affiliate_product_id INT,
    newsletter_id INT,
    subscriber_id VARCHAR(100),
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS headline_testing (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    headline_variant_a VARCHAR(500),
    headline_variant_b VARCHAR(500),
    variant_a_clicks INT DEFAULT 0,
    variant_b_clicks INT DEFAULT 0,
    winner VARCHAR(1),
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS headline_confirmations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    headline_text VARCHAR(500),
    headline_analysis LONGTEXT,
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_research (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    product_name VARCHAR(255),
    product_url VARCHAR(500),
    affiliate_link VARCHAR(500),
    commission_rate DECIMAL(5,2),
    research_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS affiliate_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_name VARCHAR(255),
    product_url VARCHAR(500),
    description LONGTEXT,
    commission_rate DECIMAL(5,2),
    advertiser VARCHAR(255),
    source_network VARCHAR(100),
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS affiliate_search_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    topic VARCHAR(255),
    search_terms VARCHAR(500),
    triggered_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS affiliate_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_name VARCHAR(255),
    placement_position INT,
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS static_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    link_url VARCHAR(500),
    link_text VARCHAR(255),
    link_position INT,
    injected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS link_injection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    injection_type VARCHAR(100),
    links_count INT,
    placement_zone VARCHAR(100),
    injected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wordpress_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    wordpress_post_id VARCHAR(100),
    wordpress_url VARCHAR(500),
    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('published', 'draft', 'scheduled', 'failed') DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS wordpress_publication_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    wordpress_post_id VARCHAR(100),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wordpress_comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    content LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wordpress_responses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    comment_id INT,
    response_text LONGTEXT,
    is_automated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wordpress_connection_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    status VARCHAR(50),
    health_score DECIMAL(3,2),
    site_health VARCHAR(50),
    posts_endpoint VARCHAR(50),
    categories_endpoint VARCHAR(50),
    post_creation VARCHAR(50),
    auth_check VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_distribution_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    platform VARCHAR(50),
    social_post_id VARCHAR(100),
    status VARCHAR(50),
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comment_moderation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    comment_text LONGTEXT,
    comment_author VARCHAR(255),
    comment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT FALSE,
    is_spam BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS comment_response_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    response_text LONGTEXT,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_refresh_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    refresh_type VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS refresh_workflow_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    current_stage VARCHAR(100),
    workflow_sequence INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_revalidation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    revalidation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_still_relevant BOOLEAN DEFAULT TRUE,
    content_update_needed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS plagiarism_recheck (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    original_plagiarism_score DECIMAL(5,2),
    recheck_plagiarism_score DECIMAL(5,2),
    recheck_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'passed', 'failed', 'needs_revision') DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS final_qa_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_post_id INT,
    final_check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    all_checks_passed BOOLEAN DEFAULT FALSE,
    issues_found VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS system_error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_type VARCHAR(100),
    error_message LONGTEXT,
    robot_name VARCHAR(100),
    error_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes VARCHAR(500),
    error_handler_needed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS error_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    error_type VARCHAR(100),
    severity VARCHAR(50),
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_successful BOOLEAN DEFAULT FALSE,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_health_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,2),
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threshold_exceeded BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    snapshot_data LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automated_rollback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    rollback_reason VARCHAR(255),
    rollback_version INT,
    rollback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rollback_status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    rollback_successful BOOLEAN DEFAULT FALSE,
    rolled_back_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS rollback_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    rollback_reason VARCHAR(255),
    rollback_version INT,
    rollback_successful BOOLEAN DEFAULT FALSE,
    rolled_back_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS isolation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    isolation_reason VARCHAR(255),
    isolated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coordinator_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    coordinator_id VARCHAR(100),
    status VARCHAR(50),
    robots_locked INT DEFAULT 0,
    conflicts_resolved INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS robot_locks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    lock_holder VARCHAR(100),
    lock_reason VARCHAR(255),
    lock_expires_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS robot_execution_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    robot_name VARCHAR(100),
    execution_time_seconds DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS digital_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    product_name VARCHAR(255),
    price DECIMAL(10,2),
    pdf_url VARCHAR(500),
    woocommerce_product_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retrofit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    status VARCHAR(50),
    details LONGTEXT,
    completed_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS page_view_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blog_id INT,
    page_url VARCHAR(500),
    user_session_id VARCHAR(100),
    time_on_page INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(100),
    report_data LONGTEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_category_mapping (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(255),
    wordpress_category_id VARCHAR(100)
);

INSERT IGNORE INTO topic_rotation (topic_name, status, cycle_number, topic_sequence, is_active) VALUES
('Health and Fitness', 'active', 1, 1, TRUE),
('Weight Loss', 'inactive', 1, 2, FALSE),
('Muscle Building', 'inactive', 1, 3, FALSE),
('Nutrition and Diet', 'inactive', 1, 4, FALSE),
('Cardiovascular Health', 'inactive', 1, 5, FALSE),
('Mental Health and Wellness', 'inactive', 1, 6, FALSE),
('Yoga and Flexibility', 'inactive', 1, 7, FALSE),
('High Intensity Training', 'inactive', 1, 8, FALSE),
('Sleep and Recovery', 'inactive', 1, 9, FALSE),
('Joint and Bone Health', 'inactive', 1, 10, FALSE),
('Immune System Boosting', 'inactive', 1, 11, FALSE),
('Energy and Stamina', 'inactive', 1, 12, FALSE),
('Stress Management', 'inactive', 1, 13, FALSE),
('Aging and Longevity', 'inactive', 1, 14, FALSE),
('Sports Performance', 'inactive', 1, 15, FALSE),
('Home Fitness Solutions', 'inactive', 1, 16, FALSE),
('Supplement Guide', 'inactive', 1, 17, FALSE),
('Habit Building and Lifestyle', 'inactive', 1, 18, FALSE);

INSERT IGNORE INTO trending_keywords (keyword, topic, search_volume, competition_level, trend_direction, trend_score) VALUES
('health and fitness', 'Health and Fitness', 50000, 'High', 'up', 8.5),
('fitness tips', 'Health and Fitness', 40000, 'High', 'up', 8.2),
('health trends 2026', 'Health and Fitness', 25000, 'Medium', 'up', 8.8),
('wellness goals', 'Health and Fitness', 30000, 'Medium', 'stable', 7.9),
('healthy lifestyle', 'Health and Fitness', 45000, 'High', 'up', 8.3),
('weight loss tips', 'Weight Loss', 60000, 'High', 'up', 8.7),
('how to lose weight fast', 'Weight Loss', 55000, 'High', 'up', 8.9),
('weight loss diet', 'Weight Loss', 50000, 'High', 'stable', 8.5),
('effective weight loss', 'Weight Loss', 45000, 'Medium', 'up', 8.4),
('weight loss motivation', 'Weight Loss', 35000, 'Medium', 'stable', 8.1),
('muscle building exercises', 'Muscle Building', 42000, 'High', 'up', 8.3),
('how to build muscle', 'Muscle Building', 55000, 'High', 'up', 8.6),
('muscle growth supplements', 'Muscle Building', 38000, 'Medium', 'up', 8.2),
('strength training', 'Muscle Building', 48000, 'High', 'stable', 8.4),
('muscle building diet', 'Muscle Building', 40000, 'Medium', 'stable', 8.0),
('nutrition tips', 'Nutrition and Diet', 45000, 'High', 'up', 8.3),
('healthy diet plan', 'Nutrition and Diet', 52000, 'High', 'stable', 8.5),
('nutrition facts', 'Nutrition and Diet', 40000, 'High', 'stable', 8.1),
('balanced diet', 'Nutrition and Diet', 38000, 'Medium', 'stable', 7.9),
('meal planning healthy', 'Nutrition and Diet', 35000, 'Medium', 'up', 8.2),
('cardiovascular health', 'Cardiovascular Health', 35000, 'Medium', 'stable', 8.1),
('heart health tips', 'Cardiovascular Health', 40000, 'High', 'up', 8.3),
('cardio workouts', 'Cardiovascular Health', 45000, 'High', 'stable', 8.4),
('blood pressure control', 'Cardiovascular Health', 38000, 'Medium', 'stable', 8.0),
('cardio exercise benefits', 'Cardiovascular Health', 32000, 'Medium', 'stable', 7.8),
('mental health tips', 'Mental Health and Wellness', 50000, 'High', 'up', 8.6),
('stress relief techniques', 'Mental Health and Wellness', 45000, 'High', 'up', 8.5),
('wellness advice', 'Mental Health and Wellness', 38000, 'Medium', 'stable', 8.2),
('mental wellbeing', 'Mental Health and Wellness', 42000, 'High', 'up', 8.3),
('anxiety management', 'Mental Health and Wellness', 48000, 'High', 'stable', 8.4),
('yoga for beginners', 'Yoga and Flexibility', 48000, 'High', 'up', 8.5),
('yoga benefits', 'Yoga and Flexibility', 45000, 'High', 'stable', 8.4),
('flexibility exercises', 'Yoga and Flexibility', 40000, 'Medium', 'up', 8.1),
('yoga poses', 'Yoga and Flexibility', 50000, 'High', 'stable', 8.6),
('stretching exercises', 'Yoga and Flexibility', 42000, 'Medium', 'stable', 8.2),
('HIIT workouts', 'High Intensity Training', 48000, 'High', 'up', 8.6),
('high intensity interval training', 'High Intensity Training', 45000, 'High', 'stable', 8.5),
('HIIT exercises', 'High Intensity Training', 42000, 'Medium', 'up', 8.2),
('intense workouts', 'High Intensity Training', 38000, 'Medium', 'stable', 8.0),
('HIIT benefits', 'High Intensity Training', 35000, 'Medium', 'stable', 7.9),
('sleep tips', 'Sleep and Recovery', 45000, 'High', 'up', 8.4),
('better sleep', 'Sleep and Recovery', 50000, 'High', 'stable', 8.5),
('sleep quality', 'Sleep and Recovery', 40000, 'Medium', 'up', 8.1),
('recovery techniques', 'Sleep and Recovery', 38000, 'Medium', 'stable', 7.9),
('rest and recovery', 'Sleep and Recovery', 42000, 'High', 'stable', 8.3),
('joint health', 'Joint and Bone Health', 35000, 'Medium', 'stable', 8.0),
('bone health tips', 'Joint and Bone Health', 38000, 'Medium', 'up', 8.1),
('arthritis relief', 'Joint and Bone Health', 42000, 'Medium', 'stable', 8.2),
('strengthen bones', 'Joint and Bone Health', 40000, 'Medium', 'stable', 8.0),
('joint pain relief', 'Joint and Bone Health', 45000, 'High', 'up', 8.3),
('immune system boost', 'Immune System Boosting', 48000, 'High', 'up', 8.5),
('boost immunity', 'Immune System Boosting', 50000, 'High', 'up', 8.6),
('immune health tips', 'Immune System Boosting', 42000, 'Medium', 'stable', 8.2),
('strengthen immunity', 'Immune System Boosting', 45000, 'High', 'up', 8.3),
('immune support', 'Immune System Boosting', 38000, 'Medium', 'stable', 8.0),
('increase energy levels', 'Energy and Stamina', 45000, 'High', 'up', 8.3),
('energy boost tips', 'Energy and Stamina', 40000, 'Medium', 'stable', 8.1),
('stamina building', 'Energy and Stamina', 38000, 'Medium', 'stable', 7.9),
('natural energy', 'Energy and Stamina', 42000, 'High', 'up', 8.2),
('fatigue relief', 'Energy and Stamina', 35000, 'Medium', 'stable', 7.8),
('stress management tips', 'Stress Management', 50000, 'High', 'up', 8.5),
('how to manage stress', 'Stress Management', 48000, 'High', 'stable', 8.4),
('stress relief', 'Stress Management', 52000, 'High', 'up', 8.6),
('anxiety relief', 'Stress Management', 45000, 'High', 'stable', 8.3),
('relaxation techniques', 'Stress Management', 42000, 'High', 'up', 8.2),
('healthy aging', 'Aging and Longevity', 38000, 'Medium', 'stable', 8.0),
('longevity tips', 'Aging and Longevity', 35000, 'Medium', 'stable', 7.9),
('anti-aging strategies', 'Aging and Longevity', 42000, 'High', 'up', 8.2),
('aging well', 'Aging and Longevity', 40000, 'Medium', 'stable', 8.1),
('lifespan extension', 'Aging and Longevity', 32000, 'Low', 'stable', 7.7),
('sports performance', 'Sports Performance', 40000, 'High', 'up', 8.2),
('athletic performance tips', 'Sports Performance', 38000, 'Medium', 'stable', 8.0),
('sports training', 'Sports Performance', 45000, 'High', 'stable', 8.3),
('athlete fitness', 'Sports Performance', 42000, 'Medium', 'up', 8.1),
('performance enhancement', 'Sports Performance', 35000, 'Medium', 'stable', 7.9),
('home workouts', 'Home Fitness Solutions', 55000, 'High', 'up', 8.7),
('home fitness equipment', 'Home Fitness Solutions', 48000, 'High', 'up', 8.5),
('workout at home', 'Home Fitness Solutions', 52000, 'High', 'stable', 8.6),
('home gym setup', 'Home Fitness Solutions', 45000, 'High', 'up', 8.4),
('indoor exercises', 'Home Fitness Solutions', 40000, 'Medium', 'stable', 8.1),
('supplement guide', 'Supplement Guide', 42000, 'High', 'up', 8.2),
('health supplements', 'Supplement Guide', 45000, 'High', 'stable', 8.3),
('vitamin supplements', 'Supplement Guide', 40000, 'Medium', 'stable', 8.0),
('supplement recommendations', 'Supplement Guide', 38000, 'Medium', 'stable', 7.9),
('best supplements', 'Supplement Guide', 48000, 'High', 'up', 8.4),
('habit building', 'Habit Building and Lifestyle', 45000, 'High', 'up', 8.3),
('lifestyle changes', 'Habit Building and Lifestyle', 40000, 'Medium', 'stable', 8.1),
('healthy habits', 'Habit Building and Lifestyle', 50000, 'High', 'up', 8.5),
('daily routines', 'Habit Building and Lifestyle', 42000, 'Medium', 'stable', 8.2),
('lifestyle tips', 'Habit Building and Lifestyle', 38000, 'Medium', 'stable', 7.9);

SET FOREIGN_KEY_CHECKS=1;
