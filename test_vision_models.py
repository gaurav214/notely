"""
Test Vision Models on OpenRouter
Find which models actually support image analysis
"""

import requests
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("❌ OPENROUTER_API_KEY not found in .env")
    exit(1)

# Vision models to test (most likely to support images on OpenRouter)
VISION_MODELS = [
    "openai/gpt-4-vision",
    "openai/gpt-4o",
    "google/gemini-pro-vision",
    "anthropic/claude-3-5-sonnet",
    "anthropic/claude-vision",
    "llava-1.5-7b-hf",
    "nvlabs/nv-vlm",
]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:8501",
    "X-Title": "Vision Model Tester"
}

print("=" * 70)
print("Testing Vision Models on OpenRouter")
print("=" * 70)
print()

# Create a simple test image (1x1 pixel PNG)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

for model in VISION_MODELS:
    print(f"Testing: {model}")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": test_image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "What color is this image?"
                    }
                ]
            }
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS - Model works!")
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]["content"]
                print(f"  Response: {msg[:80]}...")
        else:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(error_data))
            if "not found" in str(error_msg).lower() or "no route" in str(error_msg).lower():
                print(f"  ❌ Model not available on OpenRouter")
            else:
                print(f"  ❌ Error: {error_msg}")
    
    except Exception as e:
        print(f"  ❌ Connection error: {str(e)}")
    
    print()

print("=" * 70)
print("For the actual image, you'll need to:")
print("1. Use a confirmed working vision model from above")
print("2. Update llm.py with the working model name")
print("=" * 70)
