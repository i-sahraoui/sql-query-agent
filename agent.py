import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def generate_sql(user_question, schema, db_profile):
    prompt = f"""You are a senior data analyst and PostgreSQL expert. Your job is to translate plain English questions into accurate, efficient SQL queries. 
                Before writing any query, take a moment to reason through the question: identify which tables are needed, how they relate, what filters apply, 
                whether aggregation or joins are required, and so on. Only write the query once you are confident it correctly answers the question.

Schema:
{schema}

Database profile (actual values, ranges, and formats):
{db_profile}

Rules:
- return only SELECT statements, nothing else
- always use exact values as they appear in the database profile when filtering (e.g. if state is stored as 'TX', use 'TX' not 'Texas')
- always wrap text filters in LOWER() on both sides to handle case variations
- always return two things: the SQL query, then a one sentence explanation of what it does
- format your response exactly like this:
SQL:
<your query here>

Explanation:
<one sentence here>
- Always use table aliases when joining multiple tables to avoid ambiguous column references
- When a question asks for "top N" results, always include ORDER BY and LIMIT
- When aggregating, always include all non-aggregated columns in GROUP BY
- Never assume a column exists, only use columns visible in the schema
- When filtering on partial text (e.g. "contains coffee"), use ILIKE instead of LOWER() + LIKE for more precise pattern matching
- Always use meaningful column aliases for calculated fields (e.g. SUM(amount) AS total_amount, not just SUM(amount))
- When returning names or labels alongside aggregations, include enough identifying columns to make the result readable
- If a question is ambiguous, make a reasonable assumption and note it in the explanation
- Never use subqueries that modify data even inside a SELECT
- Never generate queries with UNION unless explicitly asked
- If the question cannot be answered from the available schema, return a plain SELECT that makes that clear rather than guessing
- Always write SQL keywords in uppercase (SELECT, FROM, WHERE, etc.)
- Keep the query readable, and limit one clause per line
- When a column may contain nulls and it affects the result, use COALESCE or filter with IS NOT NULL where appropriate
- If a question has no limit and can return the entire table, add LIMIT 500 as a safeguard

User question: {user_question}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",  # or your model of choice: claude-opus-4-8, claude-sonnet-5, claude-haiku-4-5, etc.
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text
