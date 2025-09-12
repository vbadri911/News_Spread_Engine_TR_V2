"""
Get Greeks Enhanced: Target 100% coverage for 22 quality tickers
Aggressive mode - we want ALL the data
"""
import asyncio
import json
import sys
from datetime import datetime
from collections import defaultdict
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks
from config import USERNAME, PASSWORD

async def get_greeks_100_coverage():
    """Get Greeks with 100% coverage target"""
    print("🧮 Getting Greeks - TARGET: 100% COVERAGE...")
    
    # Load chains
    with open("liquid_chains.json", "r") as f:
        chains = json.load(f)["liquid_chains"]
    
    sess = Session(USERNAME, PASSWORD)
    
    # Collect ALL symbols
    all_symbols = []
    symbol_info = {}
    
    for ticker, chain_data in chains.items():
        for strike in chain_data["liquid_strikes"]:
            symbol = strike["symbol"]
            all_symbols.append(symbol)
            symbol_info[symbol] = {
                "ticker": ticker,
                "strike": strike["strike"],
                "type": strike["type"],
                "bid": strike["bid"],
                "ask": strike["ask"],
                "mid": strike["mid"],
                "liquidity_score": strike["liquidity_score"]
            }
    
    print(f"📊 Total symbols to process: {len(all_symbols)}")
    print(f"🎯 Target: 100% coverage ({len(all_symbols)} Greeks)")
    
    # Process in smaller batches for better coverage
    BATCH_SIZE = 300  # Smaller batches = better coverage
    all_greeks = {}
    
    async with DXLinkStreamer(sess) as streamer:
        total_batches = (len(all_symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(all_symbols))
            batch = all_symbols[start_idx:end_idx]
            
            print(f"\n📦 Batch {batch_num + 1}/{total_batches}: {len(batch)} symbols")
            
            await streamer.subscribe(Greeks, batch)
            
            batch_greeks = {}
            start_time = asyncio.get_event_loop().time()
            missing = set(batch)
            
            # Aggressive collection - longer timeout, higher target
            while asyncio.get_event_loop().time() - start_time < 15:  # 15 seconds
                coverage = len(batch_greeks) / len(batch)
                
                if coverage >= 0.95:  # 95% target per batch
                    print(f"   ✅ {coverage:.0%} coverage achieved")
                    break
                
                try:
                    greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.2)
                    
                    if greek and greek.event_symbol in batch:
                        iv = float(greek.volatility or 0)
                        if iv > 0:
                            batch_greeks[greek.event_symbol] = {
                                "iv": round(iv, 4),
                                "delta": round(float(greek.delta or 0), 4),
                                "theta": round(float(greek.theta or 0), 4),
                                "gamma": round(float(greek.gamma or 0), 6),
                                "vega": round(float(greek.vega or 0), 4)
                            }
                            missing.discard(greek.event_symbol)
                            
                except asyncio.TimeoutError:
                    continue
            
            # Report missing
            if missing:
                print(f"   ⚠️ Missing {len(missing)} symbols, retrying...")
                
                # RETRY missing symbols
                await streamer.unsubscribe(Greeks, batch)
                await asyncio.sleep(0.5)
                await streamer.subscribe(Greeks, list(missing))
                
                retry_start = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - retry_start < 5:
                    try:
                        greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.3)
                        if greek and greek.event_symbol in missing:
                            iv = float(greek.volatility or 0)
                            if iv > 0:
                                batch_greeks[greek.event_symbol] = {
                                    "iv": round(iv, 4),
                                    "delta": round(float(greek.delta or 0), 4),
                                    "theta": round(float(greek.theta or 0), 4),
                                    "gamma": round(float(greek.gamma or 0), 6),
                                    "vega": round(float(greek.vega or 0), 4)
                                }
                    except asyncio.TimeoutError:
                        continue
            
            await streamer.unsubscribe(Greeks, list(missing) if missing else batch)
            
            all_greeks.update(batch_greeks)
            
            final_coverage = len(batch_greeks) / len(batch) * 100
            print(f"   📊 Final: {len(batch_greeks)}/{len(batch)} ({final_coverage:.1f}%)")
    
    # Calculate final coverage
    total_coverage = len(all_greeks) / len(all_symbols) * 100
    print(f"\n🎯 FINAL COVERAGE: {len(all_greeks)}/{len(all_symbols)} ({total_coverage:.1f}%)")
    
    if total_coverage < 100:
        print(f"💡 Missing {len(all_symbols) - len(all_greeks)} Greeks")
    else:
        print("🏆 100% COVERAGE ACHIEVED!")
    
    # Organize by ticker
    by_ticker = defaultdict(lambda: {"greeks": [], "stats": {}})
    
    for symbol, greek_data in all_greeks.items():
        info = symbol_info[symbol]
        ticker = info["ticker"]
        
        by_ticker[ticker]["greeks"].append({
            **info,
            **greek_data
        })
    
    # Save with enhanced metadata
    for ticker in by_ticker:
        chain_data = chains[ticker]
        by_ticker[ticker]["ticker"] = ticker
        by_ticker[ticker]["stock_price"] = chain_data["stock_price"]
        by_ticker[ticker]["expiration"] = chain_data["best_expiration"]
        by_ticker[ticker]["count"] = len(by_ticker[ticker]["greeks"])
        by_ticker[ticker]["coverage"] = (
            len(by_ticker[ticker]["greeks"]) / 
            len([s for s in symbol_info.values() if s["ticker"] == ticker]) * 100
        )
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_greeks": len(by_ticker),
        "total_greeks_target": len(all_symbols),
        "total_greeks_collected": len(all_greeks),
        "overall_coverage": total_coverage,
        "greeks": dict(by_ticker)
    }
    
    with open("greeks.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Greeks saved with {total_coverage:.1f}% coverage")

def main():
    print("="*60)
    print("STEP 5: Get Greeks (100% COVERAGE TARGET)")
    print("="*60)
    
    asyncio.run(get_greeks_100_coverage())

if __name__ == "__main__":
    main()
