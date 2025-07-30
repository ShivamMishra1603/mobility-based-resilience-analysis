import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def plot_cbg_mobility(cbg_id, inflow_df, resilience_row):
    df_plot = inflow_df[inflow_df['destination_cbg'] == cbg_id].copy()
    baseline = resilience_row['baseline']
    t0 = resilience_row['t0']
    tD = resilience_row['tD']
    t1 = resilience_row['t1']

    df_plot = df_plot[df_plot['date'].between(t0 - timedelta(days=5), t1 + timedelta(days=5))].copy()
    df_plot['baseline'] = baseline

    mask = (df_plot['date'] >= t0) & (df_plot['date'] <= t1)
    shaded = df_plot[mask]

    plt.figure(figsize=(12, 5))

    sns.lineplot(data=df_plot, x='date', y='normalized_inflow', label='Smoothed Inflow', color='blue')

    plt.axhline(baseline, color='gray', linestyle='--', label='Baseline')

    plt.fill_between(
        shaded['date'],
        shaded['normalized_inflow'],
        baseline,
        where=(shaded['normalized_inflow'] < baseline),
        interpolate=True,
        color='red',
        alpha=0.3,
        label='Area Loss'
    )

    plt.fill_between(
        shaded['date'],
        shaded['normalized_inflow'],
        baseline,
        where=(shaded['normalized_inflow'] > baseline),
        interpolate=True,
        color='lightblue',
        alpha=0.3,
        label='Area Gain'
    )

    plt.axvline(t0, color='orange', linestyle='--', label='t₀: Disaster Start')
    plt.axvline(tD, color='red', linestyle='--', label='tD: Max Impact')
    plt.axvline(t1, color='green', linestyle='--', label='t₁: Recovery')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

    plt.title(f"CBG: {cbg_id} | Resilience Ratio: {resilience_row['resilience_ratio']:.2f}")
    plt.xlabel('Date')
    plt.ylabel('Normalized Inflow')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_visits(df, start_date='2019-09-01', end_date='2019-09-30', impact_window=('2019-09-17', '2019-09-19')):
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    df['visit_type'] = df.apply(
        lambda row: 'own' if row['origin_census_block_group'] == row['destination_cbg']
        else 'inward' if row['origin_census_block_group'][:5] != row['destination_cbg'][:5]
        else 'outward',
        axis=1
    )

    visit_counts = df.groupby(['date', 'visit_type'])['destination_device_count'].sum().reset_index()
    visit_pivot = visit_counts.pivot(index='date', columns='visit_type', values='destination_device_count').fillna(0)

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=visit_pivot, linewidth=2.5)

    plt.axvspan(pd.to_datetime(impact_window[0]), pd.to_datetime(impact_window[1]), color='gray', alpha=0.3, label='Impact Window')

    plt.title("Time Series of Visits in Port Arthur")
    plt.xlabel("Date")
    plt.ylabel("Number of Visits")
    plt.legend(title='Visit Type')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_top_bottom_cbgs(inflow_df, resilience_df, n_top=3, n_bottom=3):
    top_cbgs = resilience_df.sort_values(by='resilience_ratio', ascending=False).head(n_top)['cbg'].tolist()
    bottom_cbgs = resilience_df.sort_values(by='resilience_ratio', ascending=True).head(n_bottom)['cbg'].tolist()

    print(f"{n_bottom} Least Resilient CBGs")
    for cbg in bottom_cbgs:
        row = resilience_df[resilience_df['cbg'] == cbg].iloc[0]
        plot_cbg_mobility(cbg, inflow_df, row)

    print(f"\n{n_top} Most Resilient CBGs")
    for cbg in top_cbgs:
        row = resilience_df[resilience_df['cbg'] == cbg].iloc[0]
        plot_cbg_mobility(cbg, inflow_df, row)

if __name__ == "__main__":
    from data_loader import load_data
    from mobility_processor import process_mobility_data
    from resilience_calculator import calculate_resilience_for_all_cbgs
    
    print("Loading and processing data...")
    df = load_data()
    inflow_df = process_mobility_data(df)
    
    print("Calculating resilience metrics...")
    resilience_df = calculate_resilience_for_all_cbgs(inflow_df)
    
    print("Testing visualization functions...")
    
    plot_visits(df)
    
    plot_top_bottom_cbgs(inflow_df, resilience_df, n_top=3, n_bottom=3)
    
    print("Visualization test complete!") 