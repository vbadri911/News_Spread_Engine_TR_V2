#!/usr/bin/env python3
import json
from datetime import datetime

with open('data/report_table.json', 'r') as f:
    data = json.load(f)

trades = data['report_table']

print("\n" + "="*80)
print("TOP 9 CREDIT SPREADS - READY TO TRADE")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*80)

for i, trade in enumerate(trades[:9], 1):
    print(f"\n{i}. {trade['ticker']} {trade['type']} {trade['legs']}")
    print(f"   Exp: {trade['exp_date']} ({trade['dte']} DTE)")
    print(f"   ROI: {trade['roi']} | PoP: {trade['pop']}")
    print(f"   Credit: {trade['net_credit']} | Max Loss: {trade['max_loss']}")
