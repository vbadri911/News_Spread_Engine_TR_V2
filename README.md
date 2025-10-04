# 📘 Credit Spread Finder - README

**Purpose:** Find the 9 best options trades (credit spreads) from 500 stock tickers in minutes

**What to know:** Which exact trades to place today  

**What to do:** Execute high-probability credit spreads  

**What to feel:** Confident because math backs every trade


### What's in it for me?
- Save 3 hours of manual searching daily
- Make money 70% of the time (mathematically proven)
- Never miss high-volatility opportunities
- Stop losing on shitty scanner data

# How it works:

## Build a Porftolio

### Step 00A: Download a CSV file from GitHub containing S&P 500 companies. Extract ticker symbols. Save 503 tickers to `data/sp500.json.` 

```bash
python3 pipeline/00a_get_sp500.py
```

### Step 00B: Stream live bid/ask quotes from TastyTrade for S&P500 stocks. Filter by price ($30-400) and spread (<2%). Saves liquid stocks to `data/filter1_passed.json.`

```bash
python3 pipeline/00b_filter_price.py
```

### Step 00C: Stream options chains from TastyTrade for output of `Step 00B`. Filter by expiration (15-45 days) and strike count (20+ strikes). Saves stocks with tradeable options to `data/filter2_passed.json.`

```bash
python3 pipeline/00c_filter_options.py
```

### Step 00D: Stream ATM option strikes from TastyTrade chains. Streams IV data for strikes. Filter by IV range 15-80%. Saves 66 stocks to `data/filter3_passed.json.`

```bash
python3 pipeline/00d_filter_iv.py
```

### Step 00E: Load stocks from `Step 00D`.  Score by IV (40 pts), Strik Count (30 pts), expirations (20 pts), spread tightness (10 pts).  Rank by total score.  Select top 22 tickers.  Save to `data/stocks.py`

```bash
python3 pipeline/00e_select_22.py
```

### Step 00F: Fetch 3 days of news linked to output from `Step 00E` from Finnhub.io.  Collect up to 10 artilces per stock with headlines.  Save article count and headlines `data/finnhub_news.json.`

```bash
python3 pipeline/00f_get_news.py
```


## Build Credit Spreads


### Step 01: Stream bid/ask quotes from TastyTrade for output from `Step 00E`. Save mid-price, spread, and timestamp to `data/stock_prices.json.`




