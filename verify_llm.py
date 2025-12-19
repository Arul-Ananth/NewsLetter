import sys
from backend.server.config import settings
from crewai import LLM

# Force base url update check
print(f"Testing LLM Connection to: {settings.OPENAI_API_BASE}")
print(f"Model: {settings.OPENAI_MODEL_NAME}")

try:
    llm = LLM(
        model=f"ollama/{settings.OPENAI_MODEL_NAME.split(':')[0]}",
        base_url=settings.OPENAI_API_BASE,
        timeout=30
    )
    
    print("Sending test generation request...")
    response = llm.call("Say hello")
    print(f"Response: {response}")
    print("SUCCESS: Connected to Ollama.")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
