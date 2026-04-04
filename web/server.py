"""
ICARUS Web Server — Interface web do assistente pessoal
"""

import sys
import os
import json
import datetime
import logging
import tempfile
from collections import deque
from pathlib import Path

import asyncio
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.icarus_core import IcarusCore, ICARUS_PERSONA, set_log_fn

app = FastAPI(title="ICARUS", description="Assistente Pessoal CFDM Holding", version="1.7.2")

# Buffer circular de logs — shared entre uvicorn handlers e icarus_core
LOG_BUFFER: deque = deque(maxlen=500)
_server_start = datetime.datetime.now()

def _append_log(level: str, tag: str, msg: str):
    LOG_BUFFER.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S.") +
                str(datetime.datetime.now().microsecond // 1000).zfill(3),
        "level": level,
        "tag": tag,
        "msg": msg,
    })

class BufferHandler(logging.Handler):
    def emit(self, record):
        _append_log(record.levelname, "SERVER", self.format(record))

_buf_handler = BufferHandler()
_buf_handler.setFormatter(logging.Formatter("%(name)s — %(message)s"))
logging.getLogger("uvicorn.access").addHandler(_buf_handler)
logging.getLogger("icarus").addHandler(_buf_handler)
_icarus_log = logging.getLogger("icarus")
_icarus_log.setLevel(logging.INFO)

# Instância global do ICARUS
icarus = IcarusCore()

# Conecta o hook de log do IcarusCore ao buffer compartilhado
set_log_fn(_append_log)
_append_log("INFO", "SERVER", f"ICARUS v{icarus.version} iniciado")


@app.get("/", response_class=HTMLResponse)
async def index():
    template_path = Path(__file__).parent / "templates" / "index.html"
    return template_path.read_text(encoding="utf-8")


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return JSONResponse({"error": "Mensagem vazia"}, status_code=400)

    _icarus_log.info(f"INPUT → {user_input[:80]}")
    response = icarus.process(user_input)
    _icarus_log.info(f"OUTPUT → {str(response)[:80]}")
    LOG_BUFFER.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "level": "CHAT",
        "msg": f"USER: {user_input[:60]} | ICARUS: {str(response)[:60]}"
    })

    return {
        "response": response,
        "timestamp": datetime.datetime.now().isoformat(),
        "version": icarus.version
    }


@app.get("/status")
async def status():
    return {
        "status": "online",
        "version": icarus.version,
        "agent": "ICARUS",
        "memories": icarus.memory.count(),
        "session_messages": icarus.context.count(),
        "session_start": icarus.session_start.isoformat(),
        "active_mode": icarus.active_mode
    }


@app.get("/settings")
async def get_settings():
    return {
        "conversation_flow": icarus.conversation_flow,
        "paused": icarus._paused,
    }

@app.post("/settings/conversation_flow")
async def toggle_conversation_flow():
    icarus.conversation_flow = not icarus.conversation_flow
    state = "ativado" if icarus.conversation_flow else "desativado"
    return {"conversation_flow": icarus.conversation_flow, "message": f"Fluxo conversacional {state}"}


@app.get("/modes")
async def get_modes():
    """Lista todos os modos operacionais disponíveis"""
    modes = icarus.commands_config.get("modes", {})
    result = {}
    for key, val in modes.items():
        result[key] = {
            "descricao": val.get("descricao", ""),
            "camada": val.get("camada", 0),
            "parametros": val.get("parametros", [])
        }
    return {"modes": result, "active": icarus.active_mode}


@app.post("/modes/activate")
async def activate_mode(request: Request):
    """Ativa um modo operacional"""
    data = await request.json()
    mode_name = data.get("mode", "").strip()
    if not mode_name:
        return JSONResponse({"error": "Nome do modo obrigatório"}, status_code=400)
    result = icarus.activate_mode(mode_name)
    return {"result": result, "active_mode": icarus.active_mode}


@app.post("/modes/deactivate")
async def deactivate_mode():
    """Desativa modo atual"""
    result = icarus.deactivate_mode()
    return {"result": result, "active_mode": None}


