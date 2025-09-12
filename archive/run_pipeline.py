#!/usr/bin/env python3
"""
Run the complete credit spread discovery pipeline
Enhanced version with full output display
"""
import subprocess
import sys
import time
import json
from datetime import datetime

def run_step(step_num, script, description):
    """Run a pipeline step and display all output"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run without capturing output - let it flow to console
    result = subprocess.run([sys.executable, script])
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"\n✅ Step {step_num} complete in {elapsed:.1f}s")
        return True
    else:
        print(f"\n❌ Step {step_num} failed after {elapsed:.1f}s")
        return False

def display_summary():
    """Display final summary of all collected data"""
    print("\n" + "="*80)
    print("PIPELINE SUMMARY")
    print("="*80)
    
    # Load and display key metrics from each step
    try:
        # Stock prices
        with open("stock_prices.json", "r") as f:
            prices = json.load(f)
            print(f"\n📊 STOCK PRICES: {prices['success']}/{prices['requested']} stocks")
            if prices['failed']:
                print(f"   Missing: {', '.join(prices['missing_tickers'])}")
        
        # Chains
        with open("chains.json", "r") as f:
            chains = json.load(f)
            print(f"\n⛓️  OPTIONS CHAINS: {chains['success']} tickers with chains")
        
        # Liquidity
        with open("liquid_chains.json", "r") as f:
            liquid = json.load(f)
            print(f"\n💧 LIQUIDITY: {liquid['tickers_with_liquidity']} tickers with liquid options")
        
        # Greeks
        with open("greeks.json", "r") as f:
            greeks = json.load(f)
            print(f"\n🧮 GREEKS: {greeks['tickers_with_greeks']} tickers with valid Greeks")
        
        # Spreads
        with open("spreads.json", "r") as f:
            spreads = json.load(f)
            print(f"\n📈 SPREADS: {spreads['total_spreads']} credit spreads built")
        
        # Analyzed spreads
        with open("analyzed_spreads.json", "r") as f:
            analyzed = json.load(f)
            print(f"\n🎲 ANALYSIS: {analyzed['total_spreads']} spreads with PoP calculated")
        
        # Ranked spreads
        with open("ranked_spreads.json", "r") as f:
            ranked = json.load(f)
            print(f"\n🏆 RANKING: {ranked['summary']['enter']} ENTER, {ranked['summary']['watch']} WATCH, {ranked['summary']['skip']} SKIP")
        
        # Final trades
        with open("final_trades.json", "r") as f:
            final = json.load(f)
            print(f"\n🎯 FINAL VALIDATION: {final['summary']['yes']} YES, {final['summary']['wait']} WAIT, {final['summary']['no']} NO")
            
            # Show YES trades
            yes_trades = [t for t in final['final_trades'] if t['entry_decision'] == 'YES']
            if yes_trades:
                print(f"\n💰 TRADES TO ENTER NOW:")
                for trade in yes_trades:
                    print(f"   • {trade['ticker']} {trade['type']} {trade['legs']} - ROI: {trade['roi']} PoP: {trade['pop']}")
                    print(f"     {trade['why']}")
        
    except FileNotFoundError as e:
        print(f"\n⚠️ Could not load summary data: {e}")
    except Exception as e:
        print(f"\n⚠️ Error displaying summary: {e}")

def main():
    print("\n" + "="*80)
    print("CREDIT SPREAD DISCOVERY PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    steps = [
        (1, "call_gpt_simple.py", "Get 22 stocks from GPT"),
        (2, "get_stock_prices.py", "Get real prices from TastyTrade"),
        (3, "get_options_chains.py", "Find options chains (15-45 DTE)"),
        (4, "check_liquidity.py", "Check liquidity (bid/ask < 10%)"),
        (5, "get_greeks.py", "Get Greeks (IV, Delta, Theta)"),
        (6, "calculate_spreads_fixed.py", "Build credit spreads"),
        (7, "calculate_pop_roi.py", "Calculate PoP using Black-Scholes"),
        (8, "rank_spreads.py", "Rank trades by multiple factors"),
        (9, "build_report_table.py", "Build report table"),
        (10, "call_gpt_2.py", "GPT validation with market context"),
        (11, "display_results.py", "Display final results")
    ]
    
    # Track timing
    pipeline_start = time.time()
    failed_step = None
    
    for step_num, script, description in steps:
        if not run_step(step_num, script, description):
            failed_step = step_num
            print(f"\n❌ Pipeline stopped at step {step_num}")
            break
        # Small delay between steps for readability
        time.sleep(0.5)
    
    pipeline_elapsed = time.time() - pipeline_start
    
    if not failed_step:
        print("\n" + "="*80)
        print(f"✅ PIPELINE COMPLETE in {pipeline_elapsed:.1f} seconds!")
        print("="*80)
        
        # Display comprehensive summary
        display_summary()
        
        print("\n" + "="*80)
        print("📁 OUTPUT FILES CREATED:")
        print("="*80)
        print("  • stocks.py - GPT stock selections")
        print("  • stock_prices.json - Real-time prices")
        print("  • chains.json - Options chains")
        print("  • liquid_chains.json - Liquid options only")
        print("  • greeks.json - Options Greeks")
        print("  • spreads.json - Credit spread candidates")
        print("  • analyzed_spreads.json - With PoP calculations")
        print("  • ranked_spreads.json - Multi-factor rankings")
        print("  • report_table.json - Formatted for GPT")
        print("  • final_trades.json - GPT validated trades")
        print("  • trades_*.csv - Excel-ready output")
        
        print("\n💡 NEXT STEPS:")
        print("  1. Review YES trades in final_trades.json")
        print("  2. Verify market conditions haven't changed")
        print("  3. Place orders at mid-price or better")
        print("  4. Set stop losses at 2x credit received")
    else:
        print(f"\n⚠️ Pipeline failed after {pipeline_elapsed:.1f} seconds")
        print(f"Debug step {failed_step} to resolve the issue")

if __name__ == "__main__":
    main()
