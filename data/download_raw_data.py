import os
import requests
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DATA_DIR, "online_retail.csv")

# Direct open source URL for UCI Online Retail dataset (~540,000 transaction rows)
DATA_URL = "https://raw.githubusercontent.com/datasets/online-retail/master/data/online-retail.csv"

def download_data():
    if os.path.exists(CSV_PATH):
        print(f"Dataset already exists at {CSV_PATH}")
        return CSV_PATH
    
    print(f"Downloading real-world Online Retail dataset from {DATA_URL}...")
    try:
        response = requests.get(DATA_URL, timeout=60)
        response.raise_for_status()
        with open(CSV_PATH, "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded raw dataset ({os.path.getsize(CSV_PATH) / 1024 / 1024:.2f} MB)")
    except Exception as e:
        print(f"Direct download failed: {e}. Trying alternative mirror...")
        alt_url = "https://raw.githubusercontent.com/guipsamora/pandas_exercises/master/07_Visualization/Online_Retail/Online_Retail.csv"
        response = requests.get(alt_url, timeout=60)
        response.raise_for_status()
        with open(CSV_PATH, "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded raw dataset from mirror.")

    return CSV_PATH

if __name__ == "__main__":
    download_data()
