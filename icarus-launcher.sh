#!/bin/bash
# ICARUS Launcher v1.3.0 — Inicia Cfdm Nexus + ICARUS e abre navegador
# Nexus roda em :8000 | ICARUS roda em :8001

ICARUS_DIR="/home/cfdm/Proj-CFDM-ICARUS_"
NEXUS_DIR="/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_"

# ── Display e DBUS ─────────────────────────────────────
if [ -z "$DISPLAY" ]; then
    ACTIVE_DISPLAY=$(who | grep -oP ':\d+' | head -1)
    export DISPLAY="${ACTIVE_DISPLAY:-:1}"
fi
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    DBUS_FILE="/run/user/$(id -u)/bus"
    [ -S "$DBUS_FILE" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=$DBUS_FILE"
fi

# ── 1. Cfdm Nexus (:8000) ──────────────────────────────
if curl -s --max-time 1 http://localhost:8000/status > /dev/null 2>&1; then
    echo "[✓] Cfdm Nexus já está rodando em :8000"
else
    echo "[→] Iniciando Cfdm Nexus..."
    cd "$NEXUS_DIR"
    nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8000 > /tmp/cfdm-nexus.log 2>&1 &
    NEXUS_PID=$!
    echo "    PID: $NEXUS_PID — log: /tmp/cfdm-nexus.log"
    for i in $(seq 1 15); do
        sleep 1
        curl -s --max-time 1 http://localhost:8000/status > /dev/null 2>&1 && echo "[✓] Nexus online" && break
    done
fi

# ── 2. ICARUS (:8001) ──────────────────────────────────
if curl -s --max-time 1 http://localhost:8001/status > /dev/null 2>&1; then
    echo "[✓] ICARUS já está rodando em :8001"
else
    echo "[→] Iniciando ICARUS v1.3.0..."
    cd "$ICARUS_DIR"
    nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8001 --reload > /tmp/icarus.log 2>&1 &
    ICARUS_PID=$!
    echo "    PID: $ICARUS_PID — log: /tmp/icarus.log"
    for i in $(seq 1 20); do
        sleep 1
        curl -s --max-time 1 http://localhost:8001/status > /dev/null 2>&1 && echo "[✓] ICARUS online" && break
    done
fi

# ── 3. Abre no Chrome (Web Speech API requer Chrome) ───
echo "[→] Abrindo ICARUS em http://localhost:8001"
DISPLAY="${DISPLAY:-:1}" google-chrome "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium-browser "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" xdg-open "http://localhost:8001" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ICARUS    → http://localhost:8001"
echo "  Cfdm Nexus → http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
