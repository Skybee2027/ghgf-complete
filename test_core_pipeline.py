#!/usr/bin/env python3
"""
Test script for core blogging pipeline (R2, R3, R31)
Runs the three essential robots with detailed error reporting
"""

import os
import subprocess
import sys

def run_test(robot_file, robot_name):
    """Run a single robot and report results"""
    robot_path = os.path.join('robots', robot_file)
    print(f"\n{'='*70}")
    print(f"Testing: {robot_name}")
    print(f"File: {robot_file}")
    print('='*70)

    if not os.path.exists(robot_path):
        print(f"❌ ERROR: File not found - {robot_path}")
        return False

    try:
        result = subprocess.run(
            ['python3', robot_path],
            env=os.environ,
            capture_output=True,
            text=True,
            timeout=300
        )

        print(f"Exit Code: {result.returncode}")

        if result.returncode != 0:
            print(f"\n❌ FAILED")
            print("\nSTDERR:")
            print(result.stderr)
            print("\nSTDOUT:")
            print(result.stdout)
            return False
        else:
            print(f"✅ SUCCESS")
            # Show last few lines of output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                print("\nOutput (last 10 lines):")
                for line in lines[-10:]:
                    print(f"  {line}")
            return True
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT (>5 min)")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("CORE PIPELINE TEST")
    print("Testing: R2 (Title) → R3 (Content) → R31 (WordPress Publish)")
    print("="*70)

    results = []

    # Run the three core robots
    results.append(run_test('r2_blog_title_generator.py', 'R2: Blog Title Generator'))
    results.append(run_test('r3_blog_content_generator.py', 'R3: Blog Content Generator'))
    results.append(run_test('r31_wordpress_uploader_publisher.py', 'R31: WordPress Publisher'))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if all(results):
        print("\n✅ ALL TESTS PASSED - Pipeline is working!")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
