import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

payload = {
    "contents": [{"role": "user", "parts": [{"text": "Hello"}]}]
}
headers = {'Content-Type': 'application/json'}
url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"

try:
    response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
