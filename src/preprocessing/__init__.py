from typing import List, Tuple, Optional, Dict

import pandas as pd

from src.event_log.eventlog import EventLog
from src.preprocessing.ruleset import Ruleset


# def convert_weblog(df: pd.DataFrame, src_col: str, mapping_rules: Ruleset, **el_params) -> EventLog:
#     df['activity'] = df[src_col].apply(mapping_rules.entry_to_activity)
#     return EventLog(df, **el_params)


def convert_weblog(df: pd.DataFrame, column_mapping: Dict, column_transformations: List[Tuple], **el_params) -> EventLog:
    event_df = df[list(column_mapping.keys())]
    event_df = event_df.rename(columns=column_mapping)

    transformed_cols = {to_col: df[from_col].apply(fn) for from_col, to_col, fn in column_transformations}
    event_df = event_df.assign(**transformed_cols)
    return EventLog(event_df, **el_params, ts_parse_params={})


def filter_by_session_length(df: pd.DataFrame, session_col: str, min_len: int = 2) -> pd.DataFrame:
    return df[df[session_col].groupby(df[session_col]).transform('size') >= min_len]
