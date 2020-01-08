from pathlib import Path
from typing import Optional, Dict

import pandas as pd
from src.event_log.trace import Trace

# TODO classify types of features (like in DISCO) i.e. Case, Activity, Resource, Timestamp, Other


class EventLog:
    def __init__(self, df: Optional[pd.DataFrame], case_id_attr='Case ID', activity_attr='Activity',
                 timestamp_attr='Timestamp', ts_parse_params: Optional[Dict] = None):
        self._df = df
        self.case_id_attr = case_id_attr
        self.activity_attr = activity_attr
        self.ts_attr = timestamp_attr
        self._ts_parse_params = ts_parse_params
        if ts_parse_params:
            self._df.loc[:, self.ts_attr] = pd.to_datetime(self._df[self.ts_attr], **ts_parse_params)

        log_attrs = {
            'activity': activity_attr,
            'id': case_id_attr,
            'timestamp': timestamp_attr
        }
        self.traces = df.groupby(self.case_id_attr).apply(Trace, attrs=log_attrs)  # TODO implement more performant alternative

    @classmethod
    def read_from(cls, path: Path, **kwargs):
        if path.suffix == '.csv':
            df = pd.read_csv(path, sep=',')
            return cls(df, **kwargs)
        else:
            raise NotImplementedError(f"Extension '{path.suffix}' is not recognized")

    def __iter__(self):
        for t in self.traces:
            yield t

    def get_unique_activities(self):
        return self._df[self.activity_attr].unique()

    def __getitem__(self, mask):
        df = self._df[mask]
        return EventLog(df, self.case_id_attr, self.activity_attr, self.ts_attr, self._ts_parse_params)
