from crewai import Agent
from src.tools.spacenews_scraper import SpaceNewsScraper
from src.tools.companynews_scraper import CompanyWebsiteScraper
from src.tools.globalnewswire_tool import GlobeNewswireScraper 
from src.tools.serpapi_tool import serpapi_scraper_to_txt
from src.tools.newTeardownCompilerTool import compile_teardown_rag 
from src.tools.governmentContract_tool import fetch_contracts_by_company


# Instantiate tools
spacenews_tool = SpaceNewsScraper
companynews_tool = CompanyWebsiteScraper
globalnewswire_tool = GlobeNewswireScraper
serpapi_tool = serpapi_scraper_to_txt
rag_tool = compile_teardown_rag
gov_contract_tool = fetch_contracts_by_company

# Agents
spacenews_agent = Agent(
    role="Space Industry Analyst",
    goal="Find the most interesting recent developments in the space sector and compile them in a txt file",
    backstory="An AI journalist who focuses on space innovation",
    tools=[spacenews_tool]
)

companynews_agent = Agent(
    role="Startup Analyst",
    goal="Find every bit of data on deeptech startup companies",
    backstory="You are a journalist who focuses on emerging technology startups",
    tools=[companynews_tool] 
)


globalnewswire_agent = Agent(
    role="Deep Tech Industry Analyst",
    goal="Find the most interesting recent developments in the deep tech sector and compile them in a txt file",
    backstory="An AI journalist who focuses on deep tech innovation",
    tools=[globalnewswire_tool]
)

serpapi_agent = Agent(
    role="Web Scraping Research Analyst",
    goal="Find relevant news articles about a target company from trusted sites",
    backstory=(
        "You're a focused and resourceful analyst using Google Search and BeautifulSoup to gather and store the most relevant articles about a target company."
    ),
    tools=[serpapi_tool],
)

teardown_agent = Agent(
    role="Teardown Analyst/Compiler",
    goal="Answer specific teardown questions with precision using the scraped company data",
    backstory="You're a detail-oriented business analyst at Klear tasked with analyzing company data and answering structured questions for internal strategy docs.",
    tools=[rag_tool],
    verbose=True
)

contract_agent = Agent(
    role="Government Contract Researcher",
    goal="Find and save US government contracts for a given company",
    backstory="You specialize in tracking down and organizing federal spending on specific companies.",
    tools=[gov_contract_tool],
    verbose=True
)