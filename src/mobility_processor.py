import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.analysis_config import SMOOTHING_WINDOW


def compute_daily_inflow(df):
    inflow_df = (
        df.groupby(["date", "destination_cbg"])["destination_device_count"]
        .sum()
        .reset_index()
        .rename(columns={"destination_device_count": "inflow"})
    )

    return inflow_df


def apply_smoothing(inflow_df, window=None):
    if window is None:
        window = SMOOTHING_WINDOW

    inflow_df = inflow_df.copy()
    inflow_df["smoothed_inflow"] = inflow_df.groupby("destination_cbg")[
        "inflow"
    ].transform(lambda x: x.rolling(window=window, min_periods=1, center=True).mean())

    return inflow_df


def normalize_inflow(inflow_df):
    inflow_df = inflow_df.copy()
    inflow_df["normalized_inflow"] = inflow_df.groupby("destination_cbg")[
        "smoothed_inflow"
    ].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

    return inflow_df


def process_mobility_data(df, smoothing_window=None):
    inflow_df = compute_daily_inflow(df)
    inflow_df = apply_smoothing(inflow_df, window=smoothing_window)
    inflow_df = normalize_inflow(inflow_df)

    return inflow_df


if __name__ == "__main__":
    from data_loader import load_data

    print("Loading mobility data...")
    df = load_data()
    print(f"Raw data shape: {df.shape}")

    print("\nProcessing mobility data...")
    processed_df = process_mobility_data(df)
    print(f"Processed data shape: {processed_df.shape}")
    print(f"Columns: {list(processed_df.columns)}")

    print("\nSample processed data:")
    print(processed_df.head())

    print(f"\nUnique CBGs: {processed_df['destination_cbg'].nunique()}")
    print(f"Date range: {processed_df['date'].min()} to {processed_df['date'].max()}")
