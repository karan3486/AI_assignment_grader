import openai
import requests
import sys
from dotenv import load_dotenv
import os
import json

load_dotenv()
# Your API keys
OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not OPENAI_API_KEY or not GOOGLE_API_KEY:
    print("❌ Missing API keys. Please set OPENAI_API_KEY and GOOGLE_API_KEY in your environment.")
    sys.exit(1)
GOOGLE_CX = os.getenv("GOOGLE_CX")
if not GOOGLE_CX:
    print("❌ Missing Google Custom Search Engine ID. Please set GOOGLE_CX in your environment.")
    sys.exit(1)
SERVER_URL = os.getenv("SERVER_URL")

print("=== Testing API Keys ===")

# Test 1: OpenAI API directly
print("\n1. Testing OpenAI API directly...")
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print(f"✅ OpenAI API works directly! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ OpenAI API error: {str(e)}")

# Test 2: Google API directly
print("\n2. Testing Google API directly...")
try:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": "test query",
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print(f"✅ Google API works directly! Found {len(response.json().get('items', []))} results")
    else:
        print(f"❌ Google API error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Google API error: {str(e)}")

# Test 3: Server connection
print("\n3. Testing server connection...")
try:
    response = requests.get(f"{SERVER_URL}/")
    if response.status_code == 200:
        print(f"✅ Server is running! Response: {response.json()}")
    else:
        print(f"❌ Server error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Server connection error: {str(e)}")
    sys.exit("Cannot continue without server connection")

# Test 4: Debug endpoint
print("\n4. Testing server debug endpoint...")
try:
    debug_url = f"{SERVER_URL}/debug/check_keys"
    debug_data = {
        "openai_api_key": OPENAI_API_KEY,
        "google_api_key": GOOGLE_API_KEY,
        "search_engine_id": GOOGLE_CX,
        "text": "test",
        "rubric": "test"
    }
    
    print(f"Sending keys to {debug_url}...")
    response = requests.post(debug_url, json=debug_data)
    
    if response.status_code == 200:
        print(f"✅ Debug endpoint response: {response.json()}")
    else:
        print(f"❌ Debug endpoint error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Debug endpoint error: {str(e)}")

# Test 5: Testing grading with hardcoded keys
print("\n5. Testing grade_text with hardcoded keys...")
try:
    url = f"{SERVER_URL}/tools/grade_text"
    data = {
        "text": "This is a test assignment.",
        "rubric": "Content (100%): The assignment should be a test.",
        "openai_api_key": OPENAI_API_KEY,
        "google_api_key": GOOGLE_API_KEY,
        "search_engine_id": GOOGLE_CX
    }
    
    print(f"Sending request to {url}...")
    print(f"OpenAI key length: {len(data['openai_api_key'])}")
    print(f"OpenAI key first 10 chars: {data['openai_api_key'][:10]}...")
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print(f"✅ Grading works! Response: {response.json()}")
    else:
        print(f"❌ Grading error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Grading error: {str(e)}")

print("\n=== Tests completed ===")