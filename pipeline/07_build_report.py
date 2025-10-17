
"""
Build Report Table: Top 9 spreads for GPT analysis
"""
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def build_report_table():
    print("="*60)
    print("STEP 7: Build Report (Top 9)")
    print("="*60)
    
    with open("data/ranked_spreads.json", "r") as f:
        data = json.load(f)
    
    spreads = data["ranked_spreads"][:9]
    
    try:
        from data.stocks import EDGE_REASON
    except ImportError:
        EDGE_REASON = {}
    
    sector_map = {
        "INTC": "XLK", "AMD": "XLK", "AVGO": "XLK", "CEG": "XLU", "NVDA": "XLK",
        "ORCL": "XLK", "PLTR": "XLK", "SMCI": "XLK", "GOOGL": "XLC", "AMZN": "XLY",
        "APO": "XLF", "XYZ": "XLK", "DAL": "XLI", "ETN": "XLI", "FCX": "XLB",
        "IBM": "XLK", "LULU": "XLY", "MS": "XLF", "TTD": "XLC", "UNH": "XLV",
        "TGT": "XLY", "ABT": "XLV"
    }
    
    report_entries = []
    
    for spread in spreads:
        ticker = spread["ticker"]
        
        # Handle strike formatting correctly (preserve .5 if present)
        short_strike = spread["short_strike"]
        long_strike = spread["long_strike"]
        short_str = f"{short_strike:.1f}" if short_strike % 1 != 0 else f"{int(short_strike)}"
        long_str = f"{long_strike:.1f}" if long_strike % 1 != 0 else f"{int(long_strike)}"
        legs = f"${short_str}/${long_str}"
        
        entry = {
            "rank": spread["rank"],
            "sector": sector_map.get(ticker, "Unknown"),
            "ticker": ticker,
            "type": spread["type"],
            "legs": legs,
            "exp_date": spread["expiration"]["date"],
            "dte": spread["expiration"]["dte"],
            "roi": f"{spread['roi']}%",
            "pop": f"{spread['pop']}%",
            "net_credit": f"${spread['net_credit']:.2f}",
            "max_loss": f"${spread['max_loss']:.2f}",
            "decision": spread["decision"],
            "edge_reason": EDGE_REASON.get(ticker, ""),
            "iv": spread["short_iv"],
            "delta": spread["short_delta"],
            "score": spread["score"]
        }
        report_entries.append(entry)
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_entries": len(report_entries),
        "report_table": report_entries
    }
    
    with open("data/report_table.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nReport: {len(report_entries)} trades")
    print(f"\n{'Rank':<5} {'Ticker':<8} {'Type':<12} {'ROI':<8} {'PoP':<8}")
    print("-" * 45)
    
    for entry in report_entries:
        print(f"{entry['rank']:<5} {entry['ticker']:<8} {entry['type']:<12} {entry['roi']:<8} {entry['pop']:<8}")
    
    print("\n✅ Step 7 complete: report_table.json")

if __name__ == "__main__":
    build_report_table()
