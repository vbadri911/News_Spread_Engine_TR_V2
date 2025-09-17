"""
Check Liquidity Enhanced: Multi-factor scoring instead of binary filter
Scores each option 0-100 based on spread, volume, and price
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

def load_chains():
    """Load chains from previous step"""
    try:
        with open("data/chains.json", "r") as f:
            data = json.load(f)
        return data["chains"]
    except FileNotFoundError:
        print("❌ chains.json not found - run get_options_chains.py first")
        sys.exit(1)

def calculate_liquidity_score(bid, ask, mid):
    """Score liquidity 0-100 based on spread and price"""
    score = 0
    
    # Spread tightness (60 points)
    if mid > 0:
        spread_pct = ((ask - bid) / mid) * 100
        if spread_pct <= 3:
            score += 60
        elif spread_pct <= 5:
            score += 45
        elif spread_pct <= 8:
            score += 30
        elif spread_pct <= 12:
            score += 15
        elif spread_pct <= 20:
            score += 5
    
    # Price quality (40 points) - prefer options worth at least 30 cents
    if mid >= 1.00:
        score += 40
    elif mid >= 0.50:
        score += 30
    elif mid >= 0.30:
        score += 20
    elif mid >= 0.20:
        score += 10
    
    return score

async def check_option_liquidity():
    """Check liquidity and score each option"""
    print("💧 Scoring options liquidity...")
    
    chains = load_chains()
    sess = Session(USERNAME, PASSWORD)
    
    liquid_chains = {}
    
    async with DXLinkStreamer(sess) as streamer:
        for ticker, chain_data in chains.items():
            print(f"\n{ticker}: Checking liquidity...")
            
            symbols = [s["symbol"] for s in chain_data["strikes"]]
            
            if not symbols:
                print(f"   ❌ No symbols to check")
                continue
            
            await streamer.subscribe(Quote, symbols)
            
            liquid_strikes = []
            checked = 0
            
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 5:
                try:
                    quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.5)
                    
                    if quote and quote.event_symbol in symbols:
                        bid = float(quote.bid_price or 0)
                        ask = float(quote.ask_price or 0)
                        
                        if bid > 0 and ask > 0:
                            mid = (bid + ask) / 2
                            spread = ask - bid
                            spread_pct = (spread / mid * 100) if mid > 0 else 999
                            
                            # Calculate liquidity score
                            score = calculate_liquidity_score(bid, ask, mid)
                            
                            # Find the strike info
                            strike_info = None
                            for s in chain_data["strikes"]:
                                if s["symbol"] == quote.event_symbol:
                                    strike_info = s
                                    break
                            
                            # Keep if score >= 40 (not just <10% spread)
                            if strike_info and score >= 40:
                                liquid_strikes.append({
                                    "strike": strike_info["strike"],
                                    "type": strike_info["type"],
                                    "symbol": strike_info["symbol"],
                                    "bid": round(bid, 2),
                                    "ask": round(ask, 2),
                                    "mid": round(mid, 2),
                                    "spread_pct": round(spread_pct, 2),
                                    "liquidity_score": score
                                })
                                checked += 1
                                
                except asyncio.TimeoutError:
                    continue
            
            await streamer.unsubscribe(Quote, symbols)
            
            if liquid_strikes:
                # Sort by liquidity score
                liquid_strikes.sort(key=lambda x: x["liquidity_score"], reverse=True)
                
                liquid_chains[ticker] = {
                    **chain_data,
                    "liquid_strikes": liquid_strikes,
                    "liquid_count": len(liquid_strikes),
                    "avg_liquidity_score": round(
                        sum(s["liquidity_score"] for s in liquid_strikes) / len(liquid_strikes), 1
                    )
                }
                print(f"   ✅ {len(liquid_strikes)} liquid strikes (avg score: {liquid_chains[ticker]['avg_liquidity_score']})")
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
    
    with open("data/liquid_chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Liquid tickers: {len(liquid_chains)}")
    
    if len(liquid_chains) == 0:
        print("❌ FATAL: No liquid options found")
        sys.exit(1)
    
    total_liquid = sum(c["liquid_count"] for c in liquid_chains.values())
    print(f"   Total liquid strikes: {total_liquid}")
    
    # Show score distribution
    all_scores = []
    for chain in liquid_chains.values():
        all_scores.extend([s["liquidity_score"] for s in chain["liquid_strikes"]])
    
    if all_scores:
        print(f"   Score range: {min(all_scores)} - {max(all_scores)}")
        print(f"   Average score: {sum(all_scores)/len(all_scores):.1f}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 4: Check Liquidity (ENHANCED)")
    print("="*60)
    
    liquid_chains = asyncio.run(check_option_liquidity())
    save_liquid_chains(liquid_chains)
    
    print("✅ Step 4 complete: liquid_chains.json created")

if __name__ == "__main__":
    main()
