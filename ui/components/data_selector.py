from pathlib import Path
from typing import Tuple, Optional

import streamlit as st
import pandas as pd

from src.utils import io


@st.cache
def load_data(file_name: str, src_dir: str) -> pd.DataFrame:
    if str(src_dir) == 'raw':
        return io.load_csv_data(file_name, src_dir, io.filter_dt_session)
    else:
        return io.load_csv_data(file_name, src_dir)


def select_file(src_dir: str, default: Optional[str] = None) -> Tuple[str, pd.DataFrame]:
    """
    Selection widget for choosing the file to work on.
    :param src_dir: sub-directory within the 'data'-directory from where the files should be used
    :param default: preset file
    :return: tuple with name of selected file and loaded file as pandas dataframe
    """
    available_files = io.get_available_datasets(src_dir)
    default_idx = available_files.index(default) if default is default in available_files else 0
    file_name = st.sidebar.selectbox("Source file: ", options=available_files, index=default_idx)
    if file_name is None:
        st.error("No valid file selected")
        return '', pd.DataFrame()
    else:
        st.spinner("Loading data " + file_name)
        df = load_data(file_name, src_dir)
        st.write(f"Loaded {len(df)} entries")
        return file_name, df
