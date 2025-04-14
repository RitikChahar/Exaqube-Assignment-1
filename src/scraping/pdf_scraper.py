from bs4 import BeautifulSoup
from .scraper import WebScraper

class PdfScraper:
    def __init__(self, api_key):
        self.scraper = WebScraper(api_key)
        
    def scrape_pdfs(self, url):
        result = self.scraper.scrape_url(url)
        
        if 'html' not in result or not result.get('html'):
            return {'success': False, 'url': url, 'error': 'Failed to retrieve HTML content'}
            
        html_content = result['html']
        pdf_data = self.extract_pdf_data(html_content)
        
        formatted_result = {
            'success': True,
            'url': url,
            'data': pdf_data
        }
        
        return formatted_result
        
    def extract_pdf_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        pdf_data = []
        
        table_rows = soup.select('tr.hal-table-row')
        
        for row in table_rows:
            pdf_link_element = row.select_one('a.hal-link--pdf')
            
            if pdf_link_element:
                link = pdf_link_element.get('href', '')
                title = pdf_link_element.get_text(strip=True)
                
                if link and title:
                    pdf_data.append({
                        "pdf_title": title,
                        "pdf_link": link
                    })
        
        return pdf_data