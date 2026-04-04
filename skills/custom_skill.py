"""
ICARUS Custom Responses Skill — Respostas personalizadas configuráveis
"""

import json
import re
from pathlib import Path

SKILL_NAME = "custom"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "custom_responses.json"


def load_responses() -> list:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("responses", [])
    except Exception:
        return []


def match_trigger(text: str, entry: dict) -> bool:
    trigger = entry.get("trigger", "").lower()
    mode = entry.get("match", "contains")
    t = text.lower().strip()

    if mode == "exact":
        return t == trigger
    elif mode == "exact_word":
        return bool(re.search(rf'\b{re.escape(trigger)}\b', t))
    elif mode == "startswith":
        return t.startswith(trigger)
    else:  # contains
        return trigger in t


class Skill:
    """Intercepta entradas que correspondem a respostas personalizadas"""

    def execute(self, user_input: str, context=None) -> str:
        responses = load_responses()
        for entry in responses:
            if match_trigger(user_input, entry):
                return entry.get("response", "")
        return ""

    def has_match(self, user_input: str) -> bool:
        return any(match_trigger(user_input, e) for e in load_responses())
