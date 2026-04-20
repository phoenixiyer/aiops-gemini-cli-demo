#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ADK_DIR="$PROJECT_DIR/adk-agent"

echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🤖 NovaMart Multi-Agent AIOps${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Agents:${NC}"
echo -e "    ${YELLOW}Commander${NC}  — Root orchestrator"
echo -e "    ${GREEN}Apollo${NC}     — Senior SRE (Observability + K8s + Alerting)"
echo -e "    ${PURPLE}Athena${NC}     — Security Analyst (Auth + CVE + Access Logs)"
echo ""
echo -e "  ${CYAN}UI:${NC}       http://localhost:8001/dev-ui/?app=commander"
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""

# Load .env
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.env"
  set +a
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo -e "  ERROR: GEMINI_API_KEY not set."
  echo -e "  Run: cp .env.example .env && edit .env"
  exit 1
fi

# ADK uses GOOGLE_API_KEY or GEMINI_API_KEY — export both to be safe
export GOOGLE_API_KEY="${GEMINI_API_KEY}"
export GOOGLE_GENAI_USE_VERTEXAI="false"

# Run adk web from inside adk-agent/ so it treats it as AGENTS_DIR
# The commander/ subdirectory (with __init__.py + agent.py) is the one app ADK will find
cd "$ADK_DIR"
"$PROJECT_DIR/.venv/bin/adk" web --port 8001 --host 0.0.0.0
