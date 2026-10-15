-- R8 writes featured_image_alt_text to blog_posts, but no earlier migration created it.
-- Without this column, R8's alt-text save fails and posts can miss their featured image alt text.
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS featured_image_alt_text TEXT;
