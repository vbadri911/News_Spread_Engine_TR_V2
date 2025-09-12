"""
Display Results: Show final trade table in clean format
The final output with all data and validation
"""
import json
import sys
from datetime import datetime

def load_final_trades():
    """Load final validated trades"""
    try:
        with open("final_trades.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ final_trades.json not found - run call_gpt_2.py first")
        sys.exit(1)

def display_table():
    """Display clean formatted table"""
    data = load_final_trades()
    trades = data["final_trades"]
    
    print("\n" + "="*120)
    print("FINAL CREDIT SPREAD TRADE TABLE")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*120)
    
    # Summary
    print(f"\nSUMMARY: {data['summary']['yes']} YES | {data['summary']['wait']} WAIT | {data['summary']['no']} NO")
    print("-"*120)
    
    # Table header
    print(f"\n{'SECTOR':<6} {'TICKER':<6} {'TYPE':<10} {'LEGS':<12} {'DTE':<4} {'ROI':<6} {'POP':<6} {'DECISION':<8} {'NEWS/EVENTS':<40}")
    print("-"*120)
    
    # Sort by decision (YES first, then WAIT, then NO)
    trades.sort(key=lambda x: (
        0 if x["entry_decision"] == "YES" else 
        1 if x["entry_decision"] == "WAIT" else 2
    ))
    
    for trade in trades:
        # Truncate news for display
        news = trade["news_events"][:37] + "..." if len(trade["news_events"]) > 40 else trade["news_events"]
        
        print(f"{trade['sector']:<6} {trade['ticker']:<6} {trade['type']:<10} {trade['legs']:<12} {trade['dte']:<4} {trade['roi']:<6} {trade['pop']:<6} {trade['entry_decision']:<8} {news:<40}")
    
    print("-"*120)
    
    # Detailed YES trades
    yes_trades = [t for t in trades if t["entry_decision"] == "YES"]
    if yes_trades:
        print("\n" + "="*120)
        print("TRADES TO ENTER NOW")
        print("="*120)
        
        for i, trade in enumerate(yes_trades, 1):
            print(f"\n{i}. {trade['ticker']} - {trade['type']} SPREAD")
            print(f"   Strikes: {trade['legs']} | Credit: {trade['net_credit']} | Max Loss: {trade['max_loss']}")
            print(f"   ROI: {trade['roi']} | PoP: {trade['pop']} | DTE: {trade['dte']}")
            print(f"   Edge: {trade['edge_reason']}")
            print(f"   News: {trade['news_events']}")
            print(f"   Why Enter: {trade['why']}")
            print(f"   Entry Plan: {trade['entry_plan']}")
            print(f"   Exit Plan: {trade['exit_plan']}")

def save_csv():
    """Save as CSV for Excel"""
    data = load_final_trades()
    trades = data["final_trades"]
    
    filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, "w") as f:
        # Header
        f.write("SECTOR,TICKER,TYPE,LEGS,EXP_DATE,DTE,ROI,POP,DECISION,NEWS_EVENTS,WHY,ENTRY_PLAN,EXIT_PLAN\n")
        
        # Data
        for trade in trades:
            row = [
                trade["sector"],
                trade["ticker"],
                trade["type"],
                trade["legs"],
                trade["exp_date"],
                str(trade["dte"]),
                trade["roi"],
                trade["pop"],
                trade["entry_decision"],
                trade["news_events"].replace(",", ";"),
                trade["why"].replace(",", ";"),
                trade["entry_plan"].replace(",", ";"),
                trade["exit_plan"].replace(",", ";")
            ]
            f.write(",".join(row) + "\n")
    
    print(f"\n📁 Saved to {filename}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 11: Display Final Results")
    print("="*60)
    
    # Display table
    display_table()
    
    # Save CSV
    save_csv()
    
    print("\n✅ Complete! Trade the YES signals!")

if __name__ == "__main__":
    main()
