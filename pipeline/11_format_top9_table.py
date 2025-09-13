"""
Format Top 9 Trades as a Clean Table with Entry/Exit Details
"""
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_data():
    """Load all necessary data"""
    with open("data/top9_analysis.json", "r") as f:
        gpt_analysis = json.load(f)["analysis"]
    
    with open("data/ranked_spreads.json", "r") as f:
        spreads = json.load(f)["ranked_spreads"]
    
    with open("data/report_table.json", "r") as f:
        report = json.load(f)["report_table"]
    
    return gpt_analysis, spreads, report

def parse_top9_with_details(analysis_text, spreads, report):
    """Extract top 9 trades with full details from all sources"""
    trades = []
    
    # Parse each trade from GPT analysis
    lines = analysis_text.split('\n')
    current_trade = None
    
    for line in lines:
        # Look for trade headers like "#1. MSFT Bull Put $490/$485"
        if line.strip().startswith('#') and '.' in line:
            parts = line.strip().split(' ')
            if len(parts) >= 4:
                rank = parts[0].strip('#.')
                ticker = parts[1]
                trade_type = ' '.join(parts[2:-1])
                strikes = parts[-1]
                
                # Find matching spread in ranked data for DTE
                dte = None
                net_credit = None
                max_loss = None
                for spread in spreads:
                    if (spread['ticker'] == ticker and 
                        spread['type'] == trade_type and
                        strikes in f"${spread['short_strike']:.0f}/${spread['long_strike']:.0f}"):
                        dte = spread['expiration']['dte']
                        net_credit = spread['net_credit']
                        max_loss = spread['max_loss']
                        break
                
                # If not found in spreads, check report table
                if not dte:
                    for entry in report:
                        if entry['ticker'] == ticker and strikes in entry['legs']:
                            dte = entry['dte']
                            net_credit = float(entry['net_credit'].replace('$', ''))
                            max_loss = float(entry['max_loss'].replace('$', ''))
                            break
                
                current_trade = {
                    'rank': rank,
                    'ticker': ticker,
                    'type': trade_type,
                    'strikes': strikes,
                    'dte': dte or 'N/A',
                    'net_credit': net_credit,
                    'max_loss': max_loss
                }
        
        # Look for score line
        elif current_trade and 'Score:' in line and 'ROI:' in line:
            parts = line.strip().split('|')
            for part in parts:
                if 'Score:' in part:
                    current_trade['score'] = part.split(':')[1].strip()
                elif 'ROI:' in part:
                    current_trade['roi'] = part.split(':')[1].strip()
                elif 'PoP:' in part:
                    current_trade['pop'] = part.split(':')[1].strip()
                elif 'Buffer:' in part:
                    current_trade['buffer'] = part.split(':')[1].strip()
            
            trades.append(current_trade)
            current_trade = None
    
    return trades[:9]

def print_detailed_table(trades):
    """Print detailed table with entry/exit plans"""
    # Header
    print("\n" + "="*140)
    print("TOP 9 CREDIT SPREADS - COMPLETE TRADING PLAN")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*140)
    
    # For each trade, show full details
    for i, trade in enumerate(trades, 1):
        print(f"\n{'='*70}")
        print(f"#{i}. {trade['ticker']} {trade['type']} {trade['strikes']}")
        print(f"{'='*70}")
        
        # Metrics
        print(f"📊 METRICS:")
        print(f"   • ROI: {trade.get('roi', 'N/A')}")
        print(f"   • PoP: {trade.get('pop', 'N/A')}")
        print(f"   • DTE: {trade['dte']} days")
        print(f"   • Buffer: {trade.get('buffer', 'N/A')}")
        print(f"   • Score: {trade.get('score', 'N/A')}")
        
        # Entry plan
        credit = trade.get('net_credit', 0)
        print(f"\n📍 ENTRY PLAN:")
        if 'Put' in trade['type']:
            short_strike = trade['strikes'].split('/')[0].replace('$', '')
            long_strike = trade['strikes'].split('/')[1].replace('$', '')
            print(f"   1. SELL to open {short_strike} Put")
            print(f"   2. BUY to open {long_strike} Put")
        else:  # Call spread
            short_strike = trade['strikes'].split('/')[0].replace('$', '')
            long_strike = trade['strikes'].split('/')[1].replace('$', '')
            print(f"   1. SELL to open {short_strike} Call")
            print(f"   2. BUY to open {long_strike} Call")
        
        if credit:
            print(f"   • Target Credit: ${credit:.2f} or better")
            print(f"   • Use LIMIT order at mid-price")
            print(f"   • If not filled in 5 mins, improve price by $0.05")
        
        # Exit plan
        print(f"\n🎯 EXIT PLAN:")
        if credit:
            profit_target = credit * 0.25
            stop_loss = credit * 2
            print(f"   • PROFIT TARGET: Close at ${profit_target:.2f} debit (25% of max profit)")
            print(f"   • STOP LOSS: Close if debit reaches ${stop_loss:.2f} (2x credit)")
        print(f"   • TIME EXIT: Close at 7 DTE if not hit targets")
        print(f"   • ASSIGNMENT: Roll or take assignment if ITM at expiry")
    
    # Portfolio summary
    print(f"\n{'='*140}")
    print("💼 PORTFOLIO MANAGEMENT:")
    print(f"   • Total trades: {len(trades)}")
    if trades[0].get('net_credit'):
        total_credit = sum(t.get('net_credit', 0) for t in trades)
        total_risk = sum(t.get('max_loss', 0) for t in trades) if trades[0].get('max_loss') else total_credit * 4
        print(f"   • Total credit: ${total_credit:.2f}")
        print(f"   • Total risk capital: ${total_risk:.2f}")
    print(f"   • Position sizing: Max 5% of account per trade")
    print(f"   • Enter trades in order shown for best diversification")

def save_detailed_csv(trades):
    """Save detailed CSV"""
    filename = f"top9_detailed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    with open(filename, "w") as f:
        # Header
        f.write("Rank,Ticker,Type,Strikes,DTE,ROI,PoP,Buffer,Score,Credit,Max Loss,")
        f.write("Entry Plan,Profit Target,Stop Loss\n")
        
        # Data
        for i, trade in enumerate(trades, 1):
            credit = trade.get('net_credit', 0)
            max_loss = trade.get('max_loss', 0)
            profit_target = credit * 0.25 if credit else 0
            stop_loss = credit * 2 if credit else 0
            
            entry_plan = f"Sell {trade['strikes'].split('/')[0]} Buy {trade['strikes'].split('/')[1]}"
            
            f.write(f"{i},{trade['ticker']},{trade['type']},{trade['strikes']},")
            f.write(f"{trade['dte']},{trade.get('roi', '')},{trade.get('pop', '')},")
            f.write(f"{trade.get('buffer', '')},{trade.get('score', '')},")
            f.write(f"${credit:.2f},${max_loss:.2f},")
            f.write(f"{entry_plan},${profit_target:.2f},${stop_loss:.2f}\n")
    
    print(f"\n📁 Detailed trades saved to {filename}")

def main():
    print("="*60)
    print("STEP 11: Format Top 9 Trades with Full Details")
    print("="*60)
    
    print("Loading data...")
    gpt_analysis, spreads, report = load_data()
    
    print("Parsing trades with details...")
    trades = parse_top9_with_details(gpt_analysis, spreads, report)
    
    if trades:
        # Print detailed table
        print_detailed_table(trades)
        
        # Save CSV
        save_detailed_csv(trades)
        print("\n✅ Complete trading plan generated!")
    else:
        print("❌ Could not parse trades from GPT analysis")

if __name__ == "__main__":
    main()
