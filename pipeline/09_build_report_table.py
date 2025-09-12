"""
Build Report Table: Create structured table for GPT analysis
Formats all data for final validation
"""
import json
import sys
from datetime import datetime

def load_ranked_spreads():
    """Load ranked spreads"""
    try:
        with open("data/ranked_spreads.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ ranked_spreads.json not found - run rank_spreads.py first")
        sys.exit(1)

def load_edge_reasons():
    """Load original edge reasons from GPT"""
    try:
        from data.stocks import EDGE_REASON
        return EDGE_REASON
    except ImportError:
        return {}

def build_report_table():
    """Build final report table"""
    print("📋 Building report table...")
    
    data = load_ranked_spreads()
    edge_reasons = load_edge_reasons()
    
    # Get top trades from each category
    enter_trades = data["enter_trades"][:11]  # Get 11 (1 per sector ideally)
    watch_trades = data["watch_list"][:11]
    
    # Build report entries
    report_entries = []
    
    # Map sectors (simplified SPDR mapping)
    sector_map = {
        "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "GOOGL": "XLK",
        "JPM": "XLF", "BAC": "XLF", "V": "XLF", "MA": "XLF",
        "JNJ": "XLV", "UNH": "XLV", "CVS": "XLV", "PFE": "XLV",
        "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "DIS": "XLY",
        "PG": "XLP", "KO": "XLP", "WMT": "XLP", "COST": "XLP",
        "XOM": "XLE", "CVX": "XLE", "COP": "XLE",
        "BA": "XLI", "CAT": "XLI", "HON": "XLI", "UNP": "XLI"
    }
    
    # Process ENTER trades first
    for spread in enter_trades:
        ticker = spread["ticker"]
        sector = sector_map.get(ticker, "Unknown")
        
        entry = {
            "rank": spread["rank"],
            "sector": sector,
            "ticker": ticker,
            "type": spread["type"],
            "legs": f"${spread['short_strike']:.0f}/${spread['long_strike']:.0f}",
            "exp_date": spread["expiration"]["date"],
            "dte": spread["expiration"]["dte"],
            "roi": f"{spread['roi']}%",
            "pop": f"{spread['pop']}%",
            "net_credit": f"${spread['net_credit']:.2f}",
            "max_loss": f"${spread['max_loss']:.2f}",
            "decision": spread["decision"],
            "edge_reason": edge_reasons.get(ticker, ""),
            "iv": spread["short_iv"],
            "delta": spread["short_delta"],
            "score": spread["rank_score"]
        }
        report_entries.append(entry)
    
    # Add some WATCH trades
    for spread in watch_trades[:5]:
        ticker = spread["ticker"]
        sector = sector_map.get(ticker, "Unknown")
        
        entry = {
            "rank": spread["rank"],
            "sector": sector,
            "ticker": ticker,
            "type": spread["type"],
            "legs": f"${spread['short_strike']:.0f}/${spread['long_strike']:.0f}",
            "exp_date": spread["expiration"]["date"],
            "dte": spread["expiration"]["dte"],
            "roi": f"{spread['roi']}%",
            "pop": f"{spread['pop']}%",
            "net_credit": f"${spread['net_credit']:.2f}",
            "max_loss": f"${spread['max_loss']:.2f}",
            "decision": spread["decision"],
            "edge_reason": edge_reasons.get(ticker, ""),
            "iv": spread["short_iv"],
            "delta": spread["short_delta"],
            "score": spread["rank_score"]
        }
        report_entries.append(entry)
    
    return report_entries

def save_report_table(entries):
    """Save report table"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_entries": len(entries),
        "report_table": entries
    }
    
    with open("data/report_table.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Report Table:")
    print(f"   Total entries: {len(entries)}")
    
    # Show preview
    print(f"\n📋 Preview (first 5):")
    print(f"{'Rank':<5} {'Ticker':<6} {'Type':<10} {'Legs':<12} {'ROI':<8} {'PoP':<8} {'Decision'}")
    print("-" * 60)
    
    for entry in entries[:5]:
        print(f"{entry['rank']:<5} {entry['ticker']:<6} {entry['type']:<10} {entry['legs']:<12} {entry['roi']:<8} {entry['pop']:<8} {entry['decision']}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 9: Build Report Table")
    print("="*60)
    
    # Build table
    entries = build_report_table()
    
    # Save results
    save_report_table(entries)
    
    print("✅ Step 9 complete: report_table.json created")

if __name__ == "__main__":
    main()
