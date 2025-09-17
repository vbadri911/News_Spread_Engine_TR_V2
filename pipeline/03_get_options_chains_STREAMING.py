"""
FIXED Options Chains with Real Quotes using DXLinkStreamer
Gets ALL expirations 0-45 DTE with actual bid/ask prices
Uses the same streaming approach that works in Steps 2, 4, and 5
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

async def get_chains_with_quotes():
    """Get chains with real quotes using streaming"""
    print("⛓️ Getting ALL chains with streaming quotes...")
    
    prices = load_stock_prices()
    sess = Session(USERNAME, PASSWORD)
    
    chains = {}
    failed = []
    total_expirations = 0
    total_strikes = 0
    
    today = datetime.now().date()
    
    # First, collect all option structures
    for ticker, price_data in prices.items():
        print(f"\n{ticker}: ${price_data['mid']:.2f}")
        stock_price = price_data["mid"]
        
        try:
            chain = get_option_chain(sess, ticker)
            
            if not chain:
                failed.append(ticker)
                continue
            
            ticker_data = []
            
            for exp_date, options_list in chain.items():
                dte = (exp_date - today).days
                
                if 0 <= dte <= 45:
                    min_strike = stock_price * 0.70
                    max_strike = stock_price * 1.30
                    
                    exp_options = []
                    for option in options_list:
                        strike = float(option.strike_price)
                        if min_strike <= strike <= max_strike:
                            exp_options.append({
                                'strike': strike,
                                'symbol': option.streamer_symbol,
                                'type': option.option_type.value
                            })
                    
                    if exp_options:
                        ticker_data.append({
                            'expiration_date': str(exp_date),
                            'dte': dte,
                            'options': exp_options
                        })
            
            if ticker_data:
                chains[ticker] = {
                    'stock_price': stock_price,
                    'expirations': ticker_data
                }
                total_expirations += len(ticker_data)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append(ticker)
    
    # Now stream quotes for all collected options
    print("\n📡 Streaming real quotes...")
    
    async with DXLinkStreamer(sess) as streamer:
        for ticker, chain_data in chains.items():
            print(f"\n{ticker}: Getting quotes...")
            
            for exp_data in chain_data['expirations']:
                symbols = [opt['symbol'] for opt in exp_data['options']]
                
                if not symbols:
                    continue
                
                # Subscribe to this expiration's symbols
                await streamer.subscribe(Quote, symbols)
                
                # Collect quotes
                quotes_collected = {}
                start_time = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - start_time < 3:
                    try:
                        quote = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.2)
                        
                        if quote and quote.event_symbol in symbols:
                            quotes_collected[quote.event_symbol] = {
                                'bid': float(quote.bid_price or 0),
                                'ask': float(quote.ask_price or 0)
                            }
                            
                    except asyncio.TimeoutError:
                        continue
                
                await streamer.unsubscribe(Quote, symbols)
                
                # Update options with real quotes
                strikes_dict = {}
                for opt in exp_data['options']:
                    strike = opt['strike']
                    if strike not in strikes_dict:
                        strikes_dict[strike] = {
                            'strike': strike,
                            'call_bid': 0, 'call_ask': 0,
                            'put_bid': 0, 'put_ask': 0
                        }
                    
                    if opt['symbol'] in quotes_collected:
                        q = quotes_collected[opt['symbol']]
                        if opt['type'] == 'C':
                            strikes_dict[strike]['call_bid'] = q['bid']
                            strikes_dict[strike]['call_ask'] = q['ask']
                        else:
                            strikes_dict[strike]['put_bid'] = q['bid']
                            strikes_dict[strike]['put_ask'] = q['ask']
                
                exp_data['strikes'] = list(strikes_dict.values())
                total_strikes += len(exp_data['strikes'])
                
                # Clean up options list
                del exp_data['options']
            
            # Format for compatibility
            final_expirations = []
            for exp_data in chain_data['expirations']:
                if 'strikes' in exp_data:
                    final_expirations.append({
                        'expiration_date': exp_data['expiration_date'],
                        'dte': exp_data['dte'],
                        'strikes': sorted(exp_data['strikes'], key=lambda x: x['strike'])
                    })
            
            chains[ticker] = final_expirations
            
            dtes = [e['dte'] for e in final_expirations]
            print(f"   ✅ {len(final_expirations)} expirations: {dtes}")
    
    return chains, failed, total_expirations, total_strikes

def main():
    """Main execution"""
    print("="*60)
    print("STEP 3: Get Options Chains (STREAMING)")
    print("="*60)
    
    chains, failed, total_exp, total_str = asyncio.run(get_chains_with_quotes())
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": 22,
        "success": len(chains),
        "failed": failed,
        "total_expirations": total_exp,
        "total_strikes": total_str,
        "chains": chains
    }
    
    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ CHAINS COMPLETE: {len(chains)}/22 stocks")
    print(f"   Total expirations: {total_exp}")
    print(f"   Total strikes: {total_str}")

if __name__ == "__main__":
    main()
