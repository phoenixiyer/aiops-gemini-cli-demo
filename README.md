# AIOps Demo with Gemini CLI

Welcome to the **AIOps Demo with Gemini CLI** repository! This project provides a production-grade demonstration showcasing how AI-powered site reliability engineering (SRE) agents can transform the incident lifecycle from **Detection** and **Diagnosis** to **Remediation** and **Learning**.

Powered entirely by native **Gemini CLI Extensions** (which wrap the open-source **Model Context Protocol (MCP)**), this project acts as a blueprint for building "Apollo", your own AI-Native SRE.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Demo Scenarios](#demo-scenarios)
- [Running a Demo](#running-a-demo)
- [🌐 Live Topology Dashboard](#-live-topology-dashboard)
- [🤖 Multi-Agent ADK System](#-multi-agent-adk-system)
- [Connecting to Real Systems](#connecting-to-real-systems)
- [Project Structure](#project-structure)
- [License](#license)

---

## Overview

Out of the box, this project runs **100% locally** with zero cloud infrastructure required. It uses Python scripts to simulate logs, metrics, Kubernetes environments, and alerting systems. The Gemini CLI connects to these scripts via built-in **Extensions** powered by MCP, creating a sandbox where it can investigate and resolve simulated incidents. 

**What you will see:**
- An AI Agent analyzing simulated latency, memory leaks, and CPU spikes.
- The Agent looking up SRE Runbooks to deduce root causes.
- The Agent actively executing remediation steps (e.g. scaling K8s replicas, rolling back deployments).
- The Agent automatically generating and persisting post-mortem Markdown reports directly to your filesystem.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Gemini CLI                          │
│              (AI Brain — reads GEMINI.md)                │
│                                                         │
│   "Diagnose the payment-service incident"               │
│          │              │              │                 │
│          ▼              ▼              ▼                 │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│   │Observability│ │ Kubernetes │ │  Alerting  │         │
│   │ MCP Server │ │ MCP Server │ │ MCP Server │         │
│   ├────────────┤ ├────────────┤ ├────────────┤         │
│   │• Metrics   │ │• Pods      │ │• Alerts    │         │
│   │• Logs      │ │• Deploys   │ │• Incidents │         │
│   │• Traces    │ │• Scale     │ │• History   │         │
│   │• Topology  │ │• Rollback  │ │• Reports   │         │
│   └────────────┘ └────────────┘ └────────────┘         │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Gemini CLI** installed, configured, and authenticated with your Google account.
- **Python 3.11+**
- **uv** (Python package manager) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Quick Start

```bash
# 1. Clone and enter the project
git clone <your-repository-url>
cd aiops-gemini-cli-demo

# 2. Configure your environment
cp .env.example .env
# Edit .env and add your Gemini API key (get one at https://aistudio.google.com/apikey)

# 3. Install dependencies
chmod +x scripts/setup.sh && ./scripts/setup.sh

# 4. Launch everything with one command
chmod +x scripts/start.sh && ./scripts/start.sh
```

`start.sh` does everything for you:
- 🌐 Starts the **Topology Dashboard** at `http://localhost:8080`
- 🤖 Starts the **Multi-Agent ADK UI** at `http://localhost:8001`
- Opens both browser tabs automatically
- Drops you into the **Gemini CLI** (Apollo SRE agent) in the same terminal
- Cleans up all background services when you press `Ctrl+C`

### 🛑 Stopping Services
If you backgrounded the terminal or ports get stuck, cleanly kill everything and free ports 8080/8001 by running:
```bash
chmod +x scripts/stop.sh && ./scripts/stop.sh
```

## Demo Scenarios

The `Observability` MCP Server is capable of triggering simulated infrastructure incidents so you can see the agent in action.

| # | Scenario | What Happens |
|---|----------|--------------|
| 1 | **CPU Spike** | payment-service CPU climbs 40% → 95% over 10 min |
| 2 | **Memory Leak** | order-service memory grows linearly, OOM in 30 min |
| 3 | **Cascading Failure** | DB latency spike → upstream timeouts → 5xx cascade |
| 4 | **Bad Deployment** | Canary deploy causes error rate jump 0.1% → 12% |

## Running a Demo

Inside the `gemini` CLI session, try pasting these prompts in sequence to complete the flow:

```text
1. "Trigger the cascading_failure scenario"
2. "What alerts are currently firing?"
3. "Diagnose the incident on payment-service"
4. "What does the runbook recommend?"
5. "Scale payment-service to 5 replicas"
6. "Generate a post-incident report and save it to my disk" (This will export a report to the `reports/` folder!)
```

---

## 🌐 Live Topology Dashboard

A real-time web dashboard that renders the NovaMart service dependency graph. Health states animate live as you trigger incidents from the Gemini CLI.

> Launched automatically by `./scripts/start.sh` at **http://localhost:8080**

**Dashboard features:**
- 🔴/🟡/🟢 animated D3 force-directed graph — nodes pulse red during incidents
- Flowing dashed edges when a cascading failure propagates
- Live metric cards (CPU, memory, latency, error rate) per service
- Active alerts sidebar with severity indicators
- One-click scenario injection buttons (no CLI needed)

> **Tip**: Trigger `"cascading_failure"` in Gemini CLI and watch **http://localhost:8080** light up live.

---

## 🤖 Multi-Agent ADK System

A second demo mode using [Google ADK](https://adk.dev) that exposes a web chat UI. Instead of the Gemini CLI, this mode runs **three agents in parallel**:

| Agent | Role | Tools |
|-------|------|-------|
| **Commander** | Root orchestrator — routes tasks, synthesises findings | delegates to sub-agents |
| **Apollo** | Senior SRE — same tools as the CLI demo | Observability · Kubernetes · Alerting |
| **Athena** | Security Analyst — new agent, new tools | Auth anomalies · CVE scanner · Access logs |

> Launched automatically by `./scripts/start.sh` at **http://localhost:8001**

**Try these multi-agent prompts:**

```text
"What alerts are firing? Is there a security dimension to this incident?"
"Run a full joint SRE + security assessment on payment-service"
"Check user-service for CVE exposure and any auth anomalies"
"Generate a post-incident report including the security findings"
```

Athena uses a dedicated `Security MCP Server` (`adk-agent/mcp_servers/security/server.py`) with four tools:
- `check_auth_anomalies` — credential stuffing, token leakage, impossible travel
- `scan_access_logs` — Tor exit nodes, scraper patterns, data exfiltration probes
- `evaluate_cve_exposure` — per-service CVE list with severity and remediation advice
- `get_security_posture` — overall security score across all 8 services

---

## Connecting to Real Systems

While this demo uses Python scripts to simulate metric and log data to make the initial setup bulletproof, it is designed from the ground-up so that you can trivially connect the Gemini CLI directly to your **real** infrastructure (e.g., Datadog, Splunk, Kubernetes, PagerDuty). 

Because Gemini CLI uses **Extensions** (which are fully compatible with the **Model Context Protocol**), connecting to a real system simply involves pointing the CLI extension configuration to a real open-source MCP server implementation, or rewriting the Python tools to call real APIs.

### Option 1: Use an existing open-source MCP Server
You can replace the local mock K8s server with an actual live integration by downloading a community MCP server and updating the `settings.json` file. 
For example, to configure an extension to interact with your real Kubernetes cluster, update `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "kubernetes-real": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-kubernetes"]
    }
  }
}
```
*(This assumes you have your KUBECONFIG locally configured. Next time you start `gemini`, it will automatically expose real Kubernetes commands like `list_pods` or `scale_deployment` toward your live clusters).*

### Option 2: Point the Python tools to real API endpoints
If you want to keep the custom Python servers but use real data (e.g., fetching metrics from Datadog instead of generating random numbers), simply update the Python functions located in `mcp-servers/`.

For example, open `mcp-servers/observability/server.py` and rewrite the `get_current_metrics` tool:

```python
import requests
from fastmcp import FastMCP

mcp = FastMCP("Real Observability")

@mcp.tool()
def get_current_metrics(service: str) -> str:
    """Get real time metrics from Datadog"""
    headers = {"DD-API-KEY": "YOUR_KEY", "DD-APPLICATION-KEY": "YOUR_APP"}
    
    # Query your real Datadog infrastructure
    res = requests.get(f"https://api.datadoghq.com/api/v1/query?query=avg:system.cpu.user{{service:{service}}}", headers=headers)
    
    return res.text
```
No CLI rewrite is required! The moment you save the script and restart `gemini`, it will immediately begin pulling your real infrastructure telemetry to reason over.

## Project Structure

```text
├── .gemini/settings.json            # Gemini CLI Extension config (MCP tool routing)
├── GEMINI.md                        # System prompt: Apollo persona, rules & workflow
├── LICENSE
├── mcp-servers/                     # Simulated tools for the Gemini CLI demo
│   ├── observability/server.py      #   Metrics, logs, traces, topology, scenarios
│   ├── kubernetes/server.py         #   Pods, deployments, scale, rollback
│   └── alerting/server.py           #   Alerts, incidents, post-mortem export
├── dashboard/                       # 🌐 Live topology web dashboard
│   ├── server.py                    #   FastAPI bridge + REST API
│   └── static/index.html           #   D3 dark-mode service graph
├── adk-agent/                       # 🤖 Multi-agent ADK system
│   ├── agent.py                     #   Commander + Apollo + Athena definitions
│   └── mcp_servers/security/        #   Athena's Security MCP server
├── reports/                         # 📄 Exported post-mortem reports
├── runbooks/                        # SRE playbooks (Gemini reads these)
├── scripts/
│   ├── setup.sh                     # Install dependencies
│   ├── dashboard.sh                 # Launch topology dashboard
│   ├── adk.sh                       # Launch multi-agent ADK UI
│   └── demo.sh                      # Demo flow cheat sheet
└── pyproject.toml
```

## Roadmap

- [x] **Live Topology Dashboard**: Real-time D3 service graph with health animation and scenario injection.
- [x] **Multi-Agent ADK**: Apollo (SRE) + Athena (Security) orchestrated by Commander via Google ADK.
- [ ] **SLA Impact Calculator**: Quantify incidents in revenue impact ($) and SLA budget burn.
- [ ] **Proactive Health Check**: Agent sweeps all services and flags pre-incident conditions.
- [ ] **A2A Protocol Integration**: Cross-agent communication via the Agent-to-Agent protocol.

## Author

**ArunKG**  
Staff Customer Engineer, Applied AI @ Google

## License

[MIT License](LICENSE) © 2026 Google LLC
