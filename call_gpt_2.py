"""
GPT Caller #2: Real market analysis with trade validation
"""
import os
import json
import sys
from datetime import datetime
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ Missing OPENAI_API_KEY")
    sys.exit(1)

def load_report_table():
    try:
        with open("report_table.json", "r") as f:
            data = json.load(f)
        return data["report_table"]
    except FileNotFoundError:
        print("❌ report_table.json not found")
        sys.exit(1)

def create_analysis_prompt(entries):
    prompt = f"""You are an aggressive options trader analyzing credit spreads with REAL market data.
Today: {datetime.now().strftime('%B %d, %Y')}

TRADING CRITERIA:
- Minimum PoP: 66%
- Minimum ROI: 33%
- Maximum ROI: 100% (anything higher is likely bad data)
- Timeframe: 15-45 DTE optimal

TRADES TO ANALYZE:
"""
    
    for i, entry in enumerate(entries, 1):
        prompt += f"""
{i}. {entry['ticker']} {entry['type']} {entry['legs']}
   ROI: {entry['roi']} | PoP: {entry['pop']} | DTE: {entry['dte']}
   Credit: {entry['net_credit']} | Max Loss: {entry['max_loss']}
"""
    
    prompt += """

FOR EACH TRADE, ANALYZE:
1. Is the ROI realistic? (Credit spreads rarely exceed 80% ROI)
2. Does the PoP align with current market conditions?
3. Any upcoming events (earnings, Fed, economic data)?
4. Technical levels - is the short strike at support/resistance?
5. Market sentiment for this ticker

RESPOND WITH JSON:
{
  "market_context": "Brief market overview",
  "trades": [
    {
      "ticker": "SYMBOL",
      "decision": "YES/NO/WAIT",
      "confidence": 1-10,
      "reasoning": "Why this decision",
      "risks": "Main risk to watch",
      "entry_trigger": "Specific entry condition",
      "exit_plan": "Profit target and stop loss"
    }
  ],
  "best_trade": "TICKER and why it's the best"
}

Be aggressive but realistic. Flag any suspicious data (ROI >100%, etc).
"""
    return prompt

def call_gpt(prompt):
    print("🤖 Calling GPT for market analysis...")
    
    client = OpenAI(api_key=API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert options trader who analyzes credit spreads."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temp for more consistent analysis
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        print("✅ Got GPT analysis")
        return content
        
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return None

def parse_gpt_response(content):
    try:
        # Find JSON in response
        start = content.find("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        return json.loads(json_str)
    except:
        print("⚠️ Could not parse GPT response, using fallback")
        return None

def merge_analysis(entries, gpt_data):
    """Merge GPT analysis with trades"""
    final_trades = []
    
    if gpt_data and "trades" in gpt_data:
        # Map GPT analysis to trades
        gpt_by_ticker = {t["ticker"]: t for t in gpt_data["trades"]}
        
        for entry in entries:
            ticker = entry["ticker"]
            gpt_trade = gpt_by_ticker.get(ticker, {})
            
            final_trade = {
                **entry,
                "entry_decision": gpt_trade.get("decision", "WAIT"),
                "confidence": gpt_trade.get("confidence", 5),
                "why": gpt_trade.get("reasoning", "Pending analysis"),
                "risks": gpt_trade.get("risks", "Standard market risk"),
                "entry_plan": gpt_trade.get("entry_trigger", "Enter at mid-price"),
                "exit_plan": gpt_trade.get("exit_plan", "25% profit, 2x stop loss"),
                "news_events": gpt_data.get("market_context", "Market conditions normal")
            }
            final_trades.append(final_trade)
    else:
        # Fallback to aggressive criteria
        print("⚠️ Using fallback validation")
        for entry in entries:
            roi = float(entry['roi'].rstrip('%'))
            pop = float(entry['pop'].rstrip('%'))
            
            if roi >= 33 and pop >= 66 and roi <= 100:
                decision = "YES"
                why = f"Meets criteria: {roi:.0f}% ROI, {pop:.0f}% PoP"
            else:
                decision = "NO"
                why = f"Outside criteria"
            
            final_trade = {
                **entry,
                "entry_decision": decision,
                "confidence": 7 if decision == "YES" else 3,
                "why": why,
                "risks": "Standard market risk",
                "entry_plan": "Enter at mid-price or better",
                "exit_plan": "25% profit target, 2x credit stop loss",
                "news_events": "Market analysis pending"
            }
            final_trades.append(final_trade)
    
    return final_trades

def save_final_trades(trades):
    yes = len([t for t in trades if t["entry_decision"] == "YES"])
    no = len([t for t in trades if t["entry_decision"] == "NO"])
    wait = len([t for t in trades if t["entry_decision"] == "WAIT"])
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {"total": len(trades), "yes": yes, "no": no, "wait": wait},
        "final_trades": trades
    }
    
    with open("final_trades.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results: {yes} YES | {wait} WAIT | {no} NO")
    
    # Show YES trades
    for t in trades:
        if t["entry_decision"] == "YES":
            conf = t.get("confidence", "?")
            print(f"   ✅ {t['ticker']} {t['type']} (Confidence: {conf}/10)")
            print(f"      {t.get('why', '')}")

def main():
    print("="*60)
    print("STEP 10: GPT Market Analysis")
    print("="*60)
    
    entries = load_report_table()
    prompt = create_analysis_prompt(entries)
    
    # Call GPT
    response = call_gpt(prompt)
    
    if response:
        # Parse GPT analysis
        gpt_data = parse_gpt_response(response)
        
        if gpt_data and "best_trade" in gpt_data:
            print(f"\n🏆 Best Trade: {gpt_data['best_trade']}")
    else:
        gpt_data = None
    
    # Merge and save
    final_trades = merge_analysis(entries, gpt_data)
    save_final_trades(final_trades)
    
    print("✅ Step 10 complete: final_trades.json created")

if __name__ == "__main__":
    main()
