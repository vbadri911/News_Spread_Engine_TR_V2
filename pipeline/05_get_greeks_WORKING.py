"""
Get Greeks - Build symbols from chain data
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Greeks

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

async def get_greeks():
    print("="*60)
    print("STEP 5: Get Greeks")
    print("="*60)
    
    sess = Session(USERNAME, PASSWORD)
    
    # Load chains to know what we need Greeks for
    with open("data/chains.json", "r") as f:
        chains_data = json.load(f)
    
    # Load stock prices for reference
    with open("data/stock_prices.json", "r") as f:
        prices = json.load(f)["prices"]
    
    print("\n🧮 Collecting Greeks from TastyTrade...")
    
    all_greeks = {}
    
    # Process each ticker
    for ticker in prices.keys():
        try:
            # Get the full option chain to access symbols
            chain = get_option_chain(sess, ticker)
            if not chain:
                continue
            
            # Build symbol map
            symbol_map = {}
            for exp_date, options in chain.items():
                for opt in options:
                    symbol_map[opt.streamer_symbol] = {
                        'strike': float(opt.strike_price),
                        'type': opt.option_type.value,
                        'expiration': str(exp_date)
                    }
            
            if not symbol_map:
                continue
            
            # Stream Greeks for this ticker
            symbols = list(symbol_map.keys())[:500]  # Limit per ticker
            
            print(f"\n{ticker}: Streaming {len(symbols)} Greeks...")
            
            async with DXLinkStreamer(sess) as streamer:
                await streamer.subscribe(Greeks, symbols)
                
                ticker_greeks = {}
                start_time = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - start_time < 5:
                    try:
                        greek = await asyncio.wait_for(streamer.get_event(Greeks), timeout=0.2)
                        
                        if greek and greek.event_symbol in symbols:
                            iv = float(greek.volatility or 0)
                            if iv > 0:
                                ticker_greeks[greek.event_symbol] = {
                                    'iv': round(iv, 4),
                                    'delta': round(float(greek.delta or 0), 4),
                                    'theta': round(float(greek.theta or 0), 4),
                                    'gamma': round(float(greek.gamma or 0), 6),
                                    'vega': round(float(greek.vega or 0), 4),
                                    **symbol_map[greek.event_symbol]
                                }
                    except asyncio.TimeoutError:
                        continue
                
                await streamer.unsubscribe(Greeks, symbols)
                
                if ticker_greeks:
                    all_greeks[ticker] = ticker_greeks
                    print(f"   ✅ Got {len(ticker_greeks)} Greeks")
                
        except Exception as e:
            print(f"   ❌ Error with {ticker}: {e}")
    
    # Save organized Greeks
    output = {
        "timestamp": datetime.now().isoformat(),
        "tickers_with_greeks": len(all_greeks),
        "total_greeks_collected": sum(len(g) for g in all_greeks.values()),
        "greeks": all_greeks
    }
    
    with open("data/greeks.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Greeks collected for {len(all_greeks)} tickers")
    print(f"   Total Greeks: {output['total_greeks_collected']}")

def main():
    asyncio.run(get_greeks())

if __name__ == "__main__":
    main()
