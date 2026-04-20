#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🌐 NovaMart Topology Dashboard${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}URL:${NC}      http://localhost:8080"
echo -e "  ${CYAN}Refresh:${NC}  every 3 seconds (live)"
echo ""
echo -e "  ${YELLOW}Tip:${NC} Use ${BOLD}./scripts/start.sh${NC} to launch everything at once."
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_DIR"
DASHBOARD_PORT=8080 .venv/bin/python dashboard/server.py
