import psycopg2
import random
from faker import Faker
from dotenv import load_dotenv
import os
from datetime import date

load_dotenv()
fake = Faker()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

# run schema first to create tables
with open("schema.sql", "r") as f:
    cur.execute(f.read())

# states and cities to pull from randomly
STATES = ["PA", "NY", "NJ", "CA", "TX", "FL", "IL", "OH", "GA", "NC"]
CITIES = {
    "PA": ["Philadelphia", "Pittsburgh", "Allentown"],
    "NY": ["New York", "Buffalo", "Albany"],
    "NJ": ["Newark", "Jersey City", "Trenton"],
    "CA": ["Los Angeles", "San Francisco", "San Diego"],
    "TX": ["Houston", "Dallas", "Austin"],
    "FL": ["Miami", "Orlando", "Tampa"],
    "IL": ["Chicago", "Springfield", "Naperville"],
    "OH": ["Columbus", "Cleveland", "Cincinnati"],
    "GA": ["Atlanta", "Savannah", "Augusta"],
    "NC": ["Charlotte", "Raleigh", "Durham"]
}

CATEGORIES = ["dining", "groceries", "travel", "entertainment", "utilities", "healthcare", "retail"]

# insert 200 customers
customer_ids = []
for _ in range(200):
    state = random.choice(STATES)
    city = random.choice(CITIES[state])
    cur.execute("""
        INSERT INTO customers (first_name, last_name, age, city, state, email, member_since)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING customer_id
    """, (
        fake.first_name(),
        fake.last_name(),
        random.randint(18, 75),
        city,
        state,
        fake.email(),
        fake.date_between(start_date=date(2010, 1, 1), end_date=date(2023, 12, 31))
    ))
    customer_ids.append(cur.fetchone()[0])

# 50 merchants across random states/cities
merchant_ids = []
for _ in range(50):
    state = random.choice(STATES)
    cur.execute("""
        INSERT INTO merchants (merchant_name, category, city, state)
        VALUES (%s, %s, %s, %s) RETURNING merchant_id
    """, (
        fake.company(),
        random.choice(CATEGORIES),
        random.choice(CITIES[state]),
        state
    ))
    merchant_ids.append(cur.fetchone()[0])

# 1-3 accounts per customer, no duplicates of same type
account_ids = []
for cid in customer_ids:
    num_accounts = random.randint(1, 3)
    account_types = random.sample(["checking", "savings", "credit"], num_accounts)
    for atype in account_types:
        cur.execute("""
            INSERT INTO accounts (customer_id, account_type, balance, opened_date, status)
            VALUES (%s, %s, %s, %s, %s) RETURNING account_id
        """, (
            cid,
            atype,
            round(random.uniform(-500, 50000), 2),
            fake.date_between(start_date=date(2010, 1, 1), end_date=date(2023, 12, 31)),
            random.choices(["active", "closed"], weights=[85, 15])[0]
        ))
        account_ids.append(cur.fetchone()[0])

# assuming ~10 transactions per account
for aid in account_ids:
    num_tx = random.randint(5, 15)
    for _ in range(num_tx):
        category = random.choice(CATEGORIES)
        cur.execute("""
            INSERT INTO transactions (account_id, merchant_id, amount, transaction_date, category, transaction_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            aid,
            random.choice(merchant_ids),
            round(random.uniform(1, 1500), 2),
            fake.date_between(start_date=date(2022, 1, 1), end_date=date(2024, 12, 31)),
            category,
            random.choices(["debit", "credit"], weights=[75, 25])[0]
        ))

conn.commit()
cur.close()
conn.close()
print("Done - database seeded.")
