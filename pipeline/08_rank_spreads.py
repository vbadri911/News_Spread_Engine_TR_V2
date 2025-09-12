"""
Rank Spreads: Multi-factor ranking system
Uses REAL data only - no random numbers
"""
import json
import sys
from datetime import datetime

def load_analyzed_spreads():
    """Load analyzed spreads"""
    try:
        with open("data/analyzed_spreads.json", "r") as f:
            data = json.load(f)
        return data["analyzed_spreads"]
    except FileNotFoundError:
        print("❌ analyzed_spreads.json not found - run calculate_pop_roi.py first")
        sys.exit(1)

def rank_spreads():
    """Rank spreads using multiple factors"""
    print("🏆 Ranking spreads with real data...")
    
    spreads = load_analyzed_spreads()
    
    # Add ranking factors
    for spread in spreads:
        # Factor 1: Risk-adjusted return (already calculated as score)
        score_rank = spread["score"]
        
        # Factor 2: Probability rank (higher PoP is better)
        pop_rank = spread["pop"] / 100
        
        # Factor 3: ROI rank (normalized)
        roi_rank = min(spread["roi"] / 100, 1.0)  # Cap at 100%
        
        # Factor 4: Distance from money (safety)
        distance = abs(spread["short_strike"] - spread["stock_price"]) / spread["stock_price"]
        distance_rank = min(distance * 10, 1.0)  # 10% distance = 1.0
        
        # Composite rank (weighted)
        spread["rank_score"] = round(
            score_rank * 0.4 +      # 40% weight on risk-adjusted
            pop_rank * 0.3 +         # 30% weight on probability
            roi_rank * 0.2 +         # 20% weight on ROI
            distance_rank * 0.1,     # 10% weight on safety
            2
        )
        
        # Trading decision
        if spread["pop"] >= 70 and spread["roi"] >= 20:
            spread["decision"] = "ENTER"
        elif spread["pop"] >= 60 and spread["roi"] >= 30:
            spread["decision"] = "WATCH"
        else:
            spread["decision"] = "SKIP"
    
    # Sort by composite rank
    spreads.sort(key=lambda x: x["rank_score"], reverse=True)
    
    # Add rank position
    for i, spread in enumerate(spreads):
        spread["rank"] = i + 1
    
    return spreads

def save_ranked_spreads(spreads):
    """Save ranked spreads"""
    # Group by decision
    enter = [s for s in spreads if s["decision"] == "ENTER"]
    watch = [s for s in spreads if s["decision"] == "WATCH"]
    skip = [s for s in spreads if s["decision"] == "SKIP"]
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(spreads),
            "enter": len(enter),
            "watch": len(watch),
            "skip": len(skip)
        },
        "ranked_spreads": spreads,
        "enter_trades": enter[:10],  # Top 10 to enter
        "watch_list": watch[:10]     # Top 10 to watch
    }
    
    with open("data/ranked_spreads.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Ranking Results:")
    print(f"   Total spreads: {len(spreads)}")
    print(f"   🟢 ENTER: {len(enter)}")
    print(f"   🟡 WATCH: {len(watch)}")
    print(f"   🔴 SKIP: {len(skip)}")
    
    # Show top trades
    print(f"\n🎯 Top 5 ENTER Trades:")
    for spread in enter[:5]:
        print(f"   #{spread['rank']}: {spread['ticker']} {spread['type']}")
        print(f"        Strikes: ${spread['short_strike']}/{spread['long_strike']}")
        print(f"        ROI: {spread['roi']}% | PoP: {spread['pop']}% | Score: {spread['rank_score']}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 8: Rank Spreads")
    print("="*60)
    
    # Rank spreads
    ranked_spreads = rank_spreads()
    
    # Save results
    save_ranked_spreads(ranked_spreads)
    
    print("✅ Step 8 complete: ranked_spreads.json created")

if __name__ == "__main__":
    main()
