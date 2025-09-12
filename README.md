# Credit Spread Finder

This pipeline finds options credit spreads that have a high chance of making money. It takes real market data from TastyTrade and uses math to find the best trades.

## What It Does

Takes 22 stocks and finds credit spreads (options strategies where you get paid upfront) that have:
- High probability of keeping the money (70%+ win rate)
- Good return on risk (30%+ ROI minimum)
- Actual liquidity (you can actually trade them)

## Why We Built This

Most options scanners show you garbage trades with fake prices. This pipeline only shows real, tradeable spreads by:
1. Using real-time data (no estimates)
2. Checking liquidity at every step
3. Calculating actual probability using Black-Scholes
4. Having GPT double-check for suspicious data

## How It Works - The Pipeline

### Step 1: Stock Selection (14 seconds)
**What**: GPT picks 22 stocks, 2 per sector  
**Filter**: Must have options, be liquid, have some edge  
**Output**: stocks.py with tickers and reasons

### Step 2: Get Prices (12 seconds)
**What**: Gets real bid/ask prices from TastyTrade  
**Filter**: Stock must have valid quotes  
**Output**: stock_prices.json - typically gets 22/22

### Step 3: Find Options (5 seconds)
**What**: Looks for options expiring in 15-45 days  
**Filter**: Strike prices 70-130% of current price  
**Output**: chains.json - finds ~1500 options

### Step 4: Check Liquidity (2 minutes)
**What**: Scores each option's liquidity 0-100  
**Filter**: Keeps options with score >40 (tight bid/ask, decent price)  
**Output**: liquid_chains.json - keeps ~1000 options

### Step 5: Get Greeks (30 seconds)
**What**: Gets IV, delta, theta for every liquid option  
**Filter**: Must have valid IV (no zeros)  
**Output**: greeks.json - achieves 100% coverage

### Step 6: Build Spreads (instant)
**What**: Combines options into credit spreads  
**Filter**: Out-of-the-money only, $2.50/$5/$10 wide, min $0.15 credit, ROI >5%  
**Output**: spreads.json - builds ~300 spreads

### Step 7: Calculate Probability (1 second)
**What**: Uses Black-Scholes to find real win probability  
**Filter**: None - calculates for all  
**Output**: analyzed_spreads.json with PoP added

### Step 8: Rank Trades (instant)
**What**: Scores each spread on multiple factors  
**Filter**: ENTER if PoP >70% and ROI >20%, WATCH if PoP >60% and ROI >30%  
**Output**: ranked_spreads.json - finds ~60 ENTER trades

### Step 9: Prepare Report (instant)
**What**: Formats top trades for GPT  
**Output**: report_table.json - top 15 trades

### Step 10: GPT Analysis (25 seconds)
**What**: GPT identifies the 9 best trades  
**Filter**: Checks for suspicious data (ROI >100%)  
**Output**: top9_analysis.json - final selections

## The Math

**ROI Calculation**: (credit / max_loss) × 100  
Example: Collect $100, risk $400 = 25% ROI

**Probability Calculation**: Black-Scholes formula using current price, strike price, days to expiration, implied volatility, and 5% risk-free rate

**Score Calculation**: (ROI × PoP) / 100  
Balances return vs probability - higher score = better trade

## Running It

Set credentials:
export TASTY_USERNAME='your_username'
export TASTY_PASSWORD='your_password'
export OPENAI_API_KEY='your_key'

Run pipeline (3.5 minutes):
./run_enhanced.py

See results:
python3 format_top9_table.py

## What Makes This Different

1. **100% Real Data**: No estimates, fallbacks, or fake prices
2. **Multi-Stage Filtering**: Each step removes garbage
3. **Liquidity Scoring**: Not just binary pass/fail
4. **Batch Processing**: 500 symbols at once for speed
5. **GPT Validation**: Catches suspicious data humans miss

## Typical Results

From 22 stocks:
- Finds ~1500 options
- ~1000 pass liquidity
- Builds ~300 spreads
- ~60 high-quality trades
- Top 9 selected for execution

Success rate: 70-85% win probability on selected trades

## Files Created

- stocks.py - Selected tickers
- stock_prices.json - Current prices
- chains.json - All options
- liquid_chains.json - Liquid options only
- greeks.json - IV and Greeks
- spreads.json - All spreads
- analyzed_spreads.json - With probabilities
- ranked_spreads.json - Scored and ranked
- top9_analysis.json - Final picks
- top9_trades_*.csv - Excel format

## Configuration

Edit these in any script:
- MIN_POP = 66 (66% aggressive, 70% safe)
- MIN_ROI = 33 (33% aggressive, 40% safe)
- BATCH_SIZE = 500 (Greeks batch size)
- COVERAGE_TARGET = 0.95 (Greeks coverage target)

## Common Issues

**APD showing 250% ROI**: Bad data from wide bid/ask. Verify before trading.

**Only getting MSFT/LIN trades**: These are the most liquid. Quality over quantity.

**Greeks taking forever**: Normal. Getting 100% coverage takes 30-60 seconds.

## The Edge

This finds trades that:
1. Pay you upfront (credit spreads)
2. Win 70%+ of the time (high PoP)
3. Return 30%+ on risk (good ROI)
4. Can actually be executed (liquid)

No magic. Just math and good data.
