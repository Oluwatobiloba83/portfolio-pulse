
{{ config(materialized='view') }}

WITH ranked_rates AS (
    SELECT
        date::date AS rate_date,
        'USD'::text AS base_currency,
        'NGN'::text AS target_currency,
        "rate__1_USD_in_NGN_"::numeric(18,6) AS exchange_rate,
        ROW_NUMBER() OVER (
            PARTITION BY date::date
            ORDER BY
                _airbyte_extracted_at DESC,
                _airbyte_raw_id DESC
        ) AS row_num
    FROM {{ source('raw_portfolio', 'usd_ngn_exchange_rates') }}
)

SELECT
    rate_date,
    base_currency,
    target_currency,
    exchange_rate
FROM ranked_rates
WHERE row_num = 1
