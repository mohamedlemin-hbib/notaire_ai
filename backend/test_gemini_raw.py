import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

data = {
    "contents": [{
        "parts": [{"text": "Hello, write a short welcome message."}]
    }]
}

headers = {"Content-Type": "application/json"}

try:
    print(f"Calling Gemini API at {url[:60]}...")
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        print("\nSUCCESS!")
        print(json.dumps(res_data, indent=2))
except Exception as e:
    print(f"\nFAILED: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode("utf-8"))
