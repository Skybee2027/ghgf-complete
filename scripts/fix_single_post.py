#!/usr/bin/env python3
"""
One-off fix for a single blog post. Changes exactly one row, identified by slug or title.

Steps (all-or-nothing; any failure aborts before writing):
  1. Find the post. Abort unless exactly one row matches.
  2. Back up the original content to fixes/backup-<id>.html (for rollback).
  3. Clean the new body with robots/content_sanitizer.py. Abort on any problem.
  4. Find a licensed image via R7's search (Pexels, Unsplash, Pixabay). Abort if none.
  5. Insert the image after the first paragraph, record it in image_tracking,
     set featured_image_id and featured_image_alt_text.
  6. Write content + image fields to blog_posts. Status and publish flags are NOT changed.

WordPress is not touched. Publishing is a separate step after review.
Use --dry-run to run every check without writing.
"""

import argparse
import html
import os
import shutil
import sys
from datetime import datetime, timedelta

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "robots"))

import mysql.connector  # noqa: E402
from content_sanitizer import clean_content  # noqa: E402
from r7_image_finder import ImageFinderEnhanced  # noqa: E402


def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=False,
        connection_timeout=30,
    )


def find_post(conn, slug, title_hint):
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT id, title, slug, content, status, featured_image_id, featured_image_alt_text
           FROM blog_posts WHERE slug = %s""",
        (slug,),
    )
    rows = cur.fetchall()
    if not rows and title_hint:
        cur.execute(
            """SELECT id, title, slug, content, status, featured_image_id, featured_image_alt_text
               FROM blog_posts WHERE title LIKE %s""",
            (f"%{title_hint}%",),
        )
        rows = cur.fetchall()
    cur.close()
    if len(rows) != 1:
        raise SystemExit(f"ABORT: expected exactly 1 matching post, found {len(rows)}")
    return rows[0]


def find_image(title, used_urls):
    finder = ImageFinderEnhanced()
    query = "health fitness wellness healthy lifestyle"
    for search in (finder.search_pexels, finder.search_unsplash, finder.search_pixabay):
        try:
            results = search(query, exclude_urls=used_urls)
        except Exception as exc:  # a failing provider should not stop the others
            print(f"  provider error: {exc}")
            continue
        for img in results or []:
            if img.get("url", "").startswith("https://"):
                return img
    return None


def used_image_urls(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT it.image_url FROM blog_posts bp
           JOIN image_tracking it ON bp.featured_image_id = it.id"""
    )
    urls = {r[0] for r in cur.fetchall()}
    cur.close()
    return urls


def insert_image(body, img, alt):
    credit = img.get("credit") or img.get("title") or ""
    figure = (
        f'<figure><img src="{html.escape(img["url"])}" alt="{html.escape(alt)}" />'
        f"<figcaption>{html.escape(credit)}</figcaption></figure>"
    )
    end = body.find("</p>")
    if end == -1:
        return figure + "\n" + body
    end += len("</p>")
    return body[:end] + "\n" + figure + body[end:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title-hint", default="")
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.body_file, encoding="utf-8") as fh:
        new_body = fh.read()

    conn = connect()
    try:
        post = find_post(conn, args.slug, args.title_hint)
        print(f"Found post id={post['id']} status={post['status']} title={post['title']!r}")

        # 2. Backup
        os.makedirs(os.path.join(ROOT, "fixes"), exist_ok=True)
        backup = os.path.join(ROOT, "fixes", f"backup-{post['id']}.html")
        with open(backup, "w", encoding="utf-8") as fh:
            fh.write(post["content"] or "")
        print(f"Backup written: fixes/backup-{post['id']}.html")

        # 3. Clean
        cleaned, problems = clean_content(new_body, post["title"])
        if problems:
            raise SystemExit(f"ABORT: body still has problems: {problems}")
        print(f"Body cleaned: {len(cleaned.split())} words, no problems")

        # 4. Image
        used = used_image_urls(conn)
        img = find_image(post["title"], used)
        if not img:
            raise SystemExit("ABORT: no licensed image found from Pexels, Unsplash or Pixabay")
        alt = "Healthy meal, movement, and wellness habits for 2026"
        print(f"Image selected from {img['source']}: {img['url']}")

        # 5. Build final body
        final_body = insert_image(cleaned, img, alt)

        if args.dry_run:
            print("DRY RUN: no database writes. Checks passed.")
            return

        # 6. Write
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO image_tracking (image_url, topic, used_date, blog_id, expires_date)
               VALUES (%s, %s, CURDATE(), %s, DATE_ADD(CURDATE(), INTERVAL 30 DAY))""",
            (img["url"], "health", post["id"]),
        )
        image_id = cur.lastrowid
        cur.execute(
            """UPDATE blog_posts
               SET content = %s, featured_image_id = %s, featured_image_alt_text = %s, images_found = 1
               WHERE id = %s""",
            (final_body, image_id, alt, post["id"]),
        )
        conn.commit()
        cur.close()
        print(f"UPDATED post id={post['id']}: image_tracking id={image_id}, status unchanged ({post['status']})")
    except SystemExit:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
