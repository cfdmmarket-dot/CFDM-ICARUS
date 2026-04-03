#!/usr/bin/env python3
"""
ICARUS Wake Word Detector — Processo independente (CLI / Raspberry Pi)
Detecta "ICARUS" pelo microfone → envia mensagem → ouve resposta em TTS

Uso:
    python3 scripts/wake_word.py
    python3 scripts/wake_word.py --host localhost --port 8001

Dependências:
    pip install SpeechRecognition pyaudio pyttsx3
    sudo apt install portaudio19-dev espeak-ng  (RPi / Linux)

No Raspberry Pi:
    python3 scripts/wake_word.py --rpi
"""

import argparse
import json
import sys
import time
import urllib.request

WAKE_WORDS = ["icarus", "ícarus", "icaro", "ícaro", "jarvis"]
ICARUS_URL = "http://localhost:8001"


def speak(text: str, engine=None):
    """TTS local — pyttsx3 ou espeak como fallback"""
    # Limpa markdown
    import re
    clean = re.sub(r"\*\*|__|\*|_|#{1,6}\s|`[^`]+`", "", text)
    clean = clean[:400]

    if engine:
        try:
            engine.say(clean)
            engine.runAndWait()
            return
        except Exception:
            pass

    # Fallback: espeak
    import subprocess, shutil
    for tts_cmd in [
        ["espeak-ng", "-v", "pt", "-s", "150", clean],
        ["espeak", "-v", "pt", clean],
        ["festival", "--tts"],
    ]:
        if shutil.which(tts_cmd[0]):
            try:
                subprocess.run(tts_cmd[:3] + [clean] if tts_cmd[0] != "festival" else tts_cmd,
                               input=clean.encode() if tts_cmd[0] == "festival" else None,
                               timeout=15, capture_output=True)
                return
            except Exception:
                continue
    print(f"[TTS] {clean}")


def chat(message: str, base_url: str) -> str:
    """Envia mensagem ao ICARUS e retorna resposta"""
    try:
        payload = json.dumps({"message": message}).encode()
        req = urllib.request.Request(
            f"{base_url}/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data.get("response", "Sem resposta")
    except Exception as e:
        return f"Erro ao conectar ao ICARUS: {e}"


def main():
    parser = argparse.ArgumentParser(description="ICARUS Wake Word Detector")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--lang", default="pt-BR")
    parser.add_argument("--rpi", action="store_true", help="Modo Raspberry Pi (espeak, microfone USB)")
    parser.add_argument("--mic-index", type=int, default=None, help="Índice do microfone")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    # Inicializa TTS
    tts_engine = None
    try:
        import pyttsx3
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 160)
        tts_engine.setProperty("volume", 0.9)
        voices = tts_engine.getProperty("voices")
        pt_voice = next((v for v in voices if "pt" in v.id.lower()), None)
        if pt_voice:
            tts_engine.setProperty("voice", pt_voice.id)
    except ImportError:
        print("[WARN] pyttsx3 não instalado — usando espeak")
    except Exception as e:
        print(f"[WARN] TTS: {e}")

    # Inicializa STT
    try:
        import speech_recognition as sr
    except ImportError:
        print("[ERRO] Instale: pip install SpeechRecognition pyaudio")
        sys.exit(1)

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0

    mic_kwargs = {}
    if args.mic_index is not None:
        mic_kwargs["device_index"] = args.mic_index

    print(f"[ICARUS Wake Word] Iniciado — URL: {base_url}")
    print(f"[ICARUS Wake Word] Diga uma das palavras: {WAKE_WORDS}")
    print("[ICARUS Wake Word] Ctrl+C para encerrar\n")

    speak("ICARUS iniciado. Aguardando chamado.", tts_engine)

    while True:
        # ── Fase 1: Ouvindo wake word ────────────────────────
        try:
            with sr.Microphone(**mic_kwargs) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("[AGUARDANDO] Diga 'ICARUS'...", end="\r")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4)
        except KeyboardInterrupt:
            print("\n[ICARUS] Encerrando.")
            break
        except Exception as e:
            time.sleep(0.5)
            continue

        # Transcreve wake word
        try:
            text = recognizer.recognize_google(audio, language=args.lang).lower()
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            # Offline: tenta Whisper local se disponível
            try:
                import whisper
                model = whisper.load_model("tiny")
                import tempfile, wave
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(audio.sample_width)
                    wf.setframerate(audio.sample_rate)
                    wf.writeframes(audio.get_raw_data())
                result = model.transcribe(wav_path, language="pt")
                text = result["text"].lower()
            except Exception:
                continue
        except Exception:
            continue

        # Verifica wake word
        if not any(w in text for w in WAKE_WORDS):
            continue

        # ── Fase 2: Wake word detectado ─────────────────────
        print(f"\n[ATIVADO] Palavra detectada: '{text}'")
        speak("Pode falar.", tts_engine)

        # Ouve o comando
        try:
            with sr.Microphone(**mic_kwargs) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                print("[OUVINDO] Fale seu comando...")
                audio_cmd = recognizer.listen(source, timeout=8, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            speak("Não ouvi nada. Tente novamente.", tts_engine)
            continue
        except Exception:
            continue

        # Transcreve comando
        command = ""
        try:
            command = recognizer.recognize_google(audio_cmd, language=args.lang)
        except sr.UnknownValueError:
            speak("Não entendi. Tente novamente.", tts_engine)
            continue
        except sr.RequestError:
            try:
                import whisper, tempfile, wave
                model = whisper.load_model("base")
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(audio_cmd.sample_width)
                    wf.setframerate(audio_cmd.sample_rate)
                    wf.writeframes(audio_cmd.get_raw_data())
                result = model.transcribe(wav_path, language="pt")
                command = result["text"]
            except Exception:
                speak("Sem conexão e Whisper não disponível.", tts_engine)
                continue

        if not command.strip():
            continue

        print(f"[COMANDO] {command}")

        # ── Fase 3: Envia ao ICARUS e fala resposta ─────────
        print("[PROCESSANDO] Consultando ICARUS...")
        response = chat(command, base_url)
        print(f"[ICARUS] {response[:100]}...")
        speak(response, tts_engine)
        print()


if __name__ == "__main__":
    main()
