
import os
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import psycopg
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TICKERS = ["AAPL", "MSFT", "NVDA", "KO", "XOM"]
START_DATE = "2026-01-01"

# yfinance's end date is exclusive, so include tomorrow.
END_DATE = (date.today() + timedelta(days=1)).isoformat()

UPSERT_SQL = """
INSERT INTO stock_prices (
    ticker,
    price_date,
    close_price,
    currency
)
VALUES (%s, %s, %s, %s)
ON CONFLICT (ticker, price_date)
DO UPDATE SET
    close_price = EXCLUDED.close_price,
    currency = EXCLUDED.currency;
"""


def main():
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is missing. Check your .env file."
        )

    rows = []
    errors = []

    print(f"Fetching stock prices from {START_DATE} to {END_DATE}...")

    for ticker in TICKERS:
        try:
            history = yf.Ticker(ticker).history(
                start=START_DATE,
                end=END_DATE,
                auto_adjust=False
            )

            if history.empty:
                errors.append(f"{ticker}: no price data returned")
                continue

            if "Close" not in history.columns:
                errors.append(f"{ticker}: Close column missing")
                continue

            ticker_rows = 0

            for timestamp, close_price in history["Close"].items():
                if close_price is None:
                    continue

                # Ignore missing or invalid closing prices.
                if close_price != close_price:
                    continue

                price = Decimal(str(close_price))

                if not price.is_finite() or price < 0:
                    continue

                price_date = pd.Timestamp(timestamp).date()

                rows.append((
                    ticker,
                    price_date,
                    price,
                    "USD"
                ))
                ticker_rows += 1

            print(f"{ticker}: fetched {ticker_rows} daily prices")

        except Exception as exc:
            errors.append(f"{ticker}: {exc}")

    if not rows:
        raise RuntimeError(
            "No stock prices were fetched. Check your connection "
            "and the errors above."
        )

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, rows)

    print(f"\nSuccessfully processed {len(rows)} price records.")

    if errors:
        print("\nSome tickers could not be processed:")
        for error in errors:
            print(f" - {error}")
        raise RuntimeError(
            "Stock-price ingestion was incomplete."
        )

    print("All tickers processed successfully.")


if __name__ == "__main__":
    main()
