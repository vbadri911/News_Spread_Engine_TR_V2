# 📘 AI Credit Spread Finder - README

**Purpose:** Unearth the 9 best credit spread trades from 500+ S&P 500 tickers in minutes—backed by math and market smarts.

**What to Know:** Pinpoint exact trades to place today with high-probability edges (70%+ PoP) and news-driven insights.

**What to Do:** Execute confident credit spreads with copy-paste TOS commands, guided by real-time visuals.

**What to Feel:** Empowered—because your trades are fueled by data, not guesswork or shaky scanner outputs.

---

### 🚀 What’s in It for You?

- **Save 3 Hours Daily:** Ditch manual hunting—let the pipeline do the heavy lifting.
- **Win 70% of the Time:** Math-proven Probability of Profit (PoP) with a conservative twist.
- **Seize Volatility:** Never miss high-IV opportunities with GPT-powered risk analysis.
- **Outsmart Scanners:** Say goodbye to junk data—our heat scores and sector filters beat the competition.

---

# 🔎 AI Credit Spread Finder - PIPELINE

## 🛠 Build Your Portfolio

This automated pipeline transforms raw market data into actionable trade ideas, ending with a dynamic dashboard to explore and execute.

### Step-by-Step Breakdown

**Step 00A: Get S&P 500**

