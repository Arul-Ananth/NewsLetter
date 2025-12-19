import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append("c:/Dev/news-letter")

# 1. Test Config Import
try:
    from backend.server.config import settings, AppMode
    print(f"Config Loaded. Default Mode: {settings.APP_MODE}")
except ImportError as e:
    print(f"Failed to import config: {e}")
    sys.exit(1)

# 2. Force Desktop Mode for Testing
settings.APP_MODE = AppMode.DESKTOP
settings.configure()
print(f"Forced Mode: {settings.APP_MODE}")
print(f"Data Dir: {settings.DATA_DIR}")

# 3. Test Imports
try:
    from backend.server.services.newsletter_service import newsletter_service
    from backend.server.database import create_db_and_tables
    print("Imports Successful.")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def main():
    print("\n--- Starting Verification ---")
    
    # 4. Test DB Creation
    print("Creating tables...")
    try:
        create_db_and_tables()
        print("Tables created successfully.")
    except Exception as e:
        print(f"DB Error: {e}")
        return

    # 5. Test Service Layer (Mocked Execution)
    print("Testing Newsletter Service...")
    
    # Mock the heavy blocking call to verify async wrapper only
    newsletter_service._run_crew = lambda topic: f"Mocked content for '{topic}'"
    
    try:
        result = await newsletter_service.generate_newsletter("Python Async", user_id=1)
        print(f"Success! Result: {result.content}")
    except Exception as e:
        print(f"Service Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
