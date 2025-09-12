"""
Get Greeks: IV, Delta, Theta for LIQUID options only
This is expensive - only do it for options that passed liquidity check
"""
import asyncio
import json
import sys
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks
from config import USERNAME, PASSWORD

def load_liquid_chains():
    """Load only liquid chains"""
    try:
        with open("liquid_chains.json", "r") as f:
            data = json.load(f)
        return data["liquid_chains"]
    except FileNotFoundError:
        print("❌ liquid_chains.json not found - run check_liquidity.py first")
        sys.exit(1)

async def get_real_greeks():
    """Get real Greeks - no fallbacks"""
    print("🧮 Getting real Greeks from TastyTrade...")
    
    chains = load_liquid_chains()
    sess = Session(USERNAME, PASSWORD)
    
    greeks_data = {}
    
    async with DXLinkStreamer(sess) as streamer:
        for ticker, chain_data in chains.items():
            print(f"\n{ticker}: Getting Greeks...")
            
            # Get symbols for liquid strikes only
            symbols = [s["symbol"] for s in chain_data["liquid_strikes"]]
            
            if not symbols:
                print(f"   ❌ No liquid symbols")
                continue
            
            # Subscribe to Greeks
            await streamer.subscribe(Greeks, symbols)
            
            ticker_greeks = []
            collected = 0
            
            # Collect for 8 seconds
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 8:
                try:
                    greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.5)
                    
                    if greek and greek.event_symbol in symbols:
                        # Find the strike info
                        strike_info = None
                        for s in chain_data["liquid_strikes"]:
                            if s["symbol"] == greek.event_symbol:
                                strike_info = s
                                break
                        
                        if strike_info:
                            iv = float(greek.volatility or 0)
                            delta = float(greek.delta or 0)
                            theta = float(greek.theta or 0)
                            
                            if iv > 0:  # Must have real IV
                                ticker_greeks.append({
                                    "strike": strike_info["strike"],
                                    "type": strike_info["type"],
                                    "symbol": strike_info["symbol"],
                                    "bid": strike_info["bid"],
                                    "ask": strike_info["ask"],
                                    "mid": strike_info["mid"],
                                    "iv": round(iv, 4),
                                    "delta": round(delta, 4),
                                    "theta": round(theta, 4),
                                    "gamma": round(float(greek.gamma or 0), 6),
                                    "vega": round(float(greek.vega or 0), 4)
                                })
                                collected += 1
                                
                except asyncio.TimeoutError:
                    continue
            
            await streamer.unsubscribe(Greeks, symbols)
            
            if ticker_greeks:
                greeks_data[ticker] = {
                    "ticker": ticker,
                    "stock_price": chain_data["stock_price"],
                    "expiration": chain_data["best_expiration"],
                    "greeks": ticker_greeks,
                    "count": len(ticker_greeks)
                }
                print(f"   ✅ Got Greeks for {len(ticker_greeks)} options")
            else:
                print(f"   ❌ No Greeks collected")
    
    return greeks_data

def save_greeks(greeks_data):
    """Save Greeks data"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_greeks": len(greeks_data),
        "greeks": greeks_data
    }
    
    with open("greeks.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Tickers with Greeks: {len(greeks_data)}")
    
    if len(greeks_data) == 0:
        print("❌ FATAL: No Greeks collected")
        sys.exit(1)
    
    # Show IV summary
    all_ivs = []
    for ticker_data in greeks_data.values():
        for greek in ticker_data["greeks"]:
            all_ivs.append(greek["iv"])
    
    if all_ivs:
        avg_iv = sum(all_ivs) / len(all_ivs)
        print(f"   Average IV: {avg_iv:.2%}")
        print(f"   Max IV: {max(all_ivs):.2%}")
        print(f"   Min IV: {min(all_ivs):.2%}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 5: Get Greeks")
    print("="*60)
    
    # Get Greeks
    greeks_data = asyncio.run(get_real_greeks())
    
    # Save results
    save_greeks(greeks_data)
    
    print("✅ Step 5 complete: greeks.json created")

if __name__ == "__main__":
    main()
