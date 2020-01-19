from typing import List

import pandas as pd

from src.event_log.eventlog import EventLog
from src.preprocessing.ruleset import Ruleset


def convert_weblog(df: pd.DataFrame, src_col: str, mapping_rules: Ruleset, **el_params) -> EventLog:
    df['activity'] = df[src_col].apply(mapping_rules.entry_to_activity)
    return EventLog(df, **el_params)


def filter_by_session_length(df: pd.DataFrame, session_col: str, min_len: int = 2) -> pd.DataFrame:
    return df[df[session_col].groupby(df[session_col]).transform('size') >= min_len]
