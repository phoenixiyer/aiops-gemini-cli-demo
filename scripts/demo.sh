#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🎯 AIOps Demo Launcher${NC}"
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Platform:${NC}  NovaMart (simulated e-commerce)"
echo -e "  ${CYAN}AI Agent:${NC}  Apollo (Senior SRE)"
echo -e "  ${CYAN}Tools:${NC}     Observability · Kubernetes · Alerting"
echo ""
echo -e "${BOLD}  Available Scenarios:${NC}"
echo -e "  ${YELLOW}1)${NC} CPU Spike         — Runaway regex in payment-service"
echo -e "  ${YELLOW}2)${NC} Memory Leak       — Unclosed cursors in order-service"
echo -e "  ${YELLOW}3)${NC} Cascading Failure  — DB lock causes upstream 5xx cascade"
echo -e "  ${YELLOW}4)${NC} Bad Deployment    — Breaking API change in canary deploy"
echo ""
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Getting started:${NC}"
echo -e "    ${CYAN}cd ${PROJECT_DIR}${NC}"
echo -e "    ${CYAN}gemini${NC}"
echo ""
echo -e "  ${BOLD}Suggested first prompts:${NC}"
echo -e "    ${GREEN}\"What alerts are currently firing?\"${NC}"
echo -e "    ${GREEN}\"Trigger the cascading_failure scenario\"${NC}"
echo -e "    ${GREEN}\"Diagnose the payment-service incident\"${NC}"
echo ""
echo -e "  ${BOLD}Full demo flow:${NC}"
echo -e "    1. ${GREEN}\"What alerts are currently firing?\"${NC}"
echo -e "    2. ${GREEN}\"Diagnose the incident on payment-service\"${NC}"
echo -e "    3. ${GREEN}\"Check the service topology for the blast radius\"${NC}"
echo -e "    4. ${GREEN}\"What does the runbook recommend?\"${NC}"
echo -e "    5. ${GREEN}\"Scale payment-service to 5 replicas\"${NC}"
echo -e "    6. ${GREEN}\"Generate a post-incident report\"${NC}"
echo ""
