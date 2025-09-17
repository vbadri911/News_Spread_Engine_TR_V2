"""
Get Real Greeks from TastyTrade Streaming
NO PLACEHOLDERS - Real market Greeks only
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from collections import defaultdict
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

async def get_real_greeks():
    """Stream real Greeks from TastyTrade"""
    print("="*60)
    print("STEP 5: Get REAL Greeks")
    print("="*60)
    print("\n🧮 Streaming Greeks from TastyTrade...")
    
    # Load liquid chains
    with open("data/liquid_chains.json", "r") as f:
        liquid_data = json.load(f)
    
    chains = liquid_data.get("chains", {})
    if not chains:
        print("❌ No liquid chains found")
        return
    
    sess = Session(USERNAME, PASSWORD)
    
    # Collect all symbols we need Greeks for
    all_symbols = []
    symbol_map = {}
    
    for ticker, expirations in chains.items():
        for exp_data in expirations:
            for strike in exp_data["strikes"]:
                # We need the actual option symbols from chains.json
                # Let's check what format they're in
                key = f"{ticker}_{exp_data['expiration_date']}_{strike['strike']}"
                symbol_map[key] = {
                    "ticker": ticker,
                    "strike": strike['strike'],
                    "expiration": exp_data['expiration_date'],
                    "dte": exp_data['dte']
                }
    
    print(f"📊 Need Greeks for {len(symbol_map)} strikes")
    
    # For now, let's try to get symbols from the original chains.json
    with open("data/chains.json", "r") as f:
        chains_data = json.load(f)
    
    # Build symbol list from chains
    option_symbols = []
    for ticker, exps in chains_data["chains"].items():
        for exp in exps:
            for strike in exp["strikes"]:
                # Check if we have symbols stored
                if "call_symbol" in strike and strike.get("call_bid", 0) > 0:
                    option_symbols.append(strike["call_symbol"])
                if "put_symbol" in strike and strike.get("put_bid", 0) > 0:
                    option_symbols.append(strike["put_symbol"])
    
    if not option_symbols:
        print("❌ No option symbols found - need to fix chain collection")
        return
    
    print(f"📡 Streaming Greeks for {len(option_symbols)} options...")
    
    # Stream Greeks in batches
    all_greeks = {}
    BATCH_SIZE = 300
    
    async with DXLinkStreamer(sess) as streamer:
        for i in range(0, len(option_symbols), BATCH_SIZE):
            batch = option_symbols[i:i+BATCH_SIZE]
            print(f"\n   Batch {i//BATCH_SIZE + 1}: {len(batch)} symbols")
            
            await streamer.subscribe(Greeks, batch)
            
            batch_greeks = {}
            start_time = asyncio.get_event_loop().time()
            
            # Collect for 10 seconds per batch
            while asyncio.get_event_loop().time() - start_time < 10:
                try:
                    greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.5)
                    
                    if greek and greek.event_symbol in batch:
                        iv = float(greek.volatility or 0)
                        if iv > 0:  # Only save if we have real IV
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
            print(f"      ✅ {len(batch_greeks)} Greeks ({coverage:.1f}% coverage)")
    
    # Organize and save
    total_coverage = len(all_greeks) / len(option_symbols) * 100 if option_symbols else 0
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_greeks": len(chains),
        "total_greeks_target": len(option_symbols),
        "total_greeks_collected": len(all_greeks),
        "overall_coverage": round(total_coverage, 1),
        "greeks_raw": all_greeks
    }
    
    with open("data/greeks.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ REAL Greeks collected: {len(all_greeks)}/{len(option_symbols)}")
    print(f"   Coverage: {total_coverage:.1f}%")

def main():
    asyncio.run(get_real_greeks())

if __name__ == "__main__":
    main()
