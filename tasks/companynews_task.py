from crewai import Task
from src.agents.agent import companynews_agent

companynews_task = Task(
    description="Scrape the company's website and extract all useful text-based content.",
    expected_output="A .txt file with structured information scraped from the company's homepage and subpages.",
    agent=companynews_agent

    # janne's code
    # agent=companynews_agent,
    # inputs={"company_url": "https://solestial.com/"}
)
