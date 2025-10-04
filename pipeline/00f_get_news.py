"""
Step 1B: Get Finnhub News
Collects news for stocks picked in Step 1
"""
import json
import sys
import os
from datetime import datetime, timedelta
import finnhub

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FINNHUB_API_KEY

def get_news_for_stocks():
    """Get 3 days of news for selected stocks"""
    print("="*60)
    print("STEP 1B: Get Finnhub News (VERBOSE)")
    print("="*60)
    
    # Load stocks from Step 1
    from data.stocks import STOCKS
    
    # Date range
    today = datetime.now().date()
    three_days_ago = today - timedelta(days=3)
    
    print(f"\n📰 Fetching news for {len(STOCKS)} stocks")
    print(f"📅 Date range: {three_days_ago} to {today}\n")
    
    client = finnhub.Client(api_key=FINNHUB_API_KEY)
    
    all_news = {}
    
    for i, ticker in enumerate(STOCKS, 1):
        print(f"[{i}/{len(STOCKS)}] {ticker}...", end=" ")
        
        try:
            news = client.company_news(
                ticker, 
                _from=str(three_days_ago), 
                to=str(today)
            )
            
            if news:
                all_news[ticker] = {
                    'ticker': ticker,
                    'article_count': len(news),
                    'articles': news[:10]
                }
                print(f"✅ {len(news)} articles")
                
                if news:
                    print(f"      → {news[0]['headline'][:80]}...")
            else:
                print(f"⚠️  No news")
                all_news[ticker] = {
                    'ticker': ticker,
                    'article_count': 0,
                    'articles': []
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_news[ticker] = {
                'ticker': ticker,
                'article_count': 0,
                'articles': [],
                'error': str(e)
            }
    
    # Save
    output = {
        'timestamp': datetime.now().isoformat(),
        'date_range': {
            'from': str(three_days_ago),
            'to': str(today)
        },
        'total_stocks': len(STOCKS),
        'stocks_with_news': len([s for s in all_news.values() if s['article_count'] > 0]),
        'news_data': all_news
    }
    
    with open('data/finnhub_news.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ News collection complete!")
    print(f"   Total stocks: {len(STOCKS)}")
    print(f"   With news: {output['stocks_with_news']}")
    print(f"   Total articles: {sum(s['article_count'] for s in all_news.values())}")

if __name__ == "__main__":
    get_news_for_stocks()
