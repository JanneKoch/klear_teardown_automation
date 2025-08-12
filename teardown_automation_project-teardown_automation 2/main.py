import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from crewai import Crew

#SpaceNews Scraper Agent
from tasks.spacenews_task import spacenews_task
from src.agents.agent import spacenews_agent

#CompanyNews Scraper Agent
from tasks.companynews_task import companynews_task
from src.agents.agent import companynews_agent

#GlobeNewsWire Scraper Agent
from tasks.globalnewswire_task import globalnewswire_task
from src.agents.agent import globalnewswire_agent

#SerpAPI Scraper Agent
from tasks.serpapi_task import serpapi_task
from src.agents.agent import serpapi_agent

#Teardown Compiler Agent
from tasks.teardown_task import teardown_tasks
from src.agents.agent import teardown_agent

#Government Contract Agent
from tasks.government_contract_task import government_contract_task
from src.agents.agent import contract_agent


crew = Crew(
    agents=[teardown_agent],  # 👈 Include both agents
    tasks=teardown_tasks, # 👈 Include both tasks
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff(inputs={"company_name": "Solestial"})
    print("\n🧠 FINAL RESULT:")
    print(result)