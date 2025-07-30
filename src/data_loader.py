import pandas as pd
import pyreadr
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.analysis_config import DATA_FILE

def load_raw_data(data_path=None):
    if data_path is None:
        data_path = DATA_FILE
    result = pyreadr.read_r(data_path)
    return result[list(result.keys())[0]]

def convert_data_types(df):
    df['device_count'] = df['device_count'].astype(int)
    df['destination_device_count'] = df['destination_device_count'].astype(int)
    df['year'] = df['year'].astype(int)
    df['uid'] = df['uid'].astype(int)
    df['origin_census_block_group'] = df['origin_census_block_group'].astype(str)
    df['destination_cbg'] = df['destination_cbg'].astype(str)
    df['from_cnt'] = df['from_cnt'].astype(str)
    df['to_cnt'] = df['to_cnt'].astype(str)
    return df

def add_date_column(df):
    df['date'] = df['uid'].apply(lambda x: datetime(2019, 1, 1) + timedelta(days=int(x) - 1))
    return df

def load_data(data_path=None):
    df = load_raw_data(data_path)
    df = convert_data_types(df)
    df = add_date_column(df)
    return df

if __name__ == "__main__":
    df = load_data()
    print(df.head())