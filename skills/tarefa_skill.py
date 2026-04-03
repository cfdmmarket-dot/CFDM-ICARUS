"""
ICARUS Skill — Gerenciamento de Tarefas
"""

SKILL_NAME = "tarefa"


class Skill:
    """Gerencia tarefas e lembretes"""

    def execute(self, user_input: str, context) -> str:
        import re
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from core.memory_manager import MemoryManager

        memory = MemoryManager()

        # Detecta se é adição de tarefa
        add_patterns = [r"(?:adiciona|cria|coloca|anota|lembra de|lembrar de)\s+(.+)", r"tarefa[:\s]+(.+)"]
        for pattern in add_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                task_text = match.group(1).strip()
                # Capitaliza e remove pontuação desnecessária
                task_text = task_text.rstrip(".,!?")
                task = memory.add_task(task_text)
                return f"✅ Tarefa #{task['id']} adicionada: \"{task_text}\""

        # Lista tarefas
        tasks = memory.get_tasks()
        pending = [t for t in tasks if t["status"] == "⏳"]
        done = [t for t in tasks if t["status"] == "✅"]

        if not tasks:
            return "Nenhuma tarefa ainda. Diga 'adiciona tarefa: [descrição]' para criar uma."

        lines = [f"Tarefas ({len(pending)} pendentes, {len(done)} concluídas):"]
        for t in pending[-10:]:
            lines.append(f"  [{t['id']}] {t['status']} {t['task']}")
        if done:
            lines.append(f"\n  ({len(done)} concluídas — use /tarefas para ver tudo)")

        return "\n".join(lines)
