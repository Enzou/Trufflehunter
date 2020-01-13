from typing import List

import pandas as pd

from src.event_log.eventlog import EventLog
from src.preprocessing.ruleset import Ruleset


def convert_weblog(df: pd.DataFrame, mapping_rules: Ruleset) -> EventLog:
    pass
