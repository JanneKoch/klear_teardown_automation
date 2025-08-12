from crewai.tools import tool
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin, urlparse
from collections import deque

@tool("Company Website Scraper")
def CompanyWebsiteScraper(company_url: str, max_pages: int = 15, output_folder: str = "output") -> str:
    """
    Scrapes visible text content from a company's website (e.g., https://solestial.com/)
    and saves it to a .txt file in the output/ directory.

    Args:
        company_url (str): Homepage URL of the company (e.g., "https://solestial.com/")
        max_pages (int): Max number of internal pages to visit (default: 15)

    Returns:
        str: Path to saved text file with scraped content.
    """
    try:
        visited = set()
        queue = deque([company_url])
        content = []
        base_domain = urlparse(company_url).netloc

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

        priority_keywords = ['news', 'press', 'blog', 'in the news', 'media', 'about', 'team', 'leadership']

        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited or urlparse(url).netloc != base_domain:
                continue

            try:
                response = session.get(url, timeout=5)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else url

                text_blocks = []

                # Extract headers as labels
                headers = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
                text_blocks += [f"[{header}]" for header in headers]

                # Extract content from relevant tags
                for tag in ["p", "li", "span", "article"]:
                    text_blocks += [t.get_text(strip=True) for t in soup.find_all(tag) if t.get_text(strip=True)]

                # De-duplicate
                seen = set()
                unique_blocks = []
                for block in text_blocks:
                    if block not in seen:
                        seen.add(block)
                        unique_blocks.append(block)

                if unique_blocks:
                    content.append(f"\n--- {title} ({url}) ---\n" + "\n".join(unique_blocks))

                visited.add(url)

                # Discover internal links
                internal_links = [urljoin(company_url, tag['href']) for tag in soup.find_all("a", href=True)]
                priority_links = [link for link in internal_links if any(kw in link.lower() for kw in priority_keywords)]
                other_links = [link for link in internal_links if link not in priority_links]

                # Add to queue in order
                queue.extend(priority_links + other_links)

            except Exception:
                continue  # Skip problematic pages silently

        if not content:
            return f"No content scraped from {company_url}."

        # Format and save to file
        os.makedirs(output_folder, exist_ok=True)
        company_name = base_domain.replace("www.", "").replace(".", "_")
        file_path = os.path.join(output_folder, f"{company_name}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(content))

        return f"Scraped data saved to '{file_path}'"

    except Exception as e:
        return f"Error scraping company website: {str(e)}"
