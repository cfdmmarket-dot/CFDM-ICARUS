#!/bin/bash
# ICARUS Launcher — Inicia o servidor e abre o navegador

PROJECT_DIR="/home/cfdm/Proj-CFDM-ICARUS_"
cd "$PROJECT_DIR"

# Detecta display
if [ -z "$DISPLAY" ]; then
    ACTIVE_DISPLAY=$(who | grep -oP ':\d+' | head -1)
    export DISPLAY="${ACTIVE_DISPLAY:-:1}"
fi

# DBUS
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    DBUS_FILE="/run/user/$(id -u)/bus"
    [ -S "$DBUS_FILE" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=$DBUS_FILE"
fi

# Verifica se ICARUS já está rodando na porta 8001
if pgrep -f "uvicorn web.server:app.*8001" > /dev/null; then
    echo "ICARUS já está rodando!"
else
    echo "Iniciando ICARUS v1.3.0 — JARVIS HUD..."
    cd "$PROJECT_DIR"
    nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8001 --reload > /tmp/icarus.log 2>&1 &

    # Aguarda o servidor responder
    for i in $(seq 1 15); do
        sleep 1
        curl -s http://localhost:8001 -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200" && break
    done
fi

# Abre no navegador
DISPLAY="${DISPLAY:-:1}" xdg-open "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" firefox "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium-browser "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium "http://localhost:8001" 2>/dev/null

echo "ICARUS iniciado em http://localhost:8001"
