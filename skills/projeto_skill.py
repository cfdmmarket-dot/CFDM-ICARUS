"""
ICARUS Skill — Projetos CFDM Holding
Memória viva dos projetos: status, histórico, próximos passos.
Delega tarefas ao Cfdm Nexus quando solicitado.
"""

import json
import re
import datetime
import requests
from pathlib import Path

SKILL_NAME = "projeto"

PROJECTS_FILE = Path(__file__).parent.parent / "memory" / "projects.json"
NEXUS_URL = "http://localhost:8000/chat"


# ── Helpers de I/O ────────────────────────────────────────────────────────────

def _load() -> dict:
    try:
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"projects": {}, "sessoes_recentes": []}


def _save(data: dict):
    data["_meta"]["last_sync"] = datetime.datetime.now().isoformat()
    PROJECTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _projects(data: dict) -> dict:
    return data.get("projects", {})


def _find_project(text: str, data: dict) -> tuple[str, dict] | tuple[None, None]:
    """Localiza projeto pelo nome na entrada do usuário."""
    aliases = {
        "icarus": "ICARUS",
        "note": "CfdmNote", "cfdmnote": "CfdmNote", "note c++": "CfdmNote",
        "nexus": "CfdmNexus", "cfdm nexus": "CfdmNexus", "triplex": "CfdmNexus",
        "keepsidian": "Keepsidian",
    }
    t = text.lower()
    for alias, key in aliases.items():
        if alias in t:
            p = _projects(data).get(key)
            if p:
                return key, p
    # Fallback — tenta por nome direto
    for key, p in _projects(data).items():
        if key.lower() in t or p["nome"].lower() in t:
            return key, p
    return None, None


def _nexus_ask(prompt: str) -> str:
    """Delega uma pergunta ao Nexus LLM."""
    try:
        r = requests.post(NEXUS_URL, json={
            "message": prompt,
            "provider": "auto",
            "system": "Você é um consultor técnico da CFDM Holding. Seja direto e prático."
        }, timeout=30)
        if r.status_code == 200:
            d = r.json()
            return d.get("content") or d.get("response") or ""
    except Exception:
        pass
    return ""


# ── Classe principal ───────────────────────────────────────────────────────────

