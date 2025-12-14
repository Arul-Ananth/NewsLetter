
import os
from crewai import LLM

# HARDCODED CONFIG FOR TESTING
base_url = "http://127.0.0.1:11434/v1"
model = "ollama/mistral"
api_key = "NA"

print(f"Testing Connection to: {base_url} with model: {model}")

try:
    llm = LLM(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=10,
        temperature=0.7
    )
    print("LLM Initialized. Attempting generation...")
    
    response = llm.call(
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    
    print("\n--- SUCCESS ---")
    print(response)

except Exception as e:
    print("\n--- FAILURE ---")
    print(e)
    import traceback
    traceback.print_exc()