def _clean_for_tts(text: str, max_chars: int = 400) -> str:
    """Remove markdown, prefixos técnicos e código do texto antes de sintetizar voz."""
    import re
    t = re.sub(r'\[ICARUS[^\]]*\]', '', text)
    t = re.sub(r'^\s*\[.*?\]\s*', '', t, flags=re.MULTILINE)
    t = re.sub(r'https?://\S+', '', t)
    t = re.sub(r'```[\s\S]*?```', '', t)
    t = re.sub(r'`[^`]+`', '', t)
    t = re.sub(r'pip install \S+', '', t)
    t = re.sub(r'sudo \S+', '', t)
    t = re.sub(r'\*\*|__|\*|_', '', t)
    t = re.sub(r'#{1,6}\s', '', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'\n+', ' ', t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    return t[:max_chars]


# Voz padrão — pode ser alterada via /voice/config
_tts_voice   = "pt-BR-AntonioNeural"   # Microsoft Neural (edge-tts)
_tts_rate    = "+0%"
_tts_volume  = "+0%"

# Vozes disponíveis para seleção
TTS_VOICES_PT = {
    "antonio":    ("pt-BR-AntonioNeural",   "Masculino — António (BR)"),
    "francisca":  ("pt-BR-FranciscaNeural", "Feminino  — Francisca (BR)"),
    "duarte":     ("pt-PT-DuarteNeural",    "Masculino — Duarte (PT)"),
    "raquel":     ("pt-PT-RaquelNeural",    "Feminino  — Raquel (PT)"),
}


@app.get("/voice/voices")
async def list_voices():
    """Lista vozes TTS disponíveis"""
    return {
        "current": _tts_voice,
        "voices": [
            {"id": k, "name": v[0], "desc": v[1]}
            for k, v in TTS_VOICES_PT.items()
        ]
    }


@app.post("/voice/config")
async def set_voice_config(request: Request):
    """Configura voz, velocidade e volume do TTS"""
    global _tts_voice, _tts_rate, _tts_volume
    data = await request.json()
    voice_id = data.get("voice", "").strip()
    if voice_id in TTS_VOICES_PT:
        _tts_voice = TTS_VOICES_PT[voice_id][0]
    elif voice_id:  # nome completo direto
        _tts_voice = voice_id
    rate = data.get("rate")
    if rate is not None:
        _tts_rate = f"{int(rate):+d}%"
    volume = data.get("volume")
    if volume is not None:
        _tts_volume = f"{int(volume):+d}%"
    return {"ok": True, "voice": _tts_voice, "rate": _tts_rate, "volume": _tts_volume}


@app.post("/voice/speak")
async def speak_text(request: Request):
    """
    TTS via Microsoft Edge Neural (edge-tts) — retorna MP3 para o browser reproduzir.
    Igual ao JARVIS: gera áudio de alta qualidade e devolve para playback no cliente.
    Fallback: pyttsx3 → espeak (reproduz localmente, sem retornar áudio).
    """
    from fastapi.responses import Response as FAResponse
    data = await request.json()
    text  = data.get("text", "").strip()
    voice = data.get("voice", _tts_voice)
    rate  = data.get("rate",  _tts_rate)
    vol   = data.get("volume", _tts_volume)

    if not text:
        return JSONResponse({"error": "Texto vazio"}, status_code=400)

    clean = _clean_for_tts(text)
    if not clean:
        return JSONResponse({"error": "Texto vazio após limpeza"}, status_code=400)

    # ── 1. edge-tts (Microsoft Neural — melhor qualidade, retorna MP3 ao browser) ──
    try:
        import edge_tts, asyncio, tempfile, os
        tts = edge_tts.Communicate(clean, voice=voice, rate=rate, volume=vol)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
        await tts.save(tmp_path)
        with open(tmp_path, "rb") as f:
            mp3_bytes = f.read()
        os.unlink(tmp_path)
        return FAResponse(content=mp3_bytes, media_type="audio/mpeg",
                         headers={"X-TTS-Engine": "edge-tts", "X-TTS-Voice": voice})
    except Exception:
        pass

    # ── 2. OpenAI TTS (se API key configurada) ────────────────────────────────────
    try:
        import openai as _oai, os, tempfile
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            client = _oai.OpenAI(api_key=api_key)
            resp = client.audio.speech.create(model="tts-1", voice="onyx", input=clean)
            mp3_bytes = resp.content
            return FAResponse(content=mp3_bytes, media_type="audio/mpeg",
                             headers={"X-TTS-Engine": "openai-tts", "X-TTS-Voice": "onyx"})
    except Exception:
        pass

    # ── 3. pyttsx3 / espeak — reproduz localmente (sem retornar áudio) ───────────
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        voices = engine.getProperty('voices')
        pt_voice = next((v for v in voices if 'pt' in v.id.lower()), None)
        if pt_voice:
            engine.setProperty('voice', pt_voice.id)
        engine.say(clean)
        engine.runAndWait()
        return JSONResponse({"ok": True, "engine": "pyttsx3", "local": True})
    except Exception:
        pass

    try:
        import subprocess
        subprocess.run(["espeak", "-v", "pt+m3", "-s", "155", clean],
                       timeout=15, capture_output=True)
        return JSONResponse({"ok": True, "engine": "espeak", "local": True})
    except Exception:
        pass

    return JSONResponse({"error": "Nenhum engine TTS disponível"}, status_code=503)


@app.post("/voice/transcribe")
async def transcribe_audio(request: Request):
    """Transcreve áudio via Whisper local (offline, sem depender de internet)"""
    body = await request.body()
    if not body:
        return JSONResponse({"error": "Áudio vazio", "text": ""}, status_code=400)

    suffix = ".webm"
    ct = request.headers.get("content-type", "")
    if "wav" in ct:  suffix = ".wav"
    elif "ogg" in ct: suffix = ".ogg"
    elif "mp4" in ct: suffix = ".mp4"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(body)
            tmp_path = f.name

        # Tenta faster-whisper primeiro (mais rápido)
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(tmp_path, language="pt")
            text = " ".join(s.text for s in segments).strip()
            return {"text": text, "language": info.language, "engine": "faster-whisper"}
        except ImportError:
            pass

        # Fallback: openai-whisper
        try:
            import whisper
            model = whisper.load_model("base", device="cpu")
            result = model.transcribe(tmp_path, language="pt")
            return {"text": result["text"].strip(), "language": "pt", "engine": "whisper"}
        except ImportError:
            pass

        return JSONResponse({
            "error": "Whisper não instalado. Execute: pip install faster-whisper",
            "text": "",
            "engine": "none"
        }, status_code=503)

    except Exception as e:
        return JSONResponse({"error": str(e), "text": ""}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/voice/status")
async def voice_status():
    """Verifica engines de voz disponíveis"""
    engines = {"faster_whisper": False, "whisper": False, "web_speech": True}
    try:
        import faster_whisper
        engines["faster_whisper"] = True
    except ImportError:
        pass
    try:
        import whisper
        engines["whisper"] = True
    except ImportError:
        pass
    return {
        "engines": engines,
        "recommended": "faster-whisper" if engines["faster_whisper"] else
                       "whisper" if engines["whisper"] else "web-speech-api",
        "install_cmd": "pip install faster-whisper" if not engines["faster_whisper"] else None
    }


@app.get("/agents")
async def get_agents():
    """Lista agentes disponíveis no sistema de comandos"""
    agents = icarus.commands_config.get("agents", [])
    return {"agents": agents, "total": len(agents)}


@app.get("/tasks")
async def get_tasks():
    return {"tasks": icarus.memory.get_tasks()}


@app.post("/tasks")
async def add_task(request: Request):
    data = await request.json()
    task_text = data.get("task", "").strip()
    priority = data.get("priority", "normal")
    if not task_text:
        return JSONResponse({"error": "Tarefa vazia"}, status_code=400)
    task = icarus.memory.add_task(task_text, priority)
    return {"task": task, "message": "Tarefa adicionada"}


@app.put("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    icarus.memory.complete_task(task_id)
    return {"message": f"Tarefa #{task_id} concluída"}


@app.get("/system")
async def system_stats():
    """CPU, RAM, disco e uptime do servidor"""
    stats = {
        "uptime": str(datetime.datetime.now() - _server_start).split(".")[0],
        "python": sys.version.split()[0],
        "cpu_percent": None,
        "ram_total_mb": None,
        "ram_used_mb": None,
        "ram_percent": None,
        "disk_used_gb": None,
        "disk_total_gb": None,
        "disk_percent": None,
    }
    try:
        import psutil
        stats["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        vm = psutil.virtual_memory()
        stats["ram_total_mb"] = round(vm.total / 1024**2)
        stats["ram_used_mb"] = round(vm.used / 1024**2)
        stats["ram_percent"] = vm.percent
        dk = psutil.disk_usage("/")
        stats["disk_used_gb"] = round(dk.used / 1024**3, 1)
        stats["disk_total_gb"] = round(dk.total / 1024**3, 1)
        stats["disk_percent"] = dk.percent
    except ImportError:
        stats["error"] = "psutil não instalado — pip install psutil"
    return stats


@app.get("/logs")
async def get_logs(n: int = 100):
    """Últimas N entradas do log do servidor"""
    entries = list(LOG_BUFFER)[-n:]
    return {"logs": entries, "total": len(LOG_BUFFER)}


@app.get("/logs/stream")
async def stream_logs(request: Request):
    """SSE — streaming em tempo real de novos eventos de log."""
    async def generator():
        # Envia snapshot inicial (últimas 60 entradas)
        snapshot = list(LOG_BUFFER)[-60:]
        for entry in snapshot:
            yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"

        last_len = len(LOG_BUFFER)
        while True:
            if await request.is_disconnected():
                break
            current = list(LOG_BUFFER)
            cur_len = len(current)
            if cur_len != last_len:
                # Novas entradas desde a última verificação
                if cur_len > last_len:
                    new_entries = current[last_len:]
                else:
                    # Buffer deu volta (deque maxlen) — envia todas
                    new_entries = current
                for entry in new_entries:
                    yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
                last_len = cur_len
            else:
                # Keep-alive
                yield ": ping\n\n"
            await asyncio.sleep(0.15)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


CUSTOM_RESPONSES_PATH = Path(__file__).parent.parent / "config" / "custom_responses.json"


@app.get("/custom-responses")
async def get_custom_responses():
    try:
        with open(CUSTOM_RESPONSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"responses": []}


@app.post("/custom-responses")
async def save_custom_responses(request: Request):
    data = await request.json()
    responses = data.get("responses", [])
    existing = {"_doc": "Respostas personalizadas — gatilho → resposta exata do ICARUS", "responses": responses}
    with open(CUSTOM_RESPONSES_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return {"ok": True, "total": len(responses)}


@app.delete("/custom-responses/{index}")
async def delete_custom_response(index: int):
    with open(CUSTOM_RESPONSES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    responses = data.get("responses", [])
    if 0 <= index < len(responses):
        responses.pop(index)
    data["responses"] = responses
    with open(CUSTOM_RESPONSES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "total": len(responses)}


@app.get("/deps")
async def check_deps():
    """Verifica dependências Python instaladas no servidor"""
    import importlib.util
    import importlib.metadata
    import subprocess

    def check(pkg: str, import_name: str = None) -> dict:
        name = import_name or pkg
        spec = importlib.util.find_spec(name.replace("-", "_"))
        found = spec is not None
        version = None
        if found:
            try:
                version = importlib.metadata.version(pkg)
            except Exception:
                version = "instalado"
        return {"found": found, "version": version}

    def check_bin(cmd: str) -> dict:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, timeout=3)
            out = (r.stdout or r.stderr).decode().strip().split("\n")[0]
            return {"found": r.returncode == 0, "version": out[:60] if r.returncode == 0 else None}
        except Exception:
            return {"found": False, "version": None}

    deps = [
        # required
        {"pkg": "fastapi",         "import": "fastapi",         "feature": "Servidor web",          "required": True,  "install": "pip install fastapi"},
        {"pkg": "uvicorn",         "import": "uvicorn",         "feature": "Servidor ASGI",         "required": True,  "install": "pip install uvicorn"},
        {"pkg": "requests",        "import": "requests",        "feature": "HTTP / Nexus",          "required": True,  "install": "pip install requests"},
        # voz STT
        {"pkg": "faster-whisper",  "import": "faster_whisper",  "feature": "STT offline (rápido)",  "required": False, "install": "pip install faster-whisper"},
        {"pkg": "openai-whisper",  "import": "whisper",         "feature": "STT offline (fallback)","required": False, "install": "pip install openai-whisper"},
        {"pkg": "SpeechRecognition","import":"speech_recognition","feature": "STT Web Speech fallback","required": False,"install": "pip install SpeechRecognition"},
        {"pkg": "pyaudio",         "import": "pyaudio",         "feature": "Captura de microfone",  "required": False, "install": "pip install pyaudio"},
        # voz TTS
        {"pkg": "pyttsx3",         "import": "pyttsx3",         "feature": "TTS local (ICARUS fala)","required": False,"install": "pip install pyttsx3"},
        # sistema
        {"pkg": "psutil",          "import": "psutil",          "feature": "Métricas CPU/RAM/disco","required": False, "install": "pip install psutil"},
        # RPi
        {"pkg": "RPi.GPIO",        "import": "RPi",             "feature": "GPIO Raspberry Pi",     "required": False, "install": "pip install RPi.GPIO"},
        # IA / Nexus
        {"pkg": "langchain",       "import": "langchain",       "feature": "Agentes LangChain",     "required": False, "install": "pip install langchain"},
        {"pkg": "crewai",          "import": "crewai",          "feature": "Agentes CrewAI / Nexus","required": False, "install": "pip install crewai"},
        {"pkg": "openai",          "import": "openai",          "feature": "LLM OpenAI",            "required": False, "install": "pip install openai"},
        {"pkg": "anthropic",       "import": "anthropic",       "feature": "LLM Anthropic / Claude","required": False, "install": "pip install anthropic"},
        # extras
        {"pkg": "feedparser",      "import": "feedparser",      "feature": "Skill de notícias (RSS)","required": False,"install": "pip install feedparser"},
        {"pkg": "httpx",           "import": "httpx",           "feature": "HTTP async",            "required": False, "install": "pip install httpx"},
    ]

    # binários de sistema
    bins = [
        {"name": "espeak",  "feature": "TTS sistema (fallback)", "install": "sudo apt install espeak"},
        {"name": "scrot",   "feature": "Screenshot",             "install": "sudo apt install scrot"},
        {"name": "mpv",     "feature": "Reprodução de música",   "install": "sudo apt install mpv"},
    ]

    results = []
    for d in deps:
        r = check(d["pkg"], d["import"])
        results.append({
            "name": d["pkg"],
            "feature": d["feature"],
            "required": d["required"],
            "found": r["found"],
            "version": r["version"],
            "install": d["install"],
            "type": "python",
        })

    for b in bins:
        r = check_bin(b["name"])
        results.append({
            "name": b["name"],
            "feature": b["feature"],
            "required": False,
            "found": r["found"],
            "version": r["version"],
            "install": b["install"],
            "type": "system",
        })

    missing_required = [d["name"] for d in results if d["required"] and not d["found"]]
    return {
        "deps": results,
        "total": len(results),
        "missing_required": missing_required,
        "all_ok": len(missing_required) == 0,
    }


@app.get("/nexus/agents")
async def nexus_agents_proxy():
    """Proxy para buscar agentes do Cfdm Nexus"""
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8000/agents", timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return {"agents": [], "total": 0, "error": "Nexus offline"}


@app.get("/nexus/status")
async def nexus_status_proxy():
    """Proxy para status do Cfdm Nexus"""
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8000/status", timeout=3) as r:
            data = json.loads(r.read())
            data["online"] = True
            return data
    except Exception:
        return {"online": False, "error": "Nexus offline"}


@app.post("/nexus/run")
async def nexus_run_proxy(request: Request):
    """Proxy para executar agente no Cfdm Nexus via chat ICARUS"""
    data = await request.json()
    agent = data.get("agent", "").strip()
    task = data.get("task", "").strip()
    if not agent or not task:
        return JSONResponse({"error": "agent e task obrigatórios"}, status_code=400)
    # Executa via chat do ICARUS (nexus_skill trata a mensagem)
    message = f"executar agente {agent}: {task}"
    _icarus_log.info(f"NEXUS RUN → {agent}: {task[:60]}")
    response = icarus.process(message)
    return {"response": response, "agent": agent, "task": task}


@app.get("/files/search")
async def files_search(
    dir: str = "/home",
    type: str = "all",
    name: str = "",
    recursive: bool = True
):
    """Busca arquivos por tipo e nome em um diretório"""
    import datetime as dt

    TYPE_EXTS = {
        "docs":     [".pdf", ".doc", ".docx", ".odt", ".txt", ".md", ".rtf", ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx"],
        "images":   [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
        "video":    [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v"],
        "code":     [".py", ".js", ".ts", ".html", ".css", ".cpp", ".c", ".h", ".java", ".go", ".rs", ".sh", ".json", ".yaml", ".yml", ".toml", ".xml"],
        "archives": [".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"],
    }

    base = Path(dir).expanduser()
    if not base.exists() or not base.is_dir():
        return JSONResponse({"error": f"Diretório não encontrado: {dir}"}, status_code=404)

    exts = TYPE_EXTS.get(type, None)  # None = all

    results = []
    try:
        iterator = base.rglob("*") if recursive else base.glob("*")
        for p in iterator:
            if not p.is_file():
                continue
            if exts and p.suffix.lower() not in exts:
                continue
            if name and name.lower() not in p.name.lower():
                continue
            try:
                stat = p.stat()
                results.append({
                    "name": p.name,
                    "path": str(p),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            except Exception:
                continue
            if len(results) >= 500:
                break
    except PermissionError as e:
        return JSONResponse({"error": f"Permissão negada: {e}"}, status_code=403)

    results.sort(key=lambda x: x["modified"], reverse=True)
    return {"results": results, "total": len(results), "dir": str(base)}


@app.post("/open-url")
async def open_url(request: Request):
    """Abre uma URL no navegador padrão do sistema via xdg-open"""
    import subprocess
    import re
    data = await request.json()
    url = data.get("url", "").strip()
    if not url:
        return JSONResponse({"error": "URL vazia"}, status_code=400)
    # Sanitização básica: apenas http/https
    if not re.match(r'^https?://', url):
        return JSONResponse({"error": "Apenas URLs http/https são permitidas"}, status_code=400)
    try:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "url": url}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


NEXUS_DIR = Path("/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_")
_nexus_proc = None  # referência ao processo do Nexus


@app.post("/nexus/start")
async def nexus_start():
    """Inicia o Cfdm Nexus (porta 8000) em background"""
    global _nexus_proc
    import subprocess, urllib.request
    # Já está online?
    try:
        with urllib.request.urlopen("http://localhost:8000/status", timeout=2):
            return {"ok": True, "msg": "Nexus já está online"}
    except Exception:
        pass
    # Inicia
    try:
        _nexus_proc = subprocess.Popen(
            ["python3", "-m", "uvicorn", "web.server:app",
             "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(NEXUS_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"ok": True, "msg": f"Nexus iniciando (PID {_nexus_proc.pid})…"}
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)


@app.post("/nexus/stop")
async def nexus_stop():
    """Para o processo do Cfdm Nexus"""
    global _nexus_proc
    import subprocess
    killed = []
    # Para processo que iniciamos
    if _nexus_proc and _nexus_proc.poll() is None:
        _nexus_proc.terminate()
        killed.append(_nexus_proc.pid)
        _nexus_proc = None
    # Mata qualquer uvicorn na porta 8000
    try:
        r = subprocess.run(["fuser", "-k", "8000/tcp"], capture_output=True)
        if r.returncode == 0:
            killed.append("porta 8000")
    except Exception:
        pass
    if killed:
        return {"ok": True, "msg": f"Nexus parado ({', '.join(str(k) for k in killed)})"}
    return {"ok": False, "msg": "Nexus não estava rodando"}


# Registro de apps configuráveis pelo usuário
APPS_CONFIG_PATH = Path(__file__).parent.parent / "config" / "apps.json"


def _load_apps():
    try:
        with open(APPS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"apps": []}


@app.get("/apps")
async def list_apps():
    """Lista apps/serviços configurados para controle"""
    return _load_apps()


@app.post("/apps/launch")
async def launch_app(request: Request):
    """Lança um app pelo nome ou comando"""
    import subprocess
    data = await request.json()
    name = data.get("name", "").strip()
    cmd  = data.get("cmd",  "").strip()

    if not cmd:
        # Busca no config
        apps = _load_apps().get("apps", [])
        app_entry = next((a for a in apps if a.get("name","").lower() == name.lower()), None)
        if not app_entry:
            return JSONResponse({"ok": False, "msg": f"App '{name}' não encontrado"}, status_code=404)
        cmd = app_entry.get("cmd", "")

    if not cmd:
        return JSONResponse({"ok": False, "msg": "Comando vazio"}, status_code=400)

    try:
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _icarus_log.info(f"APP LAUNCH → {cmd} (PID {proc.pid})")
        return {"ok": True, "msg": f"Iniciado: {cmd}", "pid": proc.pid}
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)


@app.post("/apps/kill")
async def kill_app(request: Request):
    """Para um processo pelo nome do executável"""
    import subprocess
    data = await request.json()
    name = data.get("name", "").strip()
    if not name:
        return JSONResponse({"ok": False, "msg": "Nome obrigatório"}, status_code=400)
    try:
        r = subprocess.run(["pkill", "-f", name], capture_output=True)
        if r.returncode == 0:
            return {"ok": True, "msg": f"Processo '{name}' encerrado"}
        return {"ok": False, "msg": f"Nenhum processo com '{name}' encontrado"}
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)


@app.get("/ecosystem/status")
def ecosystem_status():
    """Status em tempo real de todos os apps do ecossistema CFDM."""
    import subprocess
    import requests as _req

    result = {
        "icarus":   {"online": True,  "port": 8001, "version": icarus.version, "label": "ICARUS"},
        "nexus":    {"online": False, "port": 8000, "version": None, "agents": 0, "label": "Cfdm Nexus"},
        "cfdmnote": {"running": False, "pid": None, "label": "CfdmNote"},
    }

    # ── Nexus (:8000) — reutiliza o proxy existente ────────────
    try:
        r = _req.get("http://localhost:8000/status", timeout=2)
        if r.status_code == 200:
            d = r.json()
            result["nexus"]["online"]  = bool(d.get("online", True))
            result["nexus"]["version"] = d.get("version", "")
            try:
                ar = _req.get("http://localhost:8000/agents", timeout=2)
                if ar.ok:
                    ad = ar.json()
                    result["nexus"]["agents"] = len(ad.get("agents", []))
            except Exception:
                pass
    except Exception:
        pass

    # ── CfdmNote (processo local) ──────────────────────────────
    try:
        out = subprocess.run(["pgrep", "-f", "cfdmnote"], capture_output=True, text=True)
        pids = [p for p in out.stdout.strip().split('\n') if p]
        if out.returncode == 0 and pids:
            result["cfdmnote"]["running"] = True
            result["cfdmnote"]["pid"] = int(pids[0])
    except Exception:
        pass

    return result


@app.post("/ecosystem/launch")
async def ecosystem_launch(request: Request):
    """Inicia um app do ecossistema."""
    import subprocess, os
    data = await request.json()
    app_name = data.get("app", "").lower()

    display = os.environ.get("DISPLAY", ":1")
    env = {**os.environ, "DISPLAY": display}

    LAUNCHERS = {
        "nexus": [
            "bash", "-c",
            "cd '/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_' && "
            "nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8000 "
            "> /tmp/cfdm-nexus.log 2>&1 &"
        ],
        "cfdmnote": [
            "bash", "-c",
            f"DISPLAY={display} nohup /home/cfdm/Proj-Cfdm-Note_/build/cfdmnote "
            "> /tmp/cfdmnote.log 2>&1 &"
        ],
    }

    if app_name not in LAUNCHERS:
        return JSONResponse({"ok": False, "msg": f"App '{app_name}' desconhecido"}, status_code=400)

    try:
        subprocess.Popen(LAUNCHERS[app_name], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        label = {"nexus": "Cfdm Nexus", "cfdmnote": "CfdmNote"}.get(app_name, app_name)
        return {"ok": True, "msg": f"{label} iniciando..."}
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)


@app.post("/ecosystem/stop")
async def ecosystem_stop(request: Request):
    """Para um app do ecossistema."""
    import subprocess
    data = await request.json()
    app_name = data.get("app", "").lower()

    KILL_PATTERNS = {
        "nexus":    "uvicorn web.server:app.*8000",
        "cfdmnote": "build/cfdmnote",
    }

    if app_name not in KILL_PATTERNS:
        return JSONResponse({"ok": False, "msg": f"App '{app_name}' desconhecido"}, status_code=400)

    try:
        r = subprocess.run(["pkill", "-f", KILL_PATTERNS[app_name]], capture_output=True)
        label = {"nexus": "Cfdm Nexus", "cfdmnote": "CfdmNote"}.get(app_name, app_name)
        if r.returncode == 0:
            return {"ok": True, "msg": f"{label} encerrado"}
        return {"ok": False, "msg": f"{label} não estava rodando"}
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)


@app.get("/skills")
async def list_skills():
    """Lista todas as skills: builtin + dinâmicas criadas pelo Architect."""
    skills_dir = Path(__file__).parent.parent / "skills"
    dynamic_json = Path(__file__).parent.parent / "config" / "dynamic_skills.json"

    # Carrega dinâmicas
    try:
        with open(dynamic_json, "r", encoding="utf-8") as f:
            dynamic_data = json.load(f)
    except Exception:
        dynamic_data = {}

    dynamic_files = {v.get("file", "") for v in dynamic_data.values()}

    # Metadados de skills builtin conhecidas
    builtin_meta = {
        "tarefa_skill":      {"label": "Tarefas",        "icon": "✅", "desc": "Gerencia tarefas e to-dos"},
        "nexus_skill":       {"label": "Nexus",           "icon": "⚡", "desc": "Integração com Cfdm Nexus"},
        "financeiro_skill":  {"label": "Financeiro",      "icon": "💰", "desc": "Sentinela financeiro e fluxo de caixa"},
        "noticias_skill":    {"label": "Notícias",        "icon": "📰", "desc": "Briefing matinal e RSS"},
        "agenda_skill":      {"label": "Agenda",          "icon": "📅", "desc": "Compromissos e calendário local"},
        "sistema_skill":     {"label": "Sistema",         "icon": "🖥", "desc": "Hora, apps, volume, screenshot"},
        "busca_skill":       {"label": "Busca",           "icon": "🔍", "desc": "Wikipedia, clima e pesquisa"},
        "rpi_skill":         {"label": "Raspberry Pi",    "icon": "🍓", "desc": "GPIO e automação residencial"},
        "voz_skill":         {"label": "Voz",             "icon": "🎙", "desc": "Controle de TTS e STT"},
        "custom_skill":      {"label": "Respostas Custom","icon": "💬", "desc": "Respostas personalizadas por gatilho"},
        "autocode_skill":    {"label": "Architect",       "icon": "🤖", "desc": "Cria novas skills em linguagem natural"},
    }

    skills = []
    if skills_dir.exists():
        for f in sorted(skills_dir.glob("*.py")):
            if f.stem.startswith("_"):
                continue
            is_dynamic = f.name in dynamic_files
            meta = builtin_meta.get(f.stem, {})

            # Tenta extrair SKILL_NAME e trigger count do arquivo
            try:
                src = f.read_text(encoding="utf-8")
                import re as _re
                sn_m = _re.search(r'SKILL_NAME\s*=\s*["\']([^"\']+)["\']', src)
                skill_name = sn_m.group(1) if sn_m else f.stem
                tp_m = _re.findall(r'r["\'][^"\']+["\']', src)
                pattern_count = len(tp_m)
            except Exception:
                skill_name = f.stem
                pattern_count = 0

            # Info dinâmica se houver
            dyn_info = next((v for v in dynamic_data.values() if v.get("file") == f.name), {})

            skills.append({
                "file":          f.name,
                "stem":          f.stem,
                "skill_name":    skill_name,
                "label":         meta.get("label") or dyn_info.get("description", skill_name),
                "icon":          meta.get("icon", "🔧"),
                "desc":          meta.get("desc") or dyn_info.get("description", ""),
                "is_dynamic":    is_dynamic,
                "is_builtin":    not is_dynamic,
                "pattern_count": pattern_count,
                "size_bytes":    f.stat().st_size,
                "loaded":        skill_name in (icarus.router.skills or {}),
            })

    return {"skills": skills, "total": len(skills),
            "builtin": sum(1 for s in skills if s["is_builtin"]),
            "dynamic": sum(1 for s in skills if s["is_dynamic"])}


@app.get("/projects")
async def get_projects():
    """Retorna memória completa de projetos."""
    projects_file = Path(__file__).parent.parent / "memory" / "projects.json"
    try:
        return json.loads(projects_file.read_text(encoding="utf-8"))
    except Exception:
        return {"projects": {}, "sessoes_recentes": []}


@app.post("/projects/{proj_key}/log")
async def log_project_change(proj_key: str, request: Request):
    """Registra mudança em um projeto (chamado pelo Claude Code ou scripts externos)."""
    projects_file = Path(__file__).parent.parent / "memory" / "projects.json"
    try:
        data = json.loads(projects_file.read_text(encoding="utf-8"))
    except Exception:
        return JSONResponse({"error": "projects.json não encontrado"}, status_code=500)

    body = await request.json()
    resumo    = body.get("resumo", "")
    versao    = body.get("versao", "")
    arquivos  = body.get("arquivos", [])
    mudancas  = body.get("mudancas", [])

    proj = data.get("projects", {}).get(proj_key)
    if not proj:
        return JSONResponse({"error": f"Projeto '{proj_key}' não encontrado"}, status_code=404)

    # Adiciona mudanças ao histórico do projeto
    for m in reversed(mudancas):
        proj.setdefault("ultimas_mudancas", []).insert(0, m)
    proj["ultimas_mudancas"] = proj["ultimas_mudancas"][:10]
    if versao:
        proj["versao"] = versao

    # Registra sessão
    data.setdefault("sessoes_recentes", []).append({
        "data": datetime.datetime.now().strftime("%Y-%m-%d"),
        "projeto": proj_key,
        "resumo": resumo,
        "versao_resultante": versao or proj.get("versao", ""),
        "arquivos_modificados": arquivos,
    })
    data["sessoes_recentes"] = data["sessoes_recentes"][-20:]

    data["_meta"]["last_sync"] = datetime.datetime.now().isoformat()
    projects_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    _append_log("INFO", "PROJETO", f"Sessão registrada: {proj_key} — {resumo[:60]}")
    return {"ok": True, "projeto": proj_key, "versao": proj.get("versao")}


@app.patch("/projects/{proj_key}/steps")
async def update_next_steps(proj_key: str, request: Request):
    """Atualiza próximos passos de um projeto."""
    projects_file = Path(__file__).parent.parent / "memory" / "projects.json"
    try:
        data = json.loads(projects_file.read_text(encoding="utf-8"))
    except Exception:
        return JSONResponse({"error": "projects.json não encontrado"}, status_code=500)

    body = await request.json()
    steps = body.get("steps", [])
    proj = data.get("projects", {}).get(proj_key)
    if not proj:
        return JSONResponse({"error": "Projeto não encontrado"}, status_code=404)

    proj["proximos_passos"] = steps
    data["_meta"]["last_sync"] = datetime.datetime.now().isoformat()
    projects_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return {"ok": True, "steps": steps}


@app.get("/scripts")
async def list_scripts():
    """Lista scripts disponíveis em scripts/"""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    scripts = []
    if scripts_dir.exists():
        for f in sorted(scripts_dir.glob("*.py")):
            scripts.append({
                "name": f.stem,
                "file": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1)
            })
    return {"scripts": scripts, "total": len(scripts)}


# ── Autocode — Agente Architect ──────────────────────────────────────────────

@app.get("/autocode/skills")
async def list_dynamic_skills():
    """Lista skills criadas pelo Agente Architect."""
    dynamic_json = Path(__file__).parent.parent / "config" / "dynamic_skills.json"
    try:
        with open(dynamic_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    skills = []
    for name, info in data.items():
        file_path = Path(__file__).parent.parent / "skills" / info.get("file", "")
        skills.append({
            "name": name,
            "description": info.get("description", ""),
            "file": info.get("file", ""),
            "patterns": info.get("patterns", []),
            "exists": file_path.exists(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        })
    return {"skills": skills, "total": len(skills)}


@app.post("/autocode/create")
async def create_skill_api(request: Request):
    """Cria uma nova skill via API (mesma lógica do chat)."""
    body = await request.json()
    description = body.get("description", "").strip()
    if not description:
        return JSONResponse({"error": "description is required"}, status_code=400)

    result = icarus.process(f"criar skill para {description}")
    return {"result": result}


@app.delete("/autocode/skills/{skill_name}")
async def delete_dynamic_skill(skill_name: str):
    """Deleta skill dinâmica pelo nome."""
    result = icarus.process(f"deletar skill {skill_name}")
    return {"result": result}


@app.get("/autocode/preview/{skill_name}")
async def preview_skill_code(skill_name: str):
    """Retorna o código-fonte de uma skill dinâmica."""
    dynamic_json = Path(__file__).parent.parent / "config" / "dynamic_skills.json"
    try:
        with open(dynamic_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    if skill_name not in data:
        return JSONResponse({"error": "Skill não encontrada"}, status_code=404)

    file_path = Path(__file__).parent.parent / "skills" / data[skill_name].get("file", "")
    if not file_path.exists():
        return JSONResponse({"error": "Arquivo não encontrado"}, status_code=404)

    code = file_path.read_text(encoding="utf-8")
    return {"name": skill_name, "code": code, "file": data[skill_name].get("file", "")}


# ═══════════════════════════════════════════════════════════════
# ── Commands CRUD ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════
_CUSTOM_CMDS = Path(__file__).parent.parent / "config" / "custom_commands.json"
_COMMANDS_JSON = Path(__file__).parent.parent / "config" / "commands.json"
_RULES_FILE = Path(__file__).parent.parent / "config" / "rules.json"

def _load_custom_cmds():
    try: return json.loads(_CUSTOM_CMDS.read_text(encoding="utf-8"))
    except: return []

def _save_custom_cmds(data):
    _CUSTOM_CMDS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_cmd_json():
    try: return json.loads(_COMMANDS_JSON.read_text(encoding="utf-8"))
    except: return {"modes": {}}

def _save_cmd_json(data):
    _COMMANDS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_rules():
    try: return json.loads(_RULES_FILE.read_text(encoding="utf-8"))
    except: return []

def _save_rules(rules):
    _RULES_FILE.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/commands")
async def get_custom_commands():
    return {"commands": _load_custom_cmds()}

@app.post("/commands")
async def create_command(request: Request):
    body = await request.json()
    key = (body.get("key") or "").strip()
    if not key:
        return JSONResponse({"error": "key obrigatório"}, status_code=400)
    cmds = _load_custom_cmds()
    cmd = {
        "id": str(int(datetime.datetime.now().timestamp() * 1000)),
        "key": key,
        "desc": (body.get("desc") or "").strip(),
        "response": (body.get("response") or "").strip(),
        "exception": (body.get("exception") or "").strip(),
        "observation": (body.get("observation") or "").strip(),
        "cat": (body.get("cat") or "Custom").strip(),
        "example": (body.get("example") or "").strip(),
        "created": datetime.datetime.now().isoformat(),
    }
    cmds.append(cmd)
    _save_custom_cmds(cmds)
    return {"result": "Comando criado", "command": cmd}

@app.put("/commands/{cmd_id}")
async def update_command(cmd_id: str, request: Request):
    body = await request.json()
    cmds = _load_custom_cmds()
    for i, c in enumerate(cmds):
        if c.get("id") == cmd_id:
            for f in ("key", "desc", "response", "exception", "observation", "cat", "example"):
                if f in body: cmds[i][f] = body[f]
            _save_custom_cmds(cmds)
            return {"result": "Atualizado", "command": cmds[i]}
    return JSONResponse({"error": "Não encontrado"}, status_code=404)

@app.delete("/commands/{cmd_id}")
async def delete_command(cmd_id: str):
    cmds = _load_custom_cmds()
    new = [c for c in cmds if c.get("id") != cmd_id]
    if len(new) == len(cmds):
        return JSONResponse({"error": "Não encontrado"}, status_code=404)
    _save_custom_cmds(new)
    return {"result": "Apagado"}


# ── Modes CRUD ─────────────────────────────────────────────────
@app.post("/modes/create")
async def create_mode(request: Request):
    body = await request.json()
    key = (body.get("key") or "").strip().upper().replace(" ", "_").replace("-", "_")
    if not key:
        return JSONResponse({"error": "key obrigatório"}, status_code=400)
    data = _load_cmd_json()
    data.setdefault("modes", {})
    if key in data["modes"]:
        return JSONResponse({"error": f"Modo '{key}' já existe"}, status_code=409)
    data["modes"][key] = {
        "descricao": (body.get("descricao") or "").strip(),
        "camada":    int(body.get("camada") or 6),
        "parametros": body.get("parametros") or [],
        "persona":   (body.get("persona") or "").strip(),
    }
    _save_cmd_json(data)
    icarus.reload_commands()
    return {"result": f"Modo '{key}' criado"}

@app.put("/modes/{mode_key}")
async def update_mode(mode_key: str, request: Request):
    body = await request.json()
    data = _load_cmd_json()
    key = mode_key.upper()
    if key not in data.get("modes", {}):
        return JSONResponse({"error": "Modo não encontrado"}, status_code=404)
    for f in ("descricao", "camada", "parametros", "persona"):
        if f in body: data["modes"][key][f] = body[f]
    _save_cmd_json(data)
    icarus.reload_commands()
    return {"result": f"Modo '{key}' atualizado", "mode": data["modes"][key]}

@app.delete("/modes/{mode_key}")
async def delete_mode(mode_key: str):
    data = _load_cmd_json()
    key = mode_key.upper()
    if key not in data.get("modes", {}):
        return JSONResponse({"error": "Modo não encontrado"}, status_code=404)
    del data["modes"][key]
    _save_cmd_json(data)
    icarus.reload_commands()
    return {"result": f"Modo '{key}' apagado"}


# ── Rules CRUD ─────────────────────────────────────────────────
@app.get("/rules")
async def get_rules():
    return {"rules": _load_rules()}

@app.post("/rules")
async def create_rule(request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip()
    if not name:
        return JSONResponse({"error": "name obrigatório"}, status_code=400)
    rules = _load_rules()
    rule = {
        "id":              str(int(datetime.datetime.now().timestamp() * 1000)),
        "name":            name,
        "trigger_type":    body.get("trigger_type", "text"),
        "trigger_pattern": (body.get("trigger_pattern") or "").strip(),
        "action_type":     body.get("action_type", "response"),
        "action_value":    (body.get("action_value") or "").strip(),
        "conditions":      body.get("conditions") or {},
        "enabled":         bool(body.get("enabled", True)),
        "created":         datetime.datetime.now().isoformat(),
    }
    rules.append(rule)
    _save_rules(rules)
    return {"result": "Regra criada", "rule": rule}

@app.put("/rules/{rule_id}")
async def update_rule(rule_id: str, request: Request):
    body = await request.json()
    rules = _load_rules()
    for i, r in enumerate(rules):
        if r.get("id") == rule_id:
            for f in ("name","trigger_type","trigger_pattern","action_type","action_value","conditions","enabled"):
                if f in body: rules[i][f] = body[f]
            _save_rules(rules)
            return {"result": "Atualizado", "rule": rules[i]}
    return JSONResponse({"error": "Regra não encontrada"}, status_code=404)

@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    rules = _load_rules()
    new = [r for r in rules if r.get("id") != rule_id]
    if len(new) == len(rules):
        return JSONResponse({"error": "Não encontrada"}, status_code=404)
    _save_rules(new)
    return {"result": "Regra apagada"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
