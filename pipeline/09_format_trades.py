"""
Format Top 9 Trades with News Summary
"""
import json
import re
import subprocess
from datetime import datetime


def load_data():
    with open("data/top9_analysis.json", "r") as f:
        return json.load(f)


def is_weekly(exp_date_str):
    """Check if expiration is weekly"""
    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
    day = exp_date.day
    weekday = exp_date.weekday()  # 0=Mon, 4=Fri
    if weekday != 4:  # Not Friday
        return False
    # Third Friday typically days 15-21
    if 15 <= day <= 21:
        return False  # Monthly
    return True  # Weekly


def generate_tos_command(trade, exp_date='2025-10-31', net_credit=2.45):
    """Generate TOS command for the trade"""
    ticker = trade['ticker']
    trade_type = trade['type']
    strikes = trade['strikes'].replace('$', '').split('/')
    short = float(strikes[0])
    long = float(strikes[1])

    exp = datetime.strptime(exp_date, '%Y-%m-%d')
    exp_format = exp.strftime('%d %b %y').upper()

    weekly_tag = " (Weeklys)" if is_weekly(exp_date) else ""

    opt_type = "CALL" if "Bear Call" in trade_type else "PUT"

    short_str = f"{short:.1f}" if short % 1 != 0 else f"{int(short)}"
    long_str = f"{long:.1f}" if long % 1 != 0 else f"{int(long)}"

    command = f"SELL -1 VERTICAL {ticker} 100{weekly_tag} {exp_format} {short_str}/{long_str} {opt_type} @{net_credit:.2f} LMT"
    return command


def parse_trades(analysis_text):
    trades = []
    trade_blocks = re.split(r'#\d+\.', analysis_text)[1:]

    for i, block in enumerate(trade_blocks, 1):
        lines = block.strip().split('\n')
        if not lines:
            continue

        header = lines[0].strip()
        parts = header.split()

        if len(parts) < 3:
            continue

        ticker = parts[0]
        trade_type = ' '.join(parts[1:-1])
        strikes = parts[-1]

        metrics_line = next((l for l in lines if 'DTE:' in l), '')

        dte = roi = pop = heat = "N/A"
        if metrics_line:
            if 'DTE:' in metrics_line:
                dte = re.search(r'DTE:\s*(\d+)', metrics_line)
                dte = dte.group(1) if dte else "N/A"
            if 'ROI:' in metrics_line:
                roi = re.search(r'ROI:\s*([\d.]+%)', metrics_line)
                roi = roi.group(1) if roi else "N/A"
            if 'PoP:' in metrics_line:
                pop = re.search(r'PoP:\s*([\d.]+%)', metrics_line)
                pop = pop.group(1) if pop else "N/A"
            if 'HEAT:' in metrics_line:
                heat = re.search(r'HEAT:\s*(\d+)', metrics_line)
                heat = heat.group(1) if heat else "N/A"

        catalyst = "No catalysts"
        catalyst_idx = next((idx for idx, l in enumerate(lines) if 'CATALYST RISK:' in l), None)
        if catalyst_idx and catalyst_idx + 1 < len(lines):
            catalyst = lines[catalyst_idx + 1].strip()

        rec_idx = next((idx for idx, l in enumerate(lines) if 'RECOMMENDATION:' in l), None)
        recommendation = lines[rec_idx + 1].strip() if rec_idx and rec_idx + 1 < len(lines) else "N/A"

        trades.append({
            'rank': i,
            'ticker': ticker,
            'type': trade_type,
            'strikes': strikes,
            'dte': dte,
            'roi': roi,
            'pop': pop,
            'heat': heat,
            'catalyst': catalyst,
            'recommendation': recommendation
        })

    return trades


def print_table(trades):
    print(
        "\n=============================================================================================================================================")
    print("TOP 9 CREDIT SPREADS - WITH NEWS CATALYSTS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(
        "=============================================================================================================================================")

    print(
        "\n#    Ticker   Type         Strikes      DTE   ROI      PoP      Heat  Catalyst Summary                                  TOS Command")
    print("-" * 140)

    for trade in trades:
        catalyst_short = trade['catalyst'][:50] + "..." if len(trade['catalyst']) > 50 else trade['catalyst']
        tos_cmd = generate_tos_command(trade)
        print(
            f"{trade['rank']:<5}{trade['ticker']:<9}{trade['type']:<13}{trade['strikes']:<13}{trade['dte']:<5}{trade['roi']:<9}{trade['pop']:<9}{trade['heat']:<5}{catalyst_short:<50}{tos_cmd}")

    print("-" * 140)

    trade_count = len([t for t in trades if 'Trade' in t['recommendation'] and 'Wait' not in t['recommendation']])
    wait_count = len([t for t in trades if 'Wait' in t['recommendation']])

    print(f"\nSUMMARY: {len(trades)} analyzed | {trade_count} Trade Now | {wait_count} Wait")

    print(f"\nDETAILED RECOMMENDATIONS:")
    for t in trades:
        tos_cmd = generate_tos_command(t)
        print(f"#{t['rank']} {t['ticker']}: {t['recommendation']} | TOS: {tos_cmd}")


def save_csv(trades):
    filename = f"reports/top9_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    with open(filename, "w") as f:
        f.write("Rank,Ticker,Type,Strikes,DTE,ROI,PoP,Heat,Catalyst,Recommendation,TOS Command\n")
        for t in trades:
            catalyst = t['catalyst'].replace(',', ';')
            rec = t['recommendation'].replace(',', ';')
            tos_cmd = generate_tos_command(t)
            f.write(
                f"{t['rank']},{t['ticker']},{t['type']},{t['strikes']},{t['dte']},{t['roi']},{t['pop']},{t['heat']},\"{catalyst}\",\"{rec}\",\"{tos_cmd}\"\n")

    print(f"\nSaved to {filename}")

    try:
        subprocess.run(['open', filename], check=True)
        print(f"Opened '{filename}' with default application.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to open '{filename}': {e}")


def main():
    print("=" * 60)
    print("STEP 9: Format Top 9 with News")
    print("=" * 60)

    data = load_data()
    trades = parse_trades(data['analysis'])

    if trades:
        print_table(trades)
        save_csv(trades)
        print("\nStep 9 complete")
    else:
        print("Could not parse trades")


if __name__ == "__main__":
    main()
