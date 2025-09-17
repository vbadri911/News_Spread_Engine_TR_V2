"""
FIXED Options Chain Collector - Gets ALL Expirations 0-45 DTE
This version collects ALL expiration dates, not just one
"""
import json
import sys
import os
from datetime import datetime, timedelta
from tastytrade import Session
from tastytrade.instruments import get_option_chain

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

def load_stock_prices():
    try:
        with open("data/stock_prices.json", "r") as f:
            data = json.load(f)
        return data["prices"]
    except FileNotFoundError:
        print("❌ stock_prices.json not found")
        sys.exit(1)

def get_chains():
    print("⛓️ Getting ALL chains (0-45 DTE) from TastyTrade...")
    
    prices = load_stock_prices()
    sess = Session(USERNAME, PASSWORD)
    
    chains = {}
    failed = []
    total_expirations = 0
    
    today = datetime.now().date()
    
    for ticker, price_data in prices.items():
        print(f"\n{ticker}: ${price_data['mid']:.2f}")
        stock_price = price_data["mid"]
        
        try:
            # Get COMPLETE chain with ALL expirations
            chain = get_option_chain(sess, ticker)
            
            if not chain:
                failed.append(ticker)
                continue
            
            # Collect ALL expirations from 0-45 DTE
            ticker_exps = []
            
            for exp in chain.expirations:
                exp_date = exp.expiration_date
                dte = (exp_date - today).days
                
                # Include ALL expirations 0-45 DTE
                if 0 <= dte <= 45:
                    # Get strikes 70-130% of stock price
                    min_strike = stock_price * 0.70
                    max_strike = stock_price * 1.30
                    
                    exp_strikes = []
                    for strike in exp.strikes:
                        if min_strike <= strike.strike_price <= max_strike:
                            exp_strikes.append({
                                'strike': float(strike.strike_price),
                                'call_bid': float(strike.call_bid or 0),
                                'call_ask': float(strike.call_ask or 0),
                                'put_bid': float(strike.put_bid or 0),
                                'put_ask': float(strike.put_ask or 0)
                            })
                    
                    if exp_strikes:
                        ticker_exps.append({
                            'expiration_date': str(exp_date),
                            'dte': dte,
                            'strikes': exp_strikes
                        })
            
            if ticker_exps:
                chains[ticker] = ticker_exps
                total_expirations += len(ticker_exps)
                dtes = [exp['dte'] for exp in ticker_exps]
                print(f"   ✅ {len(ticker_exps)} expirations: {dtes}")
            else:
                failed.append(ticker)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append(ticker)
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": len(prices),
        "success": len(chains),
        "failed": failed,
        "total_expirations": total_expirations,
        "chains": chains
    }
    
    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ CHAINS COMPLETE: {len(chains)}/{len(prices)} stocks")
    print(f"   Total expirations: {total_expirations}")

if __name__ == "__main__":
    get_chains()