class Skill:
    """Gerencia memória dos projetos CFDM e delega ao Nexus."""

    def execute(self, user_input: str, context=None) -> str:
        t = user_input.lower().strip()
        data = _load()

        # ── Listar todos os projetos ──────────────────────────────
        if re.search(r"\blistar?\b.*projeto|todos.*projeto|meus projeto|visão geral.*projeto|overview", t):
            return self._list_all(data)

        # ── Sessões recentes / histórico ──────────────────────────
        if re.search(r"\bhistórico\b|\bsessões?\b|\bo que foi feito\b|\brecente\b", t):
            return self._recent_sessions(data)

        # ── Próximos passos ───────────────────────────────────────
        if re.search(r"\bpróxim[oa]s?\s+(passo|etapa|feature|tarefa|sprint)\b|\bbacklog\b|\bo que falta\b", t):
            key, proj = _find_project(t, data)
            return self._next_steps(key, proj, data)

        # ── Status de projeto específico ──────────────────────────
        if re.search(r"\bstatus\b|\bsituação\b|\bdetalhes?\b|\bcomo está\b|\bversão\b", t):
            key, proj = _find_project(t, data)
            if proj:
                return self._project_detail(key, proj)
            return self._list_all(data)

        # ── Registrar mudança / atualizar memória ─────────────────
        m_upd = re.search(
            r"(?:registr|salv|anot|document|atualiz).*?(?:no projeto|em|do projeto)\s+(\w+)[:\s]+(.+)",
            t
        )
        if m_upd:
            return self._log_change(m_upd.group(1), m_upd.group(2), data)

        # ── Delegar tarefa ao Nexus para o projeto ────────────────
        if re.search(r"\bdelegar?\b|\bpedir ao nexus\b|\bmandar o nexus\b|\bpede pro nexus\b", t):
            return self._delegate_to_nexus(user_input, data)

        # ── Análise de projeto pelo Nexus ─────────────────────────
        if re.search(r"\banalisa\b|\banalise\b|\bavali[ae]\b|\bsugest[aã]o\b|\brecomend", t):
            key, proj = _find_project(t, data)
            return self._analyze_with_nexus(key, proj, user_input)

        # ── Fallback: status geral ────────────────────────────────
        key, proj = _find_project(t, data)
        if proj:
            return self._project_detail(key, proj)
        return self._list_all(data)

    # ── Formatadores ──────────────────────────────────────────────────────────

    def _list_all(self, data: dict) -> str:
        projs = _projects(data)
        lines = ["**Projetos CFDM Holding**\n"]
        status_icon = {"ativo": "🟢", "legado": "🟡", "pausado": "🔴"}
        for key, p in projs.items():
            icon = status_icon.get(p.get("status", ""), "⚪")
            ver  = p.get("versao", "—")
            desc = p.get("descricao", "")[:70]
            porta = f" · porta {p['porta']}" if p.get("porta") else ""
            lines.append(f"{icon} **{p['nome']}** v{ver}{porta}")
            lines.append(f"   {desc}")
            proximos = p.get("proximos_passos", [])
            if proximos:
                lines.append(f"   → próximo: {proximos[0]}")
            lines.append("")
        sync = data.get("_meta", {}).get("last_sync", "")[:10]
        lines.append(f"_Memória sincronizada em: {sync}_")
        return "\n".join(lines)

    def _project_detail(self, key: str, proj: dict) -> str:
        status_icon = {"ativo": "🟢", "legado": "🟡", "pausado": "🔴"}
        icon = status_icon.get(proj.get("status", ""), "⚪")
        lines = [
            f"{icon} **{proj['nome']}** v{proj.get('versao','—')} — {proj.get('status','').upper()}",
            f"{proj.get('subtitulo','')}",
            "",
            f"**Stack:** {', '.join(proj.get('stack', []))}",
        ]
        if proj.get("porta"):
            lines.append(f"**Porta:** {proj['porta']}")
        if proj.get("binario"):
            lines.append(f"**Binário:** `{proj['binario']}`")
        lines.append(f"\n**Descrição:** {proj.get('descricao','')}")

        changes = proj.get("ultimas_mudancas", [])
        if changes:
            lines.append("\n**Últimas mudanças:**")
            for c in changes[:4]:
                lines.append(f"  • {c}")

        proximos = proj.get("proximos_passos", [])
        if proximos:
            lines.append("\n**Próximos passos:**")
            for p in proximos[:4]:
                lines.append(f"  → {p}")

        if proj.get("notas"):
            lines.append(f"\n💡 {proj['notas']}")

        return "\n".join(lines)

    def _next_steps(self, key, proj, data) -> str:
        if not proj:
            # Agrega próximos passos de todos os projetos ativos
            lines = ["**Backlog — Próximos Passos por Projeto:**\n"]
            for k, p in _projects(data).items():
                if p.get("status") == "legado":
                    continue
                steps = p.get("proximos_passos", [])
                if steps:
                    lines.append(f"🔹 **{p['nome']}**")
                    for s in steps[:3]:
                        lines.append(f"   → {s}")
                    lines.append("")
            return "\n".join(lines)

        steps = proj.get("proximos_passos", [])
        if not steps:
            return f"Sem próximos passos registrados para **{proj['nome']}**."
        lines = [f"**Próximos passos — {proj['nome']}:**\n"]
        for i, s in enumerate(steps, 1):
            lines.append(f"  {i}. {s}")
        return "\n".join(lines)

    def _recent_sessions(self, data: dict) -> str:
        sessions = data.get("sessoes_recentes", [])
        if not sessions:
            return "Nenhuma sessão registrada ainda."
        lines = ["**Sessões Recentes:**\n"]
        for s in reversed(sessions[-6:]):
            lines.append(f"📅 **{s['data']}** — {s['projeto']} v{s.get('versao_resultante','?')}")
            lines.append(f"   {s['resumo']}")
            arqs = s.get("arquivos_modificados", [])
            if arqs:
                lines.append(f"   _Arquivos: {', '.join(arqs[:3])}{'...' if len(arqs)>3 else ''}_")
            lines.append("")
        return "\n".join(lines)

    def _log_change(self, proj_hint: str, change_text: str, data: dict) -> str:
        key, proj = _find_project(proj_hint, data)
        if not proj:
            return f"Projeto '{proj_hint}' não encontrado. Projetos: {', '.join(_projects(data).keys())}"
        proj.setdefault("ultimas_mudancas", []).insert(0, change_text.strip())
        proj["ultimas_mudancas"] = proj["ultimas_mudancas"][:10]
        data["projects"][key] = proj
        _save(data)
        return f"✅ Mudança registrada em **{proj['nome']}**:\n_{change_text.strip()}_"

    def _delegate_to_nexus(self, user_input: str, data: dict) -> str:
        key, proj = _find_project(user_input.lower(), data)
        context = ""
        if proj:
            context = (
                f"Projeto: {proj['nome']} v{proj.get('versao','?')}\n"
                f"Stack: {', '.join(proj.get('stack',[]))}\n"
                f"Descrição: {proj.get('descricao','')}\n"
            )
        prompt = f"{context}\nTarefa solicitada: {user_input}"
        resp = _nexus_ask(prompt)
        if resp:
            return f"**Nexus:** {resp}"
        return "Nexus offline. Inicie o Cfdm Nexus na porta 8000."

    def _analyze_with_nexus(self, key, proj, user_input: str) -> str:
        if not proj:
            return self._delegate_to_nexus(user_input, _load())
        context = (
            f"Analise o seguinte projeto da CFDM Holding:\n"
            f"Nome: {proj['nome']} v{proj.get('versao','?')}\n"
            f"Stack: {', '.join(proj.get('stack',[]))}\n"
            f"Descrição: {proj.get('descricao','')}\n"
            f"Próximos passos planejados: {'; '.join(proj.get('proximos_passos',[])[:3])}\n\n"
            f"Pedido: {user_input}"
        )
        resp = _nexus_ask(context)
        if resp:
            return f"**Análise Nexus — {proj['nome']}:**\n\n{resp}"
        return "Nexus offline. Inicie o Cfdm Nexus na porta 8000."
