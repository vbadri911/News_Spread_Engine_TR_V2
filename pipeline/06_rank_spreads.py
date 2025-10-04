"""
Rank Spreads: One spread per ticker only
"""
import json
import sys
from datetime import datetime

def rank_spreads():
    print("="*60)
    print("STEP 6: Rank Spreads (1 per ticker)")
    print("="*60)
    
    with open("data/spreads.json", "r") as f:
        data = json.load(f)
    spreads = data["spreads"]
    
    print(f"\n🏆 Ranking {len(spreads)} spreads...")
    
    # Add score = (ROI × PoP) / 100
    for spread in spreads:
        spread["score"] = round((spread["roi"] * spread["pop"]) / 100, 1)
        
        # Decision logic
        if spread["pop"] >= 70 and spread["roi"] >= 20:
            spread["decision"] = "ENTER"
        elif spread["pop"] >= 60 and spread["roi"] >= 30:
            spread["decision"] = "WATCH"
        else:
            spread["decision"] = "SKIP"
    
    # Sort by score
    spreads.sort(key=lambda x: x["score"], reverse=True)
    
    # Keep only BEST per ticker
    seen_tickers = set()
    unique_spreads = []
    
    for spread in spreads:
        if spread["ticker"] not in seen_tickers:
            seen_tickers.add(spread["ticker"])
            unique_spreads.append(spread)
    
    # Add rank
    for i, spread in enumerate(unique_spreads):
        spread["rank"] = i + 1
    
    # Group by decision
    enter = [s for s in unique_spreads if s["decision"] == "ENTER"]
    watch = [s for s in unique_spreads if s["decision"] == "WATCH"]
    skip = [s for s in unique_spreads if s["decision"] == "SKIP"]
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(unique_spreads),
            "enter": len(enter),
            "watch": len(watch),
            "skip": len(skip)
        },
        "ranked_spreads": unique_spreads,
        "enter_trades": enter,
        "watch_list": watch
    }
    
    with open("data/ranked_spreads.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results (1 per ticker):")
    print(f"   🟢 ENTER: {len(enter)}")
    print(f"   🟡 WATCH: {len(watch)}")
    print(f"   🔴 SKIP: {len(skip)}")
    
    print(f"\n🎯 Top 9 Spreads:")
    for spread in unique_spreads[:9]:
        print(f"   #{spread['rank']}: {spread['ticker']} {spread['type']} ${spread['short_strike']:.0f}/${spread['long_strike']:.0f}")
        print(f"        Score: {spread['score']} | ROI: {spread['roi']}% | PoP: {spread['pop']}%")
    
    print("\n✅ Step 6 complete: ranked_spreads.json")

if __name__ == "__main__":
    rank_spreads()
