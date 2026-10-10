
{{ config(materialized='table') }}

WITH daily_holdings AS (
    SELECT
        p.price_date,
        p.ticker,
        p.close_price,
        COALESCE(h.shares_held, 0) AS shares_held
    FROM {{ ref('stg_stock_prices') }} AS p
    LEFT JOIN LATERAL (
        SELECT
            SUM(
                CASE
                    WHEN t.trade_type = 'BUY' THEN t.shares
                    WHEN t.trade_type = 'SELL' THEN -t.shares
                    ELSE 0
                END
            ) AS shares_held
        FROM {{ ref('stg_trades') }} AS t
        WHERE t.ticker = p.ticker
          AND t.trade_date <= p.price_date
    ) AS h ON TRUE
),

daily_usd AS (
    SELECT
        price_date,
        SUM(shares_held * close_price) AS portfolio_value_usd
    FROM daily_holdings
    GROUP BY price_date
)

SELECT
    d.price_date,
    d.portfolio_value_usd,
    fx.exchange_rate AS usd_to_ngn_rate,
    CASE
        WHEN fx.exchange_rate IS NOT NULL
        THEN d.portfolio_value_usd * fx.exchange_rate
        ELSE NULL
    END AS portfolio_value_ngn
FROM daily_usd AS d
LEFT JOIN LATERAL (
    SELECT exchange_rate
    FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency = 'USD'
      AND target_currency = 'NGN'
      AND rate_date <= d.price_date
    ORDER BY rate_date DESC
    LIMIT 1
) AS fx ON TRUE
