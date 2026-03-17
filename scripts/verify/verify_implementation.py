import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from backend.common.config import AppMode, settings
from backend.common.database import create_db_and_tables
from backend.common.services.llm.newsletter_service import newsletter_service


async def main() -> None:
    settings.APP_MODE = AppMode.DESKTOP
    settings.configure()
    print(f"Forced Mode: {settings.APP_MODE}")
    print(f"Data Dir: {settings.DATA_DIR}")

    print("\n--- Starting Verification ---")
    print("Creating tables...")
    try:
        create_db_and_tables()
        print("Tables created successfully.")
    except Exception as exc:
        print(f"DB Error: {exc}")
        return

    print("Testing Newsletter Service (mocked)...")
    original_run = newsletter_service._run_crew
    newsletter_service._run_crew = lambda topic, context, api_keys, user_id, session_id: (
        f"Mocked content for '{topic}'"
    )
    try:
        result = await newsletter_service.generate_newsletter("Python Async", user_id=1)
        print(f"Success! Result: {result.content}")
    except Exception as exc:
        print(f"Service Error: {exc}")
        import traceback

        traceback.print_exc()
    finally:
        newsletter_service._run_crew = original_run


if __name__ == "__main__":
    asyncio.run(main())
