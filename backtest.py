import json
import yfinance as yf
from datetime import datetime, timedelta


def backtest_top9(top9_file, historical_expiry=False):
    with open(top9_file, 'r') as f:
        tops = json.load(f)['spreads']  # Adjust key

    results = []
    for spread in tops:
        ticker = spread['ticker']
        type_ = spread['type']
        short_strike = spread['short_strike']
        exp_date = spread['expiration']['date']
        exp_dt = datetime.strptime(exp_date, '%Y-%m-%d')
        # Fetch close at expiry (or next day)
        data = yf.download(ticker, start=exp_dt, end=exp_dt + timedelta(1))
        expiry_price = data['Close'].iloc[0] if not data.empty else None

        if expiry_price:
            if type_ == 'Bull Put':
                profitable = expiry_price > short_strike
            elif type_ == 'Bear Call':
                profitable = expiry_price < short_strike
            results.append({
                'ticker': ticker,
                'type': type_,
                'profitable': profitable,
                'expiry_price': expiry_price
            })

    win_rate = sum(r['profitable'] for r in results) / len(results) * 100 if results else 0
    print(f"Win Rate: {win_rate}%")


if __name__ == "__main__":
    backtest_top9('data/top9_analysis.json')  # Adjust path
