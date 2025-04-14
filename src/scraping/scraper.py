from firecrawl import FirecrawlApp

class WebScraper:
    def __init__(self, api_key):
        self.app = FirecrawlApp(api_key=api_key)
        
    def scrape_url(self, url):
        params = {
            'formats': ['html'],
        }
            
        response = self.app.scrape_url(url=url, params=params)
        return response