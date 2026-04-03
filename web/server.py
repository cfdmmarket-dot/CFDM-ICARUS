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

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.icarus_core import IcarusCore, ICARUS_PERSONA

app = FastAPI(title="ICARUS", description="Assistente Pessoal CFDM Holding", version="1.3.0")

# Buffer circular de logs (últimas 200 entradas)
LOG_BUFFER: deque = deque(maxlen=200)
_server_start = datetime.datetime.now()

class BufferHandler(logging.Handler):
    def emit(self, record):
        LOG_BUFFER.append({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg": self.format(record)
        })

_buf_handler = BufferHandler()
_buf_handler.setFormatter(logging.Formatter("%(name)s — %(message)s"))
logging.getLogger("uvicorn.access").addHandler(_buf_handler)
logging.getLogger("icarus").addHandler(_buf_handler)
_icarus_log = logging.getLogger("icarus")
_icarus_log.setLevel(logging.INFO)

# Instância global do ICARUS
icarus = IcarusCore()


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
            model = whisper.load_model("base")
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
async def get_logs(n: int = 50):
    """Últimas N entradas do log do servidor"""
    entries = list(LOG_BUFFER)[-n:]
    return {"logs": entries, "total": len(LOG_BUFFER)}


@app.get("/nexus/agents")
async def nexus_agents_proxy():
    """Proxy para buscar agentes do Cfdm Nexus"""
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8000/agents", timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return {"agents": [], "total": 0, "error": "Nexus offline"}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
