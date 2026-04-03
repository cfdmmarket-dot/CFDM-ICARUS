"""
ICARUS — Skill de Agenda
Agenda local persistida em memory/agenda.json.
Suporta criar, listar, e cancelar compromissos.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


AGENDA_FILE = Path(__file__).parent.parent / "memory" / "agenda.json"

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def _load() -> list:
    if AGENDA_FILE.exists():
        try:
            return json.loads(AGENDA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save(eventos: list):
    AGENDA_FILE.parent.mkdir(parents=True, exist_ok=True)
    AGENDA_FILE.write_text(json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_data(texto: str) -> str | None:
    """Tenta extrair data do texto. Retorna 'YYYY-MM-DD' ou None."""
    hoje = datetime.now()
    t = texto.lower()

    if "hoje" in t:
        return hoje.strftime("%Y-%m-%d")
    if "amanhã" in t or "amanha" in t:
        return (hoje + timedelta(days=1)).strftime("%Y-%m-%d")
    if "depois de amanhã" in t:
        return (hoje + timedelta(days=2)).strftime("%Y-%m-%d")

    # dia/mes ou dia/mes/ano
    m = re.search(r"(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", t)
    if m:
        dia, mes = int(m.group(1)), int(m.group(2))
        ano = int(m.group(3)) if m.group(3) else hoje.year
        if ano < 100:
            ano += 2000
        try:
            return datetime(ano, mes, dia).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # "15 de abril"
    for nome, num in MESES.items():
        m2 = re.search(rf"(\d{{1,2}})\s+de\s+{nome}", t)
        if m2:
            try:
                return datetime(hoje.year, num, int(m2.group(1))).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def _parse_hora(texto: str) -> str | None:
    """Extrai hora HH:MM do texto."""
    m = re.search(r"(\d{1,2})[:h](\d{2})", texto.lower())
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    m2 = re.search(r"às?\s+(\d{1,2})h?", texto.lower())
    if m2:
        return f"{int(m2.group(1)):02d}:00"
    return None


class AgendaSkill:
    """Skill de agenda local do ICARUS"""

    name = "agenda"
    description = "Agenda local: criar, listar e cancelar compromissos"

    def execute(self, user_input: str, context=None) -> str:
        text = user_input.lower()

        if any(w in text for w in ["cancelar", "remover", "deletar", "apagar"]):
            return self._cancelar(user_input)

        if any(w in text for w in ["agenda de hoje", "hoje tenho", "o que tenho hoje"]):
            return self._listar_dia(datetime.now().strftime("%Y-%m-%d"), "hoje")

        if any(w in text for w in ["amanhã", "amanha"]) and any(w in text for w in ["agenda", "tenho", "compromisso"]):
            d = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            return self._listar_dia(d, "amanhã")

        if any(w in text for w in ["agenda da semana", "semana", "próximos compromissos", "proximos"]):
            return self._listar_semana()

        if any(w in text for w in ["agendar", "marcar", "criar compromisso", "adicionar compromisso", "nova reunião", "novo evento"]):
            return self._criar(user_input)

        if any(w in text for w in ["minha agenda", "ver agenda", "listar agenda", "compromissos"]):
            return self._listar_semana()

        return (
            "Comandos de agenda:\n"
            "  'agenda de hoje'\n"
            "  'agenda de amanhã'\n"
            "  'próximos compromissos'\n"
            "  'agendar reunião com João amanhã às 14h'\n"
            "  'cancelar [número do evento]'"
        )

    def _criar(self, texto: str) -> str:
        data = _parse_data(texto)
        hora = _parse_hora(texto)

        if not data:
            return "Não consegui identificar a data. Ex: 'agendar reunião amanhã às 14h' ou 'marcar call 15/04 às 10h'"

        # Extrai título (remove palavras de comando e data/hora)
        titulo = re.sub(
            r"(agendar|marcar|criar|adicionar|compromisso|reunião|evento|nova|novo|"
            r"hoje|amanhã|amanha|depois de amanhã|\d{1,2}[/\-]\d{1,2}[/\-]?\d*|"
            r"\d{1,2}\s+de\s+\w+|às?\s+\d{1,2}[:h]\d{0,2}h?)",
            "", texto, flags=re.IGNORECASE
        ).strip(" ,.-")

        if not titulo:
            titulo = "Compromisso"

        eventos = _load()
        evento = {
            "id": len(eventos) + 1,
            "titulo": titulo.title(),
            "data": data,
            "hora": hora or "—",
            "criado_em": datetime.now().isoformat()
        }
        eventos.append(evento)
        _save(eventos)

        data_fmt = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        hora_fmt = f" às {hora}" if hora else ""
        return f"✅ Agendado: **{evento['titulo']}** — {data_fmt}{hora_fmt}"

    def _listar_dia(self, data: str, label: str) -> str:
        eventos = [e for e in _load() if e.get("data") == data]
        if not eventos:
            return f"Nenhum compromisso para {label}."

        data_fmt = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        linhas = [f"📅 Agenda de {label} ({data_fmt}):\n"]
        for e in sorted(eventos, key=lambda x: x.get("hora", "99:99")):
            hora = f"{e['hora']} — " if e.get("hora") and e["hora"] != "—" else ""
            linhas.append(f"  [{e['id']}] {hora}{e['titulo']}")
        return "\n".join(linhas)

    def _listar_semana(self) -> str:
        hoje = datetime.now()
        eventos = _load()
        proximos = []

        for e in eventos:
            try:
                d = datetime.strptime(e["data"], "%Y-%m-%d")
                if d >= hoje and (d - hoje).days <= 7:
                    proximos.append((d, e))
            except Exception:
                pass

        if not proximos:
            return "Nenhum compromisso nos próximos 7 dias."

        proximos.sort(key=lambda x: (x[0], x[1].get("hora", "99:99")))
        linhas = ["📅 Próximos compromissos (7 dias):\n"]
        for d, e in proximos:
            data_fmt = d.strftime("%d/%m (%a)").replace(
                "Mon", "Seg").replace("Tue", "Ter").replace("Wed", "Qua").replace(
                "Thu", "Qui").replace("Fri", "Sex").replace("Sat", "Sáb").replace("Sun", "Dom")
            hora = f" {e['hora']}" if e.get("hora") and e["hora"] != "—" else ""
            linhas.append(f"  [{e['id']}] {data_fmt}{hora} — {e['titulo']}")
        return "\n".join(linhas)

    def _cancelar(self, texto: str) -> str:
        m = re.search(r"\b(\d+)\b", texto)
        if not m:
            return "Informe o número do evento. Ex: 'cancelar evento 3'"

        evento_id = int(m.group(1))
        eventos = _load()
        novo = [e for e in eventos if e.get("id") != evento_id]

        if len(novo) == len(eventos):
            return f"Evento #{evento_id} não encontrado."

        _save(novo)
        return f"✅ Evento #{evento_id} cancelado."
