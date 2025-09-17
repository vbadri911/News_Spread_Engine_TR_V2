"""
FIXED Liquidity Checker - Works with multiple expirations
Processes ALL expirations from chains.json
"""
import json
import asyncio
from datetime import datetime

def load_chains():
    """Load chains data"""
    try:
        with open("data/chains.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ chains.json not found")
        return None

async def check_option_liquidity():
    """Check liquidity for all options with multiple expirations"""
    print("💧 Checking liquidity for ALL expirations...")
    
    chains_data = load_chains()
    if not chains_data or not chains_data.get("chains"):
        print("❌ No chains to check")
        return {}
    
    liquid_chains = {}
    total_liquid_options = 0
    
    for ticker, expirations_list in chains_data["chains"].items():
        print(f"\n{ticker}: Checking liquidity...")
        
        ticker_liquid_exps = []
        
        # Process each expiration
        for exp_data in expirations_list:
            exp_date = exp_data["expiration_date"]
            dte = exp_data["dte"]
            strikes = exp_data["strikes"]
            
            liquid_strikes = []
            
            for strike_data in strikes:
                strike = strike_data["strike"]
                
                # Calculate liquidity score for calls
                call_bid = strike_data.get("call_bid", 0)
                call_ask = strike_data.get("call_ask", 0)
                call_mid = (call_bid + call_ask) / 2 if call_ask > 0 else 0
                call_spread = call_ask - call_bid if call_ask > call_bid else float('inf')
                call_spread_pct = (call_spread / call_mid * 100) if call_mid > 0 else float('inf')
                
                # Calculate liquidity score for puts  
                put_bid = strike_data.get("put_bid", 0)
                put_ask = strike_data.get("put_ask", 0)
                put_mid = (put_bid + put_ask) / 2 if put_ask > 0 else 0
                put_spread = put_ask - put_bid if put_ask > put_bid else float('inf')
                put_spread_pct = (put_spread / put_mid * 100) if put_mid > 0 else float('inf')
                
                # Liquidity criteria
                call_liquid = (call_mid >= 0.30 and call_spread_pct < 10)
                put_liquid = (put_mid >= 0.30 and put_spread_pct < 10)
                
                if call_liquid or put_liquid:
                    liquid_strikes.append({
                        "strike": strike,
                        "call_bid": call_bid,
                        "call_ask": call_ask,
                        "call_liquid": call_liquid,
                        "put_bid": put_bid,
                        "put_ask": put_ask,
                        "put_liquid": put_liquid
                    })
            
            if liquid_strikes:
                ticker_liquid_exps.append({
                    "expiration_date": exp_date,
                    "dte": dte,
                    "strikes": liquid_strikes
                })
                total_liquid_options += len(liquid_strikes)
        
        if ticker_liquid_exps:
            liquid_chains[ticker] = ticker_liquid_exps
            total_strikes = sum(len(e["strikes"]) for e in ticker_liquid_exps)
            print(f"   ✅ {len(ticker_liquid_exps)} expirations with {total_strikes} liquid strikes")
        else:
            print(f"   ❌ No liquid options")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_liquidity": len(liquid_chains),
        "total_liquid_options": total_liquid_options,
        "chains": liquid_chains
    }

def main():
    """Main execution"""
    print("="*60)
    print("STEP 4: Check Liquidity (FIXED)")
    print("="*60)
    
    liquid_chains = asyncio.run(check_option_liquidity())
    
    # Save results
    with open("data/liquid_chains.json", "w") as f:
        json.dump(liquid_chains, f, indent=2)
    
    print(f"\n✅ Liquidity check complete")
    print(f"   Tickers with liquid options: {liquid_chains.get('tickers_with_liquidity', 0)}")
    print(f"   Total liquid options: {liquid_chains.get('total_liquid_options', 0)}")

if __name__ == "__main__":
    main()
