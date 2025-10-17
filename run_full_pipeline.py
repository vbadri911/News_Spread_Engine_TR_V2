#!/usr/bin/env python3
"""
Master Pipeline Runner - Complete Data Flow
"""
import subprocess
import sys
import time
from datetime import datetime

def run_step(step_name, script_path, description):
    print("\n" + "="*80)
    print(f"▶ {step_name}: {description}")
    print("="*80)
    
    start = time.time()
    result = subprocess.run([sys.executable, script_path], text=True)
    elapsed = time.time() - start
    
    if result.returncode == 0:
        print(f"\n✅ {step_name} complete ({elapsed:.1f}s)")
        return True
    else:
        print(f"\n❌ {step_name} FAILED ({elapsed:.1f}s)")
        return False

def main():
    print("\n" + "█"*80)
    print("█" + "  CREDIT SPREAD FINDER - FULL PIPELINE".center(78) + "█")
    print("█" + f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "█")
    print("█"*80)
    
    start = time.time()
    
    steps = [
        ("00a", "pipeline/00a_get_sp500.py", "Get S&P 500"),
        ("00b", "pipeline/00b_filter_price.py", "Filter Price"),
        ("00c", "pipeline/00c_filter_options.py", "Filter Options"),
        ("00d", "pipeline/00d_filter_iv.py", "Filter IV"),
        ("00e", "pipeline/00e_select_22.py", "Select 22"),
        ("00f", "pipeline/00f_get_news.py", "Get News"),
        ("00g", "pipeline/00g_gpt_sentiment_filter.py", "GPT Sentiment"),
        ("01", "pipeline/01_get_prices.py", "Get Prices"),
        ("02", "pipeline/02_get_chains.py", "Get Chains"),
        ("03", "pipeline/03_check_liquidity.py", "Check Liquidity"),
        ("04", "pipeline/04_get_greeks.py", "Get Greeks"),
        ("05", "pipeline/05_calculate_spreads.py", "Calculate Spreads"),
        ("06", "pipeline/06_rank_spreads.py", "Rank Spreads"),
        ("07", "pipeline/07_build_report.py", "Build Report"),
        ("08", "pipeline/08_gpt_analysis.py", "GPT Analysis"),
        ("09", "pipeline/09_format_trades.py", "Format Trades"),
    ]
    
    completed = 0
    for step_name, script, desc in steps:
        if run_step(step_name, script, desc):
            completed += 1
            time.sleep(0.3)
        else:
            break
    
    elapsed = time.time() - start
    print("\n" + "="*80)
    print(f"{'✅ COMPLETE' if completed == len(steps) else '❌ STOPPED'}: {completed}/{len(steps)} ({elapsed:.1f}s)")
    print("="*80)

if __name__ == "__main__":
    main()
