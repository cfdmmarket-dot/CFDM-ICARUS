#!/bin/bash
# ICARUS Launcher — Raspberry Pi
# Inicia Nexus + ICARUS + Wake Word detector
# Auto-detecta RPi e configura áudio

set -e

ICARUS_DIR="/home/$(whoami)/Proj-CFDM-ICARUS_"
NEXUS_DIR="/home/$(whoami)/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_"
LOG_DIR="/tmp"

# ── Detecta se é Raspberry Pi ──────────────────────────────
is_rpi() {
    grep -qi "raspberry" /proc/cpuinfo 2>/dev/null || \
    grep -qi "BCM" /proc/cpuinfo 2>/dev/null || \
    [ -f /etc/rpi-issue ] || \
    uname -m | grep -qi "aarch64\|armv"
}

if is_rpi; then
    echo "╔══════════════════════════════════════╗"
    echo "║  ICARUS — Raspberry Pi Mode          ║"
    echo "╚══════════════════════════════════════╝"
    IS_RPI=true
else
    echo "╔══════════════════════════════════════╗"
    echo "║  ICARUS — Desktop Mode               ║"
    echo "╚══════════════════════════════════════╝"
    IS_RPI=false
fi

# ── Configura DISPLAY ──────────────────────────────────────
if [ -z "$DISPLAY" ]; then
    ACTIVE_DISPLAY=$(who 2>/dev/null | grep -oP ':\d+' | head -1)
    export DISPLAY="${ACTIVE_DISPLAY:-:0}"
fi

if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    DBUS_FILE="/run/user/$(id -u)/bus"
    [ -S "$DBUS_FILE" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=$DBUS_FILE"
fi

# ── Configura áudio no RPi ────────────────────────────────
if [ "$IS_RPI" = true ]; then
    # Force HDMI ou 3.5mm jack
    # 0=auto, 1=3.5mm jack, 2=HDMI
    amixer cset numid=3 1 > /dev/null 2>&1 || true
    echo "[RPi] Áudio: saída 3.5mm jack"
fi

# ── 1. Cfdm Nexus (:8000) ─────────────────────────────────
echo ""
if curl -s --max-time 1 http://localhost:8000/status > /dev/null 2>&1; then
    echo "[✓] Cfdm Nexus já rodando em :8000"
else
    echo "[→] Iniciando Cfdm Nexus (:8000)..."
    cd "$NEXUS_DIR"
    nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8000 \
        > "$LOG_DIR/cfdm-nexus.log" 2>&1 &
    echo "    Log: $LOG_DIR/cfdm-nexus.log"
    for i in $(seq 1 20); do
        sleep 1
        curl -s --max-time 1 http://localhost:8000/status > /dev/null 2>&1 && \
            echo "[✓] Nexus online" && break
        [ $i -eq 20 ] && echo "[!] Nexus demorou — continuando..."
    done
fi

# ── 2. ICARUS (:8001) ─────────────────────────────────────
if curl -s --max-time 1 http://localhost:8001/status > /dev/null 2>&1; then
    echo "[✓] ICARUS já rodando em :8001"
else
    echo "[→] Iniciando ICARUS v1.4.0 (:8001)..."
    cd "$ICARUS_DIR"
    nohup python3 -m uvicorn web.server:app --host 0.0.0.0 --port 8001 --reload \
        > "$LOG_DIR/icarus.log" 2>&1 &
    echo "    Log: $LOG_DIR/icarus.log"
    for i in $(seq 1 20); do
        sleep 1
        curl -s --max-time 1 http://localhost:8001/status > /dev/null 2>&1 && \
            echo "[✓] ICARUS online" && break
        [ $i -eq 20 ] && echo "[!] ICARUS demorou — verifique $LOG_DIR/icarus.log"
    done
fi

# ── 3. Wake Word (apenas RPi ou se --wake flag) ───────────
WAKE_FLAG=false
for arg in "$@"; do [ "$arg" = "--wake" ] && WAKE_FLAG=true; done

if [ "$IS_RPI" = true ] || [ "$WAKE_FLAG" = true ]; then
    echo "[→] Iniciando Wake Word detector..."
    cd "$ICARUS_DIR"
    nohup python3 scripts/wake_word.py --rpi \
        > "$LOG_DIR/icarus-wake.log" 2>&1 &
    echo "    Log: $LOG_DIR/icarus-wake.log"
    echo "[✓] Wake Word: diga 'ICARUS' para ativar"
fi

# ── 4. Abre no navegador ──────────────────────────────────
if [ "$IS_RPI" = true ]; then
    # RPi — Chromium em modo kiosk (fullscreen)
    echo "[→] Abrindo ICARUS em kiosk mode..."
    sleep 2
    DISPLAY="${DISPLAY:-:0}" chromium-browser \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --app="http://localhost:8001" 2>/dev/null &
else
    DISPLAY="${DISPLAY:-:1}" google-chrome "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" chromium-browser "http://localhost:8001" 2>/dev/null || \
    DISPLAY="${DISPLAY:-:1}" xdg-open "http://localhost:8001" 2>/dev/null
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ICARUS     → http://localhost:8001"
echo "  Cfdm Nexus → http://localhost:8000"
echo "  Wake Word  → $([ "$IS_RPI" = true ] || [ "$WAKE_FLAG" = true ] && echo "ATIVO — diga 'ICARUS'" || echo "use --wake para ativar")"
echo "  Logs       → $LOG_DIR/icarus.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
