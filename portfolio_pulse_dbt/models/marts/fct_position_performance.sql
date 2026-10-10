
{{ config(materialized='table') }}

WITH position_costs AS (
    SELECT
        ticker,
        SUM(shares) AS shares_held,
        SUM(shares * price_paid) AS cost_basis_usd
    FROM {{ ref('stg_trades') }}
    WHERE trade_type = 'BUY'
    GROUP BY ticker
),

ranked_prices AS (
    SELECT
        ticker,
        price_date,
        close_price,
        ROW_NUMBER() OVER (
            PARTITION BY ticker
            ORDER BY price_date DESC
        ) AS price_rank
    FROM {{ ref('stg_stock_prices') }}
),

latest_prices AS (
    SELECT
        ticker,
        price_date AS latest_price_date,
        close_price AS latest_close_price
    FROM ranked_prices
    WHERE price_rank = 1
),

position_values AS (
    SELECT
        c.ticker,
        c.shares_held,
        c.cost_basis_usd,
        p.latest_price_date,
        p.latest_close_price,
        c.shares_held * p.latest_close_price
            AS market_value_usd,
        (c.shares_held * p.latest_close_price)
            - c.cost_basis_usd
            AS unrealized_gain_loss_usd
    FROM position_costs AS c
    INNER JOIN latest_prices AS p
        ON c.ticker = p.ticker
)

SELECT
    ticker,
    shares_held,
    cost_basis_usd,
    latest_price_date,
    latest_close_price,
    market_value_usd,
    unrealized_gain_loss_usd,
    CASE
        WHEN cost_basis_usd <> 0
        THEN unrealized_gain_loss_usd / cost_basis_usd * 100
        ELSE NULL
    END AS unrealized_return_pct,
    CASE
        WHEN SUM(market_value_usd) OVER () <> 0
        THEN market_value_usd
             / SUM(market_value_usd) OVER () * 100
        ELSE NULL
    END AS allocation_pct
FROM position_values
