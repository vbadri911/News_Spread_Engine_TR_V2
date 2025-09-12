"""
GPT Caller #2: Validate trades with market context
Sends report table to GPT for final analysis
"""
import os
import json
import sys
from datetime import datetime
from openai import OpenAI

# Get API key
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ Missing OPENAI_API_KEY environment variable")
    sys.exit(1)

def load_report_table():
    """Load report table"""
    try:
        with open("report_table.json", "r") as f:
            data = json.load(f)
        return data["report_table"]
    except FileNotFoundError:
        print("❌ report_table.json not found - run build_report_table.py first")
        sys.exit(1)

def create_validation_prompt(entries):
    """Create prompt for GPT validation"""
    prompt = f"""
You are validating {len(entries)} credit spread trades with REAL market data.
Today's date: {datetime.now().strftime('%Y-%m-%d')}

TRADES TO VALIDATE:
"""
    
    for entry in entries:
        prompt += f"""
Ticker: {entry['ticker']} ({entry['sector']})
Type: {entry['type']} {entry['legs']}
DTE: {entry['dte']} | ROI: {entry['roi']} | PoP: {entry['pop']}
Edge: {entry['edge_reason']}
---"""
    
    prompt += """

FOR EACH TRADE, PROVIDE:

1. NEWS_EVENTS: Recent news and upcoming catalysts (50 words max)
2. ENTRY_DECISION: YES / NO / WAIT
3. WHY: Reasoning for decision (30 words max)
4. ENTRY_PLAN: Specific entry trigger if YES/WAIT
5. EXIT_PLAN: Target profit % and stop loss

OUTPUT FORMAT (JSON):
{
  "validations": [
    {
      "ticker": "AAPL",
      "news_events": "...",
      "entry_decision": "YES/NO/WAIT",
      "why": "...",
      "entry_plan": "...",
      "exit_plan": "..."
    }
  ]
}
"""
    return prompt

def call_gpt(prompt):
    """Call GPT for validation"""
    print("🤖 Calling GPT for trade validation...")
    
    client = OpenAI(api_key=API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a risk manager validating credit spread trades."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        print("✅ Got GPT validation")
        return content
        
    except Exception as e:
        print(f"❌ GPT API error: {e}")
        sys.exit(1)

def parse_validation(content):
    """Parse GPT validation response"""
    try:
        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        
        data = json.loads(json_str)
        return data["validations"]
        
    except Exception as e:
        print(f"❌ Failed to parse validation: {e}")
        return []

def merge_validation(entries, validations):
    """Merge validation with report entries"""
    # Create lookup
    val_lookup = {v["ticker"]: v for v in validations}
    
    final_trades = []
    for entry in entries:
        ticker = entry["ticker"]
        val = val_lookup.get(ticker, {})
        
        final_trade = {
            **entry,
            "news_events": val.get("news_events", ""),
            "entry_decision": val.get("entry_decision", "WAIT"),
            "why": val.get("why", ""),
            "entry_plan": val.get("entry_plan", ""),
            "exit_plan": val.get("exit_plan", "")
        }
        final_trades.append(final_trade)
    
    return final_trades

def save_final_trades(trades):
    """Save final validated trades"""
    # Count decisions
    yes_count = len([t for t in trades if t["entry_decision"] == "YES"])
    no_count = len([t for t in trades if t["entry_decision"] == "NO"])
    wait_count = len([t for t in trades if t["entry_decision"] == "WAIT"])
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(trades),
            "yes": yes_count,
            "no": no_count,
            "wait": wait_count
        },
        "final_trades": trades
    }
    
    with open("final_trades.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Validation Results:")
    print(f"   ✅ YES: {yes_count}")
    print(f"   ❌ NO: {no_count}")
    print(f"   ⏳ WAIT: {wait_count}")
    
    # Show YES trades
    yes_trades = [t for t in trades if t["entry_decision"] == "YES"]
    if yes_trades:
        print(f"\n🎯 TRADES TO ENTER NOW:")
        for trade in yes_trades[:5]:
            print(f"   {trade['ticker']} {trade['type']} {trade['legs']}")
            print(f"      ROI: {trade['roi']} | PoP: {trade['pop']}")
            print(f"      Why: {trade['why']}")

def main():
    """Main execution"""
    print("="*60)
    print("STEP 10: GPT Trade Validation")
    print("="*60)
    
    # Load report
    entries = load_report_table()
    
    # Create validation prompt
    prompt = create_validation_prompt(entries)
    
    # Call GPT
    response = call_gpt(prompt)
    
    # Parse validation
    validations = parse_validation(response)
    
    # Merge with entries
    final_trades = merge_validation(entries, validations)
    
    # Save final trades
    save_final_trades(final_trades)
    
    print("✅ Step 10 complete: final_trades.json created")

if __name__ == "__main__":
    main()
