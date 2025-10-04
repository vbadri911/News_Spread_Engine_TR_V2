"""
Get Options Chains - Complete with symbols for Greeks matching
"""
import json
import sys
import os
import asyncio
from datetime import datetime, timedelta
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Quote

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USERNAME, PASSWORD

def load_stock_prices():
    try:
        with open("data/stock_prices.json", "r") as f:
            data = json.load(f)
        return data["prices"]
    except FileNotFoundError:
        print("❌ stock_prices.json not found")
        sys.exit(1)

async def get_chains():
    print("="*60)
    print("STEP 02: Get Options Chains")
    print("="*60)
    
    prices = load_stock_prices()
    sess = Session(USERNAME, PASSWORD)
    
    chains = {}
    today = datetime.now().date()
    
    print("\n📊 Collecting chains with symbols...")
    
    # First, get all option data INCLUDING symbols
    for ticker, price_data in prices.items():
        stock_price = price_data["mid"]
        
        try:
            chain = get_option_chain(sess, ticker)
            if not chain:
                continue
            
            ticker_expirations = []
            
            for exp_date, options_list in chain.items():
                dte = (exp_date - today).days
                if 0 <= dte <= 45:
                    
                    # Build complete strike data WITH symbols
                    strikes = {}
                    option_symbols = []
                    
                    for opt in options_list:
                        strike = float(opt.strike_price)
                        if stock_price * 0.70 <= strike <= stock_price * 1.30:
                            
                            if strike not in strikes:
                                strikes[strike] = {
                                    'strike': strike,
                                    'call_symbol': None,
                                    'put_symbol': None,
                                    'call_bid': 0,
                                    'call_ask': 0,
                                    'put_bid': 0,
                                    'put_ask': 0
                                }
                            
                            # Store the actual symbol
                            if opt.option_type.value == 'C':
                                strikes[strike]['call_symbol'] = opt.streamer_symbol
                                option_symbols.append(opt.streamer_symbol)
                            else:
                                strikes[strike]['put_symbol'] = opt.streamer_symbol
                                option_symbols.append(opt.streamer_symbol)
                    
                    if strikes:
                        # Get quotes for this expiration
                        async with DXLinkStreamer(sess) as streamer:
                            await streamer.subscribe(Quote, option_symbols)
                            
                            quotes = {}
                            start_time = asyncio.get_event_loop().time()
                            
                            while asyncio.get_event_loop().time() - start_time < 3:
                                try:
                                    quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.2)
                                    
                                    if quote and quote.event_symbol in option_symbols:
                                        bid = float(quote.bid_price or 0)
                                        ask = float(quote.ask_price or 0)
                                        if bid > 0 and ask > 0:
                                            quotes[quote.event_symbol] = {'bid': bid, 'ask': ask}
                                            
                                except asyncio.TimeoutError:
                                    continue
                            
                            await streamer.unsubscribe(Quote, option_symbols)
                        
                        # Update strikes with quotes
                        for strike_data in strikes.values():
                            if strike_data['call_symbol'] in quotes:
                                q = quotes[strike_data['call_symbol']]
                                strike_data['call_bid'] = q['bid']
                                strike_data['call_ask'] = q['ask']
                            if strike_data['put_symbol'] in quotes:
                                q = quotes[strike_data['put_symbol']]
                                strike_data['put_bid'] = q['bid']
                                strike_data['put_ask'] = q['ask']
                        
                        ticker_expirations.append({
                            'expiration_date': str(exp_date),
                            'dte': dte,
                            'strikes': sorted(list(strikes.values()), key=lambda x: x['strike'])
                        })
            
            if ticker_expirations:
                chains[ticker] = ticker_expirations
                print(f"   ✅ {ticker}: {len(ticker_expirations)} expirations")
                
        except Exception as e:
            print(f"   ❌ {ticker}: {e}")
    
    # Save complete chains with symbols
    total_exp = sum(len(exps) for exps in chains.values())
    total_strikes = sum(len(exp['strikes']) for exps in chains.values() for exp in exps)
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": len(prices),
        "success": len(chains),
        "total_expirations": total_exp,
        "total_strikes": total_strikes,
        "chains": chains
    }
    
    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Chains complete: {len(chains)}/{len(prices)} stocks")
    print(f"   Expirations: {total_exp}")
    print(f"   Strikes: {total_strikes} (with symbols)")

def main():
    asyncio.run(get_chains())

if __name__ == "__main__":
    main()
