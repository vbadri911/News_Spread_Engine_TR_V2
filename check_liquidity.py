"""
Check Liquidity: Filter out illiquid options
Keep only options with good bid/ask spreads
"""
import asyncio
import json
import sys
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote
from config import USERNAME, PASSWORD

def load_chains():
    """Load chains from previous step"""
    try:
        with open("chains.json", "r") as f:
            data = json.load(f)
        return data["chains"]
    except FileNotFoundError:
        print("❌ chains.json not found - run get_options_chains.py first")
        sys.exit(1)

async def check_option_liquidity():
    """Check bid/ask spreads for liquidity"""
    print("💧 Checking options liquidity...")
    
    chains = load_chains()
    sess = Session(USERNAME, PASSWORD)
    
    liquid_chains = {}
    
    async with DXLinkStreamer(sess) as streamer:
        for ticker, chain_data in chains.items():
            print(f"\n{ticker}: Checking liquidity...")
            
            # Get symbols for this ticker's options
            symbols = [s["symbol"] for s in chain_data["strikes"]]
            
            if not symbols:
                print(f"   ❌ No symbols to check")
                continue
            
            # Subscribe to quotes
            await streamer.subscribe(Quote, symbols)
            
            liquid_strikes = []
            checked = 0
            
            # Collect for 5 seconds
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 5:
                try:
                    quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.5)
                    
                    if quote and quote.event_symbol in symbols:
                        bid = float(quote.bid_price or 0)
                        ask = float(quote.ask_price or 0)
                        
                        if bid > 0 and ask > 0:
                            spread = ask - bid
                            mid = (bid + ask) / 2
                            spread_pct = (spread / mid * 100) if mid > 0 else 999
                            
                            # Find the strike info
                            strike_info = None
                            for s in chain_data["strikes"]:
                                if s["symbol"] == quote.event_symbol:
                                    strike_info = s
                                    break
                            
                            if strike_info and spread_pct < 10:  # Less than 10% spread
                                liquid_strikes.append({
                                    "strike": strike_info["strike"],
                                    "type": strike_info["type"],
                                    "symbol": strike_info["symbol"],
                                    "bid": round(bid, 2),
                                    "ask": round(ask, 2),
                                    "mid": round(mid, 2),
                                    "spread_pct": round(spread_pct, 2)
                                })
                                checked += 1
                                
                except asyncio.TimeoutError:
                    continue
            
            await streamer.unsubscribe(Quote, symbols)
            
            if liquid_strikes:
                liquid_chains[ticker] = {
                    **chain_data,
                    "liquid_strikes": liquid_strikes,
                    "liquid_count": len(liquid_strikes)
                }
                print(f"   ✅ {len(liquid_strikes)} liquid strikes")
            else:
                print(f"   ❌ No liquid strikes found")
    
    return liquid_chains

def save_liquid_chains(liquid_chains):
    """Save liquid chains only"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_liquidity": len(liquid_chains),
        "liquid_chains": liquid_chains
    }
    
    with open("liquid_chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Liquid tickers: {len(liquid_chains)}")
    
    if len(liquid_chains) == 0:
        print("❌ FATAL: No liquid options found")
        sys.exit(1)
    
    # Show summary
    total_liquid = sum(c["liquid_count"] for c in liquid_chains.values())
    print(f"   Total liquid strikes: {total_liquid}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 4: Check Liquidity")
    print("="*60)
    
    # Check liquidity
    liquid_chains = asyncio.run(check_option_liquidity())
    
    # Save results
    save_liquid_chains(liquid_chains)
    
    print("✅ Step 4 complete: liquid_chains.json created")

if __name__ == "__main__":
    main()
