"""
COMPLETE Options Chain Collector with Real Market Quotes
Gets ALL expirations 0-45 DTE with actual bid/ask prices
"""
import json
import sys
import os
from datetime import datetime, timedelta
from tastytrade import Session
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

def get_chains():
    print("⛓️ Getting ALL chains with REAL bid/ask prices...")
    
    prices = load_stock_prices()
    sess = Session(USERNAME, PASSWORD)
    
    chains = {}
    failed = []
    total_expirations = 0
    total_strikes = 0
    
    today = datetime.now().date()
    
    for ticker, price_data in prices.items():
        print(f"\n{ticker}: ${price_data['mid']:.2f}")
        stock_price = price_data["mid"]
        
        try:
            # Get chain structure
            chain = get_option_chain(sess, ticker)
            
            if not chain:
                print(f"   ❌ No chain")
                failed.append(ticker)
                continue
            
            ticker_expirations = []
            
            for exp_date, options_list in chain.items():
                dte = (exp_date - today).days
                
                if 0 <= dte <= 45:
                    min_strike = stock_price * 0.70
                    max_strike = stock_price * 1.30
                    
                    # Collect symbols for batch quote fetch
                    symbols_to_quote = []
                    strikes_dict = {}
                    
                    for option in options_list:
                        strike = float(option.strike_price)
                        
                        if min_strike <= strike <= max_strike:
                            symbol = option.symbol
                            symbols_to_quote.append(symbol)
                            
                            if strike not in strikes_dict:
                                strikes_dict[strike] = {
                                    'strike': strike,
                                    'call_symbol': None,
                                    'put_symbol': None,
                                    'call_bid': 0,
                                    'call_ask': 0,
                                    'put_bid': 0,
                                    'put_ask': 0
                                }
                            
                            # Identify if call or put
                            if option.option_type == 'C' or 'C' in symbol.split()[-1]:
                                strikes_dict[strike]['call_symbol'] = symbol
                            else:
                                strikes_dict[strike]['put_symbol'] = symbol
                    
                    # Fetch real quotes for all symbols at once
                    if symbols_to_quote:
                        try:
                            # Get quotes from DXFeed through TastyTrade
                            quotes = Quote.get_quotes(sess, symbols_to_quote)
                            
                            # Map quotes back to strikes
                            for quote in quotes:
                                symbol = quote.eventSymbol
                                
                                # Find the strike this quote belongs to
                                for strike_data in strikes_dict.values():
                                    if strike_data['call_symbol'] == symbol:
                                        strike_data['call_bid'] = float(quote.bidPrice or 0)
                                        strike_data['call_ask'] = float(quote.askPrice or 0)
                                    elif strike_data['put_symbol'] == symbol:
                                        strike_data['put_bid'] = float(quote.bidPrice or 0)
                                        strike_data['put_ask'] = float(quote.askPrice or 0)
                        except:
                            # If batch fetch fails, continue with 0 prices
                            print(f"      ⚠️ Could not fetch quotes for {exp_date}")
                    
                    # Add expiration if we have strikes
                    if strikes_dict:
                        exp_strikes = sorted(strikes_dict.values(), key=lambda x: x['strike'])
                        
                        # Count strikes with real quotes
                        quoted = sum(1 for s in exp_strikes if s['call_bid'] > 0 or s['put_bid'] > 0)
                        
                        ticker_expirations.append({
                            'expiration_date': str(exp_date),
                            'dte': dte,
                            'strikes': exp_strikes,
                            'quoted_count': quoted
                        })
                        total_strikes += len(exp_strikes)
            
            if ticker_expirations:
                ticker_expirations.sort(key=lambda x: x['dte'])
                chains[ticker] = ticker_expirations
                total_expirations += len(ticker_expirations)
                
                dtes = [exp['dte'] for exp in ticker_expirations]
                quoted_pct = sum(e['quoted_count'] for e in ticker_expirations) / total_strikes * 100 if total_strikes > 0 else 0
                
                print(f"   ✅ {len(ticker_expirations)} expirations: {dtes}")
                print(f"      {quoted_pct:.0f}% with real quotes")
            else:
                failed.append(ticker)
                print(f"   ❌ No valid expirations")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append(ticker)
    
    # Save complete chains with quotes
    output = {
        "timestamp": datetime.now().isoformat(),
        "requested": len(prices),
        "success": len(chains),
        "failed": failed,
        "total_expirations": total_expirations,
        "total_strikes": total_strikes,
        "chains": chains
    }
    
    with open("data/chains.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ CHAINS COMPLETE: {len(chains)}/{len(prices)} stocks")
    print(f"   Total expirations: {total_expirations}")
    print(f"   Total strikes: {total_strikes}")

if __name__ == "__main__":
    get_chains()
