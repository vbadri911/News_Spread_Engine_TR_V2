"""
Simple GPT Caller - Just read prompt.txt and call GPT
"""
import os
from datetime import datetime
from openai import OpenAI

# Get API key
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ Set: export OPENAI_API_KEY='your-key'")
    exit(1)

# Read prompt
with open("prompt.txt", "r") as f:
    prompt = f.read()

# Replace TODAY with actual date
prompt = prompt.replace("TODAY", datetime.now().strftime("%Y-%m-%d"))

print("🤖 Calling GPT...")

# Call GPT
client = OpenAI(api_key=API_KEY)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a stock analyst. Output Python code only. No explanations."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.5,
    max_tokens=1500
)

content = response.choices[0].message.content
print("✅ Got response")

# Save raw response
with open("gpt_response.txt", "w") as f:
    f.write(content)

# Try to parse
try:
    exec_globals = {}
    exec(content, exec_globals)
    
    stocks = exec_globals.get("STOCKS", [])
    reasons = exec_globals.get("EDGE_REASON", {})
    
    # Save to stocks.py
    with open("data/stocks.py", "w") as f:
        f.write(f"# Generated {datetime.now()}\n")
        f.write(f"STOCKS = {stocks}\n\n")
        f.write(f"EDGE_REASON = {reasons}\n")
    
    print(f"✅ Saved {len(stocks)} stocks to data/stocks.py")
    
except Exception as e:
    print(f"❌ Parse error: {e}")
    print("Check gpt_response.txt for raw output")

