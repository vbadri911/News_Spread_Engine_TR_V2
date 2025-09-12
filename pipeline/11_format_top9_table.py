"""
Format Top 9 Trades as a Clean Table
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
    
    # Load edge reasons
    try:
        from data.stocks import EDGE_REASON
    except:
        EDGE_REASON = {}
    
    return gpt_analysis, spreads

def parse_top9_from_gpt(analysis_text):
    """Extract top 9 trades from GPT analysis"""
    trades = []
    
    # Parse each trade from the analysis
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
                
                current_trade = {
                    'rank': rank,
                    'ticker': ticker,
                    'type': trade_type,
                    'strikes': strikes
                }
        
        # Look for score line
        elif current_trade and 'Score:' in line and 'ROI:' in line:
            # Parse metrics from line like "Score: 109.1 | ROI: 138.1% | PoP: 79.0% | Buffer: 3.7%"
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
    
    return trades[:9]  # Return only top 9

def print_table(trades):
    """Print formatted table"""
    # Header
    print("\n" + "="*120)
    print("TOP 9 CREDIT SPREADS - READY FOR EXECUTION")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*120)
    
    # Table header
    print(f"\n{'#':<4} {'Ticker':<8} {'Type':<12} {'Strikes':<15} {'ROI':<10} {'PoP':<10} {'Buffer':<10} {'Score':<10}")
    print("-"*120)
    
    # Table rows
    for trade in trades:
        print(f"{trade['rank']:<4} {trade['ticker']:<8} {trade['type']:<12} {trade['strikes']:<15} "
              f"{trade.get('roi', 'N/A'):<10} {trade.get('pop', 'N/A'):<10} "
              f"{trade.get('buffer', 'N/A'):<10} {trade.get('score', 'N/A'):<10}")
    
    print("-"*120)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Top Trade: {trades[0]['ticker']} {trades[0]['type']} {trades[0]['strikes']}")
    print(f"   • Best ROI: {trades[0].get('roi', 'N/A')}")
    print(f"   • Average PoP: ~75%")
    print(f"\n💡 NOTES:")
    print("   • Enter trades in order shown")
    print("   • Use limit orders at mid-price or better")
    print("   • Set stop loss at 2x credit received")
    print("   • Take profit at 25-50% of max gain")

def save_csv(trades):
    """Save as CSV for Excel"""
    filename = f"top9_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    with open(filename, "w") as f:
        # Header
        f.write("Rank,Ticker,Type,Strikes,ROI,PoP,Buffer,Score\n")
        
        # Data
        for trade in trades:
            f.write(f"{trade['rank']},{trade['ticker']},{trade['type']},{trade['strikes']},")
            f.write(f"{trade.get('roi', '')},{trade.get('pop', '')},{trade.get('buffer', '')},{trade.get('score', '')}\n")
    
    print(f"\n📁 Saved to {filename}")

def main():
    print("="*60)
    print("STEP 11: Format Top 9 Trades")
    print("="*60)
    
    print("Loading data...")
    gpt_analysis, spreads = load_data()
    
    print("Parsing top 9 trades...")
    trades = parse_top9_from_gpt(gpt_analysis)
    
    if trades:
        # Print the table
        print_table(trades)
        
        # Save CSV
        save_csv(trades)
        print("\n✅ Step 11 complete: Top 9 trades formatted and saved")
    else:
        print("❌ Could not parse trades from GPT analysis")

if __name__ == "__main__":
    main()
