"""
ICARUS Memory Manager — Persistência de memória e perfil do usuário
"""

import json
import datetime
from pathlib import Path

MEMORY_DIR = Path("/home/cfdm/Proj-CFDM-ICARUS_/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

PROFILE_FILE = MEMORY_DIR / "user_profile.json"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
TASKS_FILE = MEMORY_DIR / "tasks.json"


class MemoryManager:
    """Gerencia memória de longo prazo do ICARUS"""

    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        if not PROFILE_FILE.exists():
            default_profile = {
                "name": "CFDM",
                "language": "pt-BR",
                "timezone": "America/Sao_Paulo",
                "created_at": datetime.datetime.now().isoformat(),
                "preferences": {}
            }
            PROFILE_FILE.write_text(json.dumps(default_profile, indent=2, ensure_ascii=False))

        if not MEMORIES_FILE.exists():
            MEMORIES_FILE.write_text("[]")

        if not TASKS_FILE.exists():
            TASKS_FILE.write_text("[]")

    def load_profile(self) -> dict:
        try:
            return json.loads(PROFILE_FILE.read_text())
        except Exception:
            return {"name": "CFDM", "language": "pt-BR"}

    def save_profile(self, profile: dict):
        PROFILE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False))

    def maybe_save(self, user_input: str, response: str, intent: str):
        """Salva na memória se for informação relevante"""
        keywords = ["meu nome", "prefiro", "sempre", "nunca", "lembra", "importante", "projeto"]
        if any(kw in user_input.lower() for kw in keywords):
            self.save_memory(user_input, intent)

    def save_memory(self, content: str, category: str = "general"):
        memories = self._load_memories()
        memories.append({
            "content": content,
            "category": category,
            "timestamp": datetime.datetime.now().isoformat()
        })
        # Mantém últimas 500 memórias
        if len(memories) > 500:
            memories = memories[-500:]
        MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False))

    def get_recent(self, n: int = 5) -> list:
        memories = self._load_memories()
        return [m["content"][:80] for m in memories[-n:]]

    def count(self) -> int:
        return len(self._load_memories())

    def _load_memories(self) -> list:
        try:
            return json.loads(MEMORIES_FILE.read_text())
        except Exception:
            return []

    def get_tasks(self) -> list:
        try:
            return json.loads(TASKS_FILE.read_text())
        except Exception:
            return []

    def add_task(self, task: str, priority: str = "normal") -> dict:
        tasks = self.get_tasks()
        new_task = {
            "id": len(tasks) + 1,
            "task": task,
            "priority": priority,
            "status": "⏳",
            "created_at": datetime.datetime.now().isoformat()
        }
        tasks.append(new_task)
        TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))
        return new_task

    def complete_task(self, task_id: int):
        tasks = self.get_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "✅"
                t["completed_at"] = datetime.datetime.now().isoformat()
        TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))
