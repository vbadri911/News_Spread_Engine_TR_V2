"""
GPT Detailed Analysis - Force specific, unique responses for each trade
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

def create_detailed_prompt(entries):
    """Create prompt that demands specific analysis"""
    prompt = f"""You are analyzing credit spreads on {datetime.now().strftime('%B %d, %Y')}.

CRITICAL REQUIREMENTS:
- Each trade MUST have DIFFERENT and SPECIFIC analysis
- Reference actual price levels and technical indicators
- Mention specific upcoming events (earnings dates, Fed meetings, product launches)
- NO generic responses - each analysis must be unique
- If you don't know specific details, research or state uncertainty

TRADES TO ANALYZE:
"""
    
    for i, entry in enumerate(entries[:10], 1):  # Limit to 10 for quality
        prompt += f"""
Trade #{i}:
Ticker: {entry['ticker']}
Type: {entry['type']} 
Strikes: {entry['legs']}
ROI: {entry['roi']} | PoP: {entry['pop']}
Credit: {entry['net_credit']} | DTE: {entry['dte']}
Current Stock Price: ~${entry.get('stock_price', 'Unknown')}
"""

    prompt += """

REQUIRED ANALYSIS FOR EACH TRADE (BE SPECIFIC AND DIFFERENT):

1. TECHNICAL ANALYSIS: Where EXACTLY is the short strike relative to:
   - Moving averages (specify which ones)
   - Recent support/resistance (give exact price levels)
   - Volume profile nodes
   
2. FUNDAMENTAL CATALYSTS: What SPECIFIC events affect this trade:
   - Exact earnings date if within DTE
   - Product announcements
   - Sector-specific news
   
3. RISK ASSESSMENT: What could go wrong SPECIFICALLY:
   - Key level that would trigger exit
   - Specific scenario that breaks the trade
   
4. DECISION with reasoning unique to THIS trade

FORMAT YOUR RESPONSE AS:

Trade #1 - [TICKER]:
Technical: [Specific levels and indicators]
Catalyst: [Actual upcoming events with dates]
Risk: [Specific price level or event that would invalidate]
Decision: YES/NO/WAIT
Confidence: X/10
Entry: [Specific entry conditions]

Trade #2 - [TICKER]:
[DIFFERENT analysis - no copy/paste]

BE SPECIFIC. NO GENERIC ANSWERS. Each trade gets unique analysis.
"""
    return prompt

def call_gpt_with_retry(prompt, temperature=0.7):
    """Call GPT with higher temperature for variety"""
    print("🤖 Calling GPT for detailed analysis...")
    
    client = OpenAI(api_key=API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional options analyst. Provide specific, detailed, DIFFERENT analysis for each trade. No generic responses."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,  # Higher for more variety
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return None

def parse_detailed_response(content, entries):
    """Parse the detailed response"""
    trades = []
    
    # Split by "Trade #"
    sections = content.split("Trade #")[1:]  # Skip before first trade
    
    for i, section in enumerate(sections):
        if i >= len(entries):
            break
            
        entry = entries[i]
        
        # Extract decision
        if "Decision: YES" in section:
            decision = "YES"
        elif "Decision: NO" in section:
            decision = "NO"
        else:
            decision = "WAIT"
        
        # Extract confidence
        confidence = 5
        if "Confidence:" in section:
            try:
                conf_line = [l for l in section.split('\n') if "Confidence:" in l][0]
                confidence = int(conf_line.split("/")[0].split(":")[-1].strip())
            except:
                pass
        
        # Extract unique details
        lines = section.split('\n')
        technical = next((l for l in lines if "Technical:" in l), "Analysis pending")
        catalyst = next((l for l in lines if "Catalyst:" in l), "No specific catalyst")
        risk = next((l for l in lines if "Risk:" in l), "Standard risk")
        entry_plan = next((l for l in lines if "Entry:" in l), "Enter at mid")
        
        trade = {
            **entry,
            "entry_decision": decision,
            "confidence": confidence,
            "technical_analysis": technical,
            "catalyst": catalyst,
            "risk_scenario": risk,
            "entry_plan": entry_plan,
            "why": f"{technical} | {catalyst}",
            "exit_plan": "25% profit target, 2x stop loss"
        }
        trades.append(trade)
    
    return trades

def main():
    print("="*60)
    print("STEP 10: GPT Detailed Market Analysis")
    print("="*60)
    
    # Load trades
    with open("report_table.json", "r") as f:
        entries = json.load(f)["report_table"]
    
    # Create detailed prompt
    prompt = create_detailed_prompt(entries)
    
    # Call GPT
    response = call_gpt_with_retry(prompt)
    
    if response:
        print("✅ Got detailed analysis")
        print("\n" + "="*40)
        print("GPT ANALYSIS:")
        print("="*40)
        print(response[:1500] + "..." if len(response) > 1500 else response)
        
        # Parse response
        trades = parse_detailed_response(response, entries)
    else:
        print("⚠️ Using fallback validation")
        trades = []
        for entry in entries:
            roi = float(entry['roi'].rstrip('%'))
            pop = float(entry['pop'].rstrip('%'))
            
            trade = {
                **entry,
                "entry_decision": "YES" if (roi >= 33 and pop >= 66 and roi <= 100) else "NO",
                "confidence": 7 if (roi >= 33 and pop >= 66) else 3,
                "why": f"ROI: {roi}%, PoP: {pop}%",
                "entry_plan": "Enter at mid-price",
                "exit_plan": "25% profit, 2x stop"
            }
            trades.append(trade)
    
    # Save results
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
    
    # Show unique YES decisions
    for t in trades:
        if t["entry_decision"] == "YES":
            print(f"\n✅ {t['ticker']} {t['type']} {t['legs']}")
            print(f"   Confidence: {t.get('confidence', '?')}/10")
            print(f"   {t.get('technical_analysis', '')[:100]}")

if __name__ == "__main__":
    main()
