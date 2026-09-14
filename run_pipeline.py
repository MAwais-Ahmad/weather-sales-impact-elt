import os
import sys
import subprocess
import duckdb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DBT_DIR = os.path.join(BASE_DIR, "dbt_postgres_ecom")
MULTI_SCRIPT = os.path.join(BASE_DIR, "ingestion", "multi_source_pipeline.py")
DOWNLOAD_SCRIPT = os.path.join(DATA_DIR, "download_raw_data.py")
FALLBACK_DUCKDB = os.path.join(DATA_DIR, "data_warehouse_project2.duckdb")

def main():
    print("=" * 75)
    print("  PROJECT 2: MULTI-SOURCE EXTERNAL FACTORS (SALES + WEATHER API) PIPELINE ")
    print("=" * 75)
    
    # 1. Download dataset if missing
    print("\n[STEP 1/4] Checking & Downloading Historical Sales Dataset...")
    subprocess.run([sys.executable, DOWNLOAD_SCRIPT], check=True)
    
    # 2. Run dlt Multi-Source Ingestion
    print("\n[STEP 2/4] Running Multi-Source dlt Ingestion (Sales + Open-Meteo Weather API)...")
    subprocess.run([sys.executable, MULTI_SCRIPT], check=True)
    
    # 3. Run dbt Transformations
    print("\n[STEP 3/4] Running dbt Analytical Transformation Models...")
    # Try PostgreSQL target first, fallback to duckdb_fallback if PostgreSQL service is offline
    try:
        dbt_cmd = [sys.executable, "-m", "dbt.cli.main", "run", "--project-dir", DBT_DIR, "--profiles-dir", DBT_DIR]
        subprocess.run(dbt_cmd, check=True)
    except Exception:
        print("\nPostgreSQL execution failed/offline. Falling back to DuckDB target...")
        dbt_cmd = [sys.executable, "-m", "dbt.cli.main", "run", "--project-dir", DBT_DIR, "--profiles-dir", DBT_DIR, "-t", "duckdb_fallback"]
        try:
            subprocess.run(dbt_cmd, check=True)
        except Exception:
            dbt_cmd_alt = [sys.executable, "-m", "dbt", "run", "--project-dir", DBT_DIR, "--profiles-dir", DBT_DIR, "-t", "duckdb_fallback"]
            subprocess.run(dbt_cmd_alt, check=True)
    
    # 4. Warehouse Audits & Executive Summary Matrix
    print("\n[STEP 4/4] Verifying Project 2 Analytics Warehouse & Data Marts...")
    
    # Connect to DuckDB fallback or PostgreSQL to print matrix
    if os.path.exists(FALLBACK_DUCKDB):
        con = duckdb.connect(FALLBACK_DUCKDB)
        print("\n--- EXTERNAL FACTORS DAILY SUMMARY ---")
        summary = con.execute("""
            SELECT 
                COUNT(*) AS total_days,
                ROUND(AVG(avg_temp_c), 1) AS avg_temp_c,
                SUM(total_units_sold) AS total_units_sold,
                ROUND(SUM(gross_revenue), 2) AS total_revenue_usd,
                ROUND(SUM(gross_profit), 2) AS gross_profit_usd
            FROM main.fct_daily_sales_external
        """).df()
        print(summary.to_string(index=False))
        
        print("\n--- AUTOMATED PLAIN-ENGLISH EXECUTIVE INSIGHTS ---")
        takeaways = con.execute("""
            SELECT category, sunny_daily_rev, rain_daily_rev, revenue_dip_pct, plain_english_takeaway
            FROM main.mart_executive_takeaway
        """).df()
        print(takeaways.to_string(index=False))
        con.close()
        
    print("\n" + "=" * 75)
    print(" PROJECT 2 PIPELINE EXECUTED SUCCESSFULLY! DASHBOARD READY. ")
    print("=" * 75)

if __name__ == "__main__":
    main()
