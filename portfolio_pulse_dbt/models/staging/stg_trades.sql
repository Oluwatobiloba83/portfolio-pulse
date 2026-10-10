{{ config(materialized='view') }}

SELECT
    TRIM(trade_id::text) AS trade_id,
    trade_date::date AS trade_date,
    UPPER(TRIM(ticker::text)) AS ticker,
    UPPER(TRIM(trade_type::text)) AS trade_type,
    shares::numeric(18,6) AS shares,
    price_paid::numeric(18,6) AS price_paid
FROM {{ source('raw_portfolio', 'trades') }}
