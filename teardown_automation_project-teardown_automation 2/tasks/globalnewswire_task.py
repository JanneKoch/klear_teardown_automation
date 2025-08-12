from crewai import Task
from src.agents.agent import globalnewswire_agent

globalnewswire_task = Task(
    description="Search for all GlobeNewsWire articles about company.",
    expected_output="List of article titles and links and a summary of each article. I also want every entire article extracted and compiled in a txt file.",
    agent=globalnewswire_agent
)