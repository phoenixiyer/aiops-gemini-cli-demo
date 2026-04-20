#!/usr/bin/env bash
# =============================================================================
#  NovaMart AIOps Demo — One-Command Launcher
#  Starts everything: Topology Dashboard + Multi-Agent ADK UI + Gemini CLI
# =============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Ports (change here if you have conflicts)
DASHBOARD_PORT=8080
ADK_PORT=8001

# PIDs to track for cleanup
DASHBOARD_PID=""
ADK_PID=""

# ---------------------------------------------------------------------------
# Cleanup: kill background services on exit / Ctrl+C
# ---------------------------------------------------------------------------
cleanup() {
  echo ""
  echo -e "${YELLOW}  Shutting down services...${NC}"
  [[ -n "$DASHBOARD_PID" ]] && kill "$DASHBOARD_PID" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Dashboard stopped"
  [[ -n "$ADK_PID" ]] && kill "$ADK_PID" 2>/dev/null && echo -e "  ${GREEN}✓${NC} ADK server stopped"
  # Kill any orphaned uvicorn/adk processes on these ports
  lsof -ti:"$DASHBOARD_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
  lsof -ti:"$ADK_PORT"       2>/dev/null | xargs kill -9 2>/dev/null || true
  echo ""
  exit 0
}
trap cleanup INT TERM EXIT

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
clear
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🚀 NovaMart AIOps Demo — Full Stack Launcher${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
if [[ -f "$PROJECT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.env"
  set +a
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo -e "  ${RED}ERROR:${NC} GEMINI_API_KEY not set."
  echo -e "  Run: ${BOLD}cp .env.example .env${NC} then add your key."
  exit 1
fi

# ---------------------------------------------------------------------------
# Kill anything already using our ports
# ---------------------------------------------------------------------------
for PORT in $DASHBOARD_PORT $ADK_PORT; do
  if lsof -ti:"$PORT" &>/dev/null; then
    echo -e "  ${YELLOW}⚠${NC}  Port $PORT in use — freeing it..."
    lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
    sleep 0.5
  fi
done

# ---------------------------------------------------------------------------
# Start Topology Dashboard (port 8080)
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}[1/3]${NC} Starting Topology Dashboard on port ${BOLD}$DASHBOARD_PORT${NC}..."
DASHBOARD_PORT=$DASHBOARD_PORT \
  "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/dashboard/server.py" \
  > "$PROJECT_DIR/.dashboard.log" 2>&1 &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
for i in {1..15}; do
  if curl -sf "http://localhost:$DASHBOARD_PORT/api/topology" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Dashboard ready → ${BOLD}http://localhost:$DASHBOARD_PORT${NC}"
    break
  fi
  sleep 0.5
done

# ---------------------------------------------------------------------------
# Start ADK Multi-Agent Web UI (port 8001)
# ---------------------------------------------------------------------------
echo -e "  ${CYAN}[2/3]${NC} Starting Multi-Agent ADK UI on port ${BOLD}$ADK_PORT${NC}..."

# ADK needs GOOGLE_API_KEY (not just GEMINI_API_KEY) + Vertex AI disabled
export GOOGLE_API_KEY="${GEMINI_API_KEY}"
export GOOGLE_GENAI_USE_VERTEXAI="false"

# Run from adk-agent/ — ADK treats it as AGENTS_DIR and finds commander/ inside
cd "$PROJECT_DIR/adk-agent"
"$PROJECT_DIR/.venv/bin/adk" web \
  --port "$ADK_PORT" \
  --host 0.0.0.0 \
  > "$PROJECT_DIR/.adk.log" 2>&1 &
ADK_PID=$!
cd "$PROJECT_DIR"

# Wait for ADK to be ready
for i in {1..20}; do
  if curl -sf "http://localhost:$ADK_PORT" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} ADK UI ready       → ${BOLD}http://localhost:$ADK_PORT/dev-ui/?app=commander${NC}"
    break
  fi
  sleep 0.5
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ✅ All services running:${NC}"
echo ""
echo -e "  ${CYAN}🌐 Topology Dashboard${NC}   http://localhost:${DASHBOARD_PORT}"
echo -e "  ${PURPLE}🤖 Multi-Agent ADK UI${NC}   http://localhost:${ADK_PORT}"
echo ""
echo -e "${BOLD}  [3/3] Launching Gemini CLI (Apollo SRE Agent)...${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Tip:${NC} Try these prompts to see all three in action:"
echo -e "    \"Trigger the cascading_failure scenario\""
echo -e "      ↳ Watch ${BOLD}http://localhost:${DASHBOARD_PORT}${NC} turn red"
echo -e "    Then open ${BOLD}http://localhost:${ADK_PORT}${NC} for:"
echo -e "    \"Run a joint SRE + security assessment on payment-service\""
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""

# Open browser tabs
open "http://localhost:${DASHBOARD_PORT}" 2>/dev/null || \
  xdg-open "http://localhost:${DASHBOARD_PORT}" 2>/dev/null || true
sleep 0.5
open "http://localhost:${ADK_PORT}" 2>/dev/null || \
  xdg-open "http://localhost:${ADK_PORT}" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Drop into Gemini CLI — this is the foreground process
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"
exec gemini
