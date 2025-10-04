"""
Filter by options availability
"""
import json
import sys
import os
from datetime import datetime
from tastytrade import Session
from tastytrade.instruments import get_option_chain

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

def filter_options():
    print("="*60)
    print("STEP 0C: Filter Options")
    print("="*60)
    
    with open("data/filter1_passed.json", "r") as f:
        stocks = json.load(f)
    
    print(f"Input: {len(stocks)} stocks")
    
    sess = Session(USERNAME, PASSWORD)
    passed = []
    failed = []
    
    today = datetime.now().date()
    
    for stock_data in stocks:
        ticker = stock_data['ticker']
        
        try:
            chain = get_option_chain(sess, ticker)
            
            if not chain:
                failed.append({'ticker': ticker, 'reason': 'no chain'})
                continue
            
            good_exps = []
            for exp_date in chain.keys():
                dte = (exp_date - today).days
                if 15 <= dte <= 45:
                    good_exps.append({'date': str(exp_date), 'dte': dte})
            
            if not good_exps:
                failed.append({'ticker': ticker, 'reason': 'no 15-45 DTE'})
                continue
            
            best_exp = datetime.strptime(good_exps[0]['date'], '%Y-%m-%d').date()
            options = chain[best_exp]
            
            if len(options) < 20:
                failed.append({'ticker': ticker, 'reason': f'only {len(options)} strikes'})
                continue
            
            passed.append({
                **stock_data,
                'expirations': len(good_exps),
                'best_expiration': good_exps[0],
                'strikes_count': len(options)
            })
            
        except Exception as e:
            failed.append({'ticker': ticker, 'reason': str(e)[:30]})
    
    return passed, failed

def save_results(passed, failed):
    with open('data/filter2_passed.json', 'w') as f:
        json.dump(passed, f, indent=2)
    
    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: 20+ strikes, 15-45 DTE")

def main():
    passed, failed = filter_options()
    save_results(passed, failed)
    print("Step 0C complete")

if __name__ == "__main__":
    main()
