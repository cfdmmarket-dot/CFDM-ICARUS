"""
ICARUS Context Engine — Gerencia contexto da sessão atual
"""

import datetime
from collections import deque


class ContextEngine:
    """Mantém contexto da conversa atual em memória"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)
        self.session_data = {}

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        })

    def get_recent(self, n: int = 5) -> str:
        recent = list(self.messages)[-n:]
        lines = []
        for m in recent:
            prefix = "Usuário" if m["role"] == "user" else "ICARUS"
            lines.append(f"{prefix}: {m['content'][:100]}")
        return "\n".join(lines)

    def get_all(self) -> list:
        return list(self.messages)

    def count(self) -> int:
        return len(self.messages)

    def clear(self):
        self.messages.clear()
        self.session_data.clear()

    def set(self, key: str, value):
        self.session_data[key] = value

    def get(self, key: str, default=None):
        return self.session_data.get(key, default)
