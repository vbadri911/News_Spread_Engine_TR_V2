#!/usr/bin/env python3
"""
Master Pipeline - Beautiful Data Flow
Runs all 15 steps and shows the data cascade
"""
import subprocess
import sys
import time
import json
from datetime import datetime

def print_header():
    print("\n" + "="*80)
    print("💎 CREDIT SPREAD FINDER - MASTER PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

def run_step(num, script, description):
    """Run step and show data flow"""
    print(f"\n{'─'*80}")
    print(f"⚡ STEP {num}: {description}")
    print(f"{'─'*80}")
    
    start = time.time()
    result = subprocess.run([sys.executable, script])
    elapsed = time.time() - start
    
    if result.returncode == 0:
        print(f"✅ Complete ({elapsed:.1f}s)")
        return True
    else:
        print(f"❌ Failed ({elapsed:.1f}s)")
        return False

def show_flow():
    """Show data flow summary"""
    print("\n" + "="*80)
    print("📊 DATA FLOW SUMMARY")
    print("="*80)
    
    try:
        with open("data/sp500.json", "r") as f:
            sp500 = json.load(f)
            print(f"\n🎯 S&P 500: {len(sp500)} tickers")
        
        with open("data/filter1_passed.json", "r") as f:
            f1 = json.load(f)
            pct1 = len(f1)/len(sp500)*100
            print(f"   ↓ Price Filter: {len(f1)} passed ({pct1:.1f}%)")
        
        with open("data/filter2_passed.json", "r") as f:
            f2 = json.load(f)
            pct2 = len(f2)/len(f1)*100
            print(f"   ↓ Options Filter: {len(f2)} passed ({pct2:.1f}%)")
        
        with open("data/filter3_passed.json", "r") as f:
            f3 = json.load(f)
            pct3 = len(f3)/len(f2)*100
            print(f"   ↓ IV Filter: {len(f3)} passed ({pct3:.1f}%)")
        
        with open("data/stocks.py", "r") as f:
            content = f.read()
            import ast
            stocks = ast.literal_eval(content.split("=")[1].split("\n")[0])
            print(f"   ↓ Top Scored: {len(stocks)} selected")
        
        with open("data/spreads.json", "r") as f:
            spreads = json.load(f)
            print(f"\n📈 Spreads Built: {spreads['total_spreads']}")
        
        with open("data/ranked_spreads.json", "r") as f:
            ranked = json.load(f)
            print(f"   ↓ Ranked: {ranked['summary']['total']}")
            print(f"   ↓ Top 22 (1 per ticker): {len(ranked['top_22'])}")
        
        with open("data/top9_analysis.json", "r") as f:
            top9 = json.load(f)
            print(f"\n🎯 Final Output: 9 trades ready")
            
    except Exception as e:
        print(f"⚠️ Could not load summary: {e}")

def main():
    print_header()
    
    steps = [
        ("00A", "pipeline/00a_get_sp500.py", "Get S&P 500 tickers"),
        ("00B", "pipeline/00b_filter_price.py", "Filter by price & spread"),
        ("00C", "pipeline/00c_filter_options.py", "Filter by options chains"),
        ("00D", "pipeline/00d_filter_iv.py", "Filter by IV range"),
        ("00E", "pipeline/00e_select_22.py", "Score & select top 22"),
        ("00F", "pipeline/00f_get_news.py", "Fetch news headlines"),
        ("01", "pipeline/01_get_prices.py", "Get real-time prices"),
        ("02", "pipeline/02_get_chains.py", "Get options chains"),
        ("03", "pipeline/03_check_liquidity.py", "Check liquidity"),
        ("04", "pipeline/04_get_greeks.py", "Collect Greeks"),
        ("05", "pipeline/05_calculate_spreads.py", "Calculate spreads"),
        ("06", "pipeline/06_rank_spreads.py", "Rank by score"),
        ("07", "pipeline/07_build_report.py", "Build report table"),
        ("08", "pipeline/08_gpt_analysis.py", "GPT 5W1H analysis"),
        ("09", "pipeline/09_format_trades.py", "Format final trades")
    ]
    
    pipeline_start = time.time()
    failed_at = None
    
    for num, script, desc in steps:
        if not run_step(num, script, desc):
            failed_at = num
            break
        time.sleep(0.5)
    
    elapsed = time.time() - pipeline_start
    
    if not failed_at:
        show_flow()
        print(f"\n{'='*80}")
        print(f"✅ PIPELINE COMPLETE ({elapsed:.1f}s total)")
        print(f"{'='*80}")
        print("\n💰 Run: python3 pipeline/09_format_trades.py")
        print("📊 To see your 9 trades")
    else:
        print(f"\n❌ Pipeline stopped at step {failed_at}")
        print(f"Total time: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
