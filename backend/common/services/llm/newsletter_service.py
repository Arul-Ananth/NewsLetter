import asyncio

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
        llm = build_llm(api_keys=api_keys)
        clipboard_query = is_clipboard_history_query(topic)
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

        crew = build_newsletter_crew(topic=topic, context=combined_context, llm=llm, tools=tools)
        result = crew.kickoff()
        return str(result)


newsletter_service = NewsletterService()
