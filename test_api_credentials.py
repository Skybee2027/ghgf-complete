#!/usr/bin/env python3
"""
Test API Credentials
Tests each AI provider's credentials and connection
"""

import os
import sys

print("="*80)
print("API CREDENTIALS TEST")
print("="*80)
print()

# Get credentials from environment
groq_key = os.getenv('GROQ_API_KEY', '').strip()
groq_model = os.getenv('GROQ_MODEL', '').strip()
gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
gemini_model = os.getenv('GEMINI_MODEL', '').strip()
cohere_key = os.getenv('COHERE_API_KEY', '').strip()
cohere_model = os.getenv('COHERE_MODEL', '').strip()
openai_key = os.getenv('OPENAI_API_KEY', '').strip()
openai_model = os.getenv('OPENAI_MODEL', '').strip()

# Summary
print("CREDENTIALS CONFIGURED:")
print("-" * 80)
print(f"GROQ_API_KEY:     {'✓ SET' if groq_key else '✗ MISSING'}")
print(f"GROQ_MODEL:       {'✓ SET to: ' + groq_model if groq_model else '✗ MISSING'}")
print(f"GEMINI_API_KEY:   {'✓ SET' if gemini_key else '✗ MISSING'}")
print(f"GEMINI_MODEL:     {'✓ SET to: ' + gemini_model if gemini_model else '✗ MISSING'}")
print(f"COHERE_API_KEY:   {'✓ SET' if cohere_key else '✗ MISSING'}")
print(f"COHERE_MODEL:     {'✓ SET to: ' + cohere_model if cohere_model else '✗ MISSING'}")
print(f"OPENAI_API_KEY:   {'✓ SET' if openai_key else '✗ MISSING'}")
print(f"OPENAI_MODEL:     {'✓ SET to: ' + openai_model if openai_model else '✗ MISSING'}")
print()

# Test each provider
print("="*80)
print("TESTING API CONNECTIONS")
print("="*80)
print()

results = {
    'groq': {'configured': False, 'connected': False, 'error': None},
    'gemini': {'configured': False, 'connected': False, 'error': None},
    'cohere': {'configured': False, 'connected': False, 'error': None},
    'openai': {'configured': False, 'connected': False, 'error': None},
}

# Test Groq
print("1. GROQ")
print("-" * 80)
if groq_key and groq_model:
    results['groq']['configured'] = True
    print(f"   ✓ API Key: SET")
    print(f"   ✓ Model: {groq_model}")
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        # Try to make a simple test call
        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": "say ok"}],
            max_tokens=10,
            timeout=10
        )
        print(f"   ✓ CONNECTION TEST: SUCCESS")
        results['groq']['connected'] = True
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"   ✗ CONNECTION TEST FAILED: {error_msg}")
        results['groq']['error'] = error_msg
else:
    print(f"   ✗ Not configured (key: {bool(groq_key)}, model: {bool(groq_model)})")
print()

# Test Gemini
print("2. GEMINI")
print("-" * 80)
if gemini_key and gemini_model:
    results['gemini']['configured'] = True
    print(f"   ✓ API Key: SET")
    print(f"   ✓ Model: {gemini_model}")
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(gemini_model)
        response = model.generate_content("say ok", request_options={"timeout": 10})
        print(f"   ✓ CONNECTION TEST: SUCCESS")
        results['gemini']['connected'] = True
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"   ✗ CONNECTION TEST FAILED: {error_msg}")
        results['gemini']['error'] = error_msg
else:
    print(f"   ✗ Not configured (key: {bool(gemini_key)}, model: {bool(gemini_model)})")
print()

# Test Cohere
print("3. COHERE")
print("-" * 80)
if cohere_key and cohere_model:
    results['cohere']['configured'] = True
    print(f"   ✓ API Key: SET")
    print(f"   ✓ Model: {cohere_model}")
    try:
        import cohere
        client = cohere.ClientV2(api_key=cohere_key, timeout=10)
        response = client.chat(
            model=cohere_model,
            messages=[{"role": "user", "content": "say ok"}]
        )
        print(f"   ✓ CONNECTION TEST: SUCCESS")
        results['cohere']['connected'] = True
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"   ✗ CONNECTION TEST FAILED: {error_msg}")
        results['cohere']['error'] = error_msg
else:
    print(f"   ✗ Not configured (key: {bool(cohere_key)}, model: {bool(cohere_model)})")
print()

# Test OpenAI
print("4. OPENAI")
print("-" * 80)
if openai_key and openai_model:
    results['openai']['configured'] = True
    print(f"   ✓ API Key: SET")
    print(f"   ✓ Model: {openai_model}")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key, timeout=10)
        response = client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": "say ok"}],
            max_tokens=10
        )
        print(f"   ✓ CONNECTION TEST: SUCCESS")
        results['openai']['connected'] = True
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"   ✗ CONNECTION TEST FAILED: {error_msg}")
        results['openai']['error'] = error_msg
else:
    print(f"   ✗ Not configured (key: {bool(openai_key)}, model: {bool(openai_model)})")
print()

# Summary
print("="*80)
print("TEST SUMMARY")
print("="*80)
print()

configured = sum(1 for r in results.values() if r['configured'])
connected = sum(1 for r in results.values() if r['connected'])

print(f"Configured: {configured}/4")
print(f"Connected:  {connected}/4")
print()

print("Details:")
for provider, result in results.items():
    status = "🟢 WORKING" if result['connected'] else ("🟡 NOT SET" if not result['configured'] else "🔴 FAILED")
    print(f"  {provider.upper():8} - {status}")
    if result['error']:
        print(f"            Error: {result['error']}")
print()

print("="*80)

if connected == 0:
    print("⚠️  WARNING: No API providers are working!")
    print("All credentials need to be fixed before blog generation can continue.")
    sys.exit(1)
elif connected < 2:
    print(f"⚠️  WARNING: Only {connected} provider working. Consider fixing others for reliability.")
    sys.exit(0)
else:
    print(f"✅ {connected}/4 providers working - Ready for content generation!")
    sys.exit(0)
