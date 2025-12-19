import asyncio
import json
import os
import requests
from typing import Union, Type
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool

from backend.server.config import settings
from backend.server.models.schemas import NewsResponse


# --- Tools ---

class SearchToolInput(BaseModel):
    query: Union[str, dict] = Field(..., description="The search topic.")

class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the internet for facts."
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: Union[str, dict]) -> str:
        if isinstance(query, dict):
            query = query.get("description", str(query))

        if not settings.SERPER_API_KEY:
            return "Error: Serper API Key missing/configured."

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": str(query)})
        headers = {
            'X-API-KEY': settings.SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            results = response.json()
            if 'organic' in results:
                return "\n".join([f"- {item['title']}: {item['snippet']}" for item in results['organic'][:3]])
            return "No results."
        except Exception as e:
            return f"Error executing search: {e}"

# --- Service Class ---

class NewsletterService:
    def __init__(self):
        # Initialize reusable components if any
        pass

    async def generate_newsletter(self, topic: str, user_id: int, context: str = "", api_keys: dict = None) -> NewsResponse:
        """
        Async entry point for generation.
        Offloads the blocking CrewAI execution to a thread.
        """
        loop = asyncio.get_running_loop()
        
        # Run blocking task in executor
        content = await loop.run_in_executor(None, self._run_crew, topic, context, api_keys)
        
        # TODO: Integrate real billing service here
        return NewsResponse(
            topic=topic,
            content=content,
            bill={"deducted": 1, "remaining": 99}
        )

    def _run_crew(self, topic: str, context: str, api_keys: dict = None) -> str:
        """
        Synchronous / Blocking CrewAI logic.
        """
        # Resolve Keys
        serper_key = (api_keys or {}).get("serper_api_key") or settings.SERPER_API_KEY
        openai_key = (api_keys or {}).get("openai_api_key") or "NA"
        
        # 1. Config LLM
        print(f"DEBUG: Initializing LLM with Base URL: {settings.OPENAI_API_BASE}")
        print(f"DEBUG: Model: {settings.OPENAI_MODEL_NAME}")
        
        llm = LLM(
            model=f"ollama/{settings.OPENAI_MODEL_NAME.split(':')[0]}", # naive parse or use full name
            base_url=settings.OPENAI_API_BASE,
            api_key=openai_key, 
            timeout=300,
            temperature=0.7
        )

        # 2. Tools
        # Use provided key or global setting
        search_tool = WebSearchTool()
        agents_tools = [search_tool] if serper_key else []

        # 3. Agents
        researcher = Agent(
            role='Researcher',
            goal=f'Find facts about {topic}',
            backstory="You find facts matching user interests.",
            tools=agents_tools,
            llm=llm,
            verbose=True
        )

        writer = Agent(
            role='Writer',
            goal='Summarize facts',
            backstory="You write concise, engaging summaries.",
            llm=llm,
            verbose=True
        )

        # 4. Tasks
        task1 = Task(
            description=f"Research '{topic}'. Context: {context}",
            expected_output="3 key facts.",
            agent=researcher
        )

        task2 = Task(
            description=f"Write a newsletter summary on '{topic}'.",
            expected_output="A short Markdown newsletter.",
            agent=writer,
            context=[task1]
        )

        # 5. Execution
        crew = Crew(
            agents=[researcher, writer],
            tasks=[task1, task2],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

# Singleton Accessor
newsletter_service = NewsletterService()
