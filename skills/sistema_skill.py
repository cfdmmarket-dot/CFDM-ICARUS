"""
ICARUS Skill — Sistema (OS automations)
Abre apps, screenshots, música, volume, hora, piadas
"""

import subprocess
import datetime
import shutil
import random
import re
from pathlib import Path

SKILL_NAME = "sistema"

JOKES = [
    "Por que o computador foi ao médico? Porque tinha um vírus! 😄",
    "O que é um programador? Um ser que transforma café em código.",
    "Por que o desenvolvedor usa óculos escuros? Porque não suporta Java!",
    "Quantos programadores são necessários para trocar uma lâmpada? Nenhum, é problema de hardware!",
    "Minha senha é 'incorreta'. Quando errar, o sistema diz: 'sua senha está incorreta'!",
    "Por que o programador saiu do emprego? Porque não recebia arrays (arreios) suficientes.",
    "O que um programador disse quando não conseguia dormir? 'Vou iterar até conseguir!'",
]

APP_MAP = {
    "chrome": "google-chrome",
    "chromium": "chromium-browser",
    "firefox": "firefox",
    "terminal": "x-terminal-emulator",
    "arquivos": "nautilus",
    "gerenciador de arquivos": "nautilus",
    "calculadora": "gnome-calculator",
    "editor": "gedit",
    "gedit": "gedit",
    "vscode": "code",
    "código": "code",
    "code": "code",
    "spotify": "spotify",
    "discord": "discord",
    "telegram": "telegram-desktop",
    "vlc": "vlc",
    "gimp": "gimp",
    "obs": "obs",
    "blender": "blender",
}


