WITH raw_w AS (
    SELECT * FROM raw_data.raw_weather
)
SELECT
    CAST(CAST(date AS VARCHAR) AS DATE) AS weather_date,
    CAST(max_temp_c AS DOUBLE PRECISION) AS max_temp_c,
    CAST(min_temp_c AS DOUBLE PRECISION) AS min_temp_c,
    CAST(avg_temp_c AS DOUBLE PRECISION) AS avg_temp_c,
    CAST(precipitation_mm AS DOUBLE PRECISION) AS precipitation_mm,
    CAST(weather_code AS INTEGER) AS weather_code,
    CAST(weather_condition AS VARCHAR) AS weather_condition
FROM raw_w
WHERE date IS NOT NULL
