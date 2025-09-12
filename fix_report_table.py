"""
Fix report table to include ALL good trades
"""
import json
from datetime import datetime

# Load ranked spreads
with open("ranked_spreads.json", "r") as f:
    data = json.load(f)

# Get ALL enter trades (not just 11)
enter_trades = data["enter_trades"]
watch_trades = data["watch_list"]

print(f"Found {len(enter_trades)} ENTER trades")
print(f"Found {len(watch_trades)} WATCH trades")

# Build report with ALL enter trades
report_entries = []

for spread in enter_trades:
    entry = {
        "rank": spread["rank"],
        "sector": "Unknown",  # Would need sector mapping
        "ticker": spread["ticker"],
        "type": spread["type"],
        "legs": f"${spread['short_strike']:.0f}/${spread['long_strike']:.0f}",
        "exp_date": spread["expiration"]["date"],
        "dte": spread["expiration"]["dte"],
        "roi": f"{spread['roi']}%",
        "pop": f"{spread['pop']}%",
        "net_credit": f"${spread['net_credit']:.2f}",
        "max_loss": f"${spread['max_loss']:.2f}",
        "decision": spread["decision"],
        "edge_reason": "Market analysis pending",
        "iv": spread["short_iv"],
        "delta": spread["short_delta"],
        "score": spread["rank_score"]
    }
    report_entries.append(entry)

# Save expanded report
output = {
    "timestamp": datetime.now().isoformat(),
    "total_entries": len(report_entries),
    "report_table": report_entries
}

with open("report_table_full.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Created report with {len(report_entries)} trades")
print("\nTop 10 trades:")
for i, e in enumerate(report_entries[:10], 1):
    print(f"  {i}. {e['ticker']} {e['type']} {e['legs']}: ROI={e['roi']} PoP={e['pop']}")
