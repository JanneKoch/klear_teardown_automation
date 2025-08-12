from crewai import Task
from src.agents.agent import serpapi_agent

serpapi_task = Task(
    description="Use SerpAPI to search for `{company_name}` in trusted news sources: `{target_sites}`. Save article texts to `.txt` files.",
    expected_output="Multiple .txt files containing article text scraped using BeautifulSoup from Google search results via SerpAPI.",
    agent=serpapi_agent
)