from __future__ import annotations

import asyncio
from datetime import datetime

from backend.common.models.schemas import NewsResponse
from backend.common.services.llm.crew_builder import build_newsletter_crew
from backend.common.services.llm.provider_factory import build_llm
from backend.common.services.llm.tool_policy import build_search_tools
from backend.common.services.memory.memory_sanitizer import sanitize_memory_context
from backend.common.services.memory.vector_db import (
    get_memory_context,
    get_recent_clipboard_context,
    is_clipboard_history_query,
)

TIME_SENSITIVE_TERMS = (
    "today",
    "todays",
    "current date",
    "actual current date",
    "latest",
    "recent",
)
CURRENT_EVENTS_TERMS = (
    "world events",
    "world event",
    "world news",
    "news today",
    "current events",
    "headlines",
)


def _is_time_sensitive_query(topic: str) -> bool:
    lowered = topic.lower()
    return any(term in lowered for term in TIME_SENSITIVE_TERMS)


def _is_current_events_query(topic: str) -> bool:
    lowered = topic.lower()
    return _is_time_sensitive_query(topic) and any(term in lowered for term in CURRENT_EVENTS_TERMS)


def _needs_current_date(topic: str) -> bool:
    lowered = topic.lower()
    return "today" in lowered or "todays date" in lowered or "today's date" in lowered or "current date" in lowered


def _runtime_now() -> datetime:
    return datetime.now().astimezone()


def _runtime_date_label(now: datetime) -> str:
    return now.strftime("%B %d, %Y")


def _runtime_datetime_context(now: datetime) -> str:
    return (
        f"Runtime Date Context:\n"
        f"- Today is {_runtime_date_label(now)}.\n"
        f"- Local timestamp: {now.isoformat()}.\n"
        f"- Treat references to 'today' and 'current' as this local runtime date."
    )


def _format_date_only_response(now: datetime) -> str:
    return (
        "### Current Date\n\n"
        f"Today is **{_runtime_date_label(now)}**.\n\n"
        f"Local timestamp: `{now.isoformat()}`"
    )


def _clean_search_lines(result: str, *, limit: int = 3) -> list[str]:
    lines: list[str] = []
    for raw in result.splitlines():
        cleaned = raw.strip()
        if not cleaned:
            continue
        if cleaned.startswith("-"):
            cleaned = cleaned[1:].strip()
        if cleaned:
            lines.append(cleaned)
        if len(lines) >= limit:
            break
    return lines


def _search_unavailable(result: str) -> bool:
    lowered = result.lower()
    markers = (
        "web search unavailable",
        "fallback search unavailable",
        "error executing",
        "no results",
        "no extractable content",
        "search blocked by security policy",
    )
    return any(marker in lowered for marker in markers)


class NewsletterService:
    async def generate_newsletter(
        self,
        topic: str,
        user_id: int,
        context: str = "",
        api_keys: dict | None = None,
        session_id: str | None = None,
    ) -> NewsResponse:
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(
            None,
            self._run_crew,
            topic,
            context,
            api_keys or {},
            user_id,
            session_id,
        )

        return NewsResponse(
            topic=topic,
            content=content,
            bill={"deducted": 1, "remaining": 99},
        )

    def _run_crew(
        self,
        topic: str,
        context: str,
        api_keys: dict,
        user_id: int,
        session_id: str | None,
    ) -> str:
        now = _runtime_now()
        llm = build_llm(api_keys=api_keys)
        clipboard_query = is_clipboard_history_query(topic)
        time_sensitive = _is_time_sensitive_query(topic)
        current_events_query = _is_current_events_query(topic)
        date_only_query = _needs_current_date(topic) and not current_events_query and not clipboard_query
        tools = [] if clipboard_query else build_search_tools(api_keys=api_keys)

        memory_context = get_memory_context(user_id=user_id, topic=topic, session_id=session_id)
        clipboard_context = get_recent_clipboard_context(topic=topic, session_id=session_id)
        safe_memory = sanitize_memory_context(memory_context) if memory_context else ""
        combined_context = context.strip()
        clipboard_missing = (
            "No recent clipboard entries were captured." in clipboard_context
            or "No recent clipboard entries matched:" in clipboard_context
        )
        if clipboard_query and clipboard_missing:
            return (
                "### Clipboard History\n\n"
                "No relevant clipboard history was found for this request. "
                "The app did not find a recent clipboard entry matching your query."
            )
        if clipboard_context:
            combined_context = f"{combined_context}\n\n{clipboard_context}".strip()
        if safe_memory:
            combined_context = f"{combined_context}\n\nMemory Context:\n{safe_memory}".strip()
        if clipboard_query:
            combined_context = (
                f"{combined_context}\n\n"
                "Instruction: This is a clipboard-history question. Answer from Clipboard History Context first. "
                "Do not use external research for this request."
            ).strip()

        if date_only_query:
            return _format_date_only_response(now)

        if time_sensitive:
            combined_context = f"{combined_context}\n\n{_runtime_datetime_context(now)}".strip()

        if current_events_query:
            return self._build_current_events_brief(topic=topic, now=now, tools=tools)

        crew = build_newsletter_crew(
            topic=topic,
            context=combined_context,
            llm=llm,
            tools=tools,
            time_sensitive=time_sensitive,
            runtime_date_label=_runtime_date_label(now) if time_sensitive else None,
        )
        result = crew.kickoff()
        return str(result)

    def _build_current_events_brief(self, *, topic: str, now: datetime, tools: list) -> str:
        date_label = _runtime_date_label(now)
        if not tools:
            return (
                "### Global News Update\n\n"
                f"**Date:** {date_label}\n\n"
                "Current-date web search is unavailable, so Lumeward cannot verify today's world events right now."
            )

        query = f"world news {date_label}"
        result = tools[0].run(query)
        if _search_unavailable(result):
            return (
                "### Global News Update\n\n"
                f"**Date:** {date_label}\n\n"
                "Lumeward could not verify today's world events from web search right now."
            )

        lines = _clean_search_lines(result)
        if not lines:
            return (
                "### Global News Update\n\n"
                f"**Date:** {date_label}\n\n"
                "Lumeward did not receive enough current-event search results to summarize today reliably."
            )

        bullet_text = "\n".join(f"- {line}" for line in lines)
        return (
            "### Global News Update\n\n"
            f"**Date:** {date_label}\n\n"
            "Based on current web-search results:\n"
            f"{bullet_text}"
        )


newsletter_service = NewsletterService()
