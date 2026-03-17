import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from backend.common.config import AppMode, settings
from backend.common.services.search.web_search import WebSearchTool


def main() -> int:
    settings.APP_MODE = AppMode.DESKTOP
    settings.SERPER_API_KEY = ""
    settings.configure()

    try:
        import importlib
        importlib.import_module("lxml.etree")
    except Exception as exc:
        print(f"FAIL: lxml missing for fallback search: {exc}")
        print("Install with: pip install lxml")
        return 1

    tool = WebSearchTool(serper_api_key=None, allow_fallback=True)
    result = tool.run("latest python release notes")
    print("--- Web Search Fallback Result ---")
    print(result)

    lowered = result.lower()
    if "web search unavailable" in lowered:
        print("FAIL: fallback not used.")
        return 1
    if "fallback search unavailable" in lowered or "error executing fallback search" in lowered:
        print("FAIL: fallback search failed.")
        return 1
    if not result.strip():
        print("FAIL: empty search response.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
