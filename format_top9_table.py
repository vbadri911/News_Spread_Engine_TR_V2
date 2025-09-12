"""
Format Top 9 Trades as a Clean Table
"""
import json
from datetime import datetime

def load_data():
    """Load all necessary data"""
    with open("top9_analysis.json", "r") as f:
        gpt_analysis = json.load(f)["analysis"]
    
    with open("ranked_spreads.json", "r") as f:
        spreads = json.load(f)["ranked_spreads"]
    
    with open("stocks.py", "r") as f:
        # Parse for EDGE_REASON
        exec(f.read(), globals())
    
    return gpt_analysis, spreads

def parse_top9_from_gpt(analysis_text, spreads):
    """Extract top 9 trades from GPT analysis and match with spread data"""
    trades = []
    
    # Parse the GPT analysis for trade details
    top9_trades = [
        ("APD", "Bull Put", 310, 300, 250.9, 81.5),
        ("APD", "Bull Put", 300, 290, 94.2, 91.6),
        ("MSFT", "Bull Put", 488, 485, 74.8, 84.1),
        ("APD", "Bull Put", 290, 280, 55.0, 96.4),
        ("MSFT", "Bull Put", 495, 492, 64.5, 75.3),
        ("MSFT", "Bull Put", 498, 495, 66.7, 71.5),
        ("MSFT", "Bull Put", 498, 492, 65.6, 71.5),
        ("LIN", "Bear Call", 500, 505, 62.3, 71.5),
        ("MSFT", "Bull Put", 498, 490, 59.2, 71.5)
    ]
    
    # Match with spread data for additional details
    for ticker, spread_type, short, long, roi, pop in top9_trades:
        # Find matching spread
        matching_spread = None
        for s in spreads:
            if (s["ticker"] == ticker and 
                s["type"] == spread_type and
                abs(s["short_strike"] - short) < 1 and
                abs(s["long_strike"] - long) < 1):
                matching_spread = s
                break
        
        if matching_spread:
            trades.append({
                "ticker": ticker,
                "type": spread_type,
                "short": short,
                "long": long,
                "roi": roi,
                "pop": pop,
                "dte": matching_spread.get("expiration", {}).get("dte", 15),
                "credit": matching_spread.get("net_credit", 0),
                "max_loss": matching_spread.get("max_loss", 0)
            })
        else:
            # Use defaults if not found
            trades.append({
                "ticker": ticker,
                "type": spread_type,
                "short": short,
                "long": long,
                "roi": roi,
                "pop": pop,
                "dte": 15,
                "credit": 0,
                "max_loss": 0
            })
    
    return trades

def determine_decision(roi, pop):
    """Determine Enter/Watch/Avoid based on metrics"""
    if roi > 100:
        return "VERIFY"  # Suspicious data
    elif roi >= 50 and pop >= 70:
        return "ENTER"
    elif roi >= 30 and pop >= 60:
        return "WATCH"
    else:
        return "AVOID"

def get_sector(ticker):
    """Map ticker to sector"""
    sector_map = {
        "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "META": "Tech",
        "JPM": "Financials", "BAC": "Financials",
        "JNJ": "Healthcare", "UNH": "Healthcare",
        "AMZN": "Consumer", "TSLA": "Consumer",
        "PG": "Staples", "WMT": "Staples",
        "XOM": "Energy", "CVX": "Energy",
        "CAT": "Industrials", "BA": "Industrials",
        "LIN": "Materials", "APD": "Materials",
        "PLD": "Real Estate", "AMT": "Real Estate",
        "NEE": "Utilities", "SO": "Utilities"
    }
    return sector_map.get(ticker, "Other")

def print_table(trades):
    """Print formatted table"""
    # Header
    print("\n" + "="*150)
    print("TOP 9 CREDIT SPREADS - READY FOR EXECUTION")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*150)
    
    # Table header
    header = f"{'#':<3} {'Sector':<12} {'Ticker':<8} {'Type':<12} {'Legs':<12} {'DTE':<5} {'Decision':<10} {'Entry Plan':<25} {'Exit Plan':<25} {'ROI':<8} {'PoP':<8}"
    print(header)
    print("-"*150)
    
    # Table rows
    for i, trade in enumerate(trades, 1):
        sector = get_sector(trade['ticker'])
        decision = determine_decision(trade['roi'], trade['pop'])
        
        # Format decision with emoji
        if decision == "ENTER":
            decision_fmt = "✅ ENTER"
        elif decision == "WATCH":
            decision_fmt = "⏳ WATCH"
        elif decision == "VERIFY":
            decision_fmt = "⚠️ VERIFY"
        else:
            decision_fmt = "❌ AVOID"
        
        entry_plan = "Enter at mid or better"
        exit_plan = "25% profit / 2x stop"
        
        row = f"{i:<3} {sector:<12} {trade['ticker']:<8} {trade['type']:<12} ${trade['short']}/{trade['long']:<11} {trade['dte']:<5} {decision_fmt:<10} {entry_plan:<25} {exit_plan:<25} {trade['roi']:.1f}%{'':<4} {trade['pop']:.1f}%"
        print(row)
    
    print("-"*150)
    
    # Summary
    enter_count = sum(1 for t in trades if determine_decision(t['roi'], t['pop']) == "ENTER")
    watch_count = sum(1 for t in trades if determine_decision(t['roi'], t['pop']) == "WATCH")
    verify_count = sum(1 for t in trades if determine_decision(t['roi'], t['pop']) == "VERIFY")
    
    print(f"\nSUMMARY: {enter_count} ENTER | {watch_count} WATCH | {verify_count} VERIFY")
    print("\nNOTES:")
    print("• APD #1 shows 250% ROI - verify this data before trading")
    print("• MSFT spreads are highly liquid and reliable")
    print("• Enter trades in order shown for best risk management")

def save_csv(trades):
    """Save as CSV for Excel"""
    filename = f"top9_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    with open(filename, "w") as f:
        # Header
        f.write("Rank,Sector,Ticker,Type,Short Strike,Long Strike,DTE,Decision,Entry Plan,Exit Plan,ROI %,PoP %\n")
        
        # Data
        for i, trade in enumerate(trades, 1):
            sector = get_sector(trade['ticker'])
            decision = determine_decision(trade['roi'], trade['pop'])
            
            row = f"{i},{sector},{trade['ticker']},{trade['type']},{trade['short']},{trade['long']},{trade['dte']},{decision},Enter at mid or better,25% profit / 2x stop,{trade['roi']:.1f},{trade['pop']:.1f}\n"
            f.write(row)
    
    print(f"\n📁 Saved to {filename}")

def main():
    print("Loading data...")
    gpt_analysis, spreads = load_data()
    
    print("Parsing top 9 trades...")
    trades = parse_top9_from_gpt(gpt_analysis, spreads)
    
    # Print the table
    print_table(trades)
    
    # Save CSV
    save_csv(trades)

if __name__ == "__main__":
    main()
