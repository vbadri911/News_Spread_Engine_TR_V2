"""
Calculate Spreads: Build credit spreads with ALL collected options
Uses everything we have in greeks.json
"""
import json
import sys
from datetime import datetime

def load_greeks():
    """Load Greeks data"""
    try:
        with open("greeks.json", "r") as f:
            data = json.load(f)
        return data["greeks"]
    except FileNotFoundError:
        print("❌ greeks.json not found")
        sys.exit(1)

def build_credit_spreads():
    """Build credit spreads from ALL options"""
    print("🔨 Building credit spreads from ALL options...")
    
    greeks_data = load_greeks()
    all_spreads = []
    
    for ticker, data in greeks_data.items():
        stock_price = data["stock_price"]
        options = data["greeks"]
        
        # Get ALL calls and puts
        calls = [o for o in options if o["type"] == "C"]
        puts = [o for o in options if o["type"] == "P"]
        
        # Sort by strike
        calls.sort(key=lambda x: x["strike"])
        puts.sort(key=lambda x: x["strike"], reverse=True)
        
        print(f"\n{ticker}: ${stock_price:.2f}")
        print(f"  Total Calls: {len(calls)}, Total Puts: {len(puts)}")
        ticker_spreads = []
        
        # Build BEAR CALL spreads - only use OTM calls
        otm_calls = [c for c in calls if c["strike"] > stock_price]
        for i, short_call in enumerate(otm_calls[:-1]):
            for long_call in otm_calls[i+1:i+5]:  # Check next 4 strikes
                width = long_call["strike"] - short_call["strike"]
                
                if 2.5 <= width <= 10:
                    net_credit = short_call["mid"] - long_call["mid"]
                    
                    if net_credit > 0.15:  # 15 cents minimum
                        max_loss = width - net_credit
                        roi = (net_credit / max_loss * 100) if max_loss > 0 else 0
                        
                        if roi > 5:  # 5% minimum ROI
                            spread = {
                                "ticker": ticker,
                                "type": "Bear Call",
                                "stock_price": stock_price,
                                "short_strike": short_call["strike"],
                                "long_strike": long_call["strike"],
                                "width": round(width, 2),
                                "net_credit": round(net_credit, 2),
                                "max_loss": round(max_loss, 2),
                                "roi": round(roi, 1),
                                "short_iv": short_call["iv"],
                                "short_delta": abs(short_call["delta"]),
                                "expiration": data["expiration"]
                            }
                            ticker_spreads.append(spread)
        
        # Build BULL PUT spreads - only use OTM puts
        otm_puts = [p for p in puts if p["strike"] < stock_price]
        for i, short_put in enumerate(otm_puts[:-1]):
            for long_put in otm_puts[i+1:i+5]:  # Check next 4 strikes
                width = short_put["strike"] - long_put["strike"]
                
                if 2.5 <= width <= 10:
                    net_credit = short_put["mid"] - long_put["mid"]
                    
                    if net_credit > 0.15:  # 15 cents minimum
                        max_loss = width - net_credit
                        roi = (net_credit / max_loss * 100) if max_loss > 0 else 0
                        
                        if roi > 5:  # 5% minimum ROI
                            spread = {
                                "ticker": ticker,
                                "type": "Bull Put",
                                "stock_price": stock_price,
                                "short_strike": short_put["strike"],
                                "long_strike": long_put["strike"],
                                "width": round(width, 2),
                                "net_credit": round(net_credit, 2),
                                "max_loss": round(max_loss, 2),
                                "roi": round(roi, 1),
                                "short_iv": short_put["iv"],
                                "short_delta": abs(short_put["delta"]),
                                "expiration": data["expiration"]
                            }
                            ticker_spreads.append(spread)
        
        print(f"  ✅ Built {len(ticker_spreads)} spreads")
        all_spreads.extend(ticker_spreads)
    
    return all_spreads

def save_spreads(spreads):
    """Save spread data"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_spreads": len(spreads),
        "spreads": spreads
    }
    
    with open("spreads.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Total spreads: {len(spreads)}")
    
    if len(spreads) == 0:
        print("❌ No valid spreads found")
        return
    
    # Show summary
    bear_calls = len([s for s in spreads if s["type"] == "Bear Call"])
    bull_puts = len([s for s in spreads if s["type"] == "Bull Put"])
    print(f"   Bear Calls: {bear_calls}")
    print(f"   Bull Puts: {bull_puts}")
    
    # Show best ROI
    spreads.sort(key=lambda x: x["roi"], reverse=True)
    print(f"\n🏆 Top 5 by ROI:")
    for spread in spreads[:5]:
        print(f"   {spread['ticker']} {spread['type']} ${spread['short_strike']:.0f}/${spread['long_strike']:.0f}: {spread['roi']}% ROI")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 6: Calculate Spreads (ALL OPTIONS)")
    print("="*60)
    
    spreads = build_credit_spreads()
    save_spreads(spreads)
    
    print("✅ Step 6 complete: spreads.json created")

if __name__ == "__main__":
    main()
