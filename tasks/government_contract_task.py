from crewai import Task
from src.agents.agent import contract_agent

government_contract_task = Task(
    description="Use the USAspending API to find government contracts awarded to {company_name} and save them to a text file.",
    expected_output="Path to a text file with contract data",
    agent=contract_agent,
)
