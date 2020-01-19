import functools
import os
from pathlib import Path
from typing import Callable, List, Optional

import pandas as pd

_DATA_DIR = Path('./data/')


def get_available_datasets(path="raw") -> List[str]:
    return os.listdir(_DATA_DIR / path)


def filter_dt_session(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.ua_type != "Xhr"].drop(['ua_type'], axis=1)


@functools.lru_cache()
def load_csv_data(file_name: str, src_dir: str = 'raw', prep_fn: Optional[Callable] = None) -> pd.DataFrame:
    """
    Read csv file from directory.
    """
    _DATA_DIR = Path('./data/')
    allow_cache = src_dir == "raw"

    if allow_cache:  # try 'caching' raw file to avoid applying the prep_fn needlessly
        filtered_file = _DATA_DIR / 'interim' / file_name
        if os.path.exists(filtered_file):
            return pd.read_csv(filtered_file)

    df = pd.read_csv(_DATA_DIR / src_dir / file_name)
    if prep_fn is not None:
        df_filtered = prep_fn(df)
        print(f"Filtered out {len(df) - len(df_filtered)} entries")
        df = df_filtered
    print(f"Loaded data: {len(df)}")

    if allow_cache:
        df.to_csv(filtered_file, index=False)  # store filtered DF for later re-usage
        print("Saved filtered dataframe")

    return df
