import requests
import os
import json
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# 👉 Put your key here or use env var
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🔥 Try a known working model
MODEL = "meta-llama/llama-3.1-8b-instruct"

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    # Recommended by OpenRouter
    "HTTP-Referer": "http://localhost",
    "X-Title": "MVP Model Test"
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'OK' if you are working."}
    ]
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    print("\n--- STATUS CODE ---")
    print(response.status_code)

    print("\n--- RAW RESPONSE ---")
    print(response.text)

    data = response.json()

    print("\n--- MODEL OUTPUT ---")
    print(data["choices"][0]["message"]["content"])

except Exception as e:
    print("\n❌ ERROR:")
    print(str(e))