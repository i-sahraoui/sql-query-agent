import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from schema_reader import get_schema
from db_sampler import get_db_profile
from agent import generate_sql
from executor import execute, parse_response

load_dotenv()

LOG_FILE = "query_log.csv"

def log_query(question, sql):
    # write each query to csv, create file with header if it doesn't exist
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "question", "generated_sql"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question, sql])

def main():
    print("Loading schema and database profile...")
    schema = get_schema()
    db_profile = get_db_profile()
    print("Type your question or 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "quit":
            print("Exiting.")
            break

        if not question:
            continue

        print("\nGenerating query...")
        agent_response = generate_sql(question, schema, db_profile)

        sql, explanation, parse_error = parse_response(agent_response)
        if not parse_error and sql:
            log_query(question, sql)

        execute(agent_response)
        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    main()
