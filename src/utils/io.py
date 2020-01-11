import os
from pathlib import Path
from typing import Callable

import pandas as pd


def filter_dt_session(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df.ua_type != "Xhr", df.columns != 'ua_type']


def load_csv_data(file_name: str, prep_fn: Callable = filter_dt_session) -> pd.DataFrame:
    """
    Read csv file from directory.
    """
    data_dir = Path('./data/')
    filtered_file = data_dir / 'interim' / file_name

    if os.path.exists(filtered_file):
        return pd.read_csv(filtered_file)
    else:
        df = pd.read_csv(data_dir / 'raw' / file_name)
        df_filtered = prep_fn(df)
        print(f"Loaded data: {len(df)} / after filtering {len(df_filtered)}")
        df_filtered.to_csv(filtered_file)  # store filtered DF for later re-usage
        print("Saved filtered dataframe")

        return df_filtered