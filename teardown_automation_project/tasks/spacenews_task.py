from crewai import Task
from src.agents.agent import spacenews_agent

spacenews_task = Task(
    description="Search for all SpaceNews articles about company.",
    expected_output="List of article titles and links and a summary of each article. I also want every entire article extracted and compiled in a txt file.",
    agent=spacenews_agent
)