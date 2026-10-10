
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError(
        "DATABASE_URL is missing. Check your local .env file."
    )

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS stock_prices (
    ticker TEXT NOT NULL,
    price_date DATE NOT NULL,
    close_price NUMERIC(18, 6) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    PRIMARY KEY (ticker, price_date),
    CHECK (close_price >= 0)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY,
    trade_date DATE NOT NULL,
    ticker TEXT NOT NULL,
    trade_type TEXT NOT NULL
        CHECK (trade_type IN ('BUY', 'SELL')),
    shares NUMERIC(18, 6) NOT NULL
        CHECK (shares > 0),
    price_paid NUMERIC(18, 6) NOT NULL
        CHECK (price_paid >= 0)
);

CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date DATE NOT NULL,
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    exchange_rate NUMERIC(18, 6) NOT NULL
        CHECK (exchange_rate > 0),
    PRIMARY KEY (rate_date, base_currency, target_currency)
);
"""

def main():
    database_url = DATABASE_URL
    if database_url is None:
        raise ValueError(
            "DATABASE_URL is missing. Check your local .env file."
        )

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLES_SQL)

            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN (
                      'stock_prices',
                      'trades',
                      'exchange_rates'
                  )
                ORDER BY table_name;
            """)

            tables = cur.fetchall()

    print("Database setup completed.")
    print("Tables created or already present:")

    for (table_name,) in tables:
        print(f" - {table_name}")

if __name__ == "__main__":
    main()
