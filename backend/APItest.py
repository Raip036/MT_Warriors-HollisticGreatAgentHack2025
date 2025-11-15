"""
Quick test script for Holistic AI Bedrock API
Run this first to verify your credentials work
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
api_url = os.getenv('HOLISTIC_AI_API_URL')

print("="*70)
print("🧪 QUICK API TEST")
print("="*70)

# Check credentials
print("\n📋 Checking credentials...")
if not team_id:
    print("❌ HOLISTIC_AI_TEAM_ID not found in .env")
    exit(1)
if not api_token:
    print("❌ HOLISTIC_AI_API_TOKEN not found in .env")
    exit(1)
if not api_url:
    print("❌ HOLISTIC_AI_API_URL not found in .env")
    exit(1)

print(f"✅ Team ID: {team_id}")
print(f"✅ API Token: {api_token[:10]}...")
print(f"✅ API URL: {api_url}")

# Test request
print("\n📤 Sending test request...")

headers = {
    "Content-Type": "application/json",
    "X-Api-Token": api_token
}

# Try with api_token in payload (API might expect it there)
payload = {
    "team_id": team_id,
    "api_token": api_token,
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "messages": [{"role": "user", "content": "Hello! Say 'API is working!' in one sentence."}],
    "max_tokens": 1024
}

try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS! Response:")
        print(f"{result}")
        print("\n🎉 Your API credentials are working correctly!")
        print("You can now run: python pharmacy_agent.py")
    else:
        print(f"\n❌ Request failed")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Connection Error: {e}")
    print("Check your internet connection")
except requests.exceptions.Timeout:
    print(f"\n❌ Request timed out")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*70)