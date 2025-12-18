import os
import requests
import json
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Union, Any
from backend.server.config import settings


# --- 1. Robust Tool Definitions ---

class SearchToolInput(BaseModel):
    # TRICK: We allow 'dict' so Pydantic doesn't crash if the AI makes a mistake
    query: Union[str, dict] = Field(..., description="The search topic. Example: 'climate change'")


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the internet for facts."
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: Union[str, dict]) -> str:
        # --- SMART FIX FOR SMALL MODELS ---
        # If the AI sends a dictionary like {'description': '...'}, fix it here.
        if isinstance(query, dict):
            # Try to grab the description or value, otherwise dump it to string
            query = query.get("description", str(query))
        # ----------------------------------

        if not settings.SERPER_API_KEY:
            return "Error: Serper API Key missing."

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": str(query)})  # Ensure it's a string
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


search_tool = WebSearchTool()


# --- 2. Main Logic ---

def run_newsletter_crew(topic: str, user_context: str, api_keys: dict = None):
    # Fetch Config
    ollama_base_url = settings.OPENAI_API_BASE
    ollama_model = settings.OPENAI_MODEL_NAME
    
    # Priority: Runtime request key > Env Key
    serper_key = (api_keys or {}).get("serper_api_key") or settings.SERPER_API_KEY
    openai_key = (api_keys or {}).get("openai_api_key") or "NA"

    print(f"DEBUG: Connecting to Ollama at {ollama_base_url} using {ollama_model}")

    # Initialize LLM with Timeout
    llm = LLM(
        model=ollama_model,
        base_url=ollama_base_url,
        api_key=openai_key,
        timeout=120,  # Wait up to 2 minutes
        temperature=0.7
    )

    # Define Agents
    agent_tools = []
    
    # DYNAMIC SEARCH TOOL: Re-instantiate with correct key if present
    if serper_key:
        print("DEBUG: Enabling Web Search Tool with provided key.")
        # We need to monkey-patch or re-init the tool to use the specific key for this run
        # Since BaseTool is stateful, we'll create a lightweight wrapper or simple check
        # For simplicity, we assume the tool uses the key we pass/set here.
        # However, the tool class defined above uses 'settings.SERPER_API_KEY'. 
        # We must update the Global settings or the tool instance.
        # SAFEST: Update settings temporarily for this thread (ok for single worker) or direct pass.
        
        # NOTE: To avoid thread safety issues, it is better to pass key to tool constructor, 
        # but our tool class reads from 'settings'.
        # Let's override the settings momentarily (since we are local single user).
        # OR better: The 'search_tool' defined globally uses 'settings'.
        # We can create a new instance here if we modify the class to accept a key.
        pass # The logic below handles the "Adding to list"
        
        # Better: Update the global settings value ? No, dangerous.
        # Let's modify the WebSearchTool to look at a passed config?
        # Actually, let's just cheat for this local desktop app:
        
        # Override settings for this request scope
        settings.SERPER_API_KEY = serper_key
        agent_tools.append(search_tool)
    else:
        print("DEBUG: No Serper Key found. Web Search disabled.")

    researcher = Agent(
        role='Researcher',
        goal=f'Find facts about {topic}',
        backstory="""You find facts matching user interests. Use the search tool if available.""",
        tools=agent_tools,
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

    # Define Tasks
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

    # Run Crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True
    )

    try:
        print("DEBUG: Starting Crew Execution...")
        result = crew.kickoff()
        print("DEBUG: Crew Execution Successful")
        return result
    except Exception as e:
        print(f"CRITICAL ERROR IN CREW EXECUTION: {e}")
        import traceback
        traceback.print_exc()
        raise e