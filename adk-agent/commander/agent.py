"""
NovaMart Multi-Agent AIOps System — powered by Google ADK.

Agents:
  - Commander  : Root orchestrator that routes tasks to Apollo or Athena
  - Apollo     : Senior SRE — uses Observability, Kubernetes, Alerting MCP servers
  - Athena     : Security Analyst — uses the Security MCP server

Loaded by:  adk web --port 8001 (run from the adk-agent/ directory)
App name in UI: commander
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioConnectionParams,
    StdioServerParameters,
)

# ---------------------------------------------------------------------------
# Paths — climb: commander/ → adk-agent/ → project root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent          # adk-agent/commander/
_ADK_DIR = _HERE.parent                # adk-agent/
_PROJECT_ROOT = _ADK_DIR.parent        # aiops-gemini-cli-demo/

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------
_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ---------------------------------------------------------------------------
# MCP server paths
# ---------------------------------------------------------------------------
_UV = "uv"
_UV_ARGS = ["run", "--python", "3.11"]
_UV_ENV = {"UV_INDEX_URL": "https://pypi.org/simple/"}

_OBS_SERVER = str(_PROJECT_ROOT / "mcp-servers" / "observability" / "server.py")
_K8S_SERVER = str(_PROJECT_ROOT / "mcp-servers" / "kubernetes" / "server.py")
_ALERT_SERVER = str(_PROJECT_ROOT / "mcp-servers" / "alerting" / "server.py")
_SEC_SERVER = str(_PROJECT_ROOT / "mcp-servers" / "security" / "server.py")

# ---------------------------------------------------------------------------
# MCP Toolsets
# ---------------------------------------------------------------------------

observability_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_UV,
            args=[*_UV_ARGS, _OBS_SERVER],
            env=_UV_ENV,
        )
    ),
    tool_filter=[
        "get_current_metrics",
        "get_logs",
        "get_traces",
        "get_service_topology",
        "trigger_scenario",
    ],
)

kubernetes_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_UV,
            args=[*_UV_ARGS, _K8S_SERVER],
            env=_UV_ENV,
        )
    ),
    tool_filter=[
        "list_pods",
        "describe_pod",
        "get_deployments",
        "scale_deployment",
        "rollback_deployment",
        "get_pod_logs",
    ],
)

alerting_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_UV,
            args=[*_UV_ARGS, _ALERT_SERVER],
            env=_UV_ENV,
        )
    ),
    tool_filter=[
        "get_active_alerts",
        "acknowledge_alert",
        "create_incident",
        "resolve_incident",
        "get_incident_history",
        "export_post_mortem_report",
    ],
)

security_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_UV,
            args=[*_UV_ARGS, _SEC_SERVER],
            env=_UV_ENV,
        )
    ),
    tool_filter=[
        "check_auth_anomalies",
        "scan_access_logs",
        "evaluate_cve_exposure",
        "get_security_posture",
    ],
)

# ---------------------------------------------------------------------------
# Apollo — Senior SRE Agent
# ---------------------------------------------------------------------------

apollo = LlmAgent(
    name="Apollo",
    model=_MODEL,
    description=(
        "Apollo is a Senior SRE AI for NovaMart. "
        "Call Apollo for: incident detection, infrastructure diagnosis, Kubernetes operations "
        "(scaling, rollback), SRE runbook execution, and post-mortem report generation."
    ),
    instruction="""You are Apollo, a Senior SRE AI Agent for NovaMart.

## Your Responsibilities
- Monitor alerts and surface actionable incident summaries
- Diagnose incidents using metrics, logs, and distributed traces
- Execute remediation: scale deployments, roll back bad deploys
- Generate structured post-incident/post-mortem reports

## NovaMart Services
api-gateway | payment-service | order-service | inventory-service
user-service | notification-service | postgres-primary | redis-cache

## Incident Response Workflow
1. DETECT — get_active_alerts(), get_current_metrics(), get_service_topology()
2. DIAGNOSE — get_logs(service, "error", 15), get_traces(service, 15)
3. REMEDIATE — propose action, wait for confirmation, then scale or rollback
4. LEARN — export_post_mortem_report() to persist the report

## Safety Rules
- Never scale below 2 replicas
- Always confirm scale/rollback with the user before executing
- Never fabricate tool results

## Output Style
- Lead with the conclusion, then evidence
- Use severity emojis: 🔴 Critical  🟡 Warning  🟢 Healthy
- Be concise — SREs are busy during incidents
""",
    tools=[observability_tools, kubernetes_tools, alerting_tools],
)

# ---------------------------------------------------------------------------
# Athena — Security Analyst Agent
# ---------------------------------------------------------------------------

athena = LlmAgent(
    name="Athena",
    model=_MODEL,
    description=(
        "Athena is a Security Analyst AI for NovaMart. "
        "Call Athena for: authentication anomaly investigation, suspicious access pattern "
        "analysis, CVE exposure assessment, security posture review, and determining whether "
        "an incident has a security root cause."
    ),
    instruction="""You are Athena, a Security Analyst AI Agent for NovaMart.

## Your Responsibilities
- Detect auth anomalies: credential stuffing, token leakage, impossible travel
- Analyse access log patterns: scrapers, Tor exit nodes, data exfiltration probes
- Assess CVE exposure across service images and recommend patching priority
- Provide an overall security posture score and top risk summary
- Determine if an infrastructure incident has a security root cause

## Investigation Workflow
1. check_auth_anomalies(service) — look for credential or token abuse
2. scan_access_logs(service) — find suspicious traffic patterns
3. evaluate_cve_exposure(service) — check for known exploitable vulnerabilities
4. Correlate with SRE findings for a joint picture

## Output Style
- Lead with: 🔴 Critical Threat  🟠 Active Risk  🟡 Monitored  🟢 Clean
- Distinguish confirmed threats from indicators of compromise (IoC)
- Give actionable remediation: rotate credentials, patch versions, block IPs
""",
    tools=[security_tools],
)

# ---------------------------------------------------------------------------
# Commander — Root Orchestrator (root_agent — required by ADK)
# ---------------------------------------------------------------------------

root_agent = LlmAgent(
    name="Commander",
    model=_MODEL,
    description="NovaMart AIOps Commander — routes to Apollo (SRE) and Athena (Security).",
    instruction="""You are the NovaMart AIOps Commander.
You coordinate Apollo (SRE) and Athena (Security) for comprehensive incident response.

## Your Role
- Infrastructure issues (alerts, latency, CPU, memory, K8s ops) → Apollo
- Security concerns (auth failures, CVEs, suspicious traffic) → Athena
- Joint assessments → delegate to BOTH, then synthesise findings

## Collaboration Pattern
For incidents, run a joint assessment:
1. Ask Apollo: "What is the SRE-view of this incident?"
2. Ask Athena: "Is there a security dimension to this incident?"
3. Synthesise: Present a unified incident summary

## Output Format (joint assessments)
### 🔧 SRE Assessment (Apollo)
[Apollo's findings]

### 🔐 Security Assessment (Athena)
[Athena's findings]

### 📋 Combined Recommendation
[Unified recommendation and next steps]

You orchestrate — you do not directly call tools. Always delegate to sub-agents.
""",
    sub_agents=[apollo, athena],
)
