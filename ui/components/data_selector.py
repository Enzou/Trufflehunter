from pathlib import Path
from typing import Tuple, Optional

import streamlit as st
import pandas as pd

from src.utils import io


@st.cache
def load_data(file_name: str) -> pd.DataFrame:
    return io.load_csv_data(file_name)


def select_file(dir: Path, default: Optional[str] = None) -> Tuple[str, pd.DataFrame]:
    available_files = io.get_available_datasets()
    default_idx = available_files.index(default) if default is not None else 0
    file_name = st.sidebar.selectbox("Source web log: ", options=available_files, index=default_idx)
    st.spinner("Loading data " + file_name)
    df = load_data(file_name)
    st.write(f"Loaded {len(df)} entries")
    return file_name, df
