import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# max characters for the full profile before truncating to stay under API limits
MAX_PROFILE_LENGTH = 12000

def get_db_profile():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()

    # pull table names
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]

    # only allow alphanumeric and underscores to prevent injection
    safe_tables = [t for t in tables if t.replace("_", "").isalnum()]

    profile = ""

    for table in safe_tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cur.fetchone()[0]
        profile += f"\nTable: {table} ({row_count} rows)\n"

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        columns = cur.fetchall()

        for col, dtype in columns:
            if dtype in ("character varying", "text"):
                cur.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table}")
                distinct_count = cur.fetchone()[0]

                if distinct_count <= 30:
                    cur.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL ORDER BY {col} LIMIT 30")
                    values = [str(row[0]) for row in cur.fetchall()]
                    profile += f"  - {col} ({dtype}): [{', '.join(values)}]\n"
                else:
                    profile += f"  - {col} ({dtype}): {distinct_count} unique values (high cardinality)\n"

            elif dtype in ("numeric", "integer", "bigint", "real", "double precision"):
                cur.execute(f"SELECT MIN({col}), MAX({col}) FROM {table}")
                min_val, max_val = cur.fetchone()
                profile += f"  - {col} ({dtype}): range {min_val} to {max_val}\n"

            elif dtype == "date":
                cur.execute(f"SELECT MIN({col}), MAX({col}) FROM {table}")
                min_val, max_val = cur.fetchone()
                profile += f"  - {col} (date): {min_val} to {max_val} (format: YYYY-MM-DD)\n"

            else:
                profile += f"  - {col} ({dtype})\n"

        # 2 sample rows per table so the agent can see real data format
        cur.execute(f"SELECT * FROM {table} LIMIT 2")
        sample_rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        profile += f"  Sample rows:\n"
        for row in sample_rows:
            row_str = ", ".join(f"{col_names[i]}: {row[i]}" for i in range(len(col_names)))
            profile += f"    {row_str}\n"

        profile += f"  Null rates:\n"
        for col, dtype in columns:
            cur.execute(f"SELECT ROUND(100.0 * SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) FROM {table}")
            null_rate = cur.fetchone()[0]
            if null_rate and null_rate > 0:
                profile += f"    - {col}: {null_rate}% null\n"

    cur.close()
    conn.close()

    if len(profile) > MAX_PROFILE_LENGTH:
        profile = profile[:MAX_PROFILE_LENGTH] + "\n\n[profile truncated due to large database size]"

    return profile


if __name__ == "__main__":
    print(get_db_profile())
