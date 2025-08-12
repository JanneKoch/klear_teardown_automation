from crewai.tools import tool
from bs4 import BeautifulSoup
import requests
import time
from typing import List, Dict
import os

@tool("GlobeNewswire Press Release Scraper")
def GlobeNewswireScraper(company: str, max_articles: int = 20, output_folder: str = "output") -> str:
    """
    Searches GlobeNewswire for press releases related to the given company, scrapes each release,
    and saves full text output to a .txt file.
    """
    try:
        query = company.strip().replace(" ", "+")
        url = f"https://www.globenewswire.com/Search?q={query}"

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

        response = session.get(url)
        if response.status_code != 200:
            return f"Failed to retrieve search results. Status code: {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.select(".main-content .news-title a")

        if not posts:
            return f"No GlobeNewswire press releases found for '{company}'."

        articles = []
        for i, post in enumerate(posts[:max_articles]):
            time.sleep(10)
            article_data = scrape_gnw_article(session, post)
            if article_data:
                articles.append(article_data)

        if not articles:
            return f"No article content could be extracted for '{company}'."

        # Format and save
        result = f"GlobeNewswire press releases related to '{company}':\n\n"
        for i, article in enumerate(articles, 1):
            result += f"{i}. {article['title']}\n"
            result += f"URL: {article['url']}\n"
            result += f"Full Text:\n{article['full_text']}\n\n{'='*80}\n\n"

        filename = f"globenewswire_{company.replace(' ', '_').lower()}.txt"
        filepath = os.path.join(output_folder, filename)
        os.makedirs(output_folder, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.strip())

        return f"Saved GlobeNewswire releases to '{filepath}'"

    except Exception as e:
        return f"Error scraping GlobeNewswire: {str(e)}"

def scrape_gnw_article(session: requests.Session, post_link) -> Dict[str, str]:
    """
    Scrapes a single GlobeNewswire press release.
    """
    try:
        title = post_link.get_text(strip=True)
        url = "https://www.globenewswire.com" + post_link["href"]

        response = session.get(url)
        if response.status_code != 200:
            return {"title": title, "url": url, "full_text": f"Failed to load article: {response.status_code}"}

        soup = BeautifulSoup(response.text, "html.parser")
        content_paragraphs = soup.select(".article-body p")

        full_text = "\n".join(p.get_text(strip=True) for p in content_paragraphs if p.get_text(strip=True))

        return {
            "title": title,
            "url": url,
            "full_text": full_text or "Could not extract article content."
        }

    except Exception as e:
        return {
            "title": post_link.get_text(strip=True) if post_link else "Unknown",
            "url": post_link["href"] if post_link and post_link.has_attr("href") else "Unknown",
            "full_text": f"Error scraping article: {str(e)}"
        }
