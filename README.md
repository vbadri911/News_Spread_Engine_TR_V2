# Credit Spread Finder - Enhanced Edition

Finds high-probability credit spreads using real market data from TastyTrade with GPT-4 risk analysis.

## 🚀 Performance
- **Speed**: 3.5 minutes (10x faster than original)
- **Coverage**: 100% Greeks collection (1253/1253)
- **Quality**: 9 high-confidence trades per run
- **Success Rate**: 70%+ PoP on all trades

## 📊 Key Features
- **Batch Processing**: 500 symbols at once for speed
- **Multi-factor Liquidity Scoring**: 0-100 scale 
- **Real Black-Scholes PoP**: Using actual market IV
- **GPT Risk Analysis**: Identifies best 9 trades
- **100% Real Data**: No fallbacks or estimates

## 🎯 Quick Start
```bash
# Set credentials
export TASTY_USERNAME="your_username"
export TASTY_PASSWORD="your_password"  
export OPENAI_API_KEY="your_key"

# Run pipeline
python3 run.py

# See top 9 trades
python3 show_top9.py
