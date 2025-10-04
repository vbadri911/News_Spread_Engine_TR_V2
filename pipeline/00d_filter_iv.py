"""
Filter by IV - real strikes only
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks
from tastytrade.instruments import get_option_chain

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

async def get_iv_data():
    print("="*60)
    print("STEP 0D: Filter IV")
    print("="*60)
    
    with open("data/filter2_passed.json", "r") as f:
        stocks = json.load(f)
    
    print(f"Input: {len(stocks)} stocks")
    
    sess = Session(USERNAME, PASSWORD)
    passed = []
    failed = []
    
    # Get actual ATM strikes first
    symbols_to_check = []
    symbol_map = {}
    
    for stock_data in stocks:
        ticker = stock_data['ticker']
        exp_date_str = stock_data['best_expiration']['date']
        stock_price = stock_data['mid']
        
        try:
            chain = get_option_chain(sess, ticker)
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            
            if exp_date not in chain:
                failed.append({'ticker': ticker, 'reason': 'expiration not in chain'})
                continue
            
            options = chain[exp_date]
            calls = [opt for opt in options if opt.option_type.value == 'C']
            
            if not calls:
                failed.append({'ticker': ticker, 'reason': 'no calls found'})
                continue
            
            # Find ATM call
            atm_call = min(calls, key=lambda x: abs(float(x.strike_price) - stock_price))
            symbol = atm_call.streamer_symbol
            
            symbols_to_check.append(symbol)
            symbol_map[symbol] = stock_data
            
        except Exception as e:
            failed.append({'ticker': ticker, 'reason': str(e)[:30]})
    
    # Now get Greeks
    collected = {}
    
    async with DXLinkStreamer(sess) as streamer:
        await streamer.subscribe(Greeks, symbols_to_check)
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 10:
            try:
                greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.5)
                
                if greek and greek.event_symbol in symbols_to_check:
                    if greek.volatility and float(greek.volatility) > 0:
                        collected[greek.event_symbol] = float(greek.volatility)
                        
            except asyncio.TimeoutError:
                continue
        
        await streamer.unsubscribe(Greeks, symbols_to_check)
    
    # Process results
    for symbol, stock_data in symbol_map.items():
        ticker = stock_data['ticker']
        
        if symbol in collected:
            iv = collected[symbol]
            iv_pct = iv * 100
            
            if 15 <= iv_pct <= 80:
                passed.append({
                    **stock_data,
                    'iv': round(iv, 4),
                    'iv_pct': round(iv_pct, 1)
                })
            else:
                failed.append({'ticker': ticker, 'reason': f'IV {iv_pct:.1f}% out of range'})
        else:
            failed.append({'ticker': ticker, 'reason': 'no IV data'})
    
    return passed, failed

def save_results(passed, failed):
    with open("data/filter3_passed.json", "w") as f:
        json.dump(passed, f, indent=2)
    
    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: IV 15-80%")

async def main():
    passed, failed = await get_iv_data()
    save_results(passed, failed)
    print("Step 0D complete")

if __name__ == "__main__":
    asyncio.run(main())
