"""
Get Options Chains: WIDER strike range for credit spreads
Gets strikes from 70% to 130% of stock price
"""
import json
import sys
import os
from datetime import datetime, timedelta
from tastytrade import Session
from tastytrade.instruments import get_option_chain

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

def load_stock_prices():
    """Load stocks that have prices"""
    try:
        with open("data/stock_prices.json", "r") as f:
            data = json.load(f)
        return data["prices"]
    except FileNotFoundError:
        print("❌ stock_prices.json not found - run get_stock_prices.py first")
        sys.exit(1)

def get_chains():
    """Get options chains for all stocks"""
    print("⛓️ Getting WIDER options chains from TastyTrade...")
    
    prices = load_stock_prices()
    sess = Session(USERNAME, PASSWORD)
    
    chains = {}
    failed = []
    
    # Target expiration range (15-45 DTE)
    today = datetime.now().date()
    min_date = today + timedelta(days=15)
    max_date = today + timedelta(days=45)
    
    for ticker, price_data in prices.items():
        print(f"\n{ticker}: Getting chain...")
        stock_price = price_data["mid"]
        
        try:
            chain = get_option_chain(sess, ticker)
            
            if not chain:
                print(f"   ❌ No options chain")
                failed.append(ticker)
                continue
            
            # Find suitable expirations
            suitable_exps = []
            for exp_date in chain.keys():
                dte = (exp_date - today).days
                if 15 <= dte <= 45:
                    suitable_exps.append({
                        "date": exp_date.isoformat(),
                        "dte": dte
                    })
            
            if not suitable_exps:
                print(f"   ⚠️ No expirations in 15-45 DTE range")
                failed.append(ticker)
                continue
            
            # Get strikes for best expiration
            best_exp = suitable_exps[0]
            exp_date = datetime.fromisoformat(best_exp["date"]).date()
            options = chain[exp_date]
            
            # WIDER RANGE: 70% to 130% of stock price
            strikes = []
            for opt in options:
                strike = float(opt.strike_price)
                # Include strikes from 70% to 130%
                if stock_price * 0.70 <= strike <= stock_price * 1.30:
                    strikes.append({
                        "strike": strike,
                        "type": opt.option_type.value,
                        "symbol": opt.streamer_symbol
                    })
            
            chains[ticker] = {
                "ticker": ticker,
                "stock_price": stock_price,
                "expirations": suitable_exps,
                "best_expiration": best_exp,
                "strikes_count": len(strikes),
                "strikes": strikes  # Don't limit to 20
            }
            
            # Show strike distribution
            calls_otm = len([s for s in strikes if s["type"] == "C" and s["strike"] > stock_price])
            puts_otm = len([s for s in strikes if s["type"] == "P" and s["strike"] < stock_price])
            print(f"   ✅ {len(suitable_exps)} expirations, {len(strikes)} strikes")
            print(f"      OTM: {calls_otm} calls, {puts_otm} puts")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append(ticker)
    
    return chains, failed

def save_chains(chains, failed):
    """Save chain data"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "success": len(chains),
        "failed": len(failed),
        "chains": chains,
        "missing_tickers": failed
    }
    
    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Success: {len(chains)} tickers with chains")
    print(f"   Failed: {len(failed)} tickers")
    
    if len(chains) == 0:
        print("❌ FATAL: No chains collected")
        sys.exit(1)

def main():
    """Main execution"""
    print("="*60)
    print("STEP 3: Get Options Chains (WIDER RANGE)")
    print("="*60)
    
    # Get chains
    chains, failed = get_chains()
    
    # Save results
    save_chains(chains, failed)
    
    print("✅ Step 3 complete: chains.json created")

if __name__ == "__main__":
    main()
