
"""
Convert analyzed_spreads.json to CSV
"""
import json
import os
import subprocess
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_analyzed_spreads():
    """Load analyzed spreads from JSON"""
    try:
        with open("data/analyzed_spreads_both.json", "r") as f:
            data = json.load(f)
        return data["analyzed_spreads"]
    except FileNotFoundError:
        print("❌ analyzed_spreads.json not found - run 07_calculate_pop_roi.py first")
        raise


def convert_to_csv(spreads):
    """Convert spreads to CSV with flattened structure"""
    # Create reports directory
    os.makedirs('reports', exist_ok=True)

    # Flatten nested expiration fields
    flattened_spreads = []
    for spread in spreads:
        flat_spread = spread.copy()
        flat_spread['exp_date'] = spread['expiration']['date']
        flat_spread['dte'] = spread['expiration']['dte']
        del flat_spread['expiration']
        flattened_spreads.append(flat_spread)

    # Create DataFrame
    df = pd.DataFrame(flattened_spreads)

    # Select and order columns for CSV
    columns = [
        'ticker', 'type', 'stock_price', 'short_strike', 'long_strike', 'width',
        'net_credit', 'max_loss', 'roi', 'pop', 'score', 'short_iv', 'short_delta',
        'exp_date', 'dte'
    ]

    # Ensure only available columns are included
    df = df[[col for col in columns if col in df.columns]]

    # Create timestamped filename
    filename = f"reports/analyzed_spreads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    # Save to CSV
    df.to_csv(filename, index=False)

    print(f"\n📊 CSV file '{filename}' created successfully.")
    print(f"   Total spreads: {len(df)}")

    # Open the CSV file
    try:
        subprocess.run(['open', filename], check=True)
        print(f"Opened '{filename}' with default application.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to open '{filename}': {e}")


def main():
    """Main execution"""
    print("=" * 60)
    print("Convert analyzed_spreads.json to CSV")
    print("=" * 60)

    # Load and convert
    spreads = load_analyzed_spreads()
    convert_to_csv(spreads)

    print("✅ Conversion complete")


if __name__ == "__main__":
    main()
