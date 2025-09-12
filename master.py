"""
Master Pipeline Orchestrator with Beautiful Data Flow
Quality over quantity - 22 tickers, 100% coverage target
"""
import subprocess
import sys
import time
import json
from datetime import datetime
from collections import defaultdict

class TradingPipeline:
    def __init__(self):
        self.start_time = time.time()
        self.results = {}
        self.metrics = defaultdict(dict)
        
    def run_step(self, step_num, script, description):
        """Run a step with beautiful visualization"""
        print(f"\n{'='*80}")
        print(f"🚀 STEP {step_num}: {description}")
        print(f"{'='*80}")
        
        step_start = time.time()
        
        # Run the script
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        
        elapsed = time.time() - step_start
        
        # Parse output for metrics
        output = result.stdout
        lines = output.split('\n')
        
        # Extract key metrics from output
        if "Total Greeks collected:" in output:
            for line in lines:
                if "Total Greeks collected:" in line:
                    collected = int(line.split(":")[1].strip())
                    self.metrics[step_num]["greeks_collected"] = collected
                    
        if "liquid strikes" in output:
            for line in lines:
                if "Total liquid strikes:" in line:
                    liquid = int(line.split(":")[1].strip())
                    self.metrics[step_num]["liquid_strikes"] = liquid
                    
        if "Total spreads:" in output:
            for line in lines:
                if "Total spreads:" in line:
                    spreads = int(line.split(":")[1].strip())
                    self.metrics[step_num]["spreads_found"] = spreads
        
        # Display output
        print(output)
        
        if result.returncode == 0:
            print(f"\n✅ Step {step_num} complete in {elapsed:.1f}s")
            self.results[step_num] = {"status": "success", "time": elapsed}
            return True
        else:
            print(f"\n⚠️ Step {step_num} had issues but continuing...")
            self.results[step_num] = {"status": "partial", "time": elapsed}
            return True  # Continue anyway
    
    def display_flow(self):
        """Display beautiful data flow visualization"""
        print("\n" + "="*80)
        print("📊 DATA FLOW VISUALIZATION")
        print("="*80)
        
        # Load data from files to show flow
        try:
            # Stocks
            from stocks import STOCKS
            print(f"\n1️⃣ STOCKS: {len(STOCKS)} tickers")
            print(f"   → {', '.join(STOCKS[:5])}...")
            
            # Prices
            with open("stock_prices.json", "r") as f:
                prices = json.load(f)
                print(f"\n2️⃣ PRICES: {prices['success']}/{prices['requested']} collected")
                print(f"   → Real-time bid/ask/mid prices")
            
            # Chains
            with open("chains.json", "r") as f:
                chains = json.load(f)
                total_strikes = sum(c["strikes_count"] for c in chains["chains"].values())
                print(f"\n3️⃣ OPTIONS: {chains['success']} tickers, {total_strikes} strikes")
                print(f"   → 15-45 DTE, 70-130% of spot")
            
            # Liquidity
            with open("liquid_chains.json", "r") as f:
                liquid = json.load(f)
                total_liquid = sum(c["liquid_count"] for c in liquid["liquid_chains"].values())
                print(f"\n4️⃣ LIQUIDITY: {total_liquid} liquid options")
                print(f"   → Scored 0-100 based on spread/price")
            
            # Greeks
            with open("greeks.json", "r") as f:
                greeks = json.load(f)
                total_greeks = sum(
                    d.get("count", len(d.get("greeks", []))) 
                    for d in greeks["greeks"].values()
                )
                print(f"\n5️⃣ GREEKS: {total_greeks} options with IV/Delta")
                coverage = (total_greeks / total_liquid * 100) if total_liquid > 0 else 0
                print(f"   → {coverage:.1f}% coverage (target: 100%)")
            
            # Spreads
            with open("spreads.json", "r") as f:
                spreads = json.load(f)
                print(f"\n6️⃣ SPREADS: {spreads['total_spreads']} candidates")
                print(f"   → Credit spreads with >5% ROI")
            
            # Analysis
            with open("analyzed_spreads.json", "r") as f:
                analyzed = json.load(f)
                high_pop = len([s for s in analyzed["analyzed_spreads"] if s["pop"] >= 70])
                print(f"\n7️⃣ ANALYSIS: {analyzed['total_spreads']} with PoP")
                print(f"   → {high_pop} with >70% win rate")
            
            # Rankings
            with open("ranked_spreads.json", "r") as f:
                ranked = json.load(f)
                print(f"\n8️⃣ RANKINGS: {ranked['summary']['enter']} ENTER trades")
                print(f"   → Multi-factor scoring applied")
                
        except Exception as e:
            print(f"   ⚠️ Some data not available yet: {e}")
    
    def display_performance(self):
        """Display performance metrics"""
        print("\n" + "="*80)
        print("⚡ PERFORMANCE METRICS")
        print("="*80)
        
        total_time = time.time() - self.start_time
        
        print(f"\nTotal pipeline time: {total_time:.1f} seconds")
        print(f"\nStep breakdown:")
        for step, result in self.results.items():
            status = "✅" if result["status"] == "success" else "⚠️"
            print(f"  Step {step}: {status} {result['time']:.1f}s")
        
        # Data coverage
        try:
            with open("liquid_chains.json", "r") as f:
                liquid = json.load(f)
                total_liquid = sum(c["liquid_count"] for c in liquid["liquid_chains"].values())
            
            with open("greeks.json", "r") as f:
                greeks = json.load(f)
                total_greeks = sum(
                    d.get("count", len(d.get("greeks", []))) 
                    for d in greeks["greeks"].values()
                )
            
            coverage = (total_greeks / total_liquid * 100) if total_liquid > 0 else 0
            
            print(f"\n📊 Data Coverage:")
            print(f"  Target options: {total_liquid}")
            print(f"  Greeks collected: {total_greeks}")
            print(f"  Coverage: {coverage:.1f}% (target: 100%)")
            
            if coverage < 100:
                print(f"\n💡 To reach 100% coverage:")
                print(f"  - Increase batch timeout from 8s to 12s")
                print(f"  - Raise coverage target from 70% to 85%")
                print(f"  - Add retry for missing ATM options")
                
        except:
            pass

