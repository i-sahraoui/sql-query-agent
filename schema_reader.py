import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_schema():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()

    # pull all columns from our 4 tables
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # group columns by table and format as readable string
    schema_str = ""
    current_table = None
    for table, column, dtype in rows:
        if table != current_table:
            schema_str += f"\nTable: {table}\n"
            current_table = table
        schema_str += f"  - {column} ({dtype})\n"

    return schema_str


if __name__ == "__main__":
    print(get_schema())
