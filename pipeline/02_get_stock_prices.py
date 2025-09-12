"""
Get Stock Prices: Real prices from TastyTrade
No fallbacks - real data only
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote

# Import the stocks
try:
    from data.stocks import STOCKS
except ImportError:
    print("❌ stocks.py not found - run step 1 first")
    sys.exit(1)

async def get_real_prices():
    """Get real stock prices - no fallbacks"""
    print("💰 Getting real stock prices from TastyTrade...")
    
    sess = Session(USERNAME, PASSWORD)
    prices = {}
    failed = []
    
    async with DXLinkStreamer(sess) as streamer:
        # Subscribe to all stocks
        await streamer.subscribe(Quote, STOCKS)
        print(f"📡 Subscribed to {len(STOCKS)} stocks")
        
        # Collect for 10 seconds
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 10:
            try:
                quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.5)
                
                if quote and quote.event_symbol in STOCKS:
                    ticker = quote.event_symbol
                    bid = float(quote.bid_price or 0)
                    ask = float(quote.ask_price or 0)
                    
                    if bid > 0 and ask > 0:
                        mid = (bid + ask) / 2
                        prices[ticker] = {
                            "ticker": ticker,
                            "bid": round(bid, 2),
                            "ask": round(ask, 2),
                            "mid": round(mid, 2),
                            "spread": round(ask - bid, 2),
                            "timestamp": datetime.now().isoformat()
                        }
                        print(f"   ✅ {ticker}: ${mid:.2f}")
                        
            except asyncio.TimeoutError:
                continue
        
        await streamer.unsubscribe(Quote, STOCKS)
    
    # Check what we're missing
    for ticker in STOCKS:
        if ticker not in prices:
            failed.append(ticker)
            print(f"   ❌ {ticker}: No data")
    
    return prices, failed

def save_prices(prices, failed):
    """Save price data"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": len(STOCKS),
        "success": len(prices),
        "failed": len(failed),
        "prices": prices,
        "missing_tickers": failed
    }
    
    with open("data/stock_prices.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   Success: {len(prices)}/{len(STOCKS)}")
    print(f"   Failed: {len(failed)}")
    
    if len(prices) == 0:
        print("❌ FATAL: No prices collected")
        sys.exit(1)

def main():
    """Main execution"""
    print("="*60)
    print("STEP 2: Get Real Stock Prices")
    print("="*60)
    
    # Get prices
    prices, failed = asyncio.run(get_real_prices())
    
    # Save results
    save_prices(prices, failed)
    
    print("✅ Step 2 complete: stock_prices.json created")

if __name__ == "__main__":
    main()
