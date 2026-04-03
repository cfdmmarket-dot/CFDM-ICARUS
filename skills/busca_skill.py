"""
ICARUS Skill — Busca & Informação
Wikipedia (PT), clima (wttr.in), pesquisa Google
Sem API keys — tudo via HTTP público
"""

import urllib.request
import urllib.parse
import json
import re
import shutil
import subprocess

SKILL_NAME = "busca"


class Skill:
    def execute(self, user_input: str, context) -> str:
        t = user_input.lower().strip()

        # Clima / Tempo
        if re.search(r"tempo em|clima em|temperatura em|previs[aã]o.*tempo|como est[aá] o tempo", t):
            return self._weather(t)

        # Wikipedia — perguntas de definição
        if re.search(r"o que [eé]|quem foi|quem [eé]|me fala sobre|wikipedia|wikip[eé]dia|o que s[aã]o|como funciona|what is", t):
            return self._wikipedia(t)

        # Pesquisa geral (abre browser)
        if re.search(r"pesquisar?\s+|buscar?\s+|procurar?\s+|googl", t):
            return self._google(t)

        return (
            "Comandos de busca:\n"
            "• **Wikipedia**: 'o que é machine learning', 'quem foi Einstein'\n"
            "• **Clima**: 'tempo em Lisboa', 'clima em São Paulo'\n"
            "• **Google**: 'pesquisar receitas de bolo'"
        )

    # ── Wikipedia ────────────────────────────────────────────

    def _wikipedia(self, text):
        triggers = [
            "o que é ", "o que são ", "quem foi ", "quem é ",
            "me fala sobre ", "wikipedia ", "wikipédia ",
            "como funciona ", "what is ",
        ]
        term = text
        for trigger in triggers:
            if trigger in text:
                term = text.split(trigger, 1)[1].strip()
                break
        else:
            term = re.sub(r"^(pesquisar|buscar|procurar)\s+(sobre\s+)?", "", text).strip()

        if not term or len(term) < 2:
            return "O que deseja pesquisar na Wikipedia?"

        # Remove pontuação final
        term = re.sub(r"[?.!]+$", "", term).strip()

        try:
            encoded = urllib.parse.quote(term)
            url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(url, headers={"User-Agent": "ICARUS/1.4 (CFDM Holding)"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())

            title = data.get("title", term)
            extract = data.get("extract", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            if not extract:
                return f"'{term}' não encontrado na Wikipedia em português. Tente outro termo."

            # Limita a ~600 chars
            if len(extract) > 600:
                extract = extract[:597] + "..."

            result = f"📖 **{title}** _(Wikipedia)_\n\n{extract}"
            if page_url:
                result += f"\n\n🔗 {page_url}"
            return result

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Tenta versão em inglês
                return self._wikipedia_en(term)
            return f"⚠ Wikipedia: erro {e.code}"
        except Exception as e:
            return f"⚠ Erro ao buscar Wikipedia: {e}"

    def _wikipedia_en(self, term):
        """Fallback para Wikipedia em inglês"""
        try:
            encoded = urllib.parse.quote(term)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(url, headers={"User-Agent": "ICARUS/1.4"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            title = data.get("title", term)
            extract = data.get("extract", "")[:500]
            if extract:
                return f"📖 **{title}** _(Wikipedia EN)_\n\n{extract}"
        except Exception:
            pass
        return f"'{term}' não encontrado na Wikipedia. Tente: 'pesquisar {term}' para buscar no Google."

    # ── Clima ─────────────────────────────────────────────────

    def _weather(self, text):
        for trigger in ["tempo em ", "clima em ", "temperatura em ", "previsão em ", "previsão do tempo em "]:
            if trigger in text:
                city = text.split(trigger, 1)[1].strip()
                break
        else:
            m = re.search(r"(?:tempo|clima|temperatura|previs[aã]o)\s+(?:em\s+)?([a-záàãâéêíóôõúç\s]+)", text)
            city = m.group(1).strip() if m else "Lisboa"

        city = re.sub(r"[?.!]+$", "", city).strip()

        try:
            encoded = urllib.parse.quote(city)
            # wttr.in — sem API key, resposta formatada
            url = f"https://wttr.in/{encoded}?format=4&lang=pt"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                result = r.read().decode("utf-8").strip()

            if not result or "Unknown location" in result:
                return f"⚠ Cidade '{city}' não encontrada. Tente outro nome."

            return f"🌤 **Clima — {city.title()}**\n{result}"

        except Exception as e:
            return f"⚠ Não foi possível obter o clima de '{city}': {e}"

    # ── Google Search ─────────────────────────────────────────

    def _google(self, text):
        # Remove trigger words
        term = re.sub(
            r"^(pesquisar?\s+|buscar?\s+|procurar?\s+|googl[ea]r?\s+|busca\s+no\s+google\s+)",
            "", text
        ).strip()
        term = re.sub(r"[?.!]+$", "", term).strip()

        if not term:
            return "O que deseja pesquisar no Google?"

        encoded = urllib.parse.quote(term)
        url = f"https://www.google.com/search?q={encoded}"

        for browser in ["google-chrome", "chromium", "chromium-browser", "firefox", "xdg-open"]:
            if shutil.which(browser):
                try:
                    subprocess.Popen(
                        [browser, url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return f"🔍 Pesquisando **'{term}'** no Google..."
                except Exception:
                    continue

        return f"🔍 Pesquise em:\n{url}"
