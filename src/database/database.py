import sqlite3

def get_connection():
    conn = sqlite3.connect("scraper_data.db")
    return conn

def create_pdf_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS pdf_data (id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT, country TEXT, pdf_title TEXT, pdf_link TEXT)")
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
            country = pdf.get("country", "") 
            cursor.execute("INSERT INTO pdf_data (region, country, pdf_title, pdf_link) VALUES (?, ?, ?, ?)", (region_name, country, pdf_title, pdf_link))
    conn.commit()
    conn.close()

def fetch_pdf_data_by_region(region_input="ALL", country_input="ALL"):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT region, country, pdf_title, pdf_link FROM pdf_data"
    conditions = []
    params = []

    if region_input.lower() != "all":
        conditions.append("region = ?")
        params.append(region_input)
    if country_input.lower() != "all":
        conditions.append("country = ?")
        params.append(country_input)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_tariff_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS regions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS tariffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        region_id INTEGER,
        country TEXT, 
        liner TEXT,
        port TEXT, 
        currency TEXT,
        effective_date TEXT,
        expiry_date TEXT,
        FOREIGN KEY (region_id) REFERENCES regions (id))""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS container_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tariff_id INTEGER, 
        equipment_type TEXT, 
        size TEXT, 
        free_days INTEGER, 
        free_day_type TEXT,
        FOREIGN KEY (tariff_id) REFERENCES tariffs (id))""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS charge_buckets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        container_type_id INTEGER, 
        bucket_name TEXT, 
        start_day INTEGER, 
        end_day INTEGER, 
        rate REAL, 
        rate_unit TEXT,
        FOREIGN KEY (container_type_id) REFERENCES container_types (id))""")
    
    cursor.execute("INSERT OR IGNORE INTO regions (name) VALUES ('ALL')")
    
    conn.commit()
    conn.close()

def insert_tariff_data(data):
    conn = get_connection()
    cursor = conn.cursor()
    
    for tariff in data.get("tariffs", []):
        region_name = tariff.get("region", "ALL")
        cursor.execute("SELECT id FROM regions WHERE name = ?", (region_name,))
        region_id_result = cursor.fetchone()
        region_id = region_id_result[0] if region_id_result else 1
        
        country = tariff.get("country", "")
        liner = tariff.get("liner", "")
        port = tariff.get("port", "")
        currency = tariff.get("currency", "")
        effective_date = tariff.get("effective_date", "")
        expiry_date = tariff.get("expiry_date", "")
        
        cursor.execute("""INSERT INTO tariffs 
            (region_id, country, liner, port, currency, effective_date, expiry_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""", 
            (region_id, country, liner, port, currency, effective_date, expiry_date))
        
        tariff_id = cursor.lastrowid
        
        for container in tariff.get("container_types", []):
            equipment_type = container.get("equipment_type", "")
            size = container.get("size", "")
            free_days = container.get("free_days", 0)
            free_day_type = container.get("free_day_type", "Calendar")
            
            cursor.execute("""INSERT INTO container_types 
                (tariff_id, equipment_type, size, free_days, free_day_type) 
                VALUES (?, ?, ?, ?, ?)""", 
                (tariff_id, equipment_type, size, free_days, free_day_type))
            
            container_type_id = cursor.lastrowid
            
            for bucket in container.get("charge_buckets", []):
                bucket_name = bucket.get("bucket_name", "")
                start_day = bucket.get("start_day", 0)
                end_day = bucket.get("end_day", 0)
                rate = bucket.get("rate", 0.0)
                rate_unit = bucket.get("rate_unit", "per day")
                
                cursor.execute("""INSERT INTO charge_buckets 
                    (container_type_id, bucket_name, start_day, end_day, rate, rate_unit) 
                    VALUES (?, ?, ?, ?, ?, ?)""", 
                    (container_type_id, bucket_name, start_day, end_day, rate, rate_unit))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_pdf_table()
    create_tariff_tables()
