
import os
from litellm import completion

# HARDCODED CONFIG FOR TESTING
base_url = "http://127.0.0.1:11434"
model = "ollama/mistral"
api_key = "NA"

print(f"Testing LiteLLM Connection to: {base_url} with model: {model}")

try:
    response = completion(
        model=model,
        messages=[{"role": "user", "content": "Hello, stay concise."}],
        api_base=base_url,
        api_key=api_key
    )
    print("\n--- SUCCESS ---")
    print(response)

except Exception as e:
    print("\n--- FAILURE ---")
    print(e)
    import traceback
    traceback.print_exc()
