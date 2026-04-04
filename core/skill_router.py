"""
ICARUS Skill Router — Detecta intenção e roteia para skill correta
"""

import re
import json
from pathlib import Path

# Referência global para hot-reload de skills (usada por autocode_skill)
_global_router = None

DYNAMIC_JSON = Path(__file__).parent.parent / "config" / "dynamic_skills.json"


def _load_dynamic_patterns() -> dict:
    """Carrega padrões de skills criadas dinamicamente."""
    try:
        with open(DYNAMIC_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for name, info in data.items():
            patterns = info.get("patterns", [])
            if patterns:
                result[name] = patterns
        return result
    except Exception:
        return {}


# Mapeamento de palavras-chave → intenção
INTENT_PATTERNS = {
    "tarefa": [r"\btarefa\b", r"\btodo\b", r"\badiciona\b.*tarefa", r"\bcria.*tarefa", r"\blembra.*de"],
    "resumo": [r"\bresum", r"\bsumari", r"\bsinteti"],
    "notas": [r"\bnota\b", r"\banota", r"\bsalva", r"\bdocumenta"],
    "projeto": [r"\bprojeto\b", r"\bstatus.*projeto", r"\bprojeto.*status"],
    "nexus": [r"\bagente\b", r"\bnexus\b", r"\bcrew\b", r"\btriplex", r"\bexecutar agente\b"],
    "codigo": [r"\bcódigo\b", r"\bscript\b", r"\bprograma"],
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
    # ── Novas skills ──────────────────────────────────────
    "sistema": [
        r"\bque horas\b", r"\bhoras s[aã]o\b", r"\bque hora\b", r"\bhora atual\b",
        r"\bque dia\b", r"\bdata de hoje\b", r"\bdia [eé] hoje\b",
        r"\bscreenshot\b", r"\bcaptura de tela\b", r"\btirar foto da tela\b", r"\bprint da tela\b",
        r"\btocar m[uú]sica\b", r"\bparar m[uú]sica\b", r"\bplay m[uú]sica\b", r"\bliga a m[uú]sica\b",
        r"\bvolume\b",
        r"\bpiada\b", r"\bconta uma piada\b",
        r"\babrir\b", r"\babre\b", r"\babra\b", r"\blançar\b", r"\biniciar\b",
    ],
    "busca": [
        r"\bo que [eé]\b", r"\bo que s[aã]o\b", r"\bquem foi\b", r"\bquem [eé]\b",
        r"\bme fala sobre\b", r"\bwikip[eé]dia\b",
        r"\btempo em\b", r"\bclima em\b", r"\btemperatura em\b", r"\bprevis[aã]o do tempo\b",
        r"\bpesquisar\b", r"\bbuscar no google\b", r"\bgooglar\b",
    ],
    "rpi": [
        r"\bligar luz\b", r"\bdesligar luz\b", r"\bacender luz\b", r"\bapagar luz\b",
        r"\bar.condicionado\b", r"\bventilador\b", r"\bcampainha\b",
        r"\bgpio\b", r"\braspberry\b", r"\btomada\b",
        r"\bligar .*(sala|quarto|cozinha|banheiro)\b",
        r"\bdesligar .*(sala|quarto|cozinha|banheiro)\b",
    ],
    "projeto": [
        r"\bprojeto[s]?\b",
        r"\bstatus do (icarus|note|nexus|cfdm)\b",
        r"\bcomo (está|esta) o (icarus|note|nexus)\b",
        r"\bpróximos? passos?\b",
        r"\bbacklog\b",
        r"\bhistórico.*sessão\b",
        r"\bo que foi feito\b",
        r"\bsessões? recentes?\b",
        r"\bversão do (icarus|note|nexus)\b",
        r"\bregist(r|ra).*mudança\b",
        r"\bdelegar? (ao|para o) nexus\b",
        r"\banalis[ae].*projeto\b",
        r"\bvisão geral.*projeto\b",
    ],
    "autocode": [
        r"\bcriar?\s+skill\b",
        r"\bnova\s+skill\b",
        r"\bautocodificar?\b",
        r"\bcria\s+.*\b(skill|agente)\b",
        r"\bgerar?\s+.*skill\b",
        r"\bconstru[ií]r?\s+.*skill\b",
        r"\bimplementar?\s+skill\b",
        r"\bskills?\s+criadas?\b",
        r"\blistar?\s+skills?\b",
        r"\bdeletar?\s+skill\b",
        r"\bremover?\s+skill\b",
    ],
}


class SkillRouter:
    """Detecta intenção e retorna skill adequada"""

    def __init__(self):
        self.skills = self._load_skills()
        # Expõe referência global para hot-reload de skills criadas por autocode
        global _global_router
        _global_router = self

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

        # Builtin: sistema (OS automations)
        try:
            from skills.sistema_skill import Skill as SistemaSkill
            skills["sistema"] = SistemaSkill()
        except Exception:
            pass

        # Builtin: busca (Wikipedia + clima + Google)
        try:
            from skills.busca_skill import Skill as BuscaSkill
            skills["busca"] = BuscaSkill()
        except Exception:
            pass

        # Builtin: rpi (GPIO — só ativo em Raspberry Pi)
        try:
            from skills.rpi_skill import Skill as RpiSkill
            skills["rpi"] = RpiSkill()
        except Exception:
            pass

        # Builtin: autocode (Agente Architect — cria skills dinamicamente)
        try:
            from skills.autocode_skill import Skill as AutocodeSkill
            skills["autocode"] = AutocodeSkill()
        except Exception:
            pass

        # Builtin: projeto (memória viva dos projetos CFDM)
        try:
            from skills.projeto_skill import Skill as ProjetoSkill
            skills["projeto"] = ProjetoSkill()
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

        # Verifica padrões de skills criadas dinamicamente
        dynamic = _load_dynamic_patterns()
        for intent, patterns in dynamic.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text_lower):
                        return intent
                except re.error:
                    pass

        return "geral"

    def get_skill(self, intent: str):
        """Retorna a skill para a intenção detectada"""
        return self.skills.get(intent)
