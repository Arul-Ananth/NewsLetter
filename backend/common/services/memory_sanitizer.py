import re

INSTRUCTION_PREFIXES = (
    "thought:",
    "action:",
    "action input:",
    "observation:",
    "final answer:",
    "important:",
    "tool name:",
    "tool arguments:",
    "tool description:",
    "you only have access",
    "moving on then.",
)


def sanitize_memory_context(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if any(lower.startswith(prefix) for prefix in INSTRUCTION_PREFIXES):
            continue
        if "/docs/" in lower or lower.endswith(".md"):
            continue
        if lower.startswith("```") or lower.endswith("```"):
            continue
        if lower.startswith("tool "):
            continue
        cleaned_lines.append(raw_line)
    return "\n".join(cleaned_lines).strip()
