"""
ICARUS — Skill de Notícias
Briefing matinal e notícias por tema via RSS feeds.
Sem dependências externas — usa urllib + xml nativo do Python.
"""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


FEEDS = {
    "tecnologia": [
        ("Hacker News",  "https://news.ycombinator.com/rss"),
        ("TechCrunch",   "https://techcrunch.com/feed/"),
    ],
    "ia": [
        ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("MIT Tech",     "https://www.technologyreview.com/feed/"),
    ],
    "brasil": [
        ("G1",           "https://g1.globo.com/rss/g1/"),
    ],
    "negocios": [
        ("Reuters Biz",  "https://feeds.reuters.com/reuters/businessNews"),
    ],
}

# Feeds do briefing matinal (mistura equilibrada)
BRIEFING_FEEDS = [
    ("Hacker News",  "https://news.ycombinator.com/rss"),
    ("TechCrunch",   "https://techcrunch.com/feed/"),
    ("G1",           "https://g1.globo.com/rss/g1/"),
]


def _fetch_rss(url: str, max_items: int = 5) -> list[dict]:
    """Busca e parseia um feed RSS. Retorna lista de {title, link, date}."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ICARUS/1.2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        items = []
        # RSS 2.0
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            date  = item.findtext("pubDate", "")
            if title:
                items.append({"title": title, "link": link, "date": date})

        # Atom
        if not items:
            for entry in root.findall(".//atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", "", ns).strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                date = entry.findtext("atom:updated", "", ns)
                if title:
                    items.append({"title": title, "link": link, "date": date})

        return items
    except Exception as e:
        return []


class NoticiasSkill:
    """Skill de notícias e briefing matinal do ICARUS"""

    name = "noticias"
    description = "Notícias RSS: briefing matinal, por tema (tech/IA/brasil/negócios)"

    def execute(self, user_input: str, context=None) -> str:
        text = user_input.lower()

        if any(w in text for w in ["briefing", "matinal", "bom dia", "resumo do dia", "o que aconteceu"]):
            return self._briefing()

        for tema, feeds in FEEDS.items():
            if tema in text or (tema == "ia" and ("inteligência artificial" in text or " ia " in text)):
                return self._noticias_tema(tema, feeds)

        if any(w in text for w in ["noticias", "notícias", "últimas", "ultimas", "news"]):
            return self._briefing(max_per_feed=3)

        return (
            "Comandos de notícias:\n"
            "  'briefing matinal' — resumo do dia\n"
            "  'notícias de tecnologia'\n"
            "  'notícias de IA'\n"
            "  'notícias do brasil'\n"
            "  'notícias de negócios'"
        )

    def _briefing(self, max_per_feed: int = 4) -> str:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        linhas = [f"📰 BRIEFING MATINAL — {agora}\n"]

        total = 0
        for nome, url in BRIEFING_FEEDS:
            items = _fetch_rss(url, max_per_feed)
            if not items:
                linhas.append(f"  [{nome}] — sem conexão\n")
                continue
            linhas.append(f"── {nome} ──")
            for i, item in enumerate(items, 1):
                linhas.append(f"  {i}. {item['title']}")
            linhas.append("")
            total += len(items)

        if total == 0:
            return "Sem conexão com os feeds. Verifique sua internet."

        linhas.append(f"Total: {total} manchetes | ICARUS v1.2.0")
        return "\n".join(linhas)

    def _noticias_tema(self, tema: str, feeds: list) -> str:
        agora = datetime.now().strftime("%H:%M")
        linhas = [f"📰 Notícias: {tema.upper()} — {agora}\n"]

        for nome, url in feeds:
            items = _fetch_rss(url, 5)
            if not items:
                continue
            linhas.append(f"── {nome} ──")
            for i, item in enumerate(items, 1):
                linhas.append(f"  {i}. {item['title']}")
            linhas.append("")

        if len(linhas) == 1:
            return f"Sem notícias disponíveis sobre {tema} no momento."
        return "\n".join(linhas)
