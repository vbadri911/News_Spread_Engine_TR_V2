"""
GPT Risk Analysis - Show TOP 9 TRADES
"""
import os
import json
import sys
from datetime import datetime
from openai import OpenAI

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY

if not OPENAI_API_KEY:
    print("❌ Missing OPENAI_API_KEY")
    sys.exit(1)

def load_comprehensive_data():
    """Load ALL data we've collected"""
    data = {}
    
    with open("data/report_table.json", "r") as f:
        data["trades"] = json.load(f)["report_table"]
    
    with open("data/stock_prices.json", "r") as f:
        data["prices"] = json.load(f)["prices"]
    
    with open("data/greeks.json", "r") as f:
        greeks = json.load(f)
        data["greeks_coverage"] = greeks.get("overall_coverage", 0)
    
    with open("data/ranked_spreads.json", "r") as f:
        ranked = json.load(f)
        data["ranking_summary"] = ranked["summary"]
    
    # Enhance trades with metrics
    for trade in data["trades"]:
        ticker = trade["ticker"]
        
        if ticker in data["prices"]:
            trade["current_price"] = data["prices"][ticker]["mid"]
            trade["bid_ask_spread"] = data["prices"][ticker]["spread"]
        
        strikes = trade['legs'].replace('$', '').split('/')
        trade["short_strike"] = float(strikes[0])
        trade["long_strike"] = float(strikes[1])
        
        if "current_price" in trade:
            current = trade["current_price"]
            if "Put" in trade['type']:
                trade["buffer_pct"] = ((current - trade["short_strike"]) / current * 100)
            else:
                trade["buffer_pct"] = ((trade["short_strike"] - current) / current * 100)
    
    return data

def create_top9_prompt(data):
    """Create prompt focused on finding TOP 9 trades"""
    prompt = f"""Analyze these credit spreads and identify the TOP 9 TRADES ranked by risk-adjusted return.

RANKING CRITERIA (in order of importance):
1. Data Quality - No suspicious ROI >100% unless verified
2. Risk/Reward Ratio - (ROI × PoP) / 100 = Score
3. Buffer from Current Price - Higher buffer = safer
4. Liquidity - Tighter bid/ask = better fills
5. Diversification - Mix of tickers and strategies

TRADES TO ANALYZE:
"""
    
    for i, trade in enumerate(data["trades"], 1):
        buffer = trade.get("buffer_pct", 0)
        current = trade.get("current_price", 0)
        roi = float(trade['roi'].rstrip('%'))
        pop = float(trade['pop'].rstrip('%'))
        score = (roi * pop) / 100
        
        prompt += f"""
Trade {i}: {trade['ticker']} {trade['type']} {trade['legs']}
  Current: ${current:.2f} | Buffer: {buffer:.1f}% | Score: {score:.1f}
  ROI: {trade['roi']} | PoP: {trade['pop']} | DTE: {trade['dte']}
  Credit: {trade['net_credit']} | Max Loss: {trade['max_loss']}
"""

    prompt += """

PROVIDE YOUR TOP 9 TRADES:

=== TOP 9 TRADES (RANKED) ===

#1. [TICKER] [TYPE] [STRIKES]
    Score: [X] | ROI: [X%] | PoP: [X%] | Buffer: [X%]
    WHY: [Specific reason this is #1]
    RISK: [Main risk to watch]

#2. [TICKER] [TYPE] [STRIKES]
    Score: [X] | ROI: [X%] | PoP: [X%] | Buffer: [X%]
    WHY: [Different reason this is #2]
    RISK: [Specific risk]

[Continue through #9...]

=== EXECUTION STRATEGY ===
[How to enter these 9 trades - order, sizing, timing]

=== PORTFOLIO NOTES ===
[Concentration risks, correlations, total capital needed]

Be specific. Rank by best risk/reward. Include actual numbers.
"""
    return prompt

def display_top9(response, trades):
    """Display the top 9 trades nicely"""
    print("\n" + "="*80)
    print("🏆 TOP 9 TRADES FROM GPT ANALYSIS")
    print("="*80)
    
    if not response:
        print("No GPT response available")
        return
    
    # Find the TOP 9 section
    if "TOP 9 TRADES" in response:
        top_section_start = response.find("TOP 9 TRADES")
        top_section_end = response.find("=== EXECUTION", top_section_start)
        
        if top_section_end == -1:
            top_section = response[top_section_start:]
        else:
            top_section = response[top_section_start:top_section_end]
        
        # Print the top 9
        lines = top_section.split('\n')
        current_trade = 0
        
        for line in lines:
            if line.strip():
                if line.strip()[0].isdigit() and '.' in line:
                    current_trade += 1
                    print(f"\n{line}")
                elif current_trade > 0 and current_trade <= 9:
                    print(f"  {line.strip()}")
    
    # Show execution strategy
    if "EXECUTION STRATEGY" in response:
        exec_start = response.find("EXECUTION STRATEGY")
        exec_end = response.find("===", exec_start + 20)
        
        if exec_end == -1:
            exec_section = response[exec_start:exec_start + 500]
        else:
            exec_section = response[exec_start:exec_end]
        
        print("\n" + "="*80)
        print("📋 EXECUTION STRATEGY")
        print("="*80)
        print(exec_section.replace("=== EXECUTION STRATEGY ===", "").strip())

def main():
    print("="*60)
    print("TOP 9 TRADES ANALYSIS")
    print("="*60)
    
    # Load data
    print("📊 Loading data...")
    data = load_comprehensive_data()
    print(f"   ✓ {len(data['trades'])} trades loaded")
    
    # Create prompt
    prompt = create_top9_prompt(data)
    
    # Call GPT
    print("\n🤖 Getting TOP 9 trades from GPT...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are ranking credit spreads by risk-adjusted return. Focus on finding the 9 best trades considering ROI, PoP, buffer, and data quality. Be specific with numbers."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        
        gpt_response = response.choices[0].message.content
        print("✅ Analysis complete")
        
        # Display top 9
        display_top9(gpt_response, data["trades"])
        
        # Save full response
        with open("data/top9_analysis.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "analysis": gpt_response,
                "trade_count": len(data["trades"])
            }, f, indent=2)
        
        print("\n✅ Full analysis saved to top9_analysis.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
