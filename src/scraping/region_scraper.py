from bs4 import BeautifulSoup
from .scraper import WebScraper

class RegionScraper:
    def __init__(self, api_key):
        self.scraper = WebScraper(api_key)
        
    def scrape_regions(self, url):
        result = self.scraper.scrape_url(url)
        
        if 'html' not in result or not result.get('html'):
            return {'success': False, 'url': url, 'error': 'Failed to retrieve HTML content'}
            
        html_content = result['html']
        region_data = self.extract_region_data(html_content)
        
        formatted_result = {
            'success': True,
            'data': region_data
        }
        
        return formatted_result
        
    def extract_region_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        region_data = []
        
        region_buttons = soup.select('a.hal-button.hal-button--primary')
        
        for button in region_buttons:
            link = button.get('href', '')
            region_text = button.get_text(strip=True)
            
            region = region_text.split('\n')[0].strip() if '\n' in region_text else region_text.strip()
            
            if link and region:
                region_data.append({
                    "region": region,
                    "link": link
                })
        
        return region_data