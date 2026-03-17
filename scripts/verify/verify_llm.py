import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from backend.common.config import settings
from crewai import LLM

provider = (settings.LLM_PROVIDER or "").strip().lower()
if not provider:
    print("FAILED: LLM_PROVIDER is not set. Use 'ollama', 'openai', or 'google' in .env.")
    sys.exit(1)

try:
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            print("FAILED: OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
            sys.exit(1)
        model = settings.OPENAI_MODEL_NAME
        base_url = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        api_key = settings.OPENAI_API_KEY
    elif provider == "google":
        if not settings.GEMINI_API_KEY:
            print("FAILED: GEMINI_API_KEY is required when LLM_PROVIDER=google.")
            sys.exit(1)
        model = settings.OPENAI_MODEL_NAME
        base_url = settings.OPENAI_API_BASE or ""
        api_key = settings.GEMINI_API_KEY
    elif provider == "ollama":
        model = f"ollama/{settings.OPENAI_MODEL_NAME.split(':')[0]}"
        base_url = settings.OPENAI_API_BASE or "http://localhost:11434"
        api_key = "NA"
    else:
        print("FAILED: LLM_PROVIDER must be one of 'ollama', 'openai', or 'google'.")
        sys.exit(1)

    print(f"Provider: {provider}")
    print(f"Testing LLM Connection to: {base_url}")
    print(f"Model: {model}")

    llm = LLM(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=30,
    )

    print("Sending test generation request...")
    response = llm.call("Say hello")
    print(f"Response: {response}")
    print(f"SUCCESS: Connected using provider '{provider}'.")
except Exception as exc:
    print(f"FAILED: {exc}")
    sys.exit(1)
