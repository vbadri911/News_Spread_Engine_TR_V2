import json

# Check Greeks data
with open('/Users/badriv/PycharmProjects/News_Spread_Engine_Tradier/data/greeks.json', 'r') as f:
    data = json.load(f)

print("=== GREEKS DATA ===")
for ticker in ['AAPL', 'TSLA', 'META', 'AMZN']:
    if ticker in data['greeks']:
        info = data['greeks'][ticker]
        print(f'\n{ticker}: Stock=${info["stock_price"]:.2f}')
        strikes = [g['strike'] for g in info['greeks']]
        if strikes:
            print(f'  Strike range: ${min(strikes):.0f} - ${max(strikes):.0f}')
            print(f'  Number of options: {len(strikes)}')
            # Show first few strikes
            unique_strikes = sorted(set(strikes))[:10]
            print(f'  First strikes: {unique_strikes}')

# Check chains data
print("\n=== CHAINS DATA ===")
with open('/Users/badriv/PycharmProjects/News_Spread_Engine_Tradier/data/chains.json', 'r') as f:
    chains = json.load(f)

for ticker in ['AAPL', 'TSLA']:
    if ticker in chains['chains']:
        info = chains['chains'][ticker]
        print(f'{ticker}: Exp={info["best_expiration"]["date"]} ({info["best_expiration"]["dte"]} DTE)')
        print(f'  Total strikes available: {info["strikes_count"]}')
