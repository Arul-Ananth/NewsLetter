import sys
import asyncio
from pathlib import Path

sys.path.append("c:/Dev/news-letter")

from backend.server.config import settings, AppMode
from backend.server.services.newsletter_service import newsletter_service

# Force Desktop Mode
settings.APP_MODE = AppMode.DESKTOP
settings.configure()

async def main():
    print("--- Starting Real Generation Test ---")
    print(f"URL: {settings.OPENAI_API_BASE}")
    print(f"Model: {settings.OPENAI_MODEL_NAME}")
    
    try:
        # Real call (no mock)
        print("Sending request to LLM (this may take time)...")
        result = await newsletter_service.generate_newsletter("Physics", user_id=1)
        print("\n--- Result Content ---")
        print(result.content[:500] + "...") 
        print("--- End Result ---")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
