from crewai import LLM

from backend.common.config import AppMode, settings


def build_llm(api_keys: dict | None = None) -> LLM:
    keys = api_keys or {}
    provider = (settings.LLM_PROVIDER or "").strip().lower()
    if not provider:
        raise ValueError("LLM_PROVIDER is not set. Use 'ollama', 'openai', or 'google' in .env.")

    if provider == "openai":
        openai_key = keys.get("openai_api_key") or settings.OPENAI_API_KEY
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        model = settings.OPENAI_MODEL_NAME
        base_url = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        api_key = openai_key
    elif provider == "google":
        gemini_key = keys.get("gemini_api_key") or settings.GEMINI_API_KEY
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=google.")
        model = settings.OPENAI_MODEL_NAME
        base_url = settings.OPENAI_API_BASE or ""
        api_key = gemini_key
    elif provider == "ollama":
        model = f"ollama/{settings.OPENAI_MODEL_NAME.split(':')[0]}"
        base_url = settings.OPENAI_API_BASE or "http://localhost:11434"
        api_key = "NA"
    else:
        raise ValueError("LLM_PROVIDER must be 'ollama', 'openai', or 'google'.")

    return LLM(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=300,
        temperature=0.7,
    )


def allow_search_fallback() -> bool:
    return settings.APP_MODE == AppMode.DESKTOP
