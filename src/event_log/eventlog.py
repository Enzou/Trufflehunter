from pathlib import Path
from typing import Optional, Dict, Callable, List, Union

import pandas as pd
from src.event_log.trace import Trace

import streamlit as st


# TODO classify types of features (like in DISCO) i.e. Case, Activity, Resource, Timestamp, Other

# visitID -> Case ID
class EventLog:
    def __init__(self, df: Optional[pd.DataFrame], case_id_attr='visitId', activity_attr='Activity',
                 timestamp_attr='Timestamp', ts_parse_params: Optional[Dict] = None, **kwargs):
        self._df = df
        self.case_id_attr = case_id_attr
        self.activity_attr = activity_attr
        self.ts_attr = timestamp_attr
        self._ts_parse_params = ts_parse_params
        if ts_parse_params:
            self._df.loc[:, self.ts_attr] = pd.to_datetime(self._df[self.ts_attr], **ts_parse_params)

        log_attrs = {
            'activity_attr': activity_attr,
            'case_id_attr': case_id_attr,
            'timestamp_attr': timestamp_attr
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

    def get_case_ids(self):
        return self._df[self.case_id_attr]

    def __len__(self):
        return len(self._df)

    def __getitem__(self, mask):
        df = self._df[mask]
        return EventLog(df, self.case_id_attr, self.activity_attr, self.ts_attr, self._ts_parse_params)

    def get_trace(self, case_id: str) -> Trace:
        try:
            trace = next(t for t in self.traces if t.id == case_id)
            return trace
        except StopIteration:
            ValueError(f"No case with id '{case_id}' found!")

    def get_traces(self, filter_fn: Optional[Callable] = None) -> pd.Series:
        """
        Returns a series of all traces matching the predicate (if given).
        :param filter_fn: predicate function for filtering the return traces
        E.g. to select only the traces with at least 2 activities the predicate `lambda traces: traces.str.len() >= 2` can be used
        :return: collection of traces meeting the criteria
        """
        if filter_fn:
            return self.traces[filter_fn]
        else:
            return self.traces

    def set_clusters(self, cluster_map: Dict) -> None:
        """
        Tags each trace with a cluster number
        :param cluster_map: dict mapping the visitId to a cluster number
        """
        self._df['cluster'] = self._df[self.case_id_attr].map(cluster_map)

    def shatter(self, by: str) -> List:
        pass

    def export_to_csv(self, dest_file: Union[Path, str]) -> None:
        self._df.to_csv(dest_file, index=False)
