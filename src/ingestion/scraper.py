import requests
from bs4 import BeautifulSoup

class F1LiveWebScraper:
    def __init__(self):
        # We define headers so the official servers recognize the script as a valid browser request
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_and_extract_text(self, url: str) -> str:
        """Hits a live URL, scrapes the webpage, and filters out clean text paragraphs."""
        print(f"🌐 [WEB SCRAPER] Initializing live connection to: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ Failed to access webpage. HTTP Status: {response.status_code}")
                return ""
            
            # Parse the raw HTML markup tree
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Strip away non-informative elements like scripts, ads, and navigation bars
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.extract()
                
            # Extract paragraphs and structural data blocks
            paragraphs = [p.get_text().strip() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'table'])]
            clean_text = "\n".join([line for line in paragraphs if line])
            
            print(f"✅ Successfully scraped {len(clean_text)} characters of live text data.")
            return clean_text
            
        except Exception as e:
            print(f"❌ Scraping error encountered: {str(e)}")
            return ""