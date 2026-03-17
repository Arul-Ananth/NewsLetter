import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from backend.common.config import AppMode, settings
from backend.common.services.llm.newsletter_service import newsletter_service


async def _run_for_mode(mode: AppMode) -> bool:
    settings.APP_MODE = mode
    settings.configure()

    original_run = newsletter_service._run_crew
    newsletter_service._run_crew = lambda topic, context, api_keys, user_id, session_id: (
        f"Mocked content for {topic} ({mode.value})"
    )
    try:
        result = await newsletter_service.generate_newsletter(
            topic="Testing",
            user_id=1,
            context="context",
            api_keys={},
            session_id="verify",
        )
    finally:
        newsletter_service._run_crew = original_run

    if not result.content or mode.value not in result.content:
        print(f"FAIL: unexpected content for {mode.value}: {result.content}")
        return False
    return True


async def main() -> int:
    ok_desktop = await _run_for_mode(AppMode.DESKTOP)
    ok_server = await _run_for_mode(AppMode.SERVER)
    return 0 if (ok_desktop and ok_server) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
