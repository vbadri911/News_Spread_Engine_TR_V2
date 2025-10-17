"""
Filter by options availability
"""
import json
import sys
import os
from datetime import datetime, timedelta
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import TRADIER_TOKEN

base_url = 'https://api.tradier.com'
headers = {'Authorization': f'Bearer {TRADIER_TOKEN}', 'Accept': 'application/json'}

def process_ticker(stock_data):
    ticker = stock_data['ticker']
    today = datetime.now().date()
    try:
        # Get expirations
        resp = requests.get(f'{base_url}/v1/markets/options/expirations', params={'symbol': ticker}, headers=headers)
        if resp.status_code != 200:
            return None, {'ticker': ticker, 'reason': 'no chain'}

        exp_data = resp.json().get('expirations')
        if not exp_data:
            return None, {'ticker': ticker, 'reason': 'no chain'}
        exps = exp_data.get('date', []) if isinstance(exp_data, dict) else [e['date'] for e in exp_data]

        good_exps = []
        for exp_str in exps:
            exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
            dte = (exp_date - today).days
            if 15 <= dte <= 45:
                good_exps.append({'date': exp_str, 'dte': dte})

        if not good_exps:
            return None, {'ticker': ticker, 'reason': 'no 15-45 DTE'}

        good_exps.sort(key=lambda x: x['date'])
        best_exp_str = good_exps[0]['date']

        # Fetch chain
        resp_chain = requests.get(f'{base_url}/v1/markets/options/chains', params={'symbol': ticker, 'expiration': best_exp_str}, headers=headers)
        if resp_chain.status_code != 200:
            return None, {'ticker': ticker, 'reason': 'no chain'}

        chain_data = resp_chain.json().get('options', {}).get('option', [])
        if not chain_data:
            return None, {'ticker': ticker, 'reason': 'no chain'}

        if len(chain_data) < 20:
            return None, {'ticker': ticker, 'reason': f'only {len(chain_data)} strikes'}

        return {
            **stock_data,
            'expirations': len(good_exps),
            'best_expiration': good_exps[0],
            'strikes_count': len(chain_data)
        }, None
    except Exception as e:
        return None, {'ticker': ticker, 'reason': str(e)[:30]}

def filter_options():
    print("="*60)
    print("STEP 0C: Filter Options")
    print("="*60)

    with open("data/filter1_passed.json", "r") as f:
        stocks = json.load(f)

    print(f"Input: {len(stocks)} stocks")

    passed = []
    failed = []

    with ThreadPoolExecutor(max_workers=10) as executor:  # Safe under 120/min
        futures = [executor.submit(process_ticker, stock_data) for stock_data in stocks]
        for future in concurrent.futures.as_completed(futures):
            pass_item, fail_item = future.result()
            if pass_item:
                passed.append(pass_item)
            if fail_item:
                failed.append(fail_item)

    return passed, failed

def save_results(passed, failed):
    with open('data/filter2_passed.json', 'w') as f:
        json.dump(passed, f, indent=2)

    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: 20+ strikes, 15-45 DTE")

def main():
    passed, failed = filter_options()
    save_results(passed, failed)
    print("Step 0C complete")

if __name__ == "__main__":
    main()
