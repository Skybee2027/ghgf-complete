#!/usr/bin/env python3
"""
Diagnostic tool to test image API connectivity and credentials
Tests: Unsplash, Pexels, Pixabay, Replicate SDXL, HuggingFace
"""

import os
import requests
import sys
from datetime import datetime

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'

def print_header(title):
    print(f"\n{'='*70}\n{BOLD}{title}{RESET}\n{'='*70}")

def test_unsplash():
    """Test Unsplash API"""
    print(f"\n{BOLD}Testing UNSPLASH{RESET}")
    api_key = os.getenv('UNSPLASH_API_KEY', '')

    if not api_key:
        print(f"  {RED}✗ API key not configured{RESET}")
        print("    Set UNSPLASH_API_KEY environment variable or GitHub Secret")
        print("    Get free key at: https://unsplash.com/oauth/applications")
        return False

    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            'query': 'fitness',
            'per_page': 3,
            'client_id': api_key,
            'orientation': 'landscape'
        }
        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f"  {GREEN}✓ Successfully connected{RESET}")
            print(f"    Found {len(results)} images for 'fitness'")
            if results:
                print(f"    First result: {results[0]['urls']['regular'][:60]}...")
            return True
        elif response.status_code == 401:
            print(f"  {RED}✗ Invalid or expired API key{RESET}")
            return False
        else:
            print(f"  {RED}✗ API returned status {response.status_code}{RESET}")
            print(f"    Response: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  {RED}✗ Connection error: {str(e)}{RESET}")
        return False

def test_pexels():
    """Test Pexels API"""
    print(f"\n{BOLD}Testing PEXELS{RESET}")
    api_key = os.getenv('PEXELS_API_KEY', '')

    if not api_key:
        print(f"  {RED}✗ API key not configured{RESET}")
        print("    Set PEXELS_API_KEY environment variable or GitHub Secret")
        print("    Get free key at: https://www.pexels.com/api/")
        return False

    try:
        url = "https://api.pexels.com/v1/search"
        headers = {'Authorization': api_key}
        params = {'query': 'fitness', 'per_page': 3}
        response = requests.get(url, headers=headers, params=params, timeout=5)

        if response.status_code == 200:
            results = response.json().get('photos', [])
            print(f"  {GREEN}✓ Successfully connected{RESET}")
            print(f"    Found {len(results)} images for 'fitness'")
            if results:
                print(f"    First result: {results[0]['src']['large'][:60]}...")
            return True
        elif response.status_code == 401:
            print(f"  {RED}✗ Invalid or expired API key{RESET}")
            return False
        else:
            print(f"  {RED}✗ API returned status {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"  {RED}✗ Connection error: {str(e)}{RESET}")
        return False

def test_pixabay():
    """Test Pixabay API"""
    print(f"\n{BOLD}Testing PIXABAY{RESET}")
    api_key = os.getenv('PIXABAY_API_KEY', '')

    if not api_key:
        print(f"  {RED}✗ API key not configured{RESET}")
        print("    Set PIXABAY_API_KEY environment variable or GitHub Secret")
        print("    Get free key at: https://pixabay.com/api/")
        return False

    try:
        url = "https://pixabay.com/api/"
        params = {
            'key': api_key,
            'q': 'fitness',
            'image_type': 'photo',
            'per_page': 3,
            'order': 'popular'
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            results = response.json().get('hits', [])
            print(f"  {GREEN}✓ Successfully connected{RESET}")
            print(f"    Found {len(results)} images for 'fitness'")
            if results:
                print(f"    First result: {results[0]['largeImageURL'][:60]}...")
            return True
        elif response.status_code == 400:
            print(f"  {RED}✗ Invalid API key or request{RESET}")
            return False
        else:
            print(f"  {RED}✗ API returned status {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"  {RED}✗ Connection error: {str(e)}{RESET}")
        return False

def test_replicate():
    """Test Replicate API (AI image generation)"""
    print(f"\n{BOLD}Testing REPLICATE (SDXL AI Generation){RESET}")
    api_token = os.getenv('REPLICATE_API_TOKEN', '')

    if not api_token:
        print(f"  {RED}✗ API token not configured{RESET}")
        print("    Set REPLICATE_API_TOKEN environment variable or GitHub Secret")
        print("    Get free credits at: https://replicate.com/")
        return False

    try:
        print(f"  {YELLOW}⚠ Replicate requires credits to test{RESET}")
        print(f"    This test is skipped to avoid charges")
        print(f"    Credentials appear configured, but test requires manual verification")
        return None  # Skip actual test
    except Exception as e:
        print(f"  {RED}✗ Error: {str(e)}{RESET}")
        return False

def test_huggingface():
    """Test HuggingFace API"""
    print(f"\n{BOLD}Testing HUGGINGFACE (AI Generation){RESET}")
    api_key = os.getenv('HUGGINGFACE_API_KEY', '')

    if not api_key:
        print(f"  {RED}✗ API key not configured{RESET}")
        print("    Set HUGGINGFACE_API_KEY environment variable or GitHub Secret")
        print("    Get free key at: https://huggingface.co/settings/tokens")
        return False

    try:
        print(f"  {YELLOW}⚠ HuggingFace test requires inference available{RESET}")
        print(f"    Credentials appear configured, but full test requires manual verification")
        return None  # Skip actual test
    except Exception as e:
        print(f"  {RED}✗ Error: {str(e)}{RESET}")
        return False

def main():
    print_header("IMAGE API DIAGNOSTIC TEST")
    print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        'unsplash': test_unsplash(),
        'pexels': test_pexels(),
        'pixabay': test_pixabay(),
        'replicate': test_replicate(),
        'huggingface': test_huggingface()
    }

    print("\n" + "="*70)
    print(f"{BOLD}SUMMARY{RESET}")
    print("="*70)

    working = sum(1 for r in results.values() if r is True)
    configured = sum(1 for r in results.values() if r is not False)

    print(f"\nWorking APIs: {GREEN}{working}{RESET}/5")
    print(f"Configured APIs: {configured}/5\n")

    for api, status in results.items():
        if status is True:
            symbol = f"{GREEN}✓ WORKING{RESET}"
        elif status is None:
            symbol = f"{YELLOW}~ CONFIGURED{RESET}"
        else:
            symbol = f"{RED}✗ NOT WORKING{RESET}"
        print(f"  {api:15} {symbol}")

    print(f"\n{BOLD}RECOMMENDATION:{RESET}")
    if working >= 2:
        print(f"  {GREEN}✓ At least 2 stock photo APIs are working - R7 should succeed{RESET}")
    elif working == 1:
        print(f"  {YELLOW}⚠ Only 1 API working - configure a second for reliability{RESET}")
    else:
        print(f"  {RED}✗ No APIs working - R7 will find 0 images{RESET}")
        print(f"    Configure at least 2 of: Unsplash, Pexels, or Pixabay")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
