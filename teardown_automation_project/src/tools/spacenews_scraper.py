from crewai.tools import tool
from bs4 import BeautifulSoup
import requests
import time
from typing import List, Dict
import os

@tool("SpaceNews Article Scraper")
def SpaceNewsScraper(company: str, max_articles: int = 20, output_folder: str = "output") -> str:
    """
    Searches SpaceNews for articles related to the given company, scrapes each article,
    and saves full text output to a .txt file.
    """
    try:
        query = company.strip().replace(" ", "+")
        url = f"https://spacenews.com/?s={query}"

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        })

        # Get search results
        response = session.get(url)
        if response.status_code != 200:
            return f"Failed to retrieve search results. Status code: {response.status_code}"
        time.sleep(10)

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.select("h2.entry-title a")

        if not posts:
            return f"No articles found on SpaceNews for '{company}'."

        # Scrape individual articles
        articles = []
        for i, post in enumerate(posts[:max_articles]):
            if i > 0:
                time.sleep(10)
            article_data = scrape_article(session, post)
            if article_data:
                articles.append(article_data)

        if not articles:
            return f"Could not scrape any article content for '{company}'."

        # Format full article text output
        result = f"Articles related to '{company}' from SpaceNews:\n\n"
        for i, article in enumerate(articles, 1):
            result += f"{i}. {article['title']}\n"
            result += f"URL: {article['url']}\n"
            result += f"Full Text:\n{article['full_text']}\n\n{'='*80}\n\n"

        # Save to text file
        filename = f"spacenews_{company.replace(' ', '_').lower()}.txt"
        filepath = os.path.join(output_folder, filename)
        os.makedirs(output_folder, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.strip())

        return f"Full article text saved to '{filepath}'"

    except Exception as e:
        return f"An error occurred while scraping SpaceNews: {str(e)}"


def scrape_article(session: requests.Session, post_link) -> Dict[str, str]:
    """
    Scrapes an individual SpaceNews article and returns full text.
    """
    try:
        title = post_link.get_text(strip=True)
        url = post_link["href"]

        response = session.get(url)
        if response.status_code != 200:
            return {"title": title, "url": url, "full_text": f"Could not retrieve article content: {response.status_code}"}

        soup = BeautifulSoup(response.text, "html.parser")

        content_selectors = [
            ".entry-content p",
            ".post-content p",
            "article p",
            ".content p"
        ]

        content_paragraphs = []
        for selector in content_selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                content_paragraphs = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                break

        if not content_paragraphs:
            return {"title": title, "url": url, "full_text": "Could not extract article content."}

        full_text = "\n".join(content_paragraphs)

        return {
            "title": title,
            "url": url,
            "full_text": full_text
        }

    except Exception as e:
        return {
            "title": post_link.get_text(strip=True) if post_link else "Unknown",
            "url": post_link["href"] if post_link and post_link.has_attr("href") else "Unknown",
            "full_text": f"Error scraping article: {str(e)}"
        }
