"""
ICARUS Skill — Auto-Codificação (Agente Architect)
Cria novas skills em linguagem natural usando o Nexus LLM.
Gera código Python, escreve em skills/, registra padrões, recarrega roteador.
"""

import re
import json
import importlib.util
import requests
from pathlib import Path

SKILL_NAME = "autocode"

SKILLS_DIR  = Path(__file__).parent
CONFIG_DIR  = SKILLS_DIR.parent / "config"
DYNAMIC_JSON = CONFIG_DIR / "dynamic_skills.json"
NEXUS_URL   = "http://localhost:8000/chat"

# ── Prompt-template enviado ao Nexus LLM ─────────────────────────────────────
_SYSTEM_PROMPT = """Você é um engenheiro de software especialista em Python.
Sua tarefa: criar um módulo de skill Python para o assistente ICARUS.

TEMPLATE OBRIGATÓRIO:
```python
\"\"\"
ICARUS Skill — {description}
\"\"\"
import re
from pathlib import Path

SKILL_NAME = "{skill_name}"      # identificador único, snake_case

TRIGGER_PATTERNS = [             # regex que ativam esta skill
    r"\\bprimeiro padrao\\b",
    r"\\bsegundo padrao\\b",
]

class Skill:
    def execute(self, user_input: str, context=None) -> str:
        # Implemente a lógica aqui
        return "Resposta da skill"
```

REGRAS:
1. Retorne APENAS o bloco de código Python (dentro de ```python ... ```)
2. SKILL_NAME deve ser snake_case, curto, descritivo
3. TRIGGER_PATTERNS deve ter pelo menos 2 padrões regex em português
4. A classe Skill deve ter execute(self, user_input, context) -> str
5. Respostas em português brasileiro
6. Sem imports externos que não sejam stdlib ou requests
7. Trate erros com try/except e retorne mensagem amigável
"""


def _ask_nexus(description: str) -> str:
    """Chama o Nexus LLM para gerar o código da skill."""
    try:
        payload = {
            "message": f"Crie uma skill ICARUS para: {description}",
            "provider": "auto",
            "system": _SYSTEM_PROMPT,
        }
        r = requests.post(NEXUS_URL, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            return data.get("content") or data.get("response") or ""
    except Exception as e:
        return f"ERRO:{e}"
    return ""


def _extract_code(llm_response: str) -> str:
    """Extrai bloco ```python ... ``` da resposta do LLM."""
    m = re.search(r"```python\s*([\s\S]+?)```", llm_response)
    if m:
        return m.group(1).strip()
    # Fallback: tenta encontrar código mesmo sem fence
    if "class Skill" in llm_response and "SKILL_NAME" in llm_response:
        return llm_response.strip()
    return ""


def _sanitize_name(text: str) -> str:
    """Gera um nome de arquivo seguro a partir da descrição."""
    name = re.sub(r"[^\w\s]", "", text.lower())
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"_+", "_", name)[:32]
    return name or "custom"


def _extract_skill_name(code: str) -> str:
    """Extrai SKILL_NAME = '...' do código gerado."""
    m = re.search(r'SKILL_NAME\s*=\s*["\']([^"\']+)["\']', code)
    return m.group(1) if m else "custom"


def _extract_patterns(code: str) -> list:
    """Extrai lista TRIGGER_PATTERNS do código gerado."""
    m = re.search(r"TRIGGER_PATTERNS\s*=\s*\[([\s\S]+?)\]", code)
    if not m:
        return []
    raw = m.group(1)
    patterns = re.findall(r'r["\']([^"\']+)["\']', raw)
    return patterns


