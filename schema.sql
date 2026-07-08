-- drop tables if they exist
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    age INTEGER,
    city VARCHAR(100),
    state VARCHAR(50),
    email VARCHAR(100),
    member_since DATE
);

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    account_type VARCHAR(20) CHECK (account_type IN ('checking', 'savings', 'credit')),
    balance NUMERIC(12, 2),
    opened_date DATE,
    status VARCHAR(10) CHECK (status IN ('active', 'closed'))
);

CREATE TABLE merchants (
    merchant_id SERIAL PRIMARY KEY,
    merchant_name VARCHAR(100),
    category VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50)
);

-- transactions reference both accounts and merchants
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id),
    merchant_id INTEGER REFERENCES merchants(merchant_id),
    amount NUMERIC(10, 2),
    transaction_date DATE,
    category VARCHAR(50),
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('debit', 'credit'))
);
