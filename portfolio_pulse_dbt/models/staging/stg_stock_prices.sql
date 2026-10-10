{{ config(materialized='view') }}

SELECT
    UPPER(TRIM(ticker)) AS ticker,
    price_date::date AS price_date,
    close_price::numeric(18,6) AS close_price,
    UPPER(TRIM(currency)) AS currency
FROM {{ source('portfolio', 'stock_prices') }}
