#!/usr/bin/env bash
# =============================================================================
#  NovaMart AIOps Demo — Service Stopper
#  Gracefully stops the Topology Dashboard and Multi-Agent ADK UI and frees ports.
# =============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Ports to clean up
DASHBOARD_PORT=8080
ADK_PORT=8001

echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🛑 Stopping NovaMart Demo Services${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""

killed_something=false

for PORT in $DASHBOARD_PORT $ADK_PORT; do
  if lsof -ti:"$PORT" &>/dev/null; then
    echo -e "  ${YELLOW}Stopping service on port $PORT...${NC}"
    lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
    killed_something=true
    sleep 0.5
  fi
done

if [ "$killed_something" = true ]; then
  echo ""
  echo -e "  ${GREEN}✓${NC} All ports successfully freed and services stopped."
else
  echo -e "  ${GREEN}✓${NC} No services were found running on ports $DASHBOARD_PORT or $ADK_PORT."
fi

echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""
exit 0
