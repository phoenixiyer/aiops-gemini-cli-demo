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

# 2. Run setup script to install dependencies
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Launch Gemini CLI
gemini
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
├── .gemini/settings.json    # Extension configuration (routes MCP tools to CLI)
├── GEMINI.md                # System prompt: AI persona, rules & workflow
├── LICENSE                  # MIT License
├── mcp-servers/             # Python-based simulated tools (Observability, K8s, Alerts)
├── reports/                 # 📄 Exported post-mortem Markdown reports
├── runbooks/                # SRE playbooks that Gemini reads to diagnose problems
├── scripts/                 # Lifecycle and setup helpers
└── pyproject.toml           # Python project config
```

## Roadmap

- [ ] **A2UI Protocol Integration**: Future updates will implement the Agent-to-UI (A2UI) protocol capability.
- [ ] **Dynamic Dashboards**: The CLI will soon be able to auto-generate and render dynamic visualizations natively based on live production issues.

## Author

**ArunKG**  
Staff Customer Engineer, Applied AI @ Google

## License

[MIT License](LICENSE) © 2026 Google LLC
