import sqlite3

def get_connection():
    conn = sqlite3.connect("scraper_data.db")
    return conn

def create_pdf_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS pdf_data (id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT, pdf_title TEXT, pdf_link TEXT)")
    conn.commit()
    conn.close()

def insert_pdf_data(all_data):
    conn = get_connection()
    cursor = conn.cursor()
    for region in all_data.get("regions", []):
        region_name = region.get("region", "")
        for pdf in region.get("pdfs", []):
            pdf_title = pdf.get("pdf_title", "")
            pdf_link = pdf.get("pdf_link", "")
            cursor.execute("INSERT INTO pdf_data (region, pdf_title, pdf_link) VALUES (?, ?, ?)", (region_name, pdf_title, pdf_link))
    conn.commit()
    conn.close()

def fetch_pdf_data_by_region(region_input):
    conn = get_connection()
    cursor = conn.cursor()
    if region_input.lower() == "all":
        cursor.execute("SELECT region, pdf_title, pdf_link FROM pdf_data")
    else:
        cursor.execute("SELECT region, pdf_title, pdf_link FROM pdf_data WHERE region = ?", (region_input,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_tariff_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tariffs (id INTEGER PRIMARY KEY AUTOINCREMENT, area TEXT, country TEXT, charge_type TEXT, port TEXT, currency TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS container_types (id INTEGER PRIMARY KEY AUTOINCREMENT, tariff_id INTEGER, type TEXT, size TEXT, free_time_days INTEGER, free_time_day_type TEXT, detention_days INTEGER, detention_day_type TEXT, detention_rate REAL, FOREIGN KEY (tariff_id) REFERENCES tariffs (id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS rate_tiers (id INTEGER PRIMARY KEY AUTOINCREMENT, container_type_id INTEGER, tier_name TEXT, start_day INTEGER, end_day INTEGER, rate REAL, rate_unit TEXT, FOREIGN KEY (container_type_id) REFERENCES container_types (id))")
    conn.commit()
    conn.close()

def insert_tariff_data(data):
    conn = get_connection()
    cursor = conn.cursor()
    for tariff in data.get("tariffs", []):
        area = tariff.get("area", "")
        country = tariff.get("country", "")
        charge_type = tariff.get("charge_type", "")
        port = tariff.get("port", "")
        currency = tariff.get("currency", "")
        cursor.execute("INSERT INTO tariffs (area, country, charge_type, port, currency) VALUES (?, ?, ?, ?, ?)", (area, country, charge_type, port, currency))
        tariff_id = cursor.lastrowid
        for container in tariff.get("container_types", []):
            c_type = container.get("type", "")
            size = container.get("size", "")
            free_time = container.get("free_time", {})
            free_time_days = free_time.get("days", None)
            free_time_day_type = free_time.get("day_type", "")
            detention = container.get("detention", {})
            detention_days = detention.get("days", None)
            detention_day_type = detention.get("day_type", "")
            detention_rate = detention.get("rate", None)
            cursor.execute("INSERT INTO container_types (tariff_id, type, size, free_time_days, free_time_day_type, detention_days, detention_day_type, detention_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tariff_id, c_type, size, free_time_days, free_time_day_type, detention_days, detention_day_type, detention_rate))
            container_type_id = cursor.lastrowid
            for tier in container.get("rate_tiers", []):
                tier_name = tier.get("tier_name", "")
                start_day = tier.get("start_day", None)
                end_day = tier.get("end_day", None)
                rate = tier.get("rate", None)
                rate_unit = tier.get("rate_unit", "")
                cursor.execute("INSERT INTO rate_tiers (container_type_id, tier_name, start_day, end_day, rate, rate_unit) VALUES (?, ?, ?, ?, ?, ?)", (container_type_id, tier_name, start_day, end_day, rate, rate_unit))
    conn.commit()
    conn.close()

def fetch_tariff_data_by_area(area_value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, area, country, charge_type, port, currency FROM tariffs WHERE area = ?", (area_value,))
    tariffs_rows = cursor.fetchall()
    
    result = []
    for row in tariffs_rows:
        tariff_id, area, country, charge_type, port, currency = row
        tariff_dict = {
            "area": area,
            "country": country,
            "charge_type": charge_type,
            "port": port,
            "currency": currency,
            "container_types": []
        }
        
        cursor.execute("SELECT id, type, size, free_time_days, free_time_day_type, detention_days, detention_day_type, detention_rate FROM container_types WHERE tariff_id = ?", (tariff_id,))
        container_rows = cursor.fetchall()
        for cont in container_rows:
            (container_type_id, c_type, size, free_time_days, free_time_day_type, detention_days, detention_day_type, detention_rate) = cont
            container_dict = {
                "type": c_type,
                "size": size,
                "free_time": {
                    "days": free_time_days,
                    "day_type": free_time_day_type
                },
                "detention": {
                    "days": detention_days,
                    "day_type": detention_day_type,
                    "rate": detention_rate
                },
                "rate_tiers": []
            }
            
            cursor.execute("SELECT tier_name, start_day, end_day, rate, rate_unit FROM rate_tiers WHERE container_type_id = ?", (container_type_id,))
            tier_rows = cursor.fetchall()
            for tier in tier_rows:
                tier_name, start_day, end_day, rate, rate_unit = tier
                tier_dict = {
                    "tier_name": tier_name,
                    "start_day": start_day,
                    "end_day": end_day,
                    "rate": rate,
                    "rate_unit": rate_unit
                }
                container_dict["rate_tiers"].append(tier_dict)
            
            tariff_dict["container_types"].append(container_dict)
        
        result.append(tariff_dict)
    
    conn.close()
    return result

if __name__ == "__main__":
    create_pdf_table()
    create_tariff_tables()