class Skill:
    def __init__(self):
        self._music_proc = None

    def execute(self, user_input: str, context) -> str:
        t = user_input.lower().strip()

        # Hora e data
        if re.search(r"que horas|hora atual|horas s[aã]o|que hora", t):
            return self._get_time()
        if re.search(r"que dia|data de hoje|dia [eé] hoje|data atual", t):
            return self._get_date()
        if re.search(r"(hora|horas).*(data|dia)|(data|dia).*(hora|horas)", t):
            return self._get_time() + "\n" + self._get_date()

        # Screenshot
        if re.search(r"screenshot|captura de tela|tirar foto da tela|printscreen|print screen|print da tela", t):
            return self._screenshot()

        # Música
        if re.search(r"tocar m[uú]sica|play m[uú]sica|reproduzir|tocar musica|liga a m[uú]sica", t):
            return self._play_music(t)
        if re.search(r"parar m[uú]sica|pausar m[uú]sica|stop m[uú]sica|desliga a m[uú]sica|parar musica", t):
            return self._stop_music()

        # Volume
        if "volume" in t:
            return self._set_volume(t)

        # Piada
        if re.search(r"piada|me fa[zç] rir|conta uma piada|me diverte", t):
            return self._joke()

        # Abrir app
        if re.search(r"\babrir\b|\babre\b|\babra\b|\blançar\b|\biniciar\b|\blança\b", t):
            return self._open_app(t)

        # Desligar/reiniciar (bloqueado por segurança)
        if re.search(r"desligar computador|shutdown|desliga o pc", t):
            return "⚠ Desligar bloqueado por segurança. Use o terminal: `sudo shutdown now`"
        if re.search(r"reiniciar computador|reboot|reinicia o pc", t):
            return "⚠ Reiniciar bloqueado por segurança. Use o terminal: `sudo reboot`"

        return (
            "Comandos de sistema disponíveis:\n"
            "• **Hora**: 'que horas são'\n"
            "• **Apps**: 'abrir chrome', 'abrir terminal'\n"
            "• **Screenshot**: 'tirar screenshot'\n"
            "• **Música**: 'tocar música', 'parar música'\n"
            "• **Volume**: 'volume 70'\n"
            "• **Piada**: 'me conta uma piada'"
        )

    # ── Hora / Data ─────────────────────────────────────────

    def _get_time(self):
        now = datetime.datetime.now()
        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        return f"⏰ **{now.strftime('%H:%M:%S')}** — {dias[now.weekday()]}-feira"

    def _get_date(self):
        now = datetime.datetime.now()
        meses = [
            "janeiro","fevereiro","março","abril","maio","junho",
            "julho","agosto","setembro","outubro","novembro","dezembro"
        ]
        dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        return f"📅 **{dias[now.weekday()]}-feira, {now.day} de {meses[now.month-1]} de {now.year}**"

    # ── Screenshot ──────────────────────────────────────────

    def _screenshot(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path.home() / "Pictures" / f"icarus_{ts}.png"
        path.parent.mkdir(exist_ok=True)

        cmds = [
            ["scrot", str(path)],
            ["gnome-screenshot", "-f", str(path)],
            ["import", "-window", "root", str(path)],
            ["xwd", "-root", "-silent", "-out", str(path.with_suffix(".xwd"))],
        ]
        for cmd in cmds:
            if shutil.which(cmd[0]):
                try:
                    r = subprocess.run(cmd, capture_output=True, timeout=10)
                    if r.returncode == 0:
                        return f"📸 Screenshot salvo: `{path}`"
                except Exception:
                    continue

        return "⚠ Screenshot falhou. Instale: `sudo apt install scrot`"

    # ── Música ──────────────────────────────────────────────

    def _play_music(self, text):
        # Detecta pasta de música
        for d in [Path.home() / "Music", Path.home() / "Música", Path.home() / "music"]:
            if d.exists():
                music_dir = d
                break
        else:
            music_dir = Path.home()

        # Detecta player disponível
        player = next((p for p in ["mpv", "vlc", "mplayer", "rhythmbox"] if shutil.which(p)), None)
        if not player:
            return "⚠ Nenhum player encontrado. Instale: `sudo apt install mpv`"

        self._stop_music()  # para música anterior

        try:
            if player == "mpv":
                args = ["mpv", "--shuffle", "--no-video", str(music_dir)]
            elif player == "vlc":
                args = ["vlc", "--intf", "dummy", "--recursive=expand", str(music_dir)]
            else:
                args = [player, str(music_dir)]

            self._music_proc = subprocess.Popen(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return f"🎵 Tocando música de `{music_dir}` via **{player}**"
        except Exception as e:
            return f"⚠ Erro ao tocar música: {e}"

    def _stop_music(self):
        stopped = False
        if self._music_proc and self._music_proc.poll() is None:
            self._music_proc.terminate()
            self._music_proc = None
            stopped = True
        for player in ["mpv", "vlc", "mplayer"]:
            if shutil.which(player):
                r = subprocess.run(["pkill", "-f", player], capture_output=True)
                if r.returncode == 0:
                    stopped = True
        return "⏹ Música parada" if stopped else "Nenhuma música tocando no momento."

    # ── Volume ──────────────────────────────────────────────

    def _set_volume(self, text):
        m = re.search(r"(\d+)", text)
        if m:
            val = max(0, min(150, int(m.group(1))))
        elif re.search(r"m[aá]ximo|max|100", text):
            val = 100
        elif re.search(r"metade|meio|50", text):
            val = 50
        elif re.search(r"mudo|mute|zero|0", text):
            val = 0
        elif re.search(r"sobe|aumenta|mais", text):
            val = None  # incremento
        elif re.search(r"desce|diminui|menos", text):
            val = None  # decremento
        else:
            return "Diga o volume: 'volume 70' ou 'volume máximo'"

        if val is not None:
            for cmd in [
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"],
                ["amixer", "-D", "pulse", "set", "Master", f"{val}%"],
                ["amixer", "set", "Master", f"{val}%"],
            ]:
                if shutil.which(cmd[0]):
                    r = subprocess.run(cmd, capture_output=True)
                    if r.returncode == 0:
                        return f"🔊 Volume: **{val}%**"
        else:
            direction = "+5%" if re.search(r"sobe|aumenta|mais", text) else "-5%"
            for cmd in [
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", direction],
                ["amixer", "set", "Master", direction],
            ]:
                if shutil.which(cmd[0]):
                    r = subprocess.run(cmd, capture_output=True)
                    if r.returncode == 0:
                        return f"🔊 Volume {'aumentado' if '+' in direction else 'diminuído'}"

        return "⚠ Não foi possível ajustar o volume. Verifique PulseAudio ou ALSA."

    # ── Abrir app ────────────────────────────────────────────

    def _open_app(self, text):
        # Remove trigger words
        app_text = re.sub(r"^(abrir?|abra|lançar?|lan[cç]ar?|iniciar?)\s+", "", text).strip()
        if not app_text:
            return "Qual app quer abrir?"

        # Busca no mapa
        cmd = None
        for key, val in APP_MAP.items():
            if key in app_text:
                cmd = val
                break

        if not cmd:
            # Usa o primeiro token como comando direto
            cmd = app_text.split()[0]

        if shutil.which(cmd):
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"🚀 Abrindo **{cmd}**..."

        # Tenta xdg-open como fallback
        if shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", app_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"🚀 Tentando abrir **{app_text}**..."

        return f"⚠ App '{cmd}' não encontrado. Verifique se está instalado."

    # ── Piada ────────────────────────────────────────────────

    def _joke(self):
        return f"😄 {random.choice(JOKES)}"
