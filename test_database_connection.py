#!/usr/bin/env python3
"""
Helper Script: Test Database Connection
Purpose: Verify MySQL database credentials work before using in GitHub Actions
Usage: python3 test_database_connection.py
"""

import os
import sys
import mysql.connector

def test_connection():
    """Test MySQL database connection with user input"""

    print("\n" + "="*70)
    print("DATABASE CONNECTION TESTER")
    print("="*70)
    print("\nThis script will test your MySQL database connection.\n")

    # Get credentials from user
    print("Enter your database credentials:")
    print("(Leave blank to use environment variables if set)\n")

    db_host = input("Database Host [localhost]: ").strip() or os.getenv('DB_HOST', 'localhost')
    db_user = input("Database User [root]: ").strip() or os.getenv('DB_USER', 'root')
    db_password = input("Database Password: ").strip() or os.getenv('DB_PASSWORD', '')
    db_name = input("Database Name [ghgf_blogging]: ").strip() or os.getenv('DB_NAME', 'ghgf_blogging')

    print("\n" + "-"*70)
    print("Connecting to MySQL database...")
    print("-"*70)
    print(f"Host: {db_host}")
    print(f"User: {db_user}")
    print(f"Database: {db_name}")
    print()

    try:
        # Attempt connection
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )

        print("✅ CONNECTION SUCCESSFUL!\n")

        # Get MySQL version
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"MySQL Version: {version}")

        # Check if our tables exist
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
            LIMIT 5
        """, (db_name,))

        tables = cursor.fetchall()
        print(f"\nTables in database (showing first 5):")
        for table in tables:
            print(f"  • {table[0]}")

        if len(tables) == 0:
            print("  ⚠️  No tables found - database might be empty")

        # Test blog_posts table specifically
        cursor.execute("SHOW TABLES LIKE 'blog_posts'")
        if cursor.fetchone():
            print("\n✅ blog_posts table exists")
            cursor.execute("SELECT COUNT(*) FROM blog_posts")
            count = cursor.fetchone()[0]
            print(f"   Current posts in database: {count}")
        else:
            print("\n⚠️  blog_posts table does NOT exist yet")
            print("   This is OK - the workflow will create it on first run")

        cursor.close()
        connection.close()

        print("\n" + "="*70)
        print("✅ DATABASE IS READY FOR GITHUB ACTIONS!")
        print("="*70)
        print("\nNext steps:")
        print("1. Go to: https://github.com/Skybee2027/ghgf-complete/settings/secrets/actions")
        print("2. Set these GitHub Secrets:")
        print(f"   DB_HOST = {db_host}")
        print(f"   DB_USER = {db_user}")
        print(f"   DB_PASSWORD = [your password]")
        print(f"   DB_NAME = {db_name}")
        print("3. Run the workflow: Actions → GHGF 42-Robot Pipeline → Run workflow")
        print("\n")

        return True

    except mysql.connector.Error as err:
        print(f"❌ CONNECTION FAILED!\n")

        if err.errno == 2003:
            print(f"Error: Cannot connect to MySQL server on '{db_host}:3306'")
            print("\nPossible causes:")
            print("  1. Database host is wrong or unreachable")
            print("  2. Database server is offline")
            print("  3. Firewall is blocking the connection")
            print("\nSolution:")
            print("  • If database is on cPanel, ask hosting provider for the")
            print("    remote database hostname/IP (not 'localhost')")
            print("  • Make sure you have the correct hostname/IP")

        elif err.errno == 1045:
            print("Error: Access denied for user")
            print("\nPossible causes:")
            print("  1. Username or password is wrong")
            print("  2. User doesn't have access to this database")
            print("\nSolution:")
            print("  • Double-check your username and password")
            print("  • Make sure the user has SELECT/INSERT/UPDATE permissions")

        elif err.errno == 1049:
            print(f"Error: Unknown database '{db_name}'")
            print("\nSolution:")
            print("  • The database doesn't exist yet (that's OK)")
            print("  • The workflow will create it on first run")
            print("  • But the MySQL server connection is working!")

        else:
            print(f"MySQL Error {err.errno}: {err.msg}")
            print("\nTroubleshooting:")
            print("  • Verify your credentials are correct")
            print("  • Ensure database server is accessible")
            print("  • Check firewall/network settings")

        print("\n" + "="*70)
        print("❌ CONNECTION TEST FAILED")
        print("="*70 + "\n")

        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
