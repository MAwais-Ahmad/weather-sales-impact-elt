import os
import subprocess
from dagster import asset, Definitions, ScheduleDefinition, AssetExecutionContext

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MULTI_SOURCE_SCRIPT = os.path.join(BASE_DIR, "ingestion", "multi_source_pipeline.py")
DBT_POSTGRES_DIR = os.path.join(BASE_DIR, "dbt_postgres_ecom")

@asset(group_name="multi_source_ingestion", description="Extracts Sales orders & Open-Meteo Weather REST API into PostgreSQL/DuckDB via dlt")
def multi_source_weather_sales_asset(context: AssetExecutionContext):
    """Triggers dlt multi-source extraction (Sales + Weather API)."""
    context.log.info(f"Running multi-source ingestion: {MULTI_SOURCE_SCRIPT}")
    result = subprocess.run(["python", MULTI_SOURCE_SCRIPT], capture_output=True, text=True, check=True)
    context.log.info(result.stdout)
    return "Ingested Sales & Open-Meteo Weather API records"

@asset(deps=[multi_source_weather_sales_asset], group_name="transformation", description="Executes dbt-postgres models & generates plain-English insights")
def dbt_postgres_external_mart_asset(context: AssetExecutionContext):
    """Triggers dbt-postgres models execution."""
    context.log.info(f"Running dbt build in directory: {DBT_POSTGRES_DIR}")
    # Try running postgres target, fallback to duckdb_fallback target if postgres service is offline
    try:
        result = subprocess.run(["dbt", "run", "--project-dir", DBT_POSTGRES_DIR, "--profiles-dir", DBT_POSTGRES_DIR], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        context.log.warn("Postgres run failed. Falling back to DuckDB target...")
        result = subprocess.run(["dbt", "run", "--project-dir", DBT_POSTGRES_DIR, "--profiles-dir", DBT_POSTGRES_DIR, "-t", "duckdb_fallback"], capture_output=True, text=True, check=True)
        
    context.log.info(result.stdout)
    return "dbt Project 2 analytical marts transformed successfully"

# Weekly Cron Schedule: Every Sunday at Midnight
weekly_pipeline_schedule = ScheduleDefinition(
    name="weekly_ecom_weather_pipeline_schedule",
    target=[multi_source_weather_sales_asset, dbt_postgres_external_mart_asset],
    cron_schedule="0 0 * * 0"
)

defs = Definitions(
    assets=[multi_source_weather_sales_asset, dbt_postgres_external_mart_asset],
    schedules=[weekly_pipeline_schedule]
)
