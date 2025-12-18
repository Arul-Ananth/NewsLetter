import os
import requests
import json
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Union, Optional, List
from backend.core.security import get_secret
from backend.core.db.vector import VectorDB
# --- Tools ---

class SearchToolInput(BaseModel):
    query: str = Field(..., description="The search topic.")

class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the internet for facts."
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: str) -> str:
        serper_key = get_secret("serper_api_key")
        if serper_key:
            return self._search_serper(query, serper_key)
        
        # TODO: Implement DuckDuckGo fallback
        return "Search disabled: No Serper API Key found in Secure Storage."

    def _search_serper(self, query: str, key: str) -> str:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': key,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            results = response.json()
            if 'organic' in results:
                # Return top 3 results
                return "\n".join([f"- {item['title']}: {item['snippet']}" for item in results['organic'][:3]])
            return "No results."
        except Exception as e:
            return f"Error executing search: {e}"

class RecallToolInput(BaseModel):
    query: str = Field(..., description="Topic to recall from long-term memory.")

class ContextRecallTool(BaseTool):
    name: str = "Context Recall"
    description: str = "Search long-term memory for previous research."
    args_schema: Type[BaseModel] = RecallToolInput

    def _run(self, query: str) -> str:
        try:
            vdb = VectorDB()
                results = vdb.search(vector=[0.0]*1536) 2
            # We need an embedding function here to use VectorDB effectively.
            # For now, return placeholder or assume VectorDB handles embedding (it doesn't, Qdrant client needs vector).
            # The user plan says "Stores embeddings of research results."
            # We need an embedding model.
            return "Memory recall not fully implemented (requires embedding model)."
        except Exception as e:
            return f"Error recalling context: {e}"

# --- Main Logic ---

def run_newsletter_crew(topic: str, user_context: str) -> str:
    """
    Run the newsletter generation crew.
    """
    
    # LLM Config - Default to Ollama locally
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL_VAR", "mistral")
    
    llm = LLM(
        model=f"ollama/{ollama_model}",
        base_url=ollama_base_url,
        timeout=120,
        temperature=0.7
    )

    search_tool = WebSearchTool()
    # recall_tool = ContextRecallTool() # logic incomplete without embeddings

    researcher = Agent(
        role='Researcher',
        goal=f'Find facts about {topic}',
        backstory="You find facts matching user interests. Use the search tool if available.",
        tools=[search_tool],
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

    task1 = Task(
        description=f"Research '{topic}'. \nUSER CONTEXT: {user_context}",
        expected_output="3 key facts.",
        agent=researcher
    )

    task2 = Task(
        description=f"Write a newsletter summary on '{topic}'.",
        expected_output="A short Markdown newsletter.",
        agent=writer,
        context=[task1]
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True
    )

    result = crew.kickoff()
    return str(result)
