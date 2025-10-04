"""
Select final 22 stocks
"""
import json
from datetime import datetime

def select_top_22():
    print("="*60)
    print("STEP 0E: Select 22 Stocks")
    print("="*60)
    
    with open("data/filter3_passed.json", "r") as f:
        stocks = json.load(f)
    
    print(f"Input: {len(stocks)} stocks")
    
    # Score each stock - no fallbacks
    for stock in stocks:
        score = 0
        
        # IV score
        iv_pct = stock['iv_pct']
        if iv_pct >= 40:
            score += 40
        elif iv_pct >= 30:
            score += 30
        elif iv_pct >= 25:
            score += 20
        else:
            score += 10
        
        # Strikes score
        strikes = stock['strikes_count']
        if strikes >= 100:
            score += 30
        elif strikes >= 60:
            score += 20
        else:
            score += 10
        
        # Expirations score
        expirations = stock['expirations']
        if expirations >= 4:
            score += 20
        elif expirations >= 2:
            score += 10
        
        # Spread score
        spread_pct = stock['spread_pct']
        if spread_pct < 0.05:
            score += 10
        elif spread_pct < 0.1:
            score += 5
        
        stock['score'] = score
    
    stocks.sort(key=lambda x: x['score'], reverse=True)
    selected = stocks[:22]
    
    # Save to stocks.py
    tickers = [s['ticker'] for s in selected]
    
    with open("data/stocks.py", "w") as f:
        f.write(f"# Generated {datetime.now()}\n")
        f.write(f"STOCKS = {tickers}\n")
    
    return selected

def save_results(selected):
    with open('data/filter4_passed.json', 'w') as f:
        json.dump(selected, f, indent=2)
    
    print(f"\nSelected {len(selected)} stocks")
    print(f"\nTop 5:")
    for i, s in enumerate(selected[:5], 1):
        print(f"  {i}. {s['ticker']}: IV={s['iv_pct']:.1f}%, Score={s['score']}")

def main():
    selected = select_top_22()
    save_results(selected)
    print("\nStep 0E complete")

if __name__ == "__main__":
    main()
