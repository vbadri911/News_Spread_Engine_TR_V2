"""
Filter by price and spread - no fallbacks
"""
import json
import sys
import os
from datetime import datetime
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import TRADIER_TOKEN

base_url = 'https://api.tradier.com'
headers = {'Authorization': f'Bearer {TRADIER_TOKEN}', 'Accept': 'application/json'}

def filter_price_liquidity():
    print("="*60)
    print("STEP 0B: Filter Price")
    print("="*60)

    with open("data/sp500.json", "r") as f:
        tickers = json.load(f)["tickers"]

    print(f"Input: {len(tickers)} stocks")

    passed = []
    failed = []

    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        symbols_str = ','.join(batch)

        response = requests.get(f'{base_url}/v1/markets/quotes', params={'symbols': symbols_str}, headers=headers)

        if response.status_code == 200:
            data = response.json()['quotes']
            quotes = data['quote'] if isinstance(data, dict) else data
            if not isinstance(quotes, list):
                quotes = [quotes]

            batch_quotes = {}
            for q in quotes:
                if q is None or 'symbol' not in q:
                    continue
                ticker = q['symbol']
                bid = float(q.get('bid', 0))
                ask = float(q.get('ask', 0))

                if bid > 0 and ask > 0:
                    mid = (bid + ask) / 2
                    spread_pct = ((ask - bid) / mid) * 100

                    batch_quotes[ticker] = {
                        'ticker': ticker,
                        'bid': round(bid, 2),
                        'ask': round(ask, 2),
                        'mid': round(mid, 2),
                        'spread_pct': round(spread_pct, 2)
                    }

            for ticker in batch:
                if ticker in batch_quotes:
                    data = batch_quotes[ticker]
                    if 30 <= data['mid'] <= 400 and data['spread_pct'] < 2.0:
                        passed.append(data)
                    else:
                        reason = "price out of range" if data['mid'] < 30 or data['mid'] > 400 else f"spread {data['spread_pct']:.2f}%"
                        failed.append({'ticker': ticker, 'reason': reason})
                else:
                    failed.append({'ticker': ticker, 'reason': 'no quote data'})
        else:
            for ticker in batch:
                failed.append({'ticker': ticker, 'reason': 'API error'})

    return passed, failed

def save_results(passed, failed):
    with open('data/filter1_passed.json', 'w') as f:
        json.dump(passed, f, indent=2)

    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: $30-400, spread <2%")

def main():
    passed, failed = filter_price_liquidity()
    save_results(passed, failed)
    print("Step 0B complete")

if __name__ == "__main__":
    main()