def _load_dynamic_skills() -> dict:
    """Lê config/dynamic_skills.json."""
    try:
        with open(DYNAMIC_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_dynamic_skills(data: dict):
    """Persiste config/dynamic_skills.json."""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(DYNAMIC_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _hot_load(skill_file: Path):
    """Importa o módulo recém-criado e injeta no roteador global, se disponível."""
    try:
        spec = importlib.util.spec_from_file_location(skill_file.stem, skill_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Tenta injetar no SkillRouter que está rodando
        try:
            from core.skill_router import _global_router  # injetado pelo server
            if _global_router is not None and hasattr(module, "SKILL_NAME") and hasattr(module, "Skill"):
                _global_router.skills[module.SKILL_NAME] = module.Skill()
                # Injeta padrões dinamicamente
                patterns = _extract_patterns(open(skill_file).read())
                if patterns:
                    from core.skill_router import INTENT_PATTERNS
                    INTENT_PATTERNS[module.SKILL_NAME] = [r + "" for r in patterns]
        except Exception:
            pass

        return True
    except Exception:
        return False


def _validate_code(code: str) -> tuple[bool, str]:
    """Valida sintaxe Python básica antes de escrever."""
    import ast
    try:
        ast.parse(code)
        if "class Skill" not in code:
            return False, "Código não contém 'class Skill'"
        if "SKILL_NAME" not in code:
            return False, "Código não contém 'SKILL_NAME'"
        if "def execute" not in code:
            return False, "Código não contém 'def execute'"
        return True, "ok"
    except SyntaxError as e:
        return False, f"Erro de sintaxe: {e}"


class Skill:
    """Agente Architect — cria novas skills sob demanda."""

    def execute(self, user_input: str, context=None) -> str:
        t = user_input.strip()

        # ── Listar skills dinâmicas ───────────────────────────────
        if re.search(r"\blistar?\b.*\b(skills?|agentes?)\b|\bskills? criadas?\b", t.lower()):
            return self._list_skills()

        # ── Deletar skill ─────────────────────────────────────────
        m_del = re.search(r"(?:deletar?|remover?|apagar?)\s+skill\s+[\"']?(\w+)[\"']?", t.lower())
        if m_del:
            return self._delete_skill(m_del.group(1))

        # ── Criar nova skill ──────────────────────────────────────
        description = self._parse_description(t)
        if not description:
            return (
                "Descreva o que a nova skill deve fazer.\n"
                "Exemplos:\n"
                "• _criar skill para verificar o clima_\n"
                "• _nova skill para consultar CEP_\n"
                "• _gerar skill de motivação diária_"
            )

        return self._create_skill(description)

    # ── Helpers ───────────────────────────────────────────────────

    def _parse_description(self, text: str) -> str:
        """Extrai a descrição da skill do comando do usuário."""
        patterns = [
            r"(?:criar?|cria|nova|gerar?|construir?|implementar?|desenvolver?)\s+skill\s+(?:para|de|do|da|que|para)\s+(.+)",
            r"(?:criar?|cria|nova|gerar?|construir?|implementar?|desenvolver?)\s+skill\s+(.+)",
            r"(?:autocodificar?|auto.codificar?)\s+(.+)",
            r"skill\s+(?:para|de|do|da|que)\s+(.+)",
            r"(?:cria|criar?)\s+(?:um|uma)?\s*(?:agente|skill|módulo)\s+(?:para|de|do|da|que)\s+(.+)",
        ]
        t = text.lower()
        for p in patterns:
            m = re.search(p, t)
            if m:
                desc = m.group(1).strip().rstrip(".,!?")
                if len(desc) >= 5:
                    return desc
        return ""

    def _create_skill(self, description: str) -> str:
        """Pipeline completo: LLM → validar → escrever → registrar → hot-load."""
        # 1. Gera código via Nexus
        llm_resp = _ask_nexus(description)

        if llm_resp.startswith("ERRO:") or not llm_resp:
            return (
                f"Nexus offline ou sem resposta. Não foi possível gerar a skill.\n"
                f"Inicie o Cfdm Nexus na porta 8000 e tente novamente."
            )

        # 2. Extrai bloco de código
        code = _extract_code(llm_resp)
        if not code:
            return (
                "O LLM não retornou um bloco de código válido.\n"
                "Resposta recebida:\n```\n"
                + llm_resp[:500]
                + "\n```"
            )

        # 3. Valida sintaxe
        ok, err = _validate_code(code)
        if not ok:
            return f"Código gerado inválido: {err}\n\nCódigo recebido:\n```python\n{code[:400]}\n```"

        # 4. Determina nome do arquivo
        skill_name = _extract_skill_name(code)
        file_name = f"{_sanitize_name(description)}_skill.py"
        skill_file = SKILLS_DIR / file_name

        # Evita sobrescrever skills builtin
        builtin = {"tarefa", "nexus", "financeiro", "noticias", "agenda",
                   "sistema", "busca", "rpi", "custom", "autocode", "voz"}
        if skill_name in builtin:
            skill_name = f"dyn_{skill_name}"

        # 5. Escreve arquivo
        try:
            skill_file.write_text(code, encoding="utf-8")
        except Exception as e:
            return f"Erro ao gravar arquivo: {e}"

        # 6. Registra padrões em dynamic_skills.json
        patterns = _extract_patterns(code)
        dynamic = _load_dynamic_skills()
        dynamic[skill_name] = {
            "file": file_name,
            "description": description,
            "patterns": patterns,
        }
        _save_dynamic_skills(dynamic)

        # 7. Hot-load
        loaded = _hot_load(skill_file)
        reload_note = "Skill carregada em memória." if loaded else "Reinicie o ICARUS para ativar a skill."

        # 8. Resposta
        return (
            f"Skill **{skill_name}** criada com sucesso!\n\n"
            f"Arquivo: `skills/{file_name}`\n"
            f"Padrões de ativação: {len(patterns)} detectados\n"
            f"Status: {reload_note}\n\n"
            f"```python\n{code[:600]}{'...' if len(code) > 600 else ''}\n```"
        )

    def _list_skills(self) -> str:
        dynamic = _load_dynamic_skills()
        if not dynamic:
            return "Nenhuma skill dinâmica criada ainda. Use 'criar skill para X'."
        lines = ["Skills dinâmicas criadas:\n"]
        for name, info in dynamic.items():
            lines.append(f"• **{name}** — {info.get('description', '')}")
            lines.append(f"  Arquivo: `skills/{info.get('file', '')}`")
            p = info.get("patterns", [])
            if p:
                lines.append(f"  Padrões: {', '.join(p[:3])}")
        return "\n".join(lines)

    def _delete_skill(self, name: str) -> str:
        dynamic = _load_dynamic_skills()
        if name not in dynamic:
            return f"Skill '{name}' não encontrada nas skills dinâmicas."
        file_name = dynamic[name].get("file", "")
        skill_file = SKILLS_DIR / file_name
        try:
            if skill_file.exists():
                skill_file.unlink()
        except Exception as e:
            return f"Erro ao deletar arquivo: {e}"
        del dynamic[name]
        _save_dynamic_skills(dynamic)
        return f"Skill **{name}** removida. Arquivo `{file_name}` deletado."
