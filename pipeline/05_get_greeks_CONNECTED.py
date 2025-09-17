"""
Get Greeks - Using exact symbols from chains.json for data connectivity
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

async def get_connected_greeks():
    print("="*60)
    print("STEP 5: Get Greeks (Connected)")
    print("="*60)
    
    # Load chains with symbols
    with open("data/chains.json", "r") as f:
        chains_data = json.load(f)
    
    sess = Session(USERNAME, PASSWORD)
    
    print("\n🧮 Collecting Greeks for exact chain strikes...")
    
    # Extract all option symbols from chains
    all_symbols = []
    symbol_map = {}  # Map symbol to its location in chains
    
    for ticker, expirations in chains_data["chains"].items():
        for exp_idx, exp_data in enumerate(expirations):
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
    
    # Stream Greeks in batches
    all_greeks = {}
    BATCH_SIZE = 300
    
    async with DXLinkStreamer(sess) as streamer:
        for i in range(0, len(all_symbols), BATCH_SIZE):
            batch = all_symbols[i:i+BATCH_SIZE]
            print(f"\n   Batch {i//BATCH_SIZE + 1}: {len(batch)} symbols")
            
            await streamer.subscribe(Greeks, batch)
            
            batch_greeks = {}
            start_time = asyncio.get_event_loop().time()
            
            # Collect for 8 seconds per batch
            while asyncio.get_event_loop().time() - start_time < 8:
                try:
                    greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.3)
                    
                    if greek and greek.event_symbol in batch:
                        iv = float(greek.volatility or 0)
                        if iv > 0:  # Only save real Greeks
                            batch_greeks[greek.event_symbol] = {
                                "iv": round(iv, 4),
                                "delta": round(float(greek.delta or 0), 4),
                                "theta": round(float(greek.theta or 0), 4),
                                "gamma": round(float(greek.gamma or 0), 6),
                                "vega": round(float(greek.vega or 0), 4)
                            }
                except asyncio.TimeoutError:
                    continue
            
            await streamer.unsubscribe(Greeks, batch)
            all_greeks.update(batch_greeks)
            
            coverage = len(batch_greeks) / len(batch) * 100 if batch else 0
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
            
            # Add Greeks to the exact strike location
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
    asyncio.run(get_connected_greeks())

if __name__ == "__main__":
    main()