def main():
    print("\n" + "="*80)
    print("🎯 AGGRESSIVE CREDIT SPREAD PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Configuration: MIN_POP=66% | MIN_ROI=33% | 22 Quality Tickers")
    print("="*80)
    
    pipeline = TradingPipeline()
    
    steps = [
        (1, "call_gpt_simple.py", "Get 22 Quality Stocks from GPT"),
        (2, "get_stock_prices.py", "Real-time Prices from TastyTrade"),
        (3, "get_options_chains.py", "Options Chains (70-130% range)"),
        (4, "check_liquidity.py", "Liquidity Scoring (0-100)"),
        (5, "get_greeks.py", "Batch Greeks Collection"),
        (6, "calculate_spreads_fixed.py", "Build Credit Spreads"),
        (7, "calculate_pop_roi.py", "Black-Scholes PoP Calculation"),
        (8, "rank_spreads.py", "Multi-factor Ranking"),
        (9, "build_report_table.py", "Prepare for GPT"),
        (10, "call_gpt_2.py", "GPT Validation (ALL trades)"),
        (11, "display_results.py", "Final Display")
    ]
    
    for step_num, script, description in steps:
        pipeline.run_step(step_num, script, description)
        time.sleep(0.5)  # Brief pause for readability
    
    # Display beautiful visualizations
    pipeline.display_flow()
    pipeline.display_performance()
    
    # Final recommendations
    print("\n" + "="*80)
    print("🏆 PIPELINE COMPLETE!")
    print("="*80)
    
    try:
        with open("final_trades.json", "r") as f:
            final = json.load(f)
            yes_count = final["summary"]["yes"]
            
            if yes_count > 0:
                print(f"\n✅ {yes_count} trades ready to execute!")
                print("Run 'python3 display_results.py' to see details")
            else:
                print("\n⚠️ No trades passed validation")
                print("Consider adjusting MIN_POP or MIN_ROI")
    except:
        print("\nRun 'python3 display_final_trades.py' to see results")

if __name__ == "__main__":
    main()
