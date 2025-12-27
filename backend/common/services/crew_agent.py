from typing import Any, Type, Union

from crewai import Agent, Crew, LLM, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from backend.common.config import AppMode, settings
from backend.common.services.web_search import WebSearchGoogleTool, WebSearchTool


class SearchToolInput(BaseModel):
    query: Union[str, dict] = Field(..., description="The search topic. Example: 'climate change'")


class CrewWebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the internet for facts."
    args_schema: Type[BaseModel] = SearchToolInput

    def __init__(self, serper_api_key: str | None = None, allow_fallback: bool | None = None):
        super().__init__()
        self._inner = WebSearchTool(serper_api_key=serper_api_key, allow_fallback=allow_fallback)

    def _run(self, query: Union[str, dict]) -> str:
        return self._inner.run(query)


class CrewWebSearchGoogleTool(BaseTool):
    name: str = "Web Search (Google)"
    description: str = "Search the internet for facts."
    args_schema: Type[BaseModel] = SearchToolInput

    def __init__(self, serper_api_key: str | None = None, allow_fallback: bool | None = None):
        super().__init__()
        self._inner = WebSearchGoogleTool(serper_api_key=serper_api_key, allow_fallback=allow_fallback)

    def _run(self, query: Union[str, dict]) -> str:
        return self._inner.run(query)


search_tool = CrewWebSearchTool()


def run_newsletter_crew(topic: str, user_context: str, api_keys: dict | None = None) -> Any:
    api_keys = api_keys or {}
    serper_key = api_keys.get("serper_api_key") or settings.SERPER_API_KEY

    provider = (settings.LLM_PROVIDER or "").strip().lower()
    if not provider:
        raise ValueError("LLM_PROVIDER is not set. Use 'ollama', 'openai', or 'google' in .env.")

    if provider == "openai":
        openai_key = api_keys.get("openai_api_key") or settings.OPENAI_API_KEY
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        model = settings.OPENAI_MODEL_NAME
        base_url = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        api_key = openai_key
    elif provider == "google":
        gemini_key = api_keys.get("gemini_api_key") or settings.GEMINI_API_KEY
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

    llm = LLM(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=300,
        temperature=0.7,
    )

    allow_fallback = settings.APP_MODE == AppMode.DESKTOP
    agent_tools = []
    if serper_key or allow_fallback:
        agent_tools.append(CrewWebSearchTool(serper_api_key=serper_key, allow_fallback=allow_fallback))
        agent_tools.append(CrewWebSearchGoogleTool(serper_api_key=serper_key, allow_fallback=allow_fallback))

    researcher = Agent(
        role="Researcher",
        goal=f"Find facts about {topic}",
        backstory=(
            "You find facts matching user interests. "
            "Use the Web Search tool for any external research."
        ),
        tools=agent_tools,
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
        description=f"Research '{topic}'. \nUSER CONTEXT: {user_context}",
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
    return result
