"""
Filter by IV - real strikes only
"""
import json
import sys
import os
from datetime import datetime
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import TRADIER_TOKEN

base_url = 'https://api.tradier.com'
headers = {'Authorization': f'Bearer {TRADIER_TOKEN}', 'Accept': 'application/json'}

def process_ticker(stock_data):
    ticker = stock_data['ticker']
    exp_date_str = stock_data['best_expiration']['date']
    stock_price = stock_data['mid']
    try:
        # Fetch chain for the best expiration
        resp_chain = requests.get(f'{base_url}/v1/markets/options/chains', params={'symbol': ticker, 'expiration': exp_date_str}, headers=headers)
        if resp_chain.status_code != 200:
            return None, {'ticker': ticker, 'reason': 'expiration not in chain'}

        chain_data = resp_chain.json().get('options', {}).get('option', [])
        if not chain_data:
            return None, {'ticker': ticker, 'reason': 'expiration not in chain'}

        # Find calls
        calls = [opt for opt in chain_data if opt['option_type'] == 'call']
        if not calls:
            return None, {'ticker': ticker, 'reason': 'no calls found'}

        # Find ATM call
        atm_call = min(calls, key=lambda x: abs(x['strike'] - stock_price))
        strike_price = atm_call['strike']

        # Build streamer_symbol equivalent (Tradier option symbol)
        exp_date_clean = exp_date_str.replace('-', '')
        strike_int = int(strike_price * 1000)
        symbol = f"{ticker}{exp_date_clean[2:]}C{strike_int:08d}"

        return {'symbol': symbol, 'stock_data': stock_data}, None
    except Exception as e:
        return None, {'ticker': ticker, 'reason': str(e)[:30]}

def get_iv_data():
    print("="*60)
    print("STEP 0D: Filter IV")
    print("="*60)

    with open("data/filter2_passed.json", "r") as f:
        stocks = json.load(f)

    print(f"Input: {len(stocks)} stocks")

    passed = []
    failed = []
    symbols_to_check = []
    symbol_map = {}  # Initialize here

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker, stock_data) for stock_data in stocks]
        for future in concurrent.futures.as_completed(futures):
            sym_item, fail_item = future.result()
            if sym_item:
                symbols_to_check.append(sym_item['symbol'])
                symbol_map[sym_item['symbol']] = sym_item['stock_data']
            if fail_item:
                failed.append(fail_item)

    # Now get Greeks/IV in batches
    collected = {}
    batch_size = 20
    for i in range(0, len(symbols_to_check), batch_size):
        batch = symbols_to_check[i:i+batch_size]
        params = {'symbols': ','.join(batch), 'greeks': 'true'}
        resp = requests.get(f'{base_url}/v1/markets/quotes', params=params, headers=headers)

        if resp.status_code == 200:
            quotes_data = resp.json().get('quotes', {})
            data = quotes_data.get('quote', []) 
            if not isinstance(data, list):
                data = [data] if data else []

            for opt in data:
                if not opt or 'symbol' not in opt:
                    continue
                sym = opt['symbol']
                greeks = opt.get('greeks', {})
                volatility = greeks.get('mid_iv', 0.0)
                if volatility > 0:
                    collected[sym] = volatility

    # Process results
    for symbol, stock_data in symbol_map.items():
        ticker = stock_data['ticker']

        if symbol in collected:
            iv = collected[symbol]
            iv_pct = iv * 100

            if 15 <= iv_pct <= 80:
                passed.append({
                    **stock_data,
                    'iv': round(iv, 4),
                    'iv_pct': round(iv_pct, 1)
                })
            else:
                failed.append({'ticker': ticker, 'reason': f'IV {iv_pct:.1f}% out of range'})
        else:
            failed.append({'ticker': ticker, 'reason': 'no IV data'})

    return passed, failed

def save_results(passed, failed):
    with open("data/filter3_passed.json", "w") as f:
        json.dump(passed, f, indent=2)

    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: IV 15-80%")

def main():
    passed, failed = get_iv_data()
    save_results(passed, failed)
    print("Step 0D complete")

if __name__ == "__main__":
    main()
