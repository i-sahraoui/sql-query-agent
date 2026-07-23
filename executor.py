import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate
import pandas as pd
import os

load_dotenv()

# controls what query types are allowed
# add "INSERT", "UPDATE", "DELETE" here when write access is needed (uncomment lines 119-122)
ALLOWED_QUERY_TYPES = ["SELECT", "WITH", "EXPLAIN"]

def parse_response(agent_response):
    sql = ""
    explanation = ""

    if "SQL:" in agent_response and "Explanation:" in agent_response:
        sql_part = agent_response.split("SQL:")[1].split("Explanation:")[0].strip()
        explanation_part = agent_response.split("Explanation:")[1].strip()

        # strip markdown code fences if the model wrapped the sql in them
        sql_part = sql_part.replace("```sql", "").replace("```SQL", "").replace("```", "").strip()

        # strip trailing semicolon (may cause issues with psycopg2)
        sql_part = sql_part.rstrip(";").strip()

        sql = sql_part
        explanation = explanation_part
    else:
        return "", "", "Agent returned an unexpected format. Try rephrasing your question."

    return sql, explanation, None

def validate_query(sql):
    # block multi-statement queries (e.g. SELECT ...; DROP TABLE ...)
    if ";" in sql:
        return False, "Multi-statement queries are not allowed."

    # check if query starts with an allowed type
    first_word = sql.strip().split()[0].upper()
    if first_word not in ALLOWED_QUERY_TYPES:
        return False, f"Query type '{first_word}' is not allowed."

    return True, None

def run_query(sql):
    # wrap connection in try/except
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute(sql)

        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

        cur.close()
        conn.close()

        return rows, col_names, None

    except psycopg2.OperationalError:
        return None, None, "Could not connect to the database. Make sure Docker is running and try again."
    except Exception as e:
        return None, None, f"Query execution failed: {str(e)}"

def run_and_return(agent_response):
    # used by web UI to return data instead of printing
    sql, explanation, parse_error = parse_response(agent_response)

    if parse_error:
        return None, None, None, parse_error, "error"

    if not sql:
        return None, None, None, "Couldn't parse a query from the agent response.", "error"

    allowed, reason = validate_query(sql)
    if not allowed:
        return None, None, None, f"Query blocked: {reason}", "error"

    rows, col_names, db_error = run_query(sql)

    if db_error:
        return None, None, None, db_error, "error"

    df = pd.DataFrame(rows, columns=col_names)

    # distinguish between empty results and an actual error
    status = "empty" if df.empty else "ok"

    return sql, explanation, df, None, status

def execute(agent_response):
    # used by the CLI (main.py)
    sql, explanation, parse_error = parse_response(agent_response)

    if parse_error:
        print(f"Parse error: {parse_error}")
        return

    if not sql:
        print("Couldn't parse a query from the agent response.")
        return

    allowed, reason = validate_query(sql)
    if not allowed:
        print(f"Query blocked: {reason}")
        return

    print(f"\nExplanation: {explanation}")
    print(f"\nGenerated SQL:\n{sql}\n")

    # placeholder for confirmation step when write access is added
    # if first_word != "SELECT":
    #     confirm = input("this will modify the database. continue? (y/n): ")
    #     if confirm.lower() != "y":
    #         return

    rows, col_names, db_error = run_query(sql)

    if db_error:
        print(f"Database error: {db_error}")
        return

    if rows:
        print(tabulate(rows, headers=col_names, tablefmt="pretty"))
        print(f"\n{len(rows)} row(s) returned.")
    else:
        print("Query ran successfully, but returned no results.")
