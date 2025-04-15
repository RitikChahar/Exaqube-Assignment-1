import sqlite3
from openpyxl import Workbook

def get_connection():
    conn = sqlite3.connect("scraper_data.db")
    return conn

def export_db_to_excel(filename="exported_data.xlsx"):
    conn = get_connection()
    cursor = conn.cursor()
    wb = Workbook()
    wb.remove(wb.active)

    tables = ["pdf_data", "regions", "tariffs", "container_types", "charge_buckets"]

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]

        ws = wb.create_sheet(title=table)
        ws.append(col_names)
        for row in rows:
            ws.append(row)

    conn.close()
    wb.save(filename)

if __name__ == "__main__":
    export_db_to_excel()