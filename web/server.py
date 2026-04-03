"""
ICARUS Web Server — Interface web do assistente pessoal
"""

import sys
import json
import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.icarus_core import IcarusCore, ICARUS_PERSONA

app = FastAPI(title="ICARUS", description="Assistente Pessoal CFDM Holding", version="1.1.0")

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

    response = icarus.process(user_input)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
