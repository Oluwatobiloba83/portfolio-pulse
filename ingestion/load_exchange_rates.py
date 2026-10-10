
import csv
import io
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
SOURCE_URL = (
    "https://fxconverter.tech/api/history"
    "?from=USD&to=NGN&range=2026&format=csv"
)


def fetch_exchange_rates():
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text.lstrip("\ufeff")))

    if not reader.fieldnames:
        raise ValueError("The exchange-rate source returned no CSV headers.")

    # Normalize headers to handle spaces or a UTF-8 BOM.
    headers = {header.strip().lower(): header for header in reader.fieldnames}
    date_column = headers.get("date")
    rate_column = headers.get("rate (1 usd in ngn)")

    if not date_column or not rate_column:
        raise ValueError(
            f"Unexpected CSV headers: {reader.fieldnames}"
        )

    records = []

    for row in reader:
        try:
            rate_date = date.fromisoformat(row[date_column].strip())
            rate = Decimal(row[rate_column].strip())
        except (ValueError, AttributeError, InvalidOperation) as exc:
            raise ValueError(f"Invalid exchange-rate row: {row}") from exc

        if not rate.is_finite() or rate <= 0:
            raise ValueError(f"Exchange rate must be positive: {row}")

        records.append((rate_date, rate))

    if not records:
        raise ValueError("No exchange-rate records were returned.")

    return records


def load_exchange_rates(records):
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL was not found. Check the .env file in the project root."
        )

    sql = """
        INSERT INTO public.exchange_rates (
            rate_date,
            base_currency,
            target_currency,
            exchange_rate
        )
        VALUES (%s, 'USD', 'NGN', %s)
        ON CONFLICT (rate_date, base_currency, target_currency)
        DO UPDATE SET exchange_rate = EXCLUDED.exchange_rate;
    """

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, records)

            cur.execute(
                """
                SELECT COUNT(*), MIN(rate_date), MAX(rate_date)
                FROM public.exchange_rates
                WHERE base_currency = 'USD'
                  AND target_currency = 'NGN';
                """
            )
            summary = cur.fetchone()
            if summary is None:
                raise RuntimeError(
                    "Exchange-rate summary query returned no rows."
                )
            count, first_date, last_date = summary

    print(f"Rows processed from source: {len(records)}")
    print(f"USD/NGN records now in Neon: {count}")
    print(f"Date coverage in Neon: {first_date} to {last_date}")


if __name__ == "__main__":
    try:
        rates = fetch_exchange_rates()
        load_exchange_rates(rates)
        print("Exchange-rate ingestion completed successfully.")
    except Exception as exc:
        print(f"Exchange-rate ingestion failed: {exc}")
        raise
