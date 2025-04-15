import os
import logging
import time
import urllib.parse
import requests
from dotenv import load_dotenv
from src.scraping.region_scraper import RegionScraper
from src.scraping.pdf_scraper import PdfScraper
from src.database import database
from src.extraction.process_tarffic_pdfs import process_tariff_pdfs
import config

def setup_logging():
    try:
        log_file = os.getenv('LOG_FILE', 'scraper.log')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file, mode='a'), logging.StreamHandler()])
        return logging.getLogger(__name__)
    except Exception as e:
        print("Logging setup error: " + str(e))
        raise

def scrape_with_retry(scraper_func, url, max_retries, delay, logger):
    attempts = 0
    while attempts < max_retries:
        try:
            return scraper_func(url)
        except Exception as e:
            attempts += 1
            logger.error("Scraping error for {}: {}. Attempt {}/{}".format(url, str(e), attempts, max_retries))
            time.sleep(delay)
    return {"success": False, "error": "Max retries exceeded", "data": []}

def scrape_all_pdfs(selected_region, regions, pdf_scraper, base_url, max_retries, retry_delay, logger):
    pdf_data_list = []
    for region_info in regions:
        try:
            region_name = region_info.get('region')
            if selected_region.lower() != "all" and region_name != selected_region:
                continue
            region_url = urllib.parse.urljoin(base_url, region_info.get('link'))
            logger.info("Scraping PDFs for region: " + region_name)
            pdf_result = scrape_with_retry(pdf_scraper.scrape_pdfs, region_url, max_retries, retry_delay, logger)
            pdfs_modified = []
            for pdf in pdf_result.get("data", []):
                try:
                    title = pdf.get("pdf_title", "")
                    country_name = title.split()[0] if title else ""
                    pdf["country"] = country_name
                    pdfs_modified.append(pdf)
                except Exception as e:
                    logger.error("Error processing pdf title for region {}: {}".format(region_name, str(e)))
            pdf_data_list.append({"region": region_name, "url": region_url, "pdfs": pdfs_modified})
        except Exception as e:
            logger.error("Error scraping PDFs for region {}: {}".format(region_info.get('region', 'Unknown'), str(e)))
    return pdf_data_list

if __name__ == "__main__":
    try:
        load_dotenv()
        API_KEY = os.getenv('API_KEY')
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        BASE_URL = os.getenv('BASE_URL')
        MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
        logger = setup_logging()
        logger.info("Starting scraping process")
        region_scraper = RegionScraper(API_KEY)
        main_url = urllib.parse.urljoin(BASE_URL, "/en/online-business/quotation/detention-demurrage.html")
        regions_result = scrape_with_retry(region_scraper.scrape_regions, main_url, MAX_RETRIES, RETRY_DELAY, logger)
        if not regions_result.get('success'):
            logger.error("Region scraping failed: {}".format(regions_result.get('error')))
            exit(1)
        regions = regions_result.get('data', [])
        logger.info("Regions scraped")
        selected_region = config.REGION
        pdf_scraper = PdfScraper(API_KEY)
        pdf_data_list = scrape_all_pdfs(selected_region, regions, pdf_scraper, BASE_URL, MAX_RETRIES, RETRY_DELAY, logger)
        if not pdf_data_list:
            logger.error("No matching regions found for " + selected_region)
            exit(1)
        database.create_pdf_table()
        for pdf_data in pdf_data_list:
            database.insert_pdf_data({"regions": [pdf_data]})
        logger.info("PDF data inserted")
        database.create_tariff_tables()
        process_tariff_pdfs(GEMINI_API_KEY, region=selected_region, country=config.COUNTRY)
        logger.info("PDF extraction completed")
    except Exception as e:
        logger.error("Process failed: " + str(e))
