"""
Filter by price and spread - no fallbacks
"""
import json
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote

async def filter_price_liquidity():
    print("="*60)
    print("STEP 0B: Filter Price")
    print("="*60)
    
    with open("data/sp500.json", "r") as f:
        tickers = json.load(f)["tickers"]
    
    print(f"Input: {len(tickers)} stocks")
    
    sess = Session(USERNAME, PASSWORD)
    passed = []
    failed = []
    
    async with DXLinkStreamer(sess) as streamer:
        for i in range(0, len(tickers), 50):
            batch = tickers[i:i+50]
            
            await streamer.subscribe(Quote, batch)
            
            batch_quotes = {}
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 5:
                try:
                    quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.5)
                    
                    if quote and quote.event_symbol in batch:
                        if quote.bid_price and quote.ask_price:
                            bid = float(quote.bid_price)
                            ask = float(quote.ask_price)
                            
                            if bid > 0 and ask > 0:
                                mid = (bid + ask) / 2
                                spread_pct = ((ask - bid) / mid) * 100
                                
                                batch_quotes[quote.event_symbol] = {
                                    'ticker': quote.event_symbol,
                                    'bid': round(bid, 2),
                                    'ask': round(ask, 2),
                                    'mid': round(mid, 2),
                                    'spread_pct': round(spread_pct, 2)
                                }
                except asyncio.TimeoutError:
                    continue
            
            await streamer.unsubscribe(Quote, batch)
            
            for ticker in batch:
                if ticker in batch_quotes:
                    data = batch_quotes[ticker]
                    if 30 <= data['mid'] <= 400 and data['spread_pct'] < 2.0:
                        passed.append(data)
                    else:
                        reason = "price out of range" if data['mid'] < 30 or data['mid'] > 400 else f"spread {data['spread_pct']:.2f}%"
                        failed.append({'ticker': ticker, 'reason': reason})
                else:
                    failed.append({'ticker': ticker, 'reason': 'no quote data'})
    
    return passed, failed

def save_results(passed, failed):
    with open('data/filter1_passed.json', 'w') as f:
        json.dump(passed, f, indent=2)
    
    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    print(f"\nCriteria: $30-400, spread <2%")

async def main():
    passed, failed = await filter_price_liquidity()
    save_results(passed, failed)
    print("Step 0B complete")

if __name__ == "__main__":
    asyncio.run(main())
