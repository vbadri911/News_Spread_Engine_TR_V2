#!/usr/bin/env python3
"""
Run the complete credit spread discovery pipeline
"""
import subprocess
import sys
import time

def run_step(step_num, script, description):
    """Run a pipeline step"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*60}")
    
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Step {step_num} complete")
        return True
    else:
        print(f"❌ Step {step_num} failed")
        if result.stderr:
            print(result.stderr[:500])
        return False

def main():
    print("Credit Spread Discovery Pipeline")
    print("="*60)
    
    steps = [
        (1, "call_gpt_simple.py", "Get 22 stocks from GPT"),
        (2, "get_stock_prices.py", "Get real prices"),
        (3, "get_options_chains.py", "Find options"),
        (4, "check_liquidity.py", "Check liquidity"),
        (5, "get_greeks.py", "Get Greeks"),
        (6, "calculate_spreads_fixed.py", "Build spreads"),
        (7, "calculate_pop_roi.py", "Calculate PoP"),
        (8, "rank_spreads.py", "Rank trades"),
        (9, "build_report_table.py", "Build report"),
        (10, "call_gpt_2.py", "GPT validation"),
        (11, "display_results.py", "Show results")
    ]
    
    for step_num, script, description in steps:
        if not run_step(step_num, script, description):
            print(f"\nPipeline stopped at step {step_num}")
            break
    else:
        print("\n✅ Pipeline complete!")

if __name__ == "__main__":
    main()
