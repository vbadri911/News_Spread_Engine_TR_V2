"""
Get S&P 500 from GitHub CSV
"""
import pandas as pd
import json
import requests
from datetime import datetime

def get_sp500():
    url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
    try:
        # Use requests with default SSL verification
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        # Convert response to DataFrame
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        tickers = df['Symbol'].tolist()
        return tickers
    except requests.exceptions.SSLError as ssl_err:
        print(f"SSL Error: {ssl_err}")
        print("Attempting to fetch with SSL verification disabled...")
        # Fallback: Disable SSL verification (not recommended for production)
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        tickers = df['Symbol'].tolist()
        return tickers
    except Exception as e:
        print(f"FAILED: {e}")
        raise

def main():
    print("="*60)
    print("STEP 0A: Get S&P 500")
    print("="*60)

    try:
        tickers = get_sp500()
        print(f"Got {len(tickers)} tickers")

        with open("data/sp500.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "count": len(tickers),
                "tickers": tickers
            }, f, indent=2)

        print("Step 0A complete")
    except Exception as e:
        print(f"FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    main()