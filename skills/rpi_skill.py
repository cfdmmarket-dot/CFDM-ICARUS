"""
ICARUS Skill — Raspberry Pi GPIO
Controla dispositivos físicos via GPIO (relés, LEDs, etc.)

Setup:
  pip install RPi.GPIO
  Configure os pinos em config/rpi_pins.json

Exemplo rpi_pins.json:
{
  "luz_sala": 17,
  "luz_quarto": 27,
  "ar_condicionado": 22,
  "ventilador": 24
}
"""

import json
import re
from pathlib import Path

SKILL_NAME = "rpi"

PINS_CONFIG = Path(__file__).parent.parent / "config" / "rpi_pins.json"

DEFAULT_PINS = {
    "luz_sala": 17,
    "luz_quarto": 27,
    "ar_condicionado": 22,
    "ventilador": 24,
    "campainha": 23,
}

DEVICE_EMOJI = {
    "luz": "💡",
    "ar": "❄️",
    "ventilador": "🌀",
    "campainha": "🔔",
    "tv": "📺",
    "tomada": "🔌",
}


class Skill:
    def __init__(self):
        self.pins = self._load_pins()
        self._states = {name: False for name in self.pins}
        self.gpio_available = False
        self.GPIO = None
        self._init_gpio()

    def _load_pins(self):
        if PINS_CONFIG.exists():
            try:
                return json.loads(PINS_CONFIG.read_text())
            except Exception:
                pass
        return DEFAULT_PINS.copy()

    def _init_gpio(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for name, pin in self.pins.items():
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            self.GPIO = GPIO
            self.gpio_available = True
        except ImportError:
            pass  # Não é RPi ou GPIO não instalado
        except Exception:
            pass

    def execute(self, user_input: str, context) -> str:
        t = user_input.lower().strip()

        if not self.gpio_available:
            return (
                "⚠ GPIO não disponível.\n"
                "Esta skill requer Raspberry Pi com `RPi.GPIO` instalado.\n"
                "Instale: `pip install RPi.GPIO`\n"
                f"Configure pinos em: `config/rpi_pins.json`"
            )

        # Status geral
        if re.search(r"status|estado|quais est[aã]o|o que est[aá] ligado", t):
            return self._status()

        # Desligar tudo
        if re.search(r"desligar tudo|apagar tudo|tudo off|emergência", t):
            return self._all_off()

        # Ligar/Desligar por dispositivo
        for name, pin in self.pins.items():
            name_variants = [name, name.replace("_", " "), name.replace("_", "")]
            if any(v in t for v in name_variants):
                if re.search(r"\bligar\b|\bacender\b|\bativar\b|\bon\b|\babre\b|\babrir\b", t):
                    return self._control(name, pin, True)
                if re.search(r"\bdesligar\b|\bapagar\b|\bdesativar\b|\boff\b|\bfecha\b|\bfechar\b", t):
                    return self._control(name, pin, False)
                if re.search(r"\bstatus\b|\bestado\b|\bligad\b|\bdesligad\b", t):
                    state = "ligado 🟢" if self._states[name] else "desligado 🔴"
                    return f"{self._emoji(name)} **{name.replace('_',' ').title()}**: {state}"

        # Dispositivos disponíveis
        devs = ', '.join(n.replace('_', ' ') for n in self.pins)
        return (
            f"Dispositivos GPIO configurados: **{devs}**\n"
            "Diga: 'ligar luz sala', 'desligar ar condicionado', 'status'"
        )

    def _control(self, name: str, pin: int, on: bool):
        self.GPIO.output(pin, self.GPIO.HIGH if on else self.GPIO.LOW)
        self._states[name] = on
        state = "ligado 🟢" if on else "desligado 🔴"
        return f"{self._emoji(name)} **{name.replace('_',' ').title()}**: {state}"

    def _status(self):
        lines = ["📊 **Status GPIO — Dispositivos:**"]
        for name, state in self._states.items():
            icon = "🟢 ON " if state else "🔴 OFF"
            lines.append(f"  {icon}  {self._emoji(name)} {name.replace('_',' ').title()}")
        return "\n".join(lines)

    def _all_off(self):
        for name, pin in self.pins.items():
            self.GPIO.output(pin, self.GPIO.LOW)
            self._states[name] = False
        return "🔴 **Todos os dispositivos desligados.**"

    def _emoji(self, name: str) -> str:
        for key, emoji in DEVICE_EMOJI.items():
            if key in name:
                return emoji
        return "⚡"
