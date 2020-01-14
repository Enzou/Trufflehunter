import functools
import os
from pathlib import Path
from typing import Callable, List

import pandas as pd


_DATA_DIR = Path('./data/')


def get_available_datasets() -> List[str]:
    return os.listdir(_DATA_DIR / 'raw')


def filter_dt_session(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.ua_type != "Xhr"].drop(['ua_type'], axis=1)


@functools.lru_cache()
def load_csv_data(file_name: str, prep_fn: Callable = filter_dt_session) -> pd.DataFrame:
    """
    Read csv file from directory.
    """
    _DATA_DIR = Path('./data/')
    filtered_file = _DATA_DIR / 'interim' / file_name

    if os.path.exists(filtered_file):
        return pd.read_csv(filtered_file)
    else:
        df = pd.read_csv(_DATA_DIR / 'raw' / file_name)
        df_filtered = prep_fn(df)
        print(f"Loaded data: {len(df)} / after filtering {len(df_filtered)}")
        df_filtered.to_csv(filtered_file, index=False)  # store filtered DF for later re-usage
        print("Saved filtered dataframe")

        return df_filtered