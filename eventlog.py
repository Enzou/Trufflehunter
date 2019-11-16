import itertools
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

    def get_unique_activities(self):
        return self._df[self.activity_attr].unique()

    def create_footprint_matrix(self) -> pd.DataFrame:
        unique_activities = self.get_unique_activities()

        # create transition matrix
        trans_mat = pd.DataFrame(index=unique_activities, columns=unique_activities, data=0)
        for trace in self:
            activities = trace.activities
            for ai, aj in zip(activities, activities[1:]):
                trans_mat.loc[ai, aj] += 1

        # convert to footprint matrix
        foot_mat = pd.DataFrame(index=unique_activities, columns=unique_activities, data='#')
        for row, col in itertools.product(unique_activities, unique_activities):
            fwd_transition = trans_mat.loc[row, col]
            back_transition = trans_mat.loc[col, row]
            if fwd_transition > 0 :
                if back_transition > 0:
                    foot_mat.loc[row, col] = '||'
                else:
                    foot_mat.loc[row, col] = '→'
            elif back_transition > 0:
                foot_mat.loc[row, col] = '←'
        return foot_mat
