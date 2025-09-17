"""
Calculate Credit Spreads using Connected Data (chains_with_greeks.json)
Build real spreads with actual Greeks
"""
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def calculate_spreads():
    print("="*60)
    print("STEP 6: Calculate Credit Spreads (Connected)")
    print("="*60)
    
    # Load connected data with Greeks
    with open("data/chains_with_greeks.json", "r") as f:
        data = json.load(f)
    
    chains = data["chains_with_greeks"]
    
    # Load stock prices for reference
    with open("data/stock_prices.json", "r") as f:
        prices = json.load(f)["prices"]
    
    print("\n📊 Building credit spreads from real Greeks...")
    
    all_spreads = []
    
    for ticker, expirations in chains.items():
        if ticker not in prices:
            continue
            
        stock_price = prices[ticker]["mid"]
        
        for exp_data in expirations:
            exp_date = exp_data["expiration_date"]
            dte = exp_data["dte"]
            
            # Skip if too close or too far
            if dte < 7 or dte > 45:
                continue
            
            strikes = exp_data["strikes"]
            
            # Build Bull Put Spreads (sell higher strike put, buy lower strike put)
            for i in range(len(strikes)):
                for j in range(i):
                    short_strike = strikes[i]  # Higher strike (short)
                    long_strike = strikes[j]   # Lower strike (long)
                    
                    # Check if we have put Greeks
                    if "put_greeks" not in short_strike or "put_greeks" not in long_strike:
                        continue
                    
                    # Get Greeks
                    short_iv = short_strike["put_greeks"]["iv"]
                    short_delta = abs(short_strike["put_greeks"]["delta"])
                    
                    # Target 15-30 delta for short strike
                    if short_delta < 0.15 or short_delta > 0.35:
                        continue
                    
                    # Calculate spread metrics
                    short_bid = short_strike["put_bid"]
                    short_ask = short_strike["put_ask"]
                    long_bid = long_strike["put_bid"]
                    long_ask = long_strike["put_ask"]
                    
                    if short_bid <= 0 or long_ask <= 0:
                        continue
                    
                    # Net credit = short bid - long ask
                    net_credit = short_bid - long_ask
                    width = short_strike["strike"] - long_strike["strike"]
                    
                    if net_credit <= 0.10 or width <= 0:
                        continue
                    
                    max_loss = width - net_credit
                    roi = (net_credit / max_loss) * 100
                    
                    # Probability of profit (rough estimate using delta)
                    pop = (1 - short_delta) * 100
                    
                    spread = {
                        "ticker": ticker,
                        "type": "Bull Put",
                        "stock_price": round(stock_price, 2),
                        "short_strike": short_strike["strike"],
                        "long_strike": long_strike["strike"],
                        "width": round(width, 2),
                        "net_credit": round(net_credit, 2),
                        "max_loss": round(max_loss, 2),
                        "roi": round(roi, 1),
                        "short_iv": round(short_iv * 100, 1),  # Convert to percentage
                        "short_delta": round(short_delta, 2),
                        "expiration": {"date": exp_date, "dte": dte},
                        "pop": round(pop, 1)
                    }
                    
                    # Quality filters
                    if roi >= 5 and roi <= 50 and pop >= 60:
                        all_spreads.append(spread)
            
            # Build Bear Call Spreads (sell lower strike call, buy higher strike call)
            for i in range(len(strikes)):
                for j in range(i + 1, len(strikes)):
                    short_strike = strikes[i]  # Lower strike (short)
                    long_strike = strikes[j]   # Higher strike (long)
                    
                    # Check if we have call Greeks
                    if "call_greeks" not in short_strike or "call_greeks" not in long_strike:
                        continue
                    
                    # Get Greeks
                    short_iv = short_strike["call_greeks"]["iv"]
                    short_delta = abs(short_strike["call_greeks"]["delta"])
                    
                    # Target 15-30 delta for short strike
                    if short_delta < 0.15 or short_delta > 0.35:
                        continue
                    
                    # Calculate spread metrics
                    short_bid = short_strike["call_bid"]
                    short_ask = short_strike["call_ask"]
                    long_bid = long_strike["call_bid"]
                    long_ask = long_strike["call_ask"]
                    
                    if short_bid <= 0 or long_ask <= 0:
                        continue
                    
                    # Net credit = short bid - long ask
                    net_credit = short_bid - long_ask
                    width = long_strike["strike"] - short_strike["strike"]
                    
                    if net_credit <= 0.10 or width <= 0:
                        continue
                    
                    max_loss = width - net_credit
                    roi = (net_credit / max_loss) * 100
                    
                    # Probability of profit (rough estimate using delta)
                    pop = (1 - short_delta) * 100
                    
                    spread = {
                        "ticker": ticker,
                        "type": "Bear Call",
                        "stock_price": round(stock_price, 2),
                        "short_strike": short_strike["strike"],
                        "long_strike": long_strike["strike"],
                        "width": round(width, 2),
                        "net_credit": round(net_credit, 2),
                        "max_loss": round(max_loss, 2),
                        "roi": round(roi, 1),
                        "short_iv": round(short_iv * 100, 1),  # Convert to percentage
                        "short_delta": round(short_delta, 2),
                        "expiration": {"date": exp_date, "dte": dte},
                        "pop": round(pop, 1)
                    }
                    
                    # Quality filters
                    if roi >= 5 and roi <= 50 and pop >= 60:
                        all_spreads.append(spread)
    
    # Sort by ROI
    all_spreads.sort(key=lambda x: x["roi"], reverse=True)
    
    # Save spreads
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_spreads": len(all_spreads),
        "spreads": all_spreads
    }
    
    with open("data/spreads.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Built {len(all_spreads)} credit spreads")
    print(f"   Bull Puts: {len([s for s in all_spreads if s['type'] == 'Bull Put'])}")
    print(f"   Bear Calls: {len([s for s in all_spreads if s['type'] == 'Bear Call'])}")
    
    if all_spreads:
        avg_roi = sum(s["roi"] for s in all_spreads) / len(all_spreads)
        avg_iv = sum(s["short_iv"] for s in all_spreads) / len(all_spreads)
        print(f"   Avg ROI: {avg_roi:.1f}%")
        print(f"   Avg IV: {avg_iv:.1f}%")

def main():
    calculate_spreads()

if __name__ == "__main__":
    main()
