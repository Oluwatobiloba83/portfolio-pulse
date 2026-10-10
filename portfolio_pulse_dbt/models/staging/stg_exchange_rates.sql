{{ config(materialized='view')}}

SELECT
    rate_date::date AS rate_date,
    UPPER(TRIM(base_currency)) AS base_currency,
    UPPER(TRIM(target_currency)) AS target_currency,
    exchange_rate::numeric(18,6) AS exchange_rate
FROM {{ source('portfolio', 'exchange_rates') }}
