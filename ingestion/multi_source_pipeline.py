import os
import requests
import pandas as pd
import dlt
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "online_retail.csv")

# PostgreSQL Credentials (defaults to local Postgres or environment override)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecom_external_dw")

DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

@dlt.resource(name="raw_orders", write_disposition="replace")
def fetch_retail_orders():
    """Resource 1: Ingests raw sales order transactions into raw_sales schema."""
    if not os.path.exists(DATA_PATH):
        from data.download_raw_data import download_data
        download_data()

    print("Loading Sales transactions from CSV into Pandas...")
    try:
        df = pd.read_csv(DATA_PATH, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_PATH, encoding="ISO-8859-1")
    
    df.columns = [col.strip().replace(" ", "_").lower() for col in df.columns]
    col_map = {
        'invoiceno': 'invoice_no', 'invoice': 'invoice_no',
        'stockcode': 'stock_code', 'code': 'stock_code',
        'description': 'description', 'quantity': 'quantity',
        'invoicedate': 'invoice_date', 'date': 'invoice_date',
        'unitprice': 'unit_price', 'price': 'unit_price',
        'customerid': 'customer_id', 'country': 'country'
    }
    df.rename(columns=col_map, inplace=True)
    df['description'] = df['description'].fillna('UNLABELLED PRODUCT')
    df['customer_id'] = df['customer_id'].fillna(-1).astype(int).astype(str)
    df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0.0)
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    df['invoice_date'] = pd.to_datetime(df['invoice_date'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    df['ingested_at'] = datetime.utcnow().isoformat()
    
    print(f"Yielding {len(df):,} sales records to dlt pipeline...")
    for record in df.to_dict(orient="records"):
        yield record

@dlt.resource(name="raw_weather", write_disposition="replace")
def fetch_historical_weather_api():
    """Resource 2: Ingests historical daily weather data via Open-Meteo REST API into raw_external schema."""
    print("Calling Open-Meteo Historical Weather REST API (London/UK coordinates)...")
    # Date range matching historical UK retail sales period (2010-12-01 to 2011-12-31)
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=51.5074&longitude=-0.1278&"
        "start_date=2010-12-01&end_date=2011-12-31&"
        "daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&"
        "timezone=auto"
    )
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    weather_codes = daily.get("weathercode", [])
    
    weather_records = []
    for idx, date_str in enumerate(dates):
        max_t = temp_max[idx] if idx < len(temp_max) else 15.0
        min_t = temp_min[idx] if idx < len(temp_min) else 8.0
        p = precip[idx] if idx < len(precip) else 0.0
        code = weather_codes[idx] if idx < len(weather_codes) else 0
        
        # Determine human-readable weather condition label
        if p > 5.0 or code in [61, 63, 65, 80, 81, 82]:
            condition = "Heavy Rain"
        elif p > 0.5 or code in [51, 53, 55]:
            condition = "Light Rain"
        elif max_t >= 20.0:
            condition = "Warm / Sunny"
        elif max_t <= 5.0:
            condition = "Cold / Freezing"
        else:
            condition = "Overcast / Mild"
            
        weather_records.append({
            "date": date_str,
            "max_temp_c": max_t,
            "min_temp_c": min_t,
            "avg_temp_c": round((max_t + min_t) / 2, 2),
            "precipitation_mm": p,
            "weather_code": code,
            "weather_condition": condition,
            "ingested_at": datetime.utcnow().isoformat()
        })
        
    print(f"Yielding {len(weather_records):,} historical daily weather API records...")
    for rec in weather_records:
        yield rec

def run_multi_source_pipeline():
    """Runs the multi-source dlt pipeline loading Sales & Weather API into PostgreSQL (or DuckDB fallback)."""
    # Check if Postgres is reachable, else fall back to DuckDB file warehouse
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URI, connect_timeout=3)
        conn.close()
        dest_type = dlt.destinations.postgres(credentials=DB_URI)
        print(f"Targeting PostgreSQL Database: {DB_URI}")
    except Exception as e:
        print(f"PostgreSQL connection failed ({e}). Falling back to DuckDB destination.")
        fallback_db = os.path.join(BASE_DIR, "data", "data_warehouse_project2.duckdb")
        dest_type = dlt.destinations.duckdb(credentials=fallback_db)
    
    pipeline = dlt.pipeline(
        pipeline_name="multi_source_ecom_weather",
        destination=dest_type,
        dataset_name="raw_data"
    )
    
    print("Starting Multi-Source dlt Ingestion (Sales + Open-Meteo Weather REST API)...")
    info = pipeline.run([fetch_retail_orders(), fetch_historical_weather_api()])
    print("Multi-Source Ingestion Pipeline Completed Successfully!")
    print(info)
    return info

if __name__ == "__main__":
    run_multi_source_pipeline()
