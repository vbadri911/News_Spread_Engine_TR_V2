"""
Get S&P 500 from GitHub CSV
"""
import pandas as pd
import json
from datetime import datetime

def get_sp500():
    url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
    df = pd.read_csv(url)
    tickers = df['Symbol'].tolist()
    return tickers

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
