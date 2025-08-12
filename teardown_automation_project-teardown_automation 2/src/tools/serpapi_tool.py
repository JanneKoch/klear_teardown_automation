import os
from serpapi import GoogleSearch
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

@tool("SerpAPI Article Scraper Tool")
def serpapi_scraper_to_txt(company: str, sites: str = "techcrunch.com,venturebeat.com,crunchbase.com,techstartups.com,siliconangle.com", num_results: int = 5, output_folder: str = "output") -> str:
    """
    Searches specific news sites for articles about the given company using SerpAPI,
    scrapes the article text, and saves each article into a separate .txt file in the output_folder folder.
    """
    # Debug: Check if API key is loaded
    if not SERPAPI_API_KEY:
        return "❌ Error: SERPAPI_API_KEY not found in environment variables"
    
    print(f"🔑 API Key loaded: {SERPAPI_API_KEY[:10]}...")
    
    site_list = [s.strip() for s in sites.split(",") if s.strip()]
    os.makedirs(output_folder, exist_ok=True)

    results = []
    file_count = 1

    # Try multiple search strategies
    search_strategies = [
        f"site:{sites} {company}",  # Original approach
        f"{company}",  # Broader search without site restriction
        f'"{company}"',  # Exact phrase search
        f"{company} company",  # Add "company" keyword
        f"{company} startup",  # Add "startup" keyword
    ]

    for strategy in search_strategies:
        print(f"🔍 Trying search strategy: {strategy}")
        
        params = {
            "q": strategy,
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "num": num_results
        }

        try:
            search = GoogleSearch(params)
            search_results = search.get_dict()
            
            # Handle the case where we get HTML error instead of JSON
            if isinstance(search_results, str) or not isinstance(search_results, dict):
                print(f"❌ Got non-JSON response from SerpAPI (likely server error 522)")
                print(f"Response type: {type(search_results)}")
                continue
            
            # Debug: Check what we got back
            print(f"🔍 Search results type: {type(search_results)}")
            print(f"🔍 Search results keys: {list(search_results.keys()) if isinstance(search_results, dict) else 'Not a dict'}")
            
            # Check for API errors
            if "error" in search_results:
                print(f"❌ API Error: {search_results['error']}")
                continue
                
            organic_results = search_results.get("organic_results", [])
            print(f"📄 Found {len(organic_results)} results for strategy: {strategy}")

            if len(organic_results) > 0:
                for res in organic_results:
                    title = res.get("title", "No Title")
                    link = res.get("link")
                    snippet = res.get("snippet", "")
                    
                    print(f"📰 Processing: {title}")
                    article_text = scrape_article_text(link)

                    if article_text and len(article_text) > 100:  # Only save substantial content
                        filename = os.path.join(output_folder, f"{company.lower().replace(' ', '_')}_{file_count}.txt")
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(f"Title: {title}\nURL: {link}\nSnippet: {snippet}\n\n{article_text}")
                        print(f"✅ Saved: {title} ➜ {filename}")
                        file_count += 1
                    else:
                        print(f"⚠️ Skipped (no content): {link}")
                
                # If we found results, stop trying other strategies
                if file_count > 1:
                    break
            else:
                print(f"No results for strategy: {strategy}")
                    
        except Exception as e:
            print(f"❌ Error with strategy '{strategy}': {str(e)}")
            continue

    success_message = f"Scraped and saved {file_count - 1} articles for '{company}' in '{output_folder}'"
    print(success_message)
    return success_message

def scrape_article_text(url: str) -> str:
    """
    Scrapes and returns main text content from an article URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        return text.strip()
        
    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")
        return ""