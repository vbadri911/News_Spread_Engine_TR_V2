"""
Format Top 9 Trades with News Summary
"""
import json
import re
from datetime import datetime

def load_data():
    with open("data/top9_analysis.json", "r") as f:
        return json.load(f)

def parse_trades(analysis_text):
    trades = []
    trade_blocks = re.split(r'#\d+\.', analysis_text)[1:]
    
    for i, block in enumerate(trade_blocks, 1):
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        header = lines[0].strip()
        parts = header.split()
        
        if len(parts) < 3:
            continue
            
        ticker = parts[0]
        trade_type = ' '.join(parts[1:-1])
        strikes = parts[-1]
        
        metrics_line = next((l for l in lines if 'DTE:' in l), '')
        
        dte = roi = pop = heat = "N/A"
        if metrics_line:
            if 'DTE:' in metrics_line:
                dte = re.search(r'DTE:\s*(\d+)', metrics_line)
                dte = dte.group(1) if dte else "N/A"
            if 'ROI:' in metrics_line:
                roi = re.search(r'ROI:\s*([\d.]+%)', metrics_line)
                roi = roi.group(1) if roi else "N/A"
            if 'PoP:' in metrics_line:
                pop = re.search(r'PoP:\s*([\d.]+%)', metrics_line)
                pop = pop.group(1) if pop else "N/A"
            if 'HEAT:' in metrics_line:
                heat = re.search(r'HEAT:\s*(\d+)', metrics_line)
                heat = heat.group(1) if heat else "N/A"
        
        # Extract catalyst risk summary
        catalyst = "No catalysts"
        catalyst_idx = next((idx for idx, l in enumerate(lines) if 'CATALYST RISK:' in l), None)
        if catalyst_idx and catalyst_idx + 1 < len(lines):
            catalyst = lines[catalyst_idx + 1].strip()
            # Truncate to 33 words
            words = catalyst.split()
            if len(words) > 33:
                catalyst = ' '.join(words[:33]) + "..."
        
        rec_line = next((l for l in lines if 'RECOMMENDATION:' in l), '')
        recommendation = "Pending"
        if rec_line:
            rec_idx = lines.index(rec_line)
            if rec_idx + 1 < len(lines):
                recommendation = lines[rec_idx + 1].strip()
        
        trades.append({
            'rank': i,
            'ticker': ticker,
            'type': trade_type,
            'strikes': strikes,
            'dte': dte,
            'roi': roi,
            'pop': pop,
            'heat': heat,
            'catalyst': catalyst,
            'recommendation': recommendation
        })
    
    return trades

def print_table(trades):
    print("\n" + "="*140)
    print("TOP 9 CREDIT SPREADS - WITH NEWS CATALYSTS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*140)
    
    print(f"\n{'#':<4} {'Ticker':<8} {'Type':<12} {'Strikes':<12} {'DTE':<5} {'ROI':<8} {'PoP':<8} {'Heat':<5} {'Catalyst Summary':<50}")
    print("-"*140)
    
    for trade in trades:
        catalyst_short = trade['catalyst'][:47] + "..." if len(trade['catalyst']) > 50 else trade['catalyst']
        print(f"{trade['rank']:<4} {trade['ticker']:<8} {trade['type']:<12} {trade['strikes']:<12} "
              f"{trade['dte']:<5} {trade['roi']:<8} {trade['pop']:<8} {trade['heat']:<5} {catalyst_short:<50}")
    
    print("-"*140)
    
    trade_count = len([t for t in trades if 'Trade' in t['recommendation'] and 'Wait' not in t['recommendation']])
    wait_count = len([t for t in trades if 'Wait' in t['recommendation']])
    
    print(f"\nSUMMARY: {len(trades)} analyzed | {trade_count} Trade Now | {wait_count} Wait")
    
    print(f"\nDETAILED RECOMMENDATIONS:")
    for t in trades:
        print(f"#{t['rank']} {t['ticker']}: {t['recommendation']}")

def save_csv(trades):
    filename = f"data/top9_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    with open(filename, "w") as f:
        f.write("Rank,Ticker,Type,Strikes,DTE,ROI,PoP,Heat,Catalyst,Recommendation\n")
        for t in trades:
            catalyst = t['catalyst'].replace(',', ';')
            rec = t['recommendation'].replace(',', ';')
            f.write(f"{t['rank']},{t['ticker']},{t['type']},{t['strikes']},{t['dte']},{t['roi']},{t['pop']},{t['heat']},\"{catalyst}\",\"{rec}\"\n")
    
    print(f"\nSaved to {filename}")

def main():
    print("="*60)
    print("STEP 9: Format Top 9 with News")
    print("="*60)
    
    data = load_data()
    trades = parse_trades(data['analysis'])
    
    if trades:
        print_table(trades)
        save_csv(trades)
        print("\nStep 9 complete")
    else:
        print("Could not parse trades")

if __name__ == "__main__":
    main()
