"""
ICARUS Voice Engine — STT (Whisper) + TTS (pyttsx3/Coqui)
Modo Voz: "ICARUS, [comando]" → processa → responde em áudio
"""

import threading
import queue
import os


class VoiceEngine:
    """Motor de voz do ICARUS — TTS + STT"""

    def __init__(self):
        self.tts_engine = None
        self.stt_model = None
        self.is_listening = False
        self.voice_queue = queue.Queue()
        self._init_tts()

    # ─────────────── TTS ───────────────

    def _init_tts(self):
        """Inicializa engine TTS (pyttsx3)"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", 170)    # velocidade
            self.tts_engine.setProperty("volume", 0.95)
            # Seleciona voz em português se disponível
            voices = self.tts_engine.getProperty("voices")
            for v in voices:
                if "pt" in v.id.lower() or "brazil" in v.name.lower() or "português" in v.name.lower():
                    self.tts_engine.setProperty("voice", v.id)
                    break
            self.tts_available = True
        except Exception as e:
            self.tts_available = False
            print(f"[ICARUS Voice] TTS não disponível: {e}")

    def speak(self, text: str, async_mode: bool = True):
        """Fala o texto via TTS"""
        if not self.tts_available:
            return

        # Remove formatação markdown para TTS
        clean = self._clean_for_tts(text)

        if async_mode:
            t = threading.Thread(target=self._speak_sync, args=(clean,), daemon=True)
            t.start()
        else:
            self._speak_sync(clean)

    def _speak_sync(self, text: str):
        """TTS síncrono"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[ICARUS Voice] Erro TTS: {e}")

    def _clean_for_tts(self, text: str) -> str:
        """Limpa markdown e símbolos para TTS"""
        import re
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)    # **bold**
        text = re.sub(r"\*(.+?)\*", r"\1", text)          # *italic*
        text = re.sub(r"#+\s", "", text)                   # # headings
        text = re.sub(r"`(.+?)`", r"\1", text)             # `code`
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)   # [link](url)
        text = re.sub(r"[•→✦✅⬜🔨⚠️🎯⚡🧠]", "", text)   # emojis comuns
        text = re.sub(r"\s+", " ", text)
        return text.strip()[:500]  # limita para não ficar muito longo

    # ─────────────── STT ───────────────

    def _init_stt(self):
        """Inicializa Whisper para STT (lazy load)"""
        if self.stt_model is not None:
            return True
        try:
            import whisper
            print("[ICARUS Voice] Carregando Whisper (base)...")
            self.stt_model = whisper.load_model("base")
            self.stt_available = True
            print("[ICARUS Voice] Whisper pronto.")
            return True
        except Exception as e:
            self.stt_available = False
            print(f"[ICARUS Voice] Whisper não disponível: {e}")
            return False

    def listen_once(self, duration: int = 5) -> str:
        """Grava áudio e transcreve (requer pyaudio + whisper)"""
        if not self._init_stt():
            return ""
        try:
            import pyaudio
            import wave
            import tempfile

            RATE = 16000
            CHANNELS = 1
            CHUNK = 1024

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=CHANNELS,
                            rate=RATE, input=True, frames_per_buffer=CHUNK)

            print(f"[ICARUS Voice] Ouvindo por {duration}s...")
            frames = []
            for _ in range(int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            # Salva WAV temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name

            wf = wave.open(tmp_path, "wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()

            result = self.stt_model.transcribe(tmp_path, language="pt")
            os.unlink(tmp_path)
            return result["text"].strip()

        except Exception as e:
            print(f"[ICARUS Voice] Erro STT: {e}")
            return ""

    def voice_loop(self, icarus_core, wake_word: str = "icarus"):
        """Loop contínuo de escuta (wake word detection)"""
        self._init_stt()
        self.is_listening = True
        print(f"[ICARUS Voice] Loop de voz ativo. Wake word: '{wake_word}'")
        self.speak(f"ICARUS pronto. Diga {wake_word} para ativar.")

        while self.is_listening:
            try:
                text = self.listen_once(duration=3)
                if not text:
                    continue

                text_lower = text.lower()
                print(f"[ICARUS Voice] Detectado: {text}")

                if wake_word in text_lower:
                    self.speak("Sim, estou ouvindo.")
                    command = self.listen_once(duration=6)
                    if command:
                        print(f"[ICARUS Voice] Comando: {command}")
                        response = icarus_core.process(command)
                        print(f"[ICARUS Voice] Resposta: {response}")
                        self.speak(response)

            except KeyboardInterrupt:
                self.is_listening = False
                break
            except Exception as e:
                print(f"[ICARUS Voice] Erro no loop: {e}")

    def stop(self):
        self.is_listening = False

    @property
    def status(self) -> dict:
        return {
            "tts": self.tts_available,
            "stt": getattr(self, "stt_available", False),
            "listening": self.is_listening
        }