- Download a CSV of S&P 500 companies from GitHub.
- Extract 503 ticker symbols and save to `data/sp500.json`.
- `python3 pipeline/00a_get_sp500.py`

  ![S&P 500 Tickers](https://github.com/user-attachments/assets/33d41e93-10e8-4d47-ad09-8ccfd6022801)

**Step 00B: Filter by Price**

- Stream live bid/ask quotes from TastyTrade for S&P 500 stocks.
- Filter by price ($30-400) and spread (&lt;2%).
- Save liquid stocks to `data/filter1_passed.json`.
- `python3 pipeline/00b_filter_price.py`

  ![Price Filter](https://github.com/user-attachments/assets/021b8abe-f6ea-4241-a2c0-b80208b78a0d)

**Step 00C: Filter Options**

- Stream options chains from TastyTrade for Step 00B output.
- Filter by expiration (15-45 days) and strike count (20+ strikes).
- Save tradeable options to `data/filter2_passed.json`.
- `python3 pipeline/00c_filter_options.py`

  ![Options Filter](https://github.com/user-attachments/assets/021b8abe-f6ea-4241-a2c0-b80208b78a0d)*(Truncated image ref)*

**Step 00D: Filter by IV**

- Analyze implied volatility (IV) from options chains.
- Filter for IV range (15-80%) to target high-opportunity stocks.
- Save to `data/filter3_passed.json`.
- `python3 pipeline/00d_filter_iv.py`

**Step 00E: Select Top 22**

- Rank filtered stocks by liquidity and volatility.
- Select top 22 for detailed analysis.
- Save to `data/top22.json`.
- `python3 pipeline/00e_select_22.py`

**Step 00F: Get News**

- Fetch latest news headlines for top 22 stocks via API.
- Save to `data/news.json`.
- `python3 pipeline/00f_get_news.py`

**Step 00G: GPT Sentiment Filter**

- Analyze news with GPT-4 using 5W1H (Who/What/When/Where/Why/How).
- Filter stocks with positive/volatile sentiment.
- Save to `data/sentiment_filtered.json`.
- `python3 pipeline/00g_gpt_sentiment_filter.py`

**Step 01: Get Prices**

- Fetch real-time stock prices for filtered stocks.
- Save to `data/prices.json`.
- `python3 pipeline/01_get_prices.py`

**Step 02: Get Chains**

- Pull full options chains from TastyTrade for top stocks.
- Save to `data/chains.json`.
- `python3 pipeline/02_get_chains.py`

**Step 03: Check Liquidity**

- Filter chains for options with sufficient volume/open interest.
- Save to `data/liquid_chains.json`.
- `python3 pipeline/03_check_liquidity.py`

**Step 04: Get Greeks**

- Calculate option Greeks (Delta, IV, Theta) for liquid chains.
- Save to `data/chains_with_greeks.json`.
- `python3 pipeline/04_get_greeks.py`

**Step 05: Calculate Spreads**

- Use Black-Scholes with dynamic risk-free rate (r) to compute credit spreads.
- Filter for 15-45 DTE, 20-40% width, conservative PoP.
- Save to `data/spreads.json`.
- `python3 pipeline/05_calculate_spreads.py`

**Step 06: Rank Spreads**

- Rank spreads by PoP, ROI, and liquidity.
- Save ranked data to `data/ranked_spreads.json`.
- `python3 pipeline/06_rank_spreads.py`

**Step 07: Build Report**

- Load ranked spreads, add sector mapping (XLK/XLF/XLV), edge reasons.
- Format into a report table (rank, ticker, type, strikes, DTE, ROI, PoP, credit, max loss).
- Save to `data/report_table.json`.
- `python3 pipeline/07_build_report.py`

  ![Report Table](https://github.com/user-attachments/assets/ef8928b3-2626-4e7f-84b6-e153fbcfb035)

**Step 08: GPT Analysis**

- Analyze top spreads with GPT-4 using 5W1H framework.
- Extract buffer, news headlines/summaries, heat score (1-10), and Trade/Wait/Skip recs.
- Save to `top9_analysis.json`.
- `python3 pipeline/08_gpt_analysis.py`

  ![GPT Analysis](https://github.com/user-attachments/assets/daf72a25-7746-48fa-a1ea-f2e6d4cba457)

**Step 09: Format Trades**

- Parse GPT output with regex for ticker, type, strikes, DTE, ROI, PoP, heat, recs.
- Print formatted table of top 9 trades.
- Save to timestamped CSV (e.g., `reports/top9_trades_20251017_0657.csv`).
- `python3 pipeline/09_format_trades.py`

  ![Formatted Trades](https://github.com/user-attachments/assets/e39eaa48-7725-4443-93cb-01941329e74d)

## 🤖 Automate the Pipeline

**Step 10: Run Full Pipeline**

- Automate all steps (00A-09) with a single command.
- Outputs JSONs, CSVs, and prepares data for visualization.
- `python3 run_full_pipeline.py`

## 🎨 Visualize Your Trades

**Step 11: Launch Trade Command Center**

- **New Feature!** Explore your top 9 trades interactively with the **Trade Command Center** dashboard.
- **What You Get:**
  - **Top 9 Table:** Sortable, filterable list with copy-to-clipboard TOS commands (e.g., `SELL -1 VERTICAL NVDA 100 (Weeklys) 24 OCT 25 187.5/190 CALL @0.74 LMT`).
  - **PoP Distribution:** Histogram showing safety (70%+ PoP) by trade type (Bull Put vs Bear Call).
  - **ROI vs PoP Map:** Scatter plot with heat (risk) and sector insights—hover for details.
  - **Filters:** Tweak by sector (XLK, XLV), DTE (7-45), and PoP (60-100%) to refine trades.
- **How to Use:**
  1. Run the pipeline: `python3 run_full_pipeline.py`
  2. Launch the dashboard: `streamlit run utils/viz.py`
  3. Browse at `http://localhost:8501`, copy TOS commands, and trade with confidence!
- **Why It Rocks:** Real-time insights beat static PNGs—interact, filter, and copy trades in seconds.

## 🌟 Next-Level Trading

- **Coming Soon:** Real-time price updates, AI trade recommendations, and multi-user dashboards.
- **Get Involved:** Share feedback via `data/feedback.json` in the dashboard—shape the future!

**Note:** Requires Python 3.12, TastyTrade API key, and packages (install via `pip install streamlit streamlit-aggrid pyperclip plotly pandas kaleido`).

Happy Trading! 📈