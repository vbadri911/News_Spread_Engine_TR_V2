"""
Show Top 9 Trades
"""
import json
import os

def show_top9():
    try:
        with open("data/ranked_spreads.json", "r") as f:
            data = json.load(f)
        
        enters = data.get("enter_trades", [])[:9]
        
        print("\n" + "="*80)
        print("TOP 9 CREDIT SPREADS - READY TO TRADE")
        print("="*80)
        
        for i, trade in enumerate(enters, 1):
            print(f"\n{i}. {trade['ticker']} - {trade['type']}")
            print(f"   Strikes: ${trade['short_strike']}/{trade['long_strike']}")
            print(f"   Net Credit: ${trade['net_credit']:.2f}")
            print(f"   Max Loss: ${trade['max_loss']:.2f}")
            print(f"   ROI: {trade['roi']:.1f}%")
            print(f"   PoP: {trade['pop']:.1f}%")
            print(f"   Expiration: {trade['expiration']}")
            print(f"   Short IV: {trade['short_iv']:.1f}%")
            print(f"   Short Delta: {trade['short_delta']:.2f}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_top9()
