# Credit Spread Finder Pipeline

Automated options trading pipeline using TastyTrade API for real-time market data.

## Features
- 10-step automated pipeline for credit spread discovery
- Real-time Greeks streaming (100% coverage achieved)
- Analyzes 6,800+ potential spreads per run
- Filters to top 9 trades based on ROI and probability
- Complete dashboard visualization

## Pipeline Steps
1. GPT stock selection (22 stocks across sectors)
2. Real-time stock prices via TastyTrade
3. Options chains collection (85%+ quote coverage)
4. Liquidity filtering
5. Greeks collection (IV, delta, theta, gamma, vega)
6. Credit spread construction (Bull Puts & Bear Calls)
7. Probability calculations using Black-Scholes
8. Multi-factor ranking
9. Report generation
10. GPT risk analysis

## Performance
- Runtime: ~15 minutes
- Spreads analyzed: 6,800+
- Tradeable opportunities: 300-400
- Average ROI: 13% (realistic)
- Average IV: 31% (market conditions)

## Setup
1. Copy `config.py.template` to `config.py`
2. Add your TastyTrade credentials
3. Add your OpenAI API key
4. Run: `python3 run_enhanced.py`

## Known Issues
- PoP calculations showing 100% (needs Black-Scholes fix)
- Quote collection at 85% (can improve to 95%+)
