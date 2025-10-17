#!/usr/bin/env python3
"""
Visualization Dashboard - Beautiful Data Flow
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import pyperclip

st.set_page_config(page_title="Spread Command Center", layout="wide")


@st.cache_data
def load_data():
    """Load spreads.json, latest top9 CSV, and report_table.json"""
    try:
        with open("data/spreads.json", "r") as f:
            spreads = json.load(f)['spreads']
        df_spreads = pd.DataFrame(spreads)

        latest_csv = max([f for f in os.listdir('reports') if f.endswith('.csv')],
                         key=lambda f: os.path.getctime(f'reports/{f}'))
        df_top = pd.read_csv(f"reports/{latest_csv}")

        with open("data/report_table.json", "r") as f:
            report = json.load(f)['report_table']
        df_report = pd.DataFrame(report)

        return df_spreads, df_top, df_report
    except FileNotFoundError as e:
        st.error(f"Missing file: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"Data load error: {e}")
        return None, None, None


def is_weekly(exp_date_str):
    """Check if expiration is weekly"""
    try:
        exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
        day = exp_date.day
        weekday = exp_date.weekday()  # 0=Mon, 4=Fri
        if weekday != 4:  # Not Friday
            return False
        if 15 <= day <= 21:  # Third Friday = Monthly
            return False
        return True
    except ValueError:
        return False


def generate_tos_command(ticker, trade_type, strikes, exp_date, net_credit):
    """Generate TOS command with real exp_date and net_credit"""
    strikes = strikes.replace('$', '').split('/')
    short = float(strikes[0])
    long = float(strikes[1])

    exp = datetime.strptime(exp_date, '%Y-%m-%d')
    exp_format = exp.strftime('%d %b %y').upper()

    weekly_tag = " (Weeklys)" if is_weekly(exp_date) else ""
    opt_type = "CALL" if "Bear Call" in trade_type else "PUT"

    short_str = f"{short:.1f}" if short % 1 != 0 else f"{int(short)}"
    long_str = f"{long:.1f}" if long % 1 != 0 else f"{int(long)}"

    return f"SELL -1 VERTICAL {ticker} 100{weekly_tag} {exp_format} {short_str}/{long_str} {opt_type} @{net_credit:.2f} LMT"


def apply_filters(df, sector, dte_min, dte_max, pop_min):
    """Apply sidebar filters to dataframe"""
    filtered = df.copy()
    required_cols = ['DTE', 'PoP', 'sector']
    missing_cols = [col for col in required_cols if col not in filtered.columns]
    if missing_cols:
        st.error(f"Missing columns in top9_trades.csv: {', '.join(missing_cols)}")
        return filtered

    if sector != "All":
        filtered = filtered[filtered['sector'] == sector]
    try:
        filtered = filtered[(filtered['DTE'].astype(float) >= dte_min) &
                            (filtered['DTE'].astype(float) <= dte_max)]
        filtered = filtered[filtered['PoP'].str.replace('%', '').astype(float) >= pop_min]
    except Exception as e:
        st.error(f"Filter error: {e}")
    return filtered


def merge_heat(df_spreads, df_top):
    """Merge Heat and Strikes from top9_trades.csv into spreads dataframe"""
    try:
        # Prepare df_top for merge (strip $ from strikes)
        df_top['Strikes'] = df_top['Strikes'].str.replace('$', '')
        df_spreads['strikes_key'] = df_spreads['short_strike'].astype(str) + '/' + df_spreads['long_strike'].astype(str)
        df_top['strikes_key'] = df_top['Strikes'].str.replace('$', '').str.replace('.', '')

        # Merge on ticker, type, and strikes
        merged = pd.merge(df_spreads, df_top[['Ticker', 'Type', 'Strikes', 'Heat']],
                          left_on=['ticker', 'type', 'strikes_key'],
                          right_on=['Ticker', 'Type', 'Strikes'],
                          how='left')
        merged['Heat'] = merged['Heat'].fillna(0).astype(float)  # Default to 0 if no match

        # Create strikes column in df_spreads format
        merged['strikes'] = '$' + merged['short_strike'].astype(str) + '/' + merged['long_strike'].astype(str)

        return merged.drop(columns=['strikes_key', 'Ticker', 'Type', 'Strikes'])
    except Exception as e:
        st.error(f"Heat/strikes merge error: {e}")
        return df_spreads


def main():
    st.title("Spread Command Center")
    st.markdown(
        "**Top 9 Credit Spreads with News Catalysts** | Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M'))

    # Load data
    df_spreads, df_top, df_report = load_data()
    if df_spreads is None or df_top is None or df_report is None:
        st.stop()

    # Merge sector, heat, and strikes
    sector_map = dict(zip(df_report['ticker'], df_report['sector']))
    df_spreads['sector'] = df_spreads['ticker'].map(sector_map).fillna('Other')
    df_top['sector'] = df_top['Ticker'].map(sector_map).fillna('Other')
    df_spreads = merge_heat(df_spreads, df_top)

    # Update TOS commands with real data
    for idx, row in df_top.iterrows():
        match = df_report[(df_report['ticker'] == row['Ticker']) &
                          (df_report['type'] == row['Type']) &
                          (df_report['legs'] == row['Strikes'])]
        if not match.empty:
            exp_date = match.iloc[0]['exp_date']
            net_credit = float(match.iloc[0]['net_credit'].replace('$', ''))
            df_top.at[idx, 'TOS Command'] = generate_tos_command(
                row['Ticker'], row['Type'], row['Strikes'], exp_date, net_credit
            )

    # Sidebar filters
    st.sidebar.header("Filters")
    sectors = ['All'] + sorted(df_spreads['sector'].unique())
    sector = st.sidebar.selectbox("Sector", sectors)
    dte_min, dte_max = st.sidebar.slider("DTE Range", 0, 45, (7, 45))
    pop_min = st.sidebar.slider("Min PoP (%)", 0, 100, 60)

    # Filter top9 table
    df_top_filtered = apply_filters(df_top, sector, dte_min, dte_max, pop_min)

    # Interactive Top9 Table
    st.header("Top 9 Trades")
    gb = GridOptionsBuilder.from_dataframe(df_top_filtered)
    gb.configure_default_column(filter=True, sortable=True, resizable=True)
    grid_options = gb.build()

    st.markdown("""
        <style>
        .ag-cell button {
            padding: 5px 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .ag-cell button:hover {
            background-color: #45a049;
        }
        </style>
    """, unsafe_allow_html=True)

    AgGrid(df_top_filtered, gridOptions=grid_options, height=400)

    # Copy TOS command buttons
    for index, row in df_top_filtered.iterrows():
        if st.button(f"Copy TOS: {row['Ticker']}", key=f"copy_{index}"):
            pyperclip.copy(row['TOS Command'])
            st.success(f"Copied: {row['TOS Command']}")

    # PoP Histogram
    st.header("PoP Distribution")
    fig_pop = px.histogram(df_spreads, x='pop', color='type',
                           title="PoP Distribution by Trade Type",
                           labels={'pop': 'PoP (%)', 'type': 'Trade Type'},
                           color_discrete_map={'Bull Put': 'red', 'Bear Call': 'blue'})
    st.plotly_chart(fig_pop, use_container_width=True)

    # ROI vs PoP Scatter
    st.header("ROI vs PoP")
    fig_roi = px.scatter(df_spreads, x='pop', y='roi', size='Heat', color='sector',
                         hover_data=['ticker', 'strikes'],
                         title="ROI vs PoP (Size: Heat, Color: Sector)",
                         labels={'pop': 'PoP (%)', 'roi': 'ROI (%)'})
    st.plotly_chart(fig_roi, use_container_width=True)


if __name__ == "__main__":
    main()
