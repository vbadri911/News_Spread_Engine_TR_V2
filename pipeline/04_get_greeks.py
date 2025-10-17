"""
Get Greeks - Using exact symbols from chains.json for data connectivity
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

def fetch_greeks_batch(batch):
    params = {'symbols': ','.join(batch), 'greeks': 'true'}
    resp = requests.get(f'{base_url}/v1/markets/quotes', params=params, headers=headers)
    batch_greeks = {}
    if resp.status_code == 200:
        data = resp.json().get('quotes', {}).get('quote', [])
        if not isinstance(data, list):
            data = [data] if data else []

        for opt in data:
            if not opt or 'symbol' not in opt:
                continue
            symbol = opt['symbol']
            greeks = opt.get('greeks', {})
            iv = float(greeks.get('mid_iv', 0))
            if iv > 0:
                batch_greeks[symbol] = {
                    "iv": round(iv, 4),
                    "delta": round(float(greeks.get('delta', 0)), 4),
                    "theta": round(float(greeks.get('theta', 0)), 4),
                    "gamma": round(float(greeks.get('gamma', 0)), 6),
                    "vega": round(float(greeks.get('vega', 0)), 4)
                }
    return batch_greeks

def get_connected_greeks():
    print("="*60)
    print("STEP 04: Get Greeks")
    print("="*60)

    with open("data/chains.json", "r") as f:
        chains_data = json.load(f)

    print("\n🧮 Collecting Greeks for exact chain strikes...")

    all_symbols = []
    symbol_map = {}

    for ticker, expirations in chains_data["chains"].items():
        for exp_idx, exp_data in enumerate(expirations):
            exp_date = exp_data["expiration_date"].replace('-', '')
            for strike_idx, strike in enumerate(exp_data["strikes"]):
                if strike.get("call_symbol") and strike.get("call_bid", 0) > 0:
                    symbol = strike["call_symbol"]
                    all_symbols.append(symbol)
                    symbol_map[symbol] = {
                        "ticker": ticker,
                        "exp_idx": exp_idx,
                        "strike_idx": strike_idx,
                        "type": "call",
                        "strike": strike["strike"]
                    }

                if strike.get("put_symbol") and strike.get("put_bid", 0) > 0:
                    symbol = strike["put_symbol"]
                    all_symbols.append(symbol)
                    symbol_map[symbol] = {
                        "ticker": ticker,
                        "exp_idx": exp_idx,
                        "strike_idx": strike_idx,
                        "type": "put",
                        "strike": strike["strike"]
                    }

    print(f"📊 Need Greeks for {len(all_symbols)} options")

    all_greeks = {}
    BATCH_SIZE = 20

    batches = [all_symbols[i:i + BATCH_SIZE] for i in range(0, len(all_symbols), BATCH_SIZE)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_greeks_batch, batch) for batch in batches]
        for future in concurrent.futures.as_completed(futures):
            batch_greeks = future.result()
            all_greeks.update(batch_greeks)
            coverage = len(batch_greeks) / BATCH_SIZE * 100 if BATCH_SIZE else 0
            print(f"      ✅ {len(batch_greeks)} Greeks ({coverage:.1f}%)")

    # Add Greeks back to chains structure for connectivity
    chains_with_greeks = chains_data.copy()

    for symbol, greek_data in all_greeks.items():
        if symbol in symbol_map:
            loc = symbol_map[symbol]
            ticker = loc["ticker"]
            exp_idx = loc["exp_idx"]
            strike_idx = loc["strike_idx"]
            opt_type = loc["type"]

            if opt_type == "call":
                chains_with_greeks["chains"][ticker][exp_idx]["strikes"][strike_idx]["call_greeks"] = greek_data
            else:
                chains_with_greeks["chains"][ticker][exp_idx]["strikes"][strike_idx]["put_greeks"] = greek_data

    # Save connected data
    total_coverage = len(all_greeks) / len(all_symbols) * 100 if all_symbols else 0

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_options": len(all_symbols),
        "greeks_collected": len(all_greeks),
        "coverage": round(total_coverage, 1),
        "chains_with_greeks": chains_with_greeks["chains"]  # Chains with Greeks embedded
    }

    with open("data/chains_with_greeks.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Greeks collected and connected: {len(all_greeks)}/{len(all_symbols)}")
    print(f"   Coverage: {total_coverage:.1f}%")
    print(f"   Saved to: chains_with_greeks.json")

def main():
    get_connected_greeks()

if __name__ == "__main__":
    main()
