WITH product_agg AS (
    SELECT
        stock_code,
        MAX(description) AS description,
        ROUND(CAST(AVG(unit_price) AS NUMERIC), 2) AS avg_unit_price
    FROM {{ ref('stg_orders') }}
    WHERE stock_code IS NOT NULL
    GROUP BY stock_code
),
classified AS (
    SELECT
        stock_code,
        description,
        avg_unit_price,
        CASE
            WHEN description LIKE '%BAG%' OR description LIKE '%LUGGAGE%' OR description LIKE '%TOTE%' THEN 'Bags & Accessories'
            WHEN description LIKE '%MUG%' OR description LIKE '%PLATE%' OR description LIKE '%BOWL%' OR description LIKE '%CUP%' THEN 'Kitchenware & Dining'
            WHEN description LIKE '%HEART%' OR description LIKE '%CANDLE%' OR description LIKE '%LIGHT%' OR description LIKE '%CLOCK%' OR description LIKE '%DECOR%' THEN 'Home & Living'
            WHEN description LIKE '%CHRISTMAS%' OR description LIKE '%GIFT%' OR description LIKE '%CARD%' OR description LIKE '%BOX%' OR description LIKE '%PAPER%' THEN 'Stationery & Gifts'
            WHEN description LIKE '%SCARF%' OR description LIKE '%APRON%' OR description LIKE '%HAT%' OR description LIKE '%JEWEL%' THEN 'Apparel & Jewelry'
            ELSE 'General Merchandise'
        END AS category,
        ROUND(CAST(CASE WHEN avg_unit_price > 0 THEN avg_unit_price * 0.60 ELSE 0.10 END AS NUMERIC), 2) AS unit_cost
    FROM product_agg
)
SELECT
    stock_code,
    description,
    category,
    avg_unit_price AS unit_price,
    unit_cost,
    ROUND(CAST(avg_unit_price - unit_cost AS NUMERIC), 2) AS unit_profit
FROM classified
