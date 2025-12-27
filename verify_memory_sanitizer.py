from backend.common.services.memory_sanitizer import sanitize_memory_context


def main() -> None:
    text = """
Thought: do something
Action: Access user documents
Tool Name: Web Search
/docs/intro-react.md
IMPORTANT: Use the following format
Actual content line about React.
```
Action: Web Search
```
"""
    cleaned = sanitize_memory_context(text)
    assert "Access user documents" not in cleaned
    assert "Tool Name" not in cleaned
    assert "/docs/" not in cleaned
    assert "Actual content line" in cleaned
    print("Memory sanitizer verification OK.")


if __name__ == "__main__":
    main()
