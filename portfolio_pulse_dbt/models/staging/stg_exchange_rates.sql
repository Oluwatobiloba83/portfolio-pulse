{{ config(materialized='view') }}

SELECT
    date::date AS rate_date,
    'USD'::text AS base_currency,
    'NGN'::text AS target_currency,
    "rate__1_USD_in_NGN_"::numeric(18,6) AS exchange_rate
FROM {{ source('raw_portfolio', 'usd_ngn_exchange_rates') }}
