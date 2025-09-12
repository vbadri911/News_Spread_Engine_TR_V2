# Credit Spread Finder

Finds real credit spread opportunities using actual market data from TastyTrade and AI analysis from GPT.

## What This Does

Takes 22 stock picks and finds the best credit spreads by:
1. Getting real stock prices
2. Finding liquid options
3. Calculating actual probability of profit
4. Having GPT validate the trades

No fake data. No estimates. Real prices, real Greeks, real math.

## Quick Start

1. Configure your credentials in config.py
2. Set your OpenAI API key: export OPENAI_API_KEY='your-key'
3. Run: python3 run_pipeline.py

## The Pipeline

Each step filters for quality:

1. GPT picks 22 stocks (2 per sector) with market edge
2. Get real prices from TastyTrade (must have valid quotes)
3. Find options chains (15-45 DTE, near the money)
4. Check liquidity (bid/ask spread <10%)
5. Get real Greeks (must have valid IV)
6. Build spreads (OTM only, min 30¢ credit)
7. Calculate PoP with Black-Scholes (real math)
8. Rank by ROI × PoP score
9. Format for GPT validation
10. GPT adds market context
11. Display final trades

## Requirements

- Python 3.8+
- TastyTrade account
- OpenAI API key
- pip install tastytrade openai scipy

## Output

Real trades with real probabilities, ready to execute.
