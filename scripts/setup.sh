#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🚀 AIOps Gemini CLI Demo — Setup${NC}"
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo ""

# Check Python
echo -e "${BOLD}[1/4] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓${NC} $PY_VERSION"
else
    echo -e "  ${RED}✗ Python 3.11+ is required${NC}"
    exit 1
fi

# Check uv
echo -e "${BOLD}[2/4] Checking uv...${NC}"
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1)
    echo -e "  ${GREEN}✓${NC} $UV_VERSION"
else
    echo -e "  ${YELLOW}⚠ uv not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "  ${GREEN}✓${NC} uv installed"
fi

# Install dependencies
echo -e "${BOLD}[3/3] Installing dependencies...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
uv sync 2>&1 | tail -1
echo -e "  ${GREEN}✓${NC} Dependencies installed"

echo ""
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Setup complete!${NC}"
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo ""
echo -e "  Next steps:"
echo -e "    ${BOLD}cd $PROJECT_DIR${NC}"
echo -e "    ${BOLD}gemini${NC}"
echo ""
echo -e "  Then try:"
echo -e "    ${YELLOW}\"What alerts are currently firing?\"${NC}"
echo -e "    ${YELLOW}\"Trigger the cascading_failure scenario\"${NC}"
echo ""
