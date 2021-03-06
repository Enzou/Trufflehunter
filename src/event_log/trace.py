from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Trace:
    def __init__(self, df, attrs: Dict = None):
        if not attrs:
            attrs = {}
        self.activity_attr = attrs.get('activity_attr', 'Activity')
        self.id_attr = attrs.get('case_id_attr', 'Case ID')
        self.ts_attr = attrs.get('timestamp_attr', 'Timestamp')
        self.duration_attr = attrs.get('duration_attr', 'Duration')
        self.features: List[str] = list(df.columns)
        self.id = df[self.id_attr].iloc[0]
        self._df = df
        self._events: List[Dict] = df.to_dict('records')
        self._starttime = self._events[0][self.ts_attr]

    def __iter__(self):
        return (e for e in self._events)

    @property
    def activities(self):
        # tmp_a = ['register request', 'examine thoroughly', 'examine casually', 'check ticket',
        #          'decide', 'reinitiate request', 'pay compensation', 'reject request']
        # tmp_map = {a: letter for a, letter in zip(tmp_a, 'abcdefgh')}
        return [e[self.activity_attr] for e in self._events]

    @property
    def duration(self):
        last = self._events[-1]
        return self._starttime - last[self.ts_attr] + last[self.duration_attr]

    def get_time_passed(self, ref_time):
        return ref_time - self._starttime

    def __len__(self):
        return len(self._events)

    def __getitem__(self, item):
        return self._events[item]

    def __str__(self):
        return f"[{self.id}]  {' -> '.join(self.activities)}"
