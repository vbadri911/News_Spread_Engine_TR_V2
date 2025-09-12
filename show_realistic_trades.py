import json

with open('ranked_spreads.json', 'r') as f:
    data = json.load(f)

# Filter for realistic trades only
realistic = []
for s in data['enter_trades']:
    # Real credit spreads have 10-80% ROI typically
    if 10 <= s['roi'] <= 80 and s['pop'] >= 50:
        realistic.append(s)

print(f"REALISTIC TRADES (10-80% ROI, >50% PoP):")
print(f"Found {len(realistic)} out of {len(data['enter_trades'])} ENTER trades\n")

for i, s in enumerate(realistic[:20], 1):
    print(f"{i}. {s['ticker']} {s['type']} ${s['short_strike']:.0f}/${s['long_strike']:.0f}")
    print(f"   ROI: {s['roi']}% | PoP: {s['pop']}% | Credit: ${s['net_credit']}")
    print()
