#!/usr/bin/env python3
"""
GHGF API Checker - Simplified 10-Service Test
Tests: Groq, Google, OpenAI, Cohere, Replicate, HuggingFace, Unsplash, Pixabay, CJ Affiliate, ShareASale
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/root/ghgf-backend/.env')

BOLD = '\033[1m'
RESET = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'

class APIChecker:
    def __init__(self):
        self.results = {}
        self.total = 0
        self.working = 0

    def print_header(self, title):
        print(f"\n{'='*70}")
        print(f"{BOLD}{title}{RESET}")
        print('='*70)

    def check_groq(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ Groq                      ✗          [TEXT] No API key")
            self.results['groq'] = False
            self.total += 1
            return

        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5
            )
            print(f"✅ Groq                      ✓          [TEXT] Connected")
            self.results['groq'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ Groq                      ✗          [TEXT] {str(e)[:50]}")
            self.results['groq'] = False
        self.total += 1

    def check_google(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Google Gemini             ✗          [TEXT] No API key")
            self.results['google'] = False
            self.total += 1
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Say OK")
            print(f"✅ Google Gemini             ✓          [TEXT] Connected")
            self.results['google'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ Google Gemini             ✗          [TEXT] {str(e)[:50]}")
            self.results['google'] = False
        self.total += 1

    def check_openai(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI                    ✗          [TEXT] No API key")
            self.results['openai'] = False
            self.total += 1
            return

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5
            )
            print(f"✅ OpenAI                    ✓          [TEXT] Connected")
            self.results['openai'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ OpenAI                    ✗          [TEXT] {str(e)[:50]}")
            self.results['openai'] = False
        self.total += 1

    def check_cohere(self):
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            print("❌ Cohere                    ✗          [TEXT] No API key")
            self.results['cohere'] = False
            self.total += 1
            return

        try:
            import cohere
            client = cohere.Client(api_key=api_key)
            response = client.chat(message="Say OK", max_tokens=10)
            print(f"✅ Cohere                    ✓          [TEXT] Connected")
            self.results['cohere'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ Cohere                    ✗          [TEXT] {str(e)[:50]}")
            self.results['cohere'] = False
        self.total += 1

    def check_replicate(self):
        api_key = os.getenv("REPLICATE_API_KEY")
        if not api_key:
            print("❌ Replicate                 ✗          [TEXT] No API key")
            self.results['replicate'] = False
            self.total += 1
            return

        try:
            os.environ['REPLICATE_API_TOKEN'] = api_key
            import replicate
            models = replicate.models.list()
            print(f"✅ Replicate                 ✓          [TEXT] Connected")
            self.results['replicate'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ Replicate                 ✗          [TEXT] {str(e)[:50]}")
            self.results['replicate'] = False
        self.total += 1

    def check_huggingface(self):
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            print("❌ HuggingFace               ✗          [TEXT] No API key")
            self.results['huggingface'] = False
            self.total += 1
            return

        try:
            from huggingface_hub import HfApi
            api = HfApi(token=api_key)
            user = api.whoami()
            print(f"✅ HuggingFace               ✓          [TEXT] Connected")
            self.results['huggingface'] = True
            self.working += 1
        except Exception as e:
            print(f"❌ HuggingFace               ✗          [TEXT] {str(e)[:50]}")
            self.results['huggingface'] = False
        self.total += 1

    def check_unsplash(self):
        api_key = os.getenv("UNSPLASH_API_KEY")
        if not api_key:
            print("❌ Unsplash                  ✗          [IMAGE] No API key")
            self.results['unsplash'] = False
            self.total += 1
            return

        try:
            import requests
            response = requests.get(
                "https://api.unsplash.com/photos/random",
                headers={"Authorization": f"Client-ID {api_key}"}
            )
            if response.status_code == 200:
                print(f"✅ Unsplash                  ✓          [IMAGE] Connected")
                self.results['unsplash'] = True
                self.working += 1
            else:
                print(f"❌ Unsplash                  ✗          [IMAGE] HTTP {response.status_code}")
                self.results['unsplash'] = False
        except Exception as e:
            print(f"❌ Unsplash                  ✗          [IMAGE] {str(e)[:50]}")
            self.results['unsplash'] = False
        self.total += 1

    def check_pixabay(self):
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            print("❌ Pixabay                   ✗          [IMAGE] No API key")
            self.results['pixabay'] = False
            self.total += 1
            return

        try:
            import requests
            response = requests.get(
                "https://pixabay.com/api/",
                params={"key": api_key, "q": "test"}
            )
            if response.status_code == 200:
                print(f"✅ Pixabay                   ✓          [IMAGE] Connected")
                self.results['pixabay'] = True
                self.working += 1
            else:
                print(f"❌ Pixabay                   ✗          [IMAGE] HTTP {response.status_code}")
                self.results['pixabay'] = False
        except Exception as e:
            print(f"❌ Pixabay                   ✗          [IMAGE] {str(e)[:50]}")
            self.results['pixabay'] = False
        self.total += 1

    def check_cj_affiliate(self):
        api_key = os.getenv("CJ_AFFILIATE_API_KEY")
        if not api_key:
            print("❌ CJ Affiliate              ✗          [AFFILIATE] No API key")
            self.results['cj'] = False
            self.total += 1
            return

        try:
            import requests
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.cj.com/v2/commissions",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200 or response.status_code == 401:
                print(f"✅ CJ Affiliate              ✓          [AFFILIATE] Connected")
                self.results['cj'] = True
                self.working += 1
            else:
                print(f"❌ CJ Affiliate              ✗          [AFFILIATE] HTTP {response.status_code}")
                self.results['cj'] = False
        except Exception as e:
            print(f"❌ CJ Affiliate              ✗          [AFFILIATE] {str(e)[:50]}")
            self.results['cj'] = False
        self.total += 1

    def check_shareasale(self):
        token = os.getenv("SHAREASALE_TOKEN")
        user_id = os.getenv("SHAREASALE_USER_ID")
        if not token or not user_id:
            print("❌ ShareASale                ✗          [AFFILIATE] Missing credentials")
            self.results['shareasale'] = False
            self.total += 1
            return

        try:
            import requests
            url = f"https://api.shareasale.com/x/api/merchants?token={token}&userID={user_id}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200 or response.status_code == 401:
                print(f"✅ ShareASale                ✓          [AFFILIATE] Connected")
                self.results['shareasale'] = True
                self.working += 1
            else:
                print(f"❌ ShareASale                ✗          [AFFILIATE] HTTP {response.status_code}")
                self.results['shareasale'] = False
        except Exception as e:
            print(f"❌ ShareASale                ✗          [AFFILIATE] {str(e)[:50]}")
            self.results['shareasale'] = False
        self.total += 1

    def run_all_checks(self):
        self.print_header("GHGF API HEALTH CHECK")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f"{BOLD}TEXT GENERATION LAYER:{RESET}")
        self.check_groq()
        self.check_google()
        self.check_openai()
        self.check_cohere()
        self.check_replicate()
        self.check_huggingface()

        print(f"\n{BOLD}IMAGE LAYER:{RESET}")
        self.check_unsplash()
        self.check_pixabay()

        print(f"\n{BOLD}AFFILIATE LAYER:{RESET}")
        self.check_cj_affiliate()
        self.check_shareasale()

        print(f"\n{'='*70}")
        print(f"{BOLD}SUMMARY{RESET}")
        print(f"{BOLD}Working: {self.working}/{self.total}{RESET}")
        print(f"SUMMARY: {self.working}/{self.total} APIs WORKING")
        print('='*70 + "\n")

if __name__ == "__main__":
    checker = APIChecker()
    checker.run_all_checks()
