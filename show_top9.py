"""
Display the top 9 trades from the analysis
"""
import json

# Load the GPT analysis
with open("top9_analysis.json", "r") as f:
    data = json.load(f)

print("="*80)
print("GPT'S TOP 9 TRADES ANALYSIS")
print("="*80)

# Print the full analysis
analysis = data["analysis"]
print(analysis)

print("\n" + "="*80)
print("EXTRACTED TOP TRADES")
print("="*80)

# Also show the actual trades we have
with open("final_trades.json", "r") as f:
    trades = json.load(f)["final_trades"]

# Show trades marked as YES
yes_trades = [t for t in trades if t.get("entry_decision") == "YES"]

print(f"\nTrades marked YES: {len(yes_trades)}")
for i, trade in enumerate(yes_trades[:9], 1):
    roi = trade['roi']
    pop = trade['pop']
    print(f"\n{i}. {trade['ticker']} {trade['type']} {trade['legs']}")
    print(f"   ROI: {roi} | PoP: {pop}")
    print(f"   Credit: {trade['net_credit']} | Max Loss: {trade['max_loss']}")
    print(f"   Reason: {trade.get('why', 'Meets criteria')}")
