import json
import os
import requests
import PyPDF2
from google import genai
from src.database.database import fetch_pdf_data_by_region, insert_tariff_data
from pprint import pprint

def process_tariff_pdfs(api_key, region="ALL", country="ALL"):
    try:
        rows = fetch_pdf_data_by_region(region, country)
    except Exception as e:
        print("Error fetching PDF data: " + str(e))
        return {}
    
    results = {}
    client = genai.Client(api_key=api_key)
    
    for row in rows:
        try:
            region_name, country, pdf_title, pdf_link = row
        except Exception as e:
            results["unknown_file"] = f"Row unpacking error: {str(e)}"
            continue
        
        file_path, extracted_text = download_and_extract_text(region_name, pdf_title, pdf_link)
        
        if not extracted_text:
            results[file_path] = "Failed to extract text from PDF"
            continue
            
        try:
            tariff_data = extract_tariff_data(extracted_text, client, region_name)
            insert_tariff_data(tariff_data)
            results[file_path] = "Successfully processed and saved tariff data"
        except Exception as e:
            results[file_path] = f"Failed to extract or save tariff data: {str(e)}"
    
    return results

def download_and_extract_text(region, pdf_title, pdf_link):
    try:
        dir_path = os.path.join("files", region)
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        print("Error creating directory: " + str(e))
    
    file_name = pdf_title if pdf_title.lower().endswith(".pdf") else pdf_title + ".pdf"
    file_path = os.path.join(dir_path, file_name)
    
    try:
        r = requests.get(pdf_link)
        with open(file_path, "wb") as f:
            f.write(r.content)
    except Exception:
        return file_path, ""
    
    extracted_text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text
    except Exception:
        extracted_text = ""
    
    return file_path, extracted_text

def extract_tariff_data(text, client, region="ALL"):
    prompt = f'''You are a specialized port tariff data extraction system. Extract comprehensive tariff information from the following text for region: {region}.

    Focus on extracting these key data points:
    - Region
    - Country
    - Liner/Carrier name
    - Port name
    - Equipment types and sizes
    - Currency
    - Effective and expiry dates
    - Free days and their calculation method
    - Rate tiers/buckets with their day ranges and charges

    Return the data in this JSON structure:
    {{
        "tariffs": [
            {{
                "region": "string or null",
                "country": "string or null",
                "liner": "string or null",
                "port": "string or null",
                "currency": "string or null",
                "effective_date": "string or null",
                "expiry_date": "string or null",
                "container_types": [
                    {{
                        "equipment_type": "string (e.g., Dry, Reefer, Special) or null",
                        "size": "string (e.g., 20', 40') or null",
                        "free_days": number or null,
                        "free_day_type": "string (Calendar/Working) or null",
                        "charge_buckets": [
                            {{
                                "bucket_name": "string (e.g., Bucket 1, First Period) or null",
                                "start_day": number or null,
                                "end_day": number or null,
                                "rate": number or null,
                                "rate_unit": "string (e.g., per day) or null"
                            }}
                        ]
                    }}
                ]
            }}
        ]
    }}

    Text to extract from:
    {text}

    Important: 
    1. Include ALL information you can find in the document
    2. Use precise field names as they appear in the document
    3. If a field is not explicitly mentioned in the document, use null
    4. Group related information logically by container type, port, etc.
    5. Convert all rates to numerical values without currency symbols
    6. Make sure all date fields use a consistent format (YYYY-MM-DD)
    7. If multiple container types or charge buckets exist, include them all as separate entries'''
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[len("```json"):].strip()[:-3].strip()
        
        extracted_data = json.loads(response_text)
        return extracted_data
    except Exception as e:
        print("Error calling Gemini API: " + str(e))
        raise e

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            results = process_tariff_pdfs(api_key, region="ASIA")
            print(f"Processed {len(results)} files")
            for file_path, status in results.items():
                print(f"{file_path}: {status}")
        except Exception as main_e:
            print("Error in processing tariff PDFs: " + str(main_e))
    else:
        print("Error: GEMINI_API_KEY environment variable not set")