"""
Get Options Chains - Complete with symbols for Greeks matching
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

def load_stock_prices():
    try:
        with open("data/stock_prices.json", "r") as f:
            data = json.load(f)
        return data["prices"]
    except FileNotFoundError:
        print("❌ stock_prices.json not found")
        sys.exit(1)

def process_ticker(ticker, price_data):
    stock_price = price_data["mid"]
    today = datetime.now().date()
    try:
        # Get expirations
        resp = requests.get(f'{base_url}/v1/markets/options/expirations', params={'symbol': ticker}, headers=headers)
        if resp.status_code != 200:
            print(f"   ❌ {ticker}: Error getting expirations: {resp.text}")
            return None

        exp_data = resp.json().get('expirations')
        if not exp_data:
            print(f"   ❌ {ticker}: No options chain")
            return None
        exps = exp_data.get('date', []) if isinstance(exp_data, dict) else [e['date'] for e in exp_data]

        ticker_expirations = []

        for exp_date in exps:
            exp = datetime.strptime(exp_date, '%Y-%m-%d').date()
            dte = (exp - today).days
            if 0 <= dte <= 45:
                # Fetch chain for this expiration
                resp_chain = requests.get(f'{base_url}/v1/markets/options/chains', params={'symbol': ticker, 'expiration': exp_date}, headers=headers)
                if resp_chain.status_code != 200:
                    print(f"   ❌ {ticker} ({exp_date}): Error getting chain: {resp_chain.text}")
                    continue

                chain_data = resp_chain.json().get('options', {}).get('option', [])
                if not chain_data:
                    print(f"   ❌ {ticker} ({exp_date}): Empty chain")
                    continue

                strikes = {}
                for opt in chain_data:
                    strike = opt['strike']
                    if strike not in strikes:
                        strikes[strike] = {'strike': strike}

                    # Store the actual symbol and quotes
                    exp_date_clean = exp_date.replace('-', '')
                    strike_int = int(strike * 1000)
                    symbol = f"{ticker}{exp_date_clean[2:]}{'C' if opt['option_type'] == 'call' else 'P'}{strike_int:08d}"

                    if opt['option_type'] == 'call':
                        strikes[strike]['call_symbol'] = symbol
                        strikes[strike]['call_bid'] = float(opt.get('bid', 0))
                        strikes[strike]['call_ask'] = float(opt.get('ask', 0))
                    else:
                        strikes[strike]['put_symbol'] = symbol
                        strikes[strike]['put_bid'] = float(opt.get('bid', 0))
                        strikes[strike]['put_ask'] = float(opt.get('ask', 0))

                if strikes:
                    ticker_expirations.append({
                        'expiration_date': exp_date,
                        'dte': dte,
                        'strikes': sorted(list(strikes.values()), key=lambda x: x['strike'])
                    })

        if ticker_expirations:
            print(f"   ✅ {ticker}: {len(ticker_expirations)} expirations")
            return {ticker: ticker_expirations}
        else:
            return None
    except Exception as e:
        print(f"   ❌ {ticker}: {e}")
        return None

def get_chains():
    print("="*60)
    print("STEP 02: Get Options Chains")
    print("="*60)

    prices = load_stock_prices()

    chains = {}
    print("\n📊 Collecting chains with symbols...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker, ticker, price_data) for ticker, price_data in prices.items()]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                chains.update(result)

    # Save complete chains with symbols
    total_exp = sum(len(exps) for exps in chains.values())
    total_strikes = sum(len(exp['strikes']) for exps in chains.values() for exp in exps)

    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": len(prices),
        "success": len(chains),
        "total_expirations": total_exp,
        "total_strikes": total_strikes,
        "chains": chains
    }

    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Chains complete: {len(chains)}/{len(prices)} stocks")
    print(f"   Expirations: {total_exp}")
    print(f"   Strikes: {total_strikes} (with symbols)")

def main():
    get_chains()

if __name__ == "__main__":
    main()
