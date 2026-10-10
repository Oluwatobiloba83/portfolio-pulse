
{{ config(materialized='view') }}

WITH source_trades AS (
    SELECT
        TRIM(trade_id::text) AS trade_id,
        trade_date::date AS trade_date,
        UPPER(TRIM(ticker::text)) AS ticker,
        UPPER(TRIM(trade_type::text)) AS trade_type,
        shares::numeric(18,6) AS shares,
        price_paid::numeric(18,6) AS price_paid,
        ROW_NUMBER() OVER (
            PARTITION BY TRIM(trade_id::text)
            ORDER BY _airbyte_extracted_at DESC
        ) AS row_num
    FROM {{ source('raw_portfolio', 'trades') }}
)

SELECT
    trade_id,
    trade_date,
    ticker,
    trade_type,
    shares,
    price_paid
FROM source_trades
WHERE row_num = 1
