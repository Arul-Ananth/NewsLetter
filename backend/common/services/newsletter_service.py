import asyncio

from crewai import Agent, Crew, LLM, Task

from backend.common.config import AppMode, settings
from backend.common.models.schemas import NewsResponse
from backend.common.services.web_search import WebSearchGoogleTool, WebSearchTool


class NewsletterService:
    def __init__(self) -> None:
        pass

    async def generate_newsletter(
        self,
        topic: str,
        user_id: int,
        context: str = "",
        api_keys: dict | None = None,
    ) -> NewsResponse:
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(None, self._run_crew, topic, context, api_keys or {})

        return NewsResponse(
            topic=topic,
            content=content,
            bill={"deducted": 1, "remaining": 99},
        )

    def _run_crew(self, topic: str, context: str, api_keys: dict) -> str:
        serper_key = api_keys.get("serper_api_key") or settings.SERPER_API_KEY
        openai_key = api_keys.get("openai_api_key") or "NA"

        llm = LLM(
            model=f"ollama/{settings.OPENAI_MODEL_NAME.split(':')[0]}",
            base_url=settings.OPENAI_API_BASE,
            api_key=openai_key,
            timeout=300,
            temperature=0.7,
        )

        allow_fallback = settings.APP_MODE == AppMode.DESKTOP
        tools = []
        if serper_key or allow_fallback:
            tools = [
                WebSearchTool(serper_api_key=serper_key, allow_fallback=allow_fallback),
                WebSearchGoogleTool(serper_api_key=serper_key, allow_fallback=allow_fallback),
            ]

        researcher = Agent(
            role="Researcher",
            goal=f"Find facts about {topic}",
            backstory=(
                "You find facts matching user interests. "
                "Use the Web Search tool for any external research."
            ),
            tools=tools,
            llm=llm,
            verbose=True,
        )

        writer = Agent(
            role="Writer",
            goal="Summarize facts",
            backstory="You write concise, engaging summaries.",
            llm=llm,
            verbose=True,
        )

        task1 = Task(
            description=f"Research '{topic}'. Context: {context}",
            expected_output="3 key facts.",
            agent=researcher,
        )

        task2 = Task(
            description=f"Write a newsletter summary on '{topic}'.",
            expected_output="A short Markdown newsletter.",
            agent=writer,
            context=[task1],
        )

        crew = Crew(
            agents=[researcher, writer],
            tasks=[task1, task2],
            verbose=True,
        )

        result = crew.kickoff()
        return str(result)


newsletter_service = NewsletterService()
