"""
ICARUS — Skill Financeira (Sentinela Financeiro)
Verifica contas, calcula provisões e monitora fluxo de caixa.
"""

import json
import datetime
from pathlib import Path


MEMORY_PATH = Path(__file__).parent.parent / "memory"


class FinanceiroSkill:
    """Sentinela Financeiro do ICARUS"""

    name = "financeiro"
    description = "Gestão financeira: contas, saldo, provisão, relatórios"

    def execute(self, user_input: str, context=None) -> str:
        text = user_input.lower()

        if any(w in text for w in ["contas vencendo", "vencimento", "vence", "vencendo"]):
            return self._check_due_accounts()

        if any(w in text for w in ["saldo", "disponível", "quanto tenho"]):
            return self._check_balance()

        if any(w in text for w in ["provisionar", "provisão", "provisao"]):
            return self._provision()

        if any(w in text for w in ["relatório", "relatorio", "resumo financeiro", "balanço", "balanco"]):
            return self._financial_report()

        if any(w in text for w in ["adicionar conta", "nova conta", "registrar conta"]):
            return self._add_account_guide()

        return self._financial_overview()

    def _financial_overview(self) -> str:
        finance = self._load_finance()
        contas = finance.get("contas", [])
        saldo = finance.get("saldo_disponivel", 0)
        hoje = datetime.date.today()

        vencendo = [c for c in contas if self._days_to_due(c.get("vencimento", "")) <= 7]

        lines = [f"Visão Financeira — {hoje.strftime('%d/%m/%Y')}"]
        lines.append(f"Saldo disponível: R$ {saldo:.2f}")
        lines.append(f"Contas registradas: {len(contas)}")

        if vencendo:
            total = sum(c.get("valor", 0) for c in vencendo)
            lines.append(f"\n⚠️ Vencendo nos próximos 7 dias: {len(vencendo)} conta(s) — R$ {total:.2f}")
            for c in vencendo:
                days = self._days_to_due(c.get("vencimento", ""))
                lines.append(f"  • {c.get('descricao', 'N/A')} — R$ {c.get('valor', 0):.2f} (em {days}d)")
        else:
            lines.append("Nenhuma conta vencendo nos próximos 7 dias.")

        return "\n".join(lines)

    def _check_due_accounts(self) -> str:
        finance = self._load_finance()
        contas = finance.get("contas", [])
        hoje = datetime.date.today()

        vencendo = sorted(
            [c for c in contas if c.get("status") != "pago"],
            key=lambda c: self._days_to_due(c.get("vencimento", ""))
        )

        if not vencendo:
            return "Nenhuma conta pendente registrada."

        lines = [f"Contas pendentes ({len(vencendo)}):"]
        for c in vencendo:
            days = self._days_to_due(c.get("vencimento", ""))
            status = "🔴 VENCIDA" if days < 0 else f"em {days}d"
            lines.append(f"  • {c.get('descricao', 'N/A')} — R$ {c.get('valor', 0):.2f} ({status})")

        return "\n".join(lines)

    def _check_balance(self) -> str:
        finance = self._load_finance()
        saldo = finance.get("saldo_disponivel", 0)
        contas = finance.get("contas", [])
        total_devendo = sum(c.get("valor", 0) for c in contas if c.get("status") != "pago")

        result = f"Saldo disponível: R$ {saldo:.2f}\n"
        result += f"Total em contas pendentes: R$ {total_devendo:.2f}\n"

        if saldo >= total_devendo:
            resultado = saldo - total_devendo
            result += f"Saldo após provisão: R$ {resultado:.2f} ✅"
        else:
            deficit = total_devendo - saldo
            result += f"Déficit: R$ {deficit:.2f} ⚠️ — Buscar renda extra recomendado."

        return result

    def _provision(self) -> str:
        finance = self._load_finance()
        saldo = finance.get("saldo_disponivel", 0)
        contas = finance.get("contas", [])
        total = sum(c.get("valor", 0) for c in contas if c.get("status") != "pago")

        if saldo >= total:
            return f"Montante de R$ {total:.2f} verde-sinalizado para provisão.\nSaldo restante após provisão: R$ {saldo - total:.2f} ✅"
        else:
            faltando = total - saldo
            return f"Montante atual (R$ {saldo:.2f}) insuficiente.\nFaltam R$ {faltando:.2f} para cobrir as contas.\nAtivando busca por Renda Extra no banco de dados..."

    def _financial_report(self) -> str:
        finance = self._load_finance()
        contas = finance.get("contas", [])
        saldo = finance.get("saldo_disponivel", 0)
        hoje = datetime.date.today()

        pagas = [c for c in contas if c.get("status") == "pago"]
        pendentes = [c for c in contas if c.get("status") != "pago"]

        total_pago = sum(c.get("valor", 0) for c in pagas)
        total_pendente = sum(c.get("valor", 0) for c in pendentes)

        report = [
            f"Relatório Financeiro — {hoje.strftime('%d/%m/%Y')}",
            f"{'='*40}",
            f"Saldo disponível:     R$ {saldo:.2f}",
            f"Total pago (mês):     R$ {total_pago:.2f}",
            f"Total pendente:       R$ {total_pendente:.2f}",
            f"Saldo após provisão:  R$ {saldo - total_pendente:.2f}",
            f"{'='*40}",
            f"Contas pagas: {len(pagas)} | Pendentes: {len(pendentes)}"
        ]

        return "\n".join(report)

    def _add_account_guide(self) -> str:
        return """Para adicionar conta, edite o arquivo:
~/Proj-CFDM-ICARUS_/memory/finance.json

Formato:
{
  "contas": [
    {
      "descricao": "Nome da conta",
      "valor": 0.00,
      "vencimento": "YYYY-MM-DD",
      "status": "pendente"
    }
  ],
  "saldo_disponivel": 0.00
}"""

    def _load_finance(self) -> dict:
        finance_file = MEMORY_PATH / "finance.json"
        if finance_file.exists():
            try:
                with open(finance_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Retorna estrutura padrão vazia
        return {"contas": [], "saldo_disponivel": 0.0}

    def _days_to_due(self, vencimento_str: str) -> int:
        """Calcula dias até vencimento"""
        if not vencimento_str:
            return 999
        try:
            due = datetime.date.fromisoformat(vencimento_str)
            return (due - datetime.date.today()).days
        except ValueError:
            return 999
