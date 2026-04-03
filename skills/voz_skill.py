"""
ICARUS — Skill de Voz
Controla o Voice Engine: ativar/desativar TTS, falar texto, status de voz.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class VozSkill:
    """Skill de controle de voz do ICARUS"""

    name = "voz"
    description = "Controla o motor de voz: TTS, status, ativar/desativar"

    def __init__(self):
        self._voice_engine = None

    def _get_engine(self):
        if self._voice_engine is None:
            try:
                from core.voice_engine import VoiceEngine
                self._voice_engine = VoiceEngine()
            except Exception:
                pass
        return self._voice_engine

    def execute(self, user_input: str, context=None) -> str:
        text = user_input.lower()
        engine = self._get_engine()

        if not engine:
            return "Motor de voz não disponível. Instale: pip install pyttsx3"

        if any(w in text for w in ["status de voz", "voz ativa", "como está a voz"]):
            s = engine.status
            tts = "OK" if s["tts"] else "Indisponível"
            stt = "OK" if s["stt"] else "Whisper não instalado"
            listen = "Ativa" if s["listening"] else "Inativa"
            return f"Status de Voz ICARUS:\n  TTS (fala): {tts}\n  STT (escuta): {stt}\n  Escuta contínua: {listen}"

        if any(w in text for w in ["falar", "dizer", "ler em voz"]):
            # Extrai o que deve ser falado
            for marker in ["falar ", "dizer ", "ler em voz alta "]:
                if marker in text:
                    to_speak = user_input[user_input.lower().index(marker) + len(marker):]
                    engine.speak(to_speak)
                    return f"Falando: '{to_speak[:60]}...'" if len(to_speak) > 60 else f"Falando: '{to_speak}'"
            return "O que devo falar? Ex: 'falar olá mundo'"

        if any(w in text for w in ["testar voz", "teste de voz", "ola icarus"]):
            engine.speak("Olá! Sou o ICARUS, seu assistente pessoal da CFDM Holding. Estou pronto para servir.")
            return "Teste de voz executado."

        return "Comandos de voz: 'status de voz', 'testar voz', 'falar [texto]'"
