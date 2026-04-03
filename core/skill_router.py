"""
ICARUS Skill Router — Detecta intenção e roteia para skill correta
"""

import re
from pathlib import Path


# Mapeamento de palavras-chave → intenção
INTENT_PATTERNS = {
    "tarefa": [r"\btarefa\b", r"\btodo\b", r"\badiciona\b.*tarefa", r"\bcria.*tarefa", r"\blembra.*de"],
    "pesquisa": [r"\bpesquis", r"\bbusca", r"\bprocura", r"\bo que é\b", r"\bcomo funciona"],
    "resumo": [r"\bresum", r"\bsumari", r"\bsinteti"],
    "calendario": [r"\bagend", r"\bcalend", r"\breunião\b", r"\bhorário", r"\bamanhã\b", r"\bhoje\b"],
    "notas": [r"\bnota\b", r"\banota", r"\bsalva", r"\bdocumenta"],
    "projeto": [r"\bprojeto\b", r"\bstatus.*projeto", r"\bprojeto.*status"],
    "nexus": [r"\bagente\b", r"\bnexus\b", r"\bcrew\b", r"\btriplex"],
    "codigo": [r"\bcódigo\b", r"\bscript\b", r"\bpython\b", r"\bprograma"],
    "traducao": [r"\btraduz", r"\btranslat"],
    "escrita": [r"\bescreve\b", r"\bcria.*texto", r"\bredigir", r"\bcopywrite"],
    "financeiro": [
        r"\bfinancas\b", r"\bfinanças\b", r"\bsaldo\b", r"\bconta[s]?\b",
        r"\bvenciment", r"\bpagar\b", r"\bpagamento\b", r"\bprovisao\b",
        r"\bprovisão\b", r"\bfluxo.*caixa\b", r"\bdinheiro\b", r"\breceita\b",
        r"\bdespesa\b", r"\brelatorio.*financ", r"\bfinanceiro"
    ],
    "noticias": [
        r"\bnotic[íi]as\b", r"\bbriefing\b", r"\bmatinal\b", r"\bbom dia\b",
        r"\bnews\b", r"\bmanchet", r"\bo que aconteceu", r"\resumo do dia"
    ],
    "agenda": [
        r"\bagend", r"\bcompromisso", r"\breuni[aã]o\b", r"\bmarcar\b",
        r"\bagendar\b", r"\bcalend", r"\bamanhã\b.*tenho", r"\bhoje.*tenho",
        r"\btenho.*hoje", r"\bpr[oó]ximos.*compromisso"
    ],
}


class SkillRouter:
    """Detecta intenção e retorna skill adequada"""

    def __init__(self):
        self.skills = self._load_skills()

    def _load_skills(self) -> dict:
        """Carrega skills disponíveis — inclui skills builtin"""
        skills = {}

        # Builtin: tarefa
        try:
            from skills.tarefa_skill import TarefaSkill
            skills["tarefa"] = TarefaSkill()
        except Exception:
            pass

        # Builtin: nexus
        try:
            from skills.nexus_skill import NexusSkill
            skills["nexus"] = NexusSkill()
        except Exception:
            pass

        # Builtin: financeiro
        try:
            from skills.financeiro_skill import FinanceiroSkill
            skills["financeiro"] = FinanceiroSkill()
        except Exception:
            pass

        # Builtin: noticias
        try:
            from skills.noticias_skill import NoticiasSkill
            skills["noticias"] = NoticiasSkill()
        except Exception:
            pass

        # Builtin: agenda
        try:
            from skills.agenda_skill import AgendaSkill
            skills["agenda"] = AgendaSkill()
        except Exception:
            pass

        # Carrega skills extras com SKILL_NAME
        skills_dir = Path(__file__).parent.parent / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.py"):
                if skill_file.stem.startswith("_"):
                    continue
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(skill_file.stem, skill_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "SKILL_NAME") and hasattr(module, "Skill"):
                        skills[module.SKILL_NAME] = module.Skill()
                except Exception:
                    pass

        return skills

    def detect_intent(self, text: str) -> str:
        """Detecta a intenção da mensagem"""
        text_lower = text.lower()

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent

        return "geral"

    def get_skill(self, intent: str):
        """Retorna a skill para a intenção detectada"""
        return self.skills.get(intent)
