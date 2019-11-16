from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Trace:
    def __init__(self, df, attrs:Dict=None):
        if not attrs:
            attrs = {}
        self.activity_attr = attrs.get('activity', 'Activity')
        self.id_attr = attrs.get('id', 'Case ID')
        self.ts_attr = attrs.get('timestamp', 'Timestamp')
        self.features: List[str] = list(df.columns)
        self._df = df
        self._events: List[Dict] = df.to_dict('records')

    def __iter__(self):
        return (e for e in self._events)

    @property
    def activities(self):
        # tmp_a = ['register request', 'examine thoroughly', 'examine casually', 'check ticket',
        #          'decide', 'reinitiate request', 'pay compensation', 'reject request']
        # tmp_map = {a: letter for a, letter in zip(tmp_a, 'abcdefgh')}
        return [e[self.activity_attr] for e in self._events]

    def __len__(self):
        return len(self._events)

    def __getitem__(self, item):
        return self._events[item]

