import json
import os
import requests
import PyPDF2
import openai
from ..database.database import fetch_pdf_data_by_region, insert_tariff_data, create_tariff_tables

def process_tariff_pdfs(api_key, region="ALL"):
    rows = fetch_pdf_data_by_region(region)
    
    results = {}
    client = openai.OpenAI(api_key=api_key)
    
    for row in rows:
        region_name, pdf_title, pdf_link = row
        file_path, extracted_text = download_and_extract_text(region_name, pdf_title, pdf_link)
        
        if not extracted_text:
            results[file_path] = "Failed to extract text from PDF"
            continue
            
        try:
            tariff_data = extract_tariff_data(extracted_text, client, region_name)
            create_tariff_tables()
            insert_tariff_data(tariff_data)
            results[file_path] = "Successfully processed and saved tariff data"
        except Exception as e:
            results[file_path] = f"Failed to extract or save tariff data: {str(e)}"
    
    return results

def download_and_extract_text(region, pdf_title, pdf_link):
    dir_path = os.path.join("files", region)
    os.makedirs(dir_path, exist_ok=True)
    
    file_name = pdf_title if pdf_title.endswith(".pdf") else pdf_title + ".pdf"
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
    prompt = f"""
You are a specialized port tariff data extraction system. Extract comprehensive tariff information from the following text for region: {region}.

Focus on extracting these key data points:
- Area/Region
- Country
- Charge Type (e.g., MHO, Demurrage, Detention)
- Port name and details
- Equipment types (20', 40', etc.)
- Free time periods (days)
- Day calculation method (Calendar/Working)
- Rates for different container types (Dry, Reefer, Special)
- Currency
- Rate tiers/buckets with their corresponding day ranges

Return the data in this JSON structure:
{{
    "tariffs": [
        {{
            "area": "string",
            "country": "string",
            "charge_type": "string",
            "port": "string",
            "currency": "string",
            "container_types": [
                {{
                    "type": "string (e.g., Dry, Reefer, Special)",
                    "size": "string (e.g., 20', 40')",
                    "free_time": {{
                        "days": number,
                        "day_type": "string (Calendar/Working)"
                    }},
                    "detention": {{
                        "days": number,
                        "day_type": "string",
                        "rate": number
                    }},
                    "rate_tiers": [
                        {{
                            "tier_name": "string (e.g., Tier 1)",
                            "start_day": number,
                            "end_day": number,
                            "rate": number,
                            "rate_unit": "string (e.g., per day)"
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
2. Use precise field names from the document
3. If a field is not explicitly mentioned, infer the most likely value or mark as null
4. Group related information logically by container type, port, etc.
5. Convert all rates to numerical values without currency symbols
"""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    response_text = response.choices[0].message.content.strip()
    extracted_data = json.loads(response_text)
    
    return extracted_data

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        results = process_tariff_pdfs(api_key, region="ASIA")
        print(f"Processed {len(results)} files")
        for file_path, status in results.items():
            print(f"{file_path}: {status}")
    else:
        print("Error: OPENAI_API_KEY environment variable not set")