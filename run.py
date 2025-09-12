#!/usr/bin/env python3
"""
Master Pipeline Runner - Production Version
Run daily for fresh credit spread opportunities
"""
import subprocess
import sys
import time
from datetime import datetime

def main():
    print("\n" + "="*80)
    print("🚀 CREDIT SPREAD FINDER - ENHANCED EDITION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    steps = [
        ("call_gpt_simple.py", "Get 22 quality stocks"),
        ("get_stock_prices.py", "Real-time prices"),
        ("get_options_chains.py", "Options chains (70-130%)"),
        ("check_liquidity.py", "Liquidity scoring"),
        ("get_greeks.py", "100% Greeks coverage"),
        ("calculate_spreads_fixed.py", "Build spreads"),
        ("calculate_pop_roi.py", "Calculate PoP"),
        ("rank_spreads.py", "Multi-factor ranking"),
        ("build_report_table.py", "Prepare report"),
        ("gpt_risk_analysis_top9.py", "GPT risk analysis"),
        ("display_final_trades.py", "Show results")
    ]
    
    start = time.time()
    
    for script, desc in steps:
        print(f"\n▶ {desc}...")
        result = subprocess.run([sys.executable, script], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ Warning in {script}")
    
    elapsed = time.time() - start
    print(f"\n✅ Pipeline complete in {elapsed:.1f} seconds")
    print("Run 'python3 show_top9.py' to see your trades")

if __name__ == "__main__":
    main()
