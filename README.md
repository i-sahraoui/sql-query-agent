# sql-query-agent

The purpose of this project is to allow non-technical users to execute queries in plain english. You can type a question -- "show me all customers in Texas with a savings account" -- and the agent figures out the query, runs it against your database, and returns the results. No SQL knowledge required.

I built this to demonstrate how large language models can be used as practical interfaces for relational databases.

---

## What it does

- Connects to any PostgreSQL database
- Reads your schema and samples your data automatically at startup, to understand how your data is structured and formatted
- Translates plain English questions into SQL queries via the Claude API
- Validates every query before running it (read-only by default, modifications to the database prohibited)
- Returns results as an interactive table, alongside the generated SQL and an explanation
- Logs every query to a CSV file for your records

---

## What you need before starting

- **Python 3.10+** -- [download](https://www.python.org/downloads/)
- **Docker Desktop** -- [download](https://www.docker.com/products/docker-desktop/). Local sample database
- **Anthropic API key** -- [get one](https://console.anthropic.com/). Query agent

---

## Setup

### Step 1 -- Clone The Repo + Setup Environment

```bash
git clone https://github.com/i-sahraoui/sql-query-agent.git
cd sql-query-agent
python -m venv venv
```

Activate it:
- Windows: `.\venv\Scripts\Activate.ps1`
- Mac/Linux: `source venv/bin/activate`

Then install dependencies:

```bash
pip install -r requirements.txt
```

### Step 2 -- Add Credentials

Copy `.env.example` to a new file called `.env` and fill in your values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
ANTHROPIC_API_KEY=your_key_here
```

### Step 3 -- Connect a Database

**Option A: Sample banking database**

Start a PostgreSQL container via Docker:

```bash
docker run --name sql-agent-db -e POSTGRES_PASSWORD=admin123 -e POSTGRES_DB=bankingdb -p 5432:5432 -d postgres:15
```

Then seed it with fake data:

```bash
python seed_data.py
```

This creates four tables (customers, accounts, transactions, merchants) with realistic fake data. Your `.env` should match:

```
DB_NAME=bankingdb
DB_USER=postgres
DB_PASSWORD=admin123
```

**Option B: Provide your own PostgreSQL database**

If you already have a PostgreSQL database running, just point your `.env` file at it. The agent reads your schema and data automatically and requires no changes.

Make sure your database is accessible at the host and port you specify. The user must have read access for the agent to work.

### Step 4 -- Run The App

```bash
streamlit run app.py
```

This launches the web UI in your browser, and you are ready to start querying!

To restart after a reboot:
1. Open Docker Desktop and wait for it to load
2. Run `docker start sql-agent-db` (only needed if using the sample database)
3. Activate your venv
4. Run `streamlit run app.py`

---

## How It Works

When you start the app, it connects to your database and reads two things: the schema (table names, column names, data types) and a profile of the actual data (distinct values, ranges, formats). This gets passed to the Claude API along with your question, so the agent knows what to write based on how the data is formatted, structured, abbreviated, and so forth.

Every query gets validated before it runs. By default only SELECT statements are allowed, so nothing in your database can be modified through this tool.

---

## Project Structure

```
sql-query-agent/
├── app.py              # main Streamlit web app
├── main.py             # CLI version (optional)
├── agent.py            # sends question + schema to Claude API, returns SQL
├── executor.py         # validates and runs the query, returns results
├── schema_reader.py    # reads table/column structure from the database
├── db_sampler.py       # samples data values and formats
├── seed_data.py        # generates fake banking data (sample DB only)
├── schema.sql          # creates the sample database tables
├── requirements.txt    # python dependencies
├── .env                # credentials to modify
├── .env.example        # credentials example
├── .gitignore          
└── .streamlit/
    └── config.toml     # UI theme settings
```

---

## Notes

- This tool is read-only by default. If you want to enable write operations, see the comments in `executor.py`
- Query history is saved to `query_log.csv` in the project root
- If your database is large, the startup profiling step may take a few moments
