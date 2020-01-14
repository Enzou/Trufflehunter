import re
from dataclasses import dataclass
from typing import List, Optional


class Rule:
    def __init__(self, pattern, activity_name: Optional[str] = None):
        self.pattern = pattern
        frags = pattern.split('/')
        self.activity_name = activity_name if activity_name else f"View {frags[-1].title()}"
        self.priority = pattern.count("/")

    def __repr__(self):
        return self.activity_name

    def __lt__(self, other) -> bool:
        return self.priority < other.priority

    def matches(self, text: str) -> bool:
        res = re.match(self.pattern, text)
        return res is not None

    def get_activity_name(self, text: str) -> str:
        return self.activity_name


class Ruleset:
    def __init__(self, rules: List):
        self.rules = sorted([Rule(*r) if isinstance(r, tuple) else Rule(r) for r in rules], reverse=True)

    def entry_to_activity(self, src: str) -> str:
        url_path = src.split(' ')[-1]  # assume last part is the website- path
        activity = next(r.get_activity_name(url_path) for r in self.rules if r.matches(url_path))
        return activity
