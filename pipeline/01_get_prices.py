"""
Get Stock Prices: Real prices from Tradier
Enhanced with better error handling and diagnostics
"""
import json
import sys
import os
from datetime import datetime
import requests
import yfinance as yf  # Add


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import TRADIER_TOKEN

base_url = 'https://api.tradier.com'
headers = {'Authorization': f'Bearer {TRADIER_TOKEN}', 'Accept': 'application/json'}

def check_prerequisites():
    """Check if everything is set up correctly"""
    # Check credentials
    if not TRADIER_TOKEN:
        print("❌ Missing Tradier credentials")
        print("Set TRADIER_TOKEN in pipeline/config.py")
        sys.exit(1)

    # Check if data directory exists
    if not os.path.exists("data"):
        print("📁 Creating data directory...")
        os.makedirs("data", exist_ok=True)

    # Try to import stocks
    try:
        sys.path.insert(0, 'data')
        from stocks import STOCKS
        if not STOCKS:
            print("❌ data/stocks.py is empty")
            sys.exit(1)
        return STOCKS
    except ImportError:
        print("❌ data/stocks.py not found - trying sp500.json as fallback")
        # Fallback to sp500.json
        try:
            with open("data/sp500.json", "r") as f:
                data = json.load(f)
            stocks = data.get("tickers", [])
            if not stocks:
                print("❌ data/sp500.json is empty or missing tickers")
                sys.exit(1)
            return stocks
        except Exception as e:
            print(f"❌ Failed to load sp500.json: {e}")
            sys.exit(1)

def get_real_prices():
    """Get real stock prices with better error handling"""
    print("💰 Getting real stock prices from Tradier...")

    STOCKS = check_prerequisites()

    prices = {}
    failed = []
    if 'historical' in sys.argv:  # Or check args from runner
        # Use yf for historical
        STOCKS = check_prerequisites()
        prices = {}
        hist_date = datetime.now().strftime('%Y-%m-%d')  # Mocked
        for ticker in STOCKS:
            data = yf.download(ticker, start=hist_date, end=hist_date)
            if not data.empty:
                bid = data['Low'].iloc[0]  # Approx
                ask = data['High'].iloc[0]
                mid = data['Close'].iloc[0]
                prices[ticker] = {'mid': mid, 'bid': bid, 'ask': ask}
        return prices, []
    else:
    # Existing live code
        try:
            # Batch stocks, 50 at a time (as in 02_get_stock_prices.py)
            batch_size = 50
            for i in range(0, len(STOCKS), batch_size):
                batch = STOCKS[i:i + batch_size]
                symbols_str = ','.join(batch)
                print(f"   Processing batch {i//batch_size + 1}: {len(batch)} stocks")

                response = requests.get(f'{base_url}/v1/markets/quotes', params={'symbols': symbols_str}, headers=headers)

                if response.status_code == 200:
                    data = response.json()['quotes']
                    quotes = data['quote'] if isinstance(data, dict) else data
                    if not isinstance(quotes, list):
                        quotes = [quotes] if quotes else []

                    for q in quotes:
                        if q is None or 'symbol' not in q:
                            continue
                        ticker = q['symbol']
                        bid = float(q.get('bid', 0))
                        ask = float(q.get('ask', 0))

                        if bid > 0 and ask > 0:
                            mid = (bid + ask) / 2
                            prices[ticker] = {
                                "bid": round(bid, 2),
                                "ask": round(ask, 2),
                                "mid": round(mid, 2),
                                "spread": round(ask - bid, 2),
                                "timestamp": datetime.now().isoformat()
                            }
                            print(f"   ✅ {ticker}: ${mid:.2f} (bid: ${bid:.2f}, ask: ${ask:.2f})")
                        else:
                            failed.append(ticker)
                            print(f"   ❌ {ticker}: No valid bid/ask")
                else:
                    print(f"❌ Error fetching batch {i//batch_size + 1}: {response.text[:100]}")
                    failed.extend(batch)
        except Exception as e:
            print(f"❌ Tradier connection error: {e}")
            print("This could be:")
            print("1. Invalid Tradier API token")
            print("2. Network issues")
            print("3. Tradier API problems")
            sys.exit(1)

    # Check what we're missing
    for ticker in STOCKS:
        if ticker not in prices and ticker not in failed:
            failed.append(ticker)
            print(f"   ❌ {ticker}: No data received")

    return prices, failed

def save_prices(prices, failed):
    """Save price data"""
    # Import stocks again to get the original list
    STOCKS = check_prerequisites()

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
    if len(STOCKS) > 0:
        success_rate = len(prices) / len(STOCKS) * 100
        print(f"   Success: {len(prices)}/{len(STOCKS)} ({success_rate:.1f}%)")
    else:
        print(f"   Success: {len(prices)}/{len(STOCKS)} (0.0%)")
    print(f"   Failed: {len(failed)}")

    if len(prices) == 0:
        print("❌ FATAL: No prices collected")
        print("Check your Tradier credentials and network connection")
        sys.exit(1)
    elif len(STOCKS) > 0 and len(prices) < len(STOCKS) * 0.5:
        print("⚠️ WARNING: Less than 50% success rate")
        print("Pipeline will continue but may have limited results")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 01: Get Real Stock Prices")
    print("="*60)

    # Get prices
    prices, failed = get_real_prices()

    # Save results
    save_prices(prices, failed)

    print("✅ Step 01 complete: stock_prices.json created")

if __name__ == "__main__":
    main()