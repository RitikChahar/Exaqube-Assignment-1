import sqlite3

def get_connection():
    conn = sqlite3.connect("scraper_data.db")
    return conn

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS pdf_data (id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT, pdf_title TEXT, pdf_link TEXT)")
    conn.commit()
    conn.close()

def insert_data(all_data):
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

def fetch_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pdf_data")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    create_table()