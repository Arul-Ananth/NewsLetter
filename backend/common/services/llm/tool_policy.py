from backend.common.config import settings
from backend.common.services.llm.provider_factory import allow_search_fallback
from backend.common.services.search.web_search import WebSearchGoogleTool, WebSearchTool


def build_search_tools(api_keys: dict | None = None) -> list:
    keys = api_keys or {}
    serper_key = keys.get("serper_api_key") or settings.SERPER_API_KEY
    fallback = allow_search_fallback()

    if not serper_key and not fallback:
        return []

    return [
        WebSearchTool(serper_api_key=serper_key, allow_fallback=fallback),
        WebSearchGoogleTool(serper_api_key=serper_key, allow_fallback=fallback),
    ]
