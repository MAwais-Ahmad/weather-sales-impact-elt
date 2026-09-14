WITH sunny_avg AS (
    SELECT
        category,
        avg_daily_revenue AS sunny_daily_rev
    FROM {{ ref('mart_weather_category_impact') }}
    WHERE weather_condition = 'Warm / Sunny'
),
rain_avg AS (
    SELECT
        category,
        avg_daily_revenue AS rain_daily_rev
    FROM {{ ref('mart_weather_category_impact') }}
    WHERE weather_condition IN ('Heavy Rain', 'Light Rain')
    GROUP BY category, avg_daily_revenue
),
joined AS (
    SELECT
        s.category,
        s.sunny_daily_rev,
        r.rain_daily_rev,
        ROUND(CAST(((r.rain_daily_rev - s.sunny_daily_rev) / CASE WHEN s.sunny_daily_rev > 0 THEN s.sunny_daily_rev ELSE 1 END) * 100 AS NUMERIC), 2) AS revenue_dip_pct
    FROM sunny_avg s
    JOIN rain_avg r ON s.category = r.category
)
SELECT
    category,
    sunny_daily_rev,
    rain_daily_rev,
    revenue_dip_pct,
    CASE 
        WHEN revenue_dip_pct < 0 THEN 'INSIGHT: ' || category || ' daily sales dip by ' || ABS(revenue_dip_pct) || '% on rainy days compared to sunny days. Recommend increasing online ad promotions during sunny periods.'
        ELSE 'INSIGHT: ' || category || ' sales remain strong or increase by ' || revenue_dip_pct || '% on rainy days. Recommend targeted indoor product bundles during inclement weather.'
    END AS plain_english_takeaway
FROM joined
ORDER BY ABS(revenue_dip_pct) DESC
