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

# 🔎 Credit Spread Finder - PIPELINE

##  🛠 Build a Porftolio

**Step 00A:** Download a CSV file from GitHub containing S&P 500 companies. Extract ticker symbols. Save 503 tickers to `data/sp500.json.` 

```bash
python3 pipeline/00a_get_sp500.py
```
<img width="569" height="140" alt="image" src="https://github.com/user-attachments/assets/33d41e93-10e8-4d47-ad09-8ccfd6022801" />


**Step 00B:** Stream live bid/ask quotes from TastyTrade for S&P500 stocks. Filter by price ($30-400) and spread (<2%). Saves liquid stocks to `data/filter1_passed.json.`

```bash
python3 pipeline/00b_filter_price.py
```
<img width="566" height="224" alt="image" src="https://github.com/user-attachments/assets/021b8abe-f6ea-4241-a2c0-b80208b78a0d" />


**Step 00C:** Stream options chains from TastyTrade for output of `Step 00B`. Filter by expiration (15-45 days) and strike count (20+ strikes). Saves stocks with tradeable options to `data/filter2_passed.json.`

```bash
python3 pipeline/00c_filter_options.py
```
<img width="568" height="222" alt="image" src="https://github.com/user-attachments/assets/73a77f06-85cd-4281-b75c-92b96d558bd1" />


**Step 00D:** Stream ATM option strikes from TastyTrade chains. Streams IV data for strikes. Filter by IV range 15-80%. Saves 66 stocks to `data/filter3_passed.json.`

```bash
python3 pipeline/00d_filter_iv.py
```
<img width="568" height="223" alt="image" src="https://github.com/user-attachments/assets/b6a68d8d-bde6-4e09-9e34-e7452ce578c7" />


**Step 00E:** Load stocks from `Step 00D`.  Score by IV (40 pts), Strik Count (30 pts), expirations (20 pts), spread tightness (10 pts).  Rank by total score.  Select top 22 tickers.  Save to `data/stocks.py`

```bash
python3 pipeline/00e_select_22.py
```
<img width="570" height="284" alt="image" src="https://github.com/user-attachments/assets/471ae162-dd29-4327-a056-2c411870f10c" />


**Step 00F:** Fetch 3 days of news linked to output from `Step 00E` from Finnhub.io.  Collect up to 10 artilces per stock with headlines.  Save article count and headlines `data/finnhub_news.json.`

```bash
python3 pipeline/00f_get_news.py
```
<img width="649" height="851" alt="image" src="https://github.com/user-attachments/assets/c504a233-6113-4815-8791-395433722c4a" />


## ⚙️ Build Credit Spreads


**Step 01:** Stream bid/ask quotes from TastyTrade for output from `Step 00E`. Save mid-price, spread, and timestamp to `data/stock_prices.json.`

```bash
python3 pipeline/01_get_stock_prices.py
```
<img width="567" height="569" alt="image" src="https://github.com/user-attachments/assets/a75dca0b-77f4-4197-bfcf-91bc818f5912" />



**Step 02:** Stream option chain from TastyTrade for output from `Step 01`. Filters 0-45 DTE, 70-130% strikes. Save expiration dates, strikes, call/put symbols, and bid/ask to `data/chains.json.`


```bash
python3 pipeline/02_get_chains.py
```
<img width="570" height="521" alt="image" src="https://github.com/user-attachments/assets/43d670f4-4ca7-409c-843d-8170ceb23726" />


**Step 03:** Loads output from `Step 02` (strikes). For each strike checks call/put, bid/ask. Filters by mid >= $0.30 and spread <10%. Saves liquid strikes per expiration to `data/liquid_chains.json.`

```bash
python3 pipeline/03_check_liquidity.py
```
<img width="568" height="1004" alt="image" src="https://github.com/user-attachments/assets/ae27addb-0b3f-42bb-ab5f-6b2628e89e40" />


**Step 04:** Loads outpput from `Step 02`. Extracts all call/put symbols with bids > 0. Streams Greeks (IV/delta/theta/gamma/vega) from TastyTrade in 300-symbol batches for 8 seconds each. Embeds Greeks into chain structure at exact strike locations. Saves to `data/chains_with_greeks.json.`

```bash
python3 pipeline/04_get_greeks.py
```
<img width="571" height="539" alt="image" src="https://github.com/user-attachments/assets/332ae009-62c6-4613-b2df-8171016ebefc" />


**Step 5** Loads output from `Step 4` and `Step 01`. For each ticker/expiration (7-45 DTE), pairs strikes into Bull Put and Bear Call spreads. Filters short delta 15-35% (OTM probability). Calculates credit (short bid - long ask), max loss, ROI. Uses Black-Scholes formula with strike-specific IV to calculate PoP. Filters ROI 5-50%, PoP ≥60%. Saves spreads to `data/spreads.json.`

```bash
python3 pipeline/05_calculate_spreads.py
```
<img width="569" height="997" alt="image" src="https://github.com/user-attachments/assets/98eeafd1-f0cd-49f4-a433-b2879f1bda7e" />


**Step 6** Loads output from `Step 5`. Calculates score = (ROI × PoP) / 100 for each spread. Sorts by score descending. Keeps ONLY the highest-scoring spread per ticker (22 total). Categorizes as ENTER (PoP ≥70% + ROI ≥20%), WATCH (PoP ≥60% + ROI ≥30%), or SKIP. Saves to `ranked_spreads.json.`

```bash
python3 pipeline/06_rank_spreads.py
```
<img width="562" height="510" alt="image" src="https://github.com/user-attachments/assets/91484ae5-8e1e-42e7-b735-6241aa5bf516" />


**Step 7** Loads output from `Step 06`. Selects top 9 by rank. Adds sector mapping (XLK/XLF/XLV etc). Adds edge_reason from `Step 00E`. Formats into report table with rank, ticker, type, strikes, DTE, ROI, PoP, credit, max loss. Saves to `report_table.json.`

```bash
python3 pipeline/07_build_report.py
```
<img width="579" height="330" alt="image" src="https://github.com/user-attachments/assets/ef8928b3-2626-4e7f-84b6-e153fbcfb035" />


**Step 8** Loads output from `Step 07`, `Step 01`, and `Step 0F`. For each trade, calculates buffer from strike, extracts 3 news headlines, and 3 headline summaries. Sends to GPT-4 with 5W1H analysis framework (Who/What/When/Where/Why/How). GPT assigns heat score 1-10 (risk from news/catalysts), analyzes catalyst timing, recommends Trade/Wait/Skip. Saves to `top9_analysis.json.`

```bash
python3 pipeline/08_gpt_analysis.py
```
<img width="738" height="959" alt="image" src="https://github.com/user-attachments/assets/daf72a25-7746-48fa-a1ea-f2e6d4cba457" />


**Step 9**  Loads output from `Step 08`. Uses regex to parse GPT's structured output. Extracts ticker, type, strikes, DTE, ROI, PoP, heat score (1-10), and recommendation (Trade/Wait/Skip) for each trade. Prints formatted table showing all 9 trades. Saves to CSV file with timestamp for Excel.

```bash
python3 pipeline/09_format_trades.py
```
<img width="998" height="602" alt="image" src="https://github.com/user-attachments/assets/e39eaa48-7725-4443-93cb-01941329e74d" />


## 🤖 Automate 

**Step 10** Automate the pipeline

```bash
python3 pipeline/10_run_pipeline.py
```



