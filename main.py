import os
import json
import logging
import urllib.parse
import time
import requests

from src.scraping.region_scraper import RegionScraper
from src.scraping.pdf_scraper import PdfScraper

from dotenv import load_dotenv
import os

def setup_logging():
    log_file = os.getenv('LOG_FILE', 'scraper.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def scrape_with_retry(scraper_func, url, max_retries=3, delay=2, logger=None):
    attempts = 0
    while attempts < max_retries:
        try:
            return scraper_func(url)
        except requests.exceptions.HTTPError as e:
            if "timeout" in str(e).lower() and attempts < max_retries - 1:
                attempts += 1
                logger.warning(f"Request timed out for {url}. Retrying in {delay} seconds... (Attempt {attempts}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error(f"Failed to scrape {url} after {attempts+1} attempts: {str(e)}")
                return {"success": False, "error": str(e), "data": []}
        except Exception as e:
            logger.error(f"Unexpected error when scraping {url}: {str(e)}")
            return {"success": False, "error": str(e), "data": []}
    
    return {"success": False, "error": "Max retries exceeded", "data": []}

def scrape_all_regions_and_pdfs(api_key, base_url, max_retries=3, delay=2, logger=None):
    logger.info("Starting to scrape regions and PDFs")
    
    region_scraper = RegionScraper(api_key)
    pdf_scraper = PdfScraper(api_key)
    
    main_url = f"{base_url}/en/online-business/quotation/detention-demurrage.html"
    
    regions_result = scrape_with_retry(
        scraper_func=region_scraper.scrape_regions,
        url=main_url,
        max_retries=max_retries,
        delay=delay,
        logger=logger
    )
    
    if not regions_result.get('success', False):
        logger.error(f"Failed to scrape regions: {regions_result.get('error', 'Unknown error')}")
        return None
    
    all_regions_pdf_data = {
        'success': True,
        'regions': []
    }
    
    for region_info in regions_result['data']:
        region_name = region_info['region']
        region_link = region_info['link']
        
        logger.info(f"Scraping PDFs for region: {region_name}")
        
        region_url = urllib.parse.urljoin(base_url, region_link)
        
        region_pdf_result = scrape_with_retry(
            scraper_func=pdf_scraper.scrape_pdfs,
            url=region_url,
            max_retries=max_retries,
            delay=delay,
            logger=logger
        )
        
        if region_pdf_result.get('success', False):
            region_data = {
                'region': region_name,
                'url': region_url,
                'pdfs': region_pdf_result['data']
            }
            all_regions_pdf_data['regions'].append(region_data)
            logger.info(f"Found {len(region_pdf_result['data'])} PDFs for {region_name}")
        else:
            logger.error(f"Failed to scrape PDFs for region {region_name}: {region_pdf_result.get('error', 'Unknown error')}")
            all_regions_pdf_data['regions'].append({
                'region': region_name,
                'url': region_url,
                'error': region_pdf_result.get('error', 'Unknown error'),
                'pdfs': []
            })
    
    return all_regions_pdf_data

def save_results_to_file(data, output_file, logger=None):
    logger.info(f"Saving results to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved successfully")

if __name__ == "__main__":
    load_dotenv()
    API_KEY = os.getenv('API_KEY')
    BASE_URL = os.getenv('BASE_URL')
    OUTPUT_FILE = os.getenv('OUTPUT_FILE')
    
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
    
    logger = setup_logging()
    logger.info("Starting detention and demurrage PDF scraping process")
    
    all_data = scrape_all_regions_and_pdfs(API_KEY, BASE_URL, MAX_RETRIES, RETRY_DELAY, logger)
    
    if all_data:
        save_results_to_file(all_data, OUTPUT_FILE, logger)
        
        total_pdfs = sum(len(region.get('pdfs', [])) for region in all_data['regions'])
        total_regions = len(all_data['regions'])
        
        logger.info(f"Scraping completed. Found {total_pdfs} PDFs across {total_regions} regions.")
    else:
        logger.error("Scraping process failed")