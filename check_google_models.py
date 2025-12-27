import os
import requests
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

# Try to get the key from either variable
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: No API Key found in .env file.")
    print("Please set GOOGLE_API_KEY in your .env file.")
    exit()

print(f"🔑 Using API Key: {api_key[:5]}...{api_key[-5:]}")
print("📡 Connecting to Google Gemini API...")

# Standard Google Gemini API endpoint for model listing
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! Connection established.\n")
        print("Available Models:")
        print("-" * 40)
        found_flash = False
        for model in data.get('models', []):
            # We specifically look for flash models
            if 'flash' in model['name']:
                print(f"• {model['name']}")
                found_flash = True
        print("-" * 40)

        if found_flash:
            print("\n📝 RECOMMENDATION FOR .ENV:")
            print('OPENAI_MODEL_NAME=gemini-1.5-flash')
        else:
            print("\n⚠️ WARNING: No 'flash' model found. Check your API key permissions.")

    else:
        print(f"\n❌ API request failed. Status Code: {response.status_code}")
        print("Error Message:")
        print(response.text)

except Exception as e:
    print(f"\n❌ Request failed: {e}")