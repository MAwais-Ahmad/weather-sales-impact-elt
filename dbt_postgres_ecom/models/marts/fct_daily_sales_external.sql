WITH daily_orders AS (
    SELECT
        o.order_date,
        COUNT(DISTINCT CASE WHEN NOT o.is_cancelled THEN o.invoice_no END) AS valid_orders_count,
        SUM(CASE WHEN NOT o.is_cancelled THEN o.quantity ELSE 0 END) AS total_units_sold,
        ROUND(CAST(SUM(CASE WHEN NOT o.is_cancelled THEN o.line_revenue ELSE 0 END) AS NUMERIC), 2) AS gross_revenue,
        ROUND(CAST(SUM(CASE WHEN NOT o.is_cancelled THEN o.quantity * p.unit_cost ELSE 0 END) AS NUMERIC), 2) AS total_cost
    FROM {{ ref('stg_orders') }} o
    LEFT JOIN {{ ref('dim_products') }} p ON o.stock_code = p.stock_code
    GROUP BY o.order_date
),
joined AS (
    SELECT
        d.order_date,
        d.valid_orders_count,
        d.total_units_sold,
        d.gross_revenue,
        d.total_cost,
        ROUND(CAST(d.gross_revenue - d.total_cost AS NUMERIC), 2) AS gross_profit,
        CASE WHEN d.gross_revenue > 0 THEN ROUND(CAST((d.gross_revenue - d.total_cost) / d.gross_revenue AS NUMERIC), 4) ELSE 0.0 END AS margin_pct,
        w.max_temp_c,
        w.min_temp_c,
        w.avg_temp_c,
        w.precipitation_mm,
        COALESCE(w.weather_condition, 'Overcast / Mild') AS weather_condition
    FROM daily_orders d
    LEFT JOIN {{ ref('stg_weather') }} w ON d.order_date = w.weather_date
)
SELECT * FROM joined
ORDER BY order_date ASC
