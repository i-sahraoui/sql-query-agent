import streamlit as st
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from schema_reader import get_schema
from agent import generate_sql
from executor import run_and_return, parse_response
from db_sampler import get_db_profile

load_dotenv()

st.set_page_config(page_title="SQL Query Agent", layout="wide")

# check all required env vars are present at startup
REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "ANTHROPIC_API_KEY"]
missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
if missing:
    bold_missing = ", ".join(f"**{v}**" for v in missing)
    st.error(f"Missing required environment variables: {bold_missing}. Check your .env file.")
    st.stop()

LOG_FILE = "query_log.csv"

def log_query(question, sql):
    # write each query to csv, create file with header if it doesn't exist
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "question", "generated_sql"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question, sql])

# load schema and db profile once at startup
if "schema" not in st.session_state:
    st.session_state.schema = get_schema()

if "db_profile" not in st.session_state:
    st.session_state.db_profile = get_db_profile()

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# layout
left, center, gap, right, rpad = st.columns([0.4, 3.5, 0.3, 1.5, 0.3])

with center:
    st.markdown("# SQL Query Agent")
    st.markdown("##### Ask a question for the agent to query.")
    st.write("")

    with st.form(key="query_form"):
        input_col, button_col = st.columns([5, 1])
        with input_col:
            question = st.text_input("Your question", placeholder="e.g. Show me all customers in Texas with a savings account", label_visibility="collapsed")
        with button_col:
            submit = st.form_submit_button("Submit", type="primary", use_container_width=True)

    if submit and question.strip():
        with st.spinner("Generating query..."):
            agent_response = generate_sql(question, st.session_state.schema, st.session_state.db_profile)
            sql, explanation, df, error, status = run_and_return(agent_response)

        if error:
            st.session_state.last_result = {"error": error}
        else:
            log_query(question, sql)
            st.session_state.history.append({
                "question": question,
                "row_count": len(df) if df is not None else 0
            })
            st.session_state.last_result = {
                "error": None,
                "sql": sql,
                "explanation": explanation,
                "df": df
            }

    # render results from session state
    if st.session_state.last_result:
        result = st.session_state.last_result
        st.write("")
        if result["error"]:
            st.error(result["error"])
        else:
            st.subheader("Explanation")
            st.write(result["explanation"])

            st.subheader("Generated SQL")
            st.code(result["sql"], language="sql")

            st.subheader("Results")
            if result["df"] is not None and not result["df"].empty:
                st.dataframe(result["df"], use_container_width=True)
                st.caption(f"{len(result['df'])} row(s) returned")
            else:
                st.info("No matching records found. The query ran successfully but returned no results.")

with right:
    st.markdown("""
        <h1 style="margin-top:1.6rem; padding-top:0; font-size:2rem; font-weight:700;">History</h1>
    """, unsafe_allow_html=True)
    st.write("")
    if not st.session_state.history:
        st.caption("No queries yet.")
    else:
        for entry in reversed(st.session_state.history[-3:]):
            st.markdown(f"**Q:** {entry['question']}")
            st.caption(f"{entry['row_count']} row(s) returned")
            st.divider()
