from pathlib import Path
from typing import Optional

import pandas as pd
from trace import Trace


class EventLog:
    def __init__(self, df: Optional[pd.DataFrame], datetime_fmt: Optional[str] = None):
        self._df = df
        self.case_id_attr = 'Case ID'
        self.activity_attr = 'Activity'
        self.ts_attr = 'Timestamp'
        if datetime_fmt:
            self._df['Timestamp'] = pd.to_datetime(self._df['Timestamp'], format=datetime_fmt)
        self.traces = df.groupby(self.case_id_attr).apply(Trace)    # TODO implement more performant alternative

    @classmethod
    def read_from(cls, path: Path, datetime_fmt=None):
        if path.suffix == '.csv':
            df = pd.read_csv(path, sep=';')
            return cls(df, datetime_fmt)
        else:
            raise NotImplementedError(f"Extension '{path.suffix}' is not recognized")

    def __iter__(self):
        for t in self.traces:
            yield t
