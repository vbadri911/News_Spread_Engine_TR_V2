"""
Get Options Chains: Find available strikes and expirations
Only for stocks with prices
"""
import json
import sys
from datetime import datetime, timedelta
from tastytrade import Session
from tastytrade.instruments import get_option_chain
from config import USERNAME, PASSWORD

def load_stock_prices():
    """Load stocks that have prices"""
    try:
        with open("stock_prices.json", "r") as f:
            data = json.load(f)
        return data["prices"]
    except FileNotFoundError:
        print("❌ stock_prices.json not found - run get_stock_prices.py first")
        sys.exit(1)

def get_chains():
    """Get options chains for all stocks"""
    print("⛓️ Getting options chains from TastyTrade...")
    
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
            
            # Find strikes near money (80% to 120% of stock price)
            strikes = []
            for opt in options:
                strike = float(opt.strike_price)
                if stock_price * 0.8 <= strike <= stock_price * 1.2:
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
                "strikes": strikes[:20]  # Limit to 20 strikes for now
            }
            
            print(f"   ✅ {len(suitable_exps)} expirations, {len(strikes)} strikes")
            
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
    
    with open("chains.json", "w") as f:
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
    print("STEP 3: Get Options Chains")
    print("="*60)
    
    # Get chains
    chains, failed = get_chains()
    
    # Save results
    save_chains(chains, failed)
    
    print("✅ Step 3 complete: chains.json created")

if __name__ == "__main__":
    main()
