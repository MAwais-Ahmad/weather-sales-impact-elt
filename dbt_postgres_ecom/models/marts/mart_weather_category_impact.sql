WITH cat_weather AS (
    SELECT
        p.category,
        COALESCE(w.weather_condition, 'Overcast / Mild') AS weather_condition,
        COUNT(DISTINCT o.order_date) AS active_days,
        SUM(CASE WHEN NOT o.is_cancelled THEN o.quantity ELSE 0 END) AS total_units_sold,
        ROUND(CAST(SUM(CASE WHEN NOT o.is_cancelled THEN o.line_revenue ELSE 0 END) AS NUMERIC), 2) AS total_revenue,
        ROUND(CAST(SUM(CASE WHEN NOT o.is_cancelled THEN o.quantity * p.unit_cost ELSE 0 END) AS NUMERIC), 2) AS total_cost
    FROM {{ ref('stg_orders') }} o
    JOIN {{ ref('dim_products') }} p ON o.stock_code = p.stock_code
    LEFT JOIN {{ ref('stg_weather') }} w ON o.order_date = w.weather_date
    GROUP BY p.category, COALESCE(w.weather_condition, 'Overcast / Mild')
)
SELECT
    category,
    weather_condition,
    active_days,
    total_units_sold,
    total_revenue,
    total_cost,
    ROUND(CAST(total_revenue - total_cost AS NUMERIC), 2) AS gross_profit,
    CASE WHEN total_revenue > 0 THEN ROUND(CAST((total_revenue - total_cost) / total_revenue AS NUMERIC), 4) ELSE 0.0 END AS margin_pct,
    ROUND(CAST(total_revenue / CASE WHEN active_days > 0 THEN active_days ELSE 1 END AS NUMERIC), 2) AS avg_daily_revenue
FROM cat_weather
ORDER BY category, total_revenue DESC
