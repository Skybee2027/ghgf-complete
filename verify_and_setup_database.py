#!/usr/bin/env python3
"""
Helper Script: Verify and Setup Database for GHGF Pipeline
Purpose: Ensure MySQL database has all required tables and columns for R31 and other robots
Usage: python3 verify_and_setup_database.py
"""

import os
import sys
import mysql.connector
from mysql.connector import Error as MySQLError

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

def get_db_connection(host, user, password, database):
    """Create database connection"""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conn
    except MySQLError as e:
        return None, str(e)

def verify_columns(conn):
    """Check if blog_posts table has all required columns for R31"""
    required_columns = [
        'id', 'title', 'content', 'topic', 'meta_description',
        'slug', 'category_id', 'tags', 'featured_image_id', 'version',
        'status', 'ready_for_wordpress', 'final_qa_passed', 'wordpress_post_id',
        'headline_locked', 'qa_check_passed', 'revalidation_passed'
    ]

    try:
        cursor = conn.cursor()
        cursor.execute("DESCRIBE blog_posts")
        columns = cursor.fetchall()
        cursor.close()

        existing_columns = [col[0] for col in columns]

        missing_columns = [col for col in required_columns if col not in existing_columns]

        print("\n" + "="*70)
        print(f"{BOLD}blog_posts Table Structure{RESET}")
        print("="*70)

        if missing_columns:
            print(f"\n{RED}❌ MISSING COLUMNS (R31 WILL FAIL):{RESET}")
            for col in missing_columns:
                print(f"  • {RED}{col}{RESET}")
            print(f"\n{YELLOW}Please run: mysql -u {db_user} -p ghgf_blogging < database/setup_database.sql{RESET}\n")
            return False
        else:
            print(f"\n{GREEN}✅ All required columns exist!{RESET}\n")
            return True

    except Exception as e:
        print(f"{RED}Error checking columns: {str(e)}{RESET}")
        return False

def check_post_status(conn):
    """Check status of posts in database"""
    try:
        cursor = conn.cursor(dictionary=True)

        queries = [
            ("SELECT COUNT(*) as count FROM blog_posts", "Total posts in database"),
            ("SELECT COUNT(*) as count FROM blog_posts WHERE status='draft'", "Posts with status='draft'"),
            ("SELECT COUNT(*) as count FROM blog_posts WHERE ready_for_wordpress=TRUE", "Posts ready for WordPress"),
            ("SELECT COUNT(*) as count FROM blog_posts WHERE final_qa_passed=TRUE", "Posts that passed final QA"),
            ("SELECT COUNT(*) as count FROM blog_posts WHERE wordpress_post_id IS NULL", "Posts NOT yet published to WP"),
            ("SELECT COUNT(*) as count FROM blog_posts WHERE wordpress_post_id IS NOT NULL", "Posts ALREADY published to WP"),
        ]

        print("\n" + "="*70)
        print(f"{BOLD}Blog Posts Status{RESET}")
        print("="*70 + "\n")

        for query, label in queries:
            cursor.execute(query)
            result = cursor.fetchone()
            count = result['count'] if result else 0
            print(f"{label:<50} {BLUE}{count}{RESET}")

        # Check specific posts that should be published
        cursor.execute("""
            SELECT id, title, status, ready_for_wordpress, final_qa_passed, wordpress_post_id
            FROM blog_posts
            WHERE ready_for_wordpress=TRUE AND final_qa_passed=TRUE AND wordpress_post_id IS NULL
            LIMIT 5
        """)

        posts_ready = cursor.fetchall()
        cursor.close()

        if posts_ready:
            print(f"\n{YELLOW}Posts ready to publish (not yet in WordPress):{RESET}")
            for post in posts_ready:
                print(f"  ID {post['id']}: {post['title'][:40]}...")

        return True

    except Exception as e:
        print(f"{RED}Error checking post status: {str(e)}{RESET}")
        return False

def main():
    """Main function"""

    print("\n" + "="*70)
    print(f"{BOLD}GHGF DATABASE VERIFICATION & SETUP{RESET}")
    print("="*70)

    # Get database credentials from environment or use defaults
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'ghgf_blogging')

    print(f"\nConnecting to database...")
    print(f"  Host: {db_host}")
    print(f"  User: {db_user}")
    print(f"  Database: {db_name}")

    # Try to connect
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
    except MySQLError as e:
        print(f"\n{RED}❌ CONNECTION FAILED!{RESET}")
        print(f"{RED}Error: {str(e)}{RESET}\n")

        if e.errno == 2003:
            print(f"Cannot connect to database server at {db_host}")
            print(f"\nMake sure:")
            print(f"  1. MySQL server is running")
            print(f"  2. Database host is correct ({db_host})")
            print(f"  3. Database credentials are correct")
        elif e.errno == 1045:
            print(f"Username or password is incorrect")
            print(f"\nCheck your credentials:")
            print(f"  DB_HOST={db_host}")
            print(f"  DB_USER={db_user}")
            print(f"  DB_PASSWORD={'(set)' if db_password else '(not set)'}")

        sys.exit(1)

    print(f"\n{GREEN}✅ Connected to database successfully!{RESET}")

    # Check MySQL version
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        print(f"MySQL Version: {version}")
    except:
        pass

    # Verify columns
    columns_ok = verify_columns(conn)

    # Check post status
    check_post_status(conn)

    conn.close()

    # Final status
    print("\n" + "="*70)
    if columns_ok:
        print(f"{GREEN}{BOLD}✅ Database is READY for pipeline execution!{RESET}")
    else:
        print(f"{RED}{BOLD}❌ Database needs setup before pipeline can run{RESET}")
        print(f"\n{YELLOW}To setup database, run:{RESET}")
        print(f"  mysql -h {db_host} -u {db_user} -p{db_password if db_password else ''} {db_name} < database/setup_database.sql")
    print("="*70 + "\n")

    sys.exit(0 if columns_ok else 1)

if __name__ == "__main__":
    main()
