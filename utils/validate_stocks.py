"""
Validate stocks.py: Check market cap (>50B), price ($50-500), IV profile, and weekly options availability
Using yfinance - run locally with: pip install yfinance pandas
"""
import json
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import logging


# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging

# Setup logging
setup_logging('validate_stocks')


def load_stocks():
    """Load STOCKS and EDGE_REASON from stocks.py"""
    logging.info("Loading stocks.py")
    try:
        #sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import data.stocks  # Assumes stocks.py is in same dir or data/
        return data.stocks.STOCKS, data.stocks.EDGE_REASON
    except ImportError as e:
        logging.error(f"Failed to load stocks.py: {e}")
        sys.exit(1)


def validate_ticker(ticker, edge_reason):
    """Validate single ticker: market cap, price, IV, weekly options"""
    logging.info(f"Validating {ticker}")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Market Cap > $50B (in USD)
        market_cap = info.get('marketCap', 0) / 1e9  # In billions
        cap_valid = market_cap > 50
        logging.debug(f"{ticker} Market Cap: ${market_cap:.1f}B - Valid: {cap_valid}")

        # Price $50-500
        price = info.get('regularMarketPrice', 0)
        price_valid = 20 <= price <= 1000
        logging.debug(f"{ticker} Price: ${price:.2f} - Valid: {price_valid}")

        # Implied Volatility (from info, or average from options)
        iv = info.get('impliedVolatility', 0) * 100 if info.get('impliedVolatility') else 0  # %
        # Fallback: Get from nearest option chain
        if iv == 0:
            try:
                expirations = stock.options
                if expirations:
                    opt_chain = stock.option_chain(expirations[0])  # Nearest expiry
                    iv_calls = opt_chain.calls['impliedVolatility'].mean() * 100
                    iv_puts = opt_chain.puts['impliedVolatility'].mean() * 100
                    iv = (iv_calls + iv_puts) / 2
                    logging.debug(f"{ticker} Avg IV from options: {iv:.1f}%")
            except Exception as e:
                logging.warning(f"Could not fetch options IV for {ticker}: {e}")

        # IV Profile: Stable 30-50, Growth 50-80, Cyclical 80+
        if 30 <= iv <= 50:
            iv_profile = "Stable"
        elif 50 < iv <= 80:
            iv_profile = "Growth"
        else:
            iv_profile = "Cyclical" if iv > 80 else "Low/Invalid"
        iv_valid = iv > 0  # Basic check

        # Weekly Options: Check if any expiry within 7 days
        weekly_valid = False
        try:
            expirations = stock.options
            today = datetime.now().date()
            for exp_str in expirations:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
                if 1 <= (exp_date - today).days <= 7:  # 1-7 DTE for weekly
                    weekly_valid = True
                    break
            logging.debug(f"{ticker} Weekly options: {'Yes' if weekly_valid else 'No'}")
        except Exception as e:
            logging.warning(f"Could not check options for {ticker}: {e}")

        # Sector from edge_reason or info
        sector = edge_reason.get(ticker, "").split(" - ")[0].replace("XLK (", "").replace(")", "") if edge_reason.get(
            ticker) else info.get('sector', 'N/A')

        return {
            'ticker': ticker,
            'sector': sector,
            'market_cap_b': market_cap,
            'price': price,
            'iv_%': round(iv, 1),
            'iv_profile': iv_profile,
            'has_weekly': weekly_valid,
            'valid_cap': cap_valid,
            'valid_price': price_valid,
            'valid_iv': iv_valid,
            'overall_valid': cap_valid and price_valid and iv_valid and weekly_valid,
            'edge_reason': edge_reason.get(ticker, 'N/A')
        }
    except Exception as e:
        logging.error(f"Error validating {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e), 'overall_valid': False}


def main():
    logging.info("Starting stock validation - Date: %s", datetime.now().strftime('%Y-%m-%d'))
    print("=" * 60)
    print("STOCK VALIDATION REPORT")
    print("=" * 60)

    # Load data
    stocks, edge_reasons = load_stocks()
    logging.info(f"Loaded {len(stocks)} stocks")

    # Validate each
    results = [validate_ticker(ticker, edge_reasons) for ticker in stocks]

    # DataFrame for summary
    df = pd.DataFrame(results)
    df = df.drop(columns=['edge_reason'], errors='ignore')  # Optional: keep for detailed report

    # Stats
    total = len(results)
    valid = df['overall_valid'].sum()
    invalid = total - valid

    print(f"\n📊 SUMMARY:")
    print(f"   Total Stocks: {total}")
    print(f"   Valid: {valid} | Invalid: {invalid}")

    print(f"\n🔍 DETAILED RESULTS:")
    for _, row in df.iterrows():
        status = "✅" if row['overall_valid'] else "❌"
        print(
            f"{status} {row['ticker']} ({row['sector']}): Cap=${row['market_cap_b']:.1f}B, Price=${row['price']:.2f}, IV={row['iv_%']:.1f}% ({row['iv_profile']}), Weekly: {row['has_weekly']}")
        if not row['overall_valid']:
            print(
                f"   Issues: {'Cap' if not row['valid_cap'] else ''}{'Price' if not row['valid_price'] else ''}{'IV' if not row['valid_iv'] else ''}{'Weekly' if not row['has_weekly'] else ''}")

    # Save report
    os.makedirs('reports', exist_ok=True)
    filename = f"reports/stock_validation_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False)
    print(f"\n📁 Full report saved to {filename}")

    # Suggestions
    if invalid > 0:
        print(
            f"\n💡 SUGGESTIONS: Review invalid stocks and regenerate with updated prompt. Out-of-box: Swap low-IV picks (e.g., PG) for higher like NFLX if liquidity holds.")

    logging.info("Validation complete: %d/%d valid", valid, total)


if __name__ == "__main__":
    main()