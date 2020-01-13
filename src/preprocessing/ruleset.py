from dataclasses import dataclass
from typing import List, Optional


class Rule:
    def __init__(self, pattern, activity_name: Optional[str] = None):
        self.pattern = pattern
        self.activity_name = activity_name if activity_name else f"View {pattern.title()}"
        self.priority = pattern.count("/")

    def __repr__(self):
        return self.activity_name

    def __lt__(self, other) -> bool:
        return self.priority < other.priority


class Ruleset:
    def __init__(self, rules: List):
        self.rules = sorted([Rule(*r) if isinstance(r, tuple) else Rule(r) for r in rules], reverse=True)
        a = 5
