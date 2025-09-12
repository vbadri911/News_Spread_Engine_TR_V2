import json
from datetime import datetime

# Load your realistic trades
with open('ranked_spreads.json', 'r') as f:
    data = json.load(f)

# Filter for realistic only
trades = []
for s in data['enter_trades']:
    if 10 <= s['roi'] <= 80 and s['pop'] >= 50:
        trades.append(s)

print("="*80)
print("FINAL CREDIT SPREAD RECOMMENDATIONS")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*80)

print(f"\nFound {len(trades)} HIGH-QUALITY TRADES\n")

# Group by ticker
by_ticker = {}
for t in trades:
    ticker = t['ticker']
    if ticker not in by_ticker:
        by_ticker[ticker] = []
    by_ticker[ticker].append(t)

# Display by ticker
for ticker, ticker_trades in by_ticker.items():
    print(f"\n{ticker} - {len(ticker_trades)} trades")
    print("-"*40)
    
    for t in ticker_trades[:3]:  # Top 3 per ticker
        print(f"{t['type']} Spread: ${t['short_strike']:.0f}/${t['long_strike']:.0f}")
        print(f"  Credit: ${t['net_credit']:.2f} | Max Loss: ${t['max_loss']:.2f}")
        print(f"  ROI: {t['roi']:.1f}% | PoP: {t['pop']:.1f}%")
        print(f"  Entry: Sell ${t['short_strike']:.0f} {t['type'].split()[0]}, Buy ${t['long_strike']:.0f} {t['type'].split()[0]}")
        print()

print("\n" + "="*80)
print("TRADING NOTES:")
print("- All trades expire in ~15-45 days")
print("- Enter at mid-price or better")
print("- Set stop loss at 2x credit received")
print("- Take profit at 25-50% of max profit")
print("="*80)
