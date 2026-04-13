# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=2.0.0", "pydantic>=2.0.0"]
# ///
"""Observability MCP Server — Simulated metrics, logs, traces, and topology."""

import json
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP(
    "NovaMart Observability",
    instructions="Provides real-time metrics, logs, traces, and service topology for the NovaMart platform.",
)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ServiceMetrics(BaseModel):
    service: str
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    latency_p95_ms: float = Field(ge=0)
    error_rate_percent: float = Field(ge=0)
    active_connections: int = Field(ge=0)
    requests_per_second: float = Field(ge=0)
    timestamp: str


class LogEntry(BaseModel):
    timestamp: str
    service: str
    severity: str
    message: str
    trace_id: str | None = None


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    service: str
    operation: str
    duration_ms: float
    status: str
    parent_span_id: str | None = None


# ---------------------------------------------------------------------------
# Baseline "healthy" state for each service
# ---------------------------------------------------------------------------

BASELINES: dict[str, dict] = {
    "api-gateway": {
        "cpu": 25.0,
        "memory": 40.0,
        "latency": 45.0,
        "error_rate": 0.05,
        "connections": 120,
        "rps": 850.0,
    },
    "payment-service": {
        "cpu": 35.0,
        "memory": 55.0,
        "latency": 80.0,
        "error_rate": 0.08,
        "connections": 60,
        "rps": 320.0,
    },
    "order-service": {
        "cpu": 30.0,
        "memory": 45.0,
        "latency": 60.0,
        "error_rate": 0.04,
        "connections": 80,
        "rps": 450.0,
    },
    "inventory-service": {
        "cpu": 20.0,
        "memory": 50.0,
        "latency": 35.0,
        "error_rate": 0.02,
        "connections": 40,
        "rps": 200.0,
    },
    "user-service": {
        "cpu": 22.0,
        "memory": 38.0,
        "latency": 30.0,
        "error_rate": 0.03,
        "connections": 90,
        "rps": 600.0,
    },
    "notification-service": {
        "cpu": 15.0,
        "memory": 30.0,
        "latency": 25.0,
        "error_rate": 0.01,
        "connections": 20,
        "rps": 100.0,
    },
    "postgres-primary": {
        "cpu": 40.0,
        "memory": 65.0,
        "latency": 12.0,
        "error_rate": 0.0,
        "connections": 150,
        "rps": 0.0,
    },
    "redis-cache": {
        "cpu": 10.0,
        "memory": 45.0,
        "latency": 2.0,
        "error_rate": 0.0,
        "connections": 200,
        "rps": 0.0,
    },
}

# ---------------------------------------------------------------------------
# Scenario engine — tracks active scenario state
# ---------------------------------------------------------------------------

ACTIVE_SCENARIO: dict = {"name": None, "started_at": None}

SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"


def _load_scenarios() -> dict:
    if SCENARIOS_FILE.exists():
        return json.loads(SCENARIOS_FILE.read_text())
    return {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _jitter(base: float, pct: float = 0.05) -> float:
    """Add small random jitter to a base value."""
    return base * (1 + random.uniform(-pct, pct))


def _scenario_elapsed_minutes() -> float:
    if ACTIVE_SCENARIO["started_at"] is None:
        return 0
    return (time.time() - ACTIVE_SCENARIO["started_at"]) / 60.0


def _get_scenario_overrides(service: str) -> dict | None:
    """Return metric overrides if the active scenario affects this service."""
    if ACTIVE_SCENARIO["name"] is None:
        return None
    scenarios = _load_scenarios()
    scenario = scenarios.get(ACTIVE_SCENARIO["name"])
    if not scenario:
        return None
    affected = scenario.get("affected_services", {})
    if service not in affected:
        return None
    overrides = affected[service]
    elapsed = _scenario_elapsed_minutes()
    # Linear interpolation: metrics worsen over the scenario's duration
    duration = scenario.get("duration_minutes", 10)
    progress = min(elapsed / duration, 1.0)
    result = {}
    for key, target in overrides.get("peak_metrics", {}).items():
        baseline = BASELINES.get(service, {}).get(key, 0)
        result[key] = baseline + (target - baseline) * progress
    return result


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_current_metrics(service: str) -> str:
    """Get real-time performance metrics for a specific service.

    Args:
        service: Service name (e.g. 'payment-service', 'api-gateway', 'postgres-primary')

    Returns:
        JSON with CPU, memory, latency, error rate, connections, and RPS.
    """
    baseline = BASELINES.get(service)
    if not baseline:
        available = ", ".join(sorted(BASELINES.keys()))
        return json.dumps({"error": f"Unknown service '{service}'. Available: {available}"})

    overrides = _get_scenario_overrides(service) or {}

    metrics = ServiceMetrics(
        service=service,
        cpu_percent=round(_jitter(overrides.get("cpu", baseline["cpu"])), 1),
        memory_percent=round(_jitter(overrides.get("memory", baseline["memory"])), 1),
        latency_p95_ms=round(_jitter(overrides.get("latency", baseline["latency"])), 1),
        error_rate_percent=round(
            _jitter(overrides.get("error_rate", baseline["error_rate"]), 0.1), 2
        ),
        active_connections=int(_jitter(overrides.get("connections", baseline["connections"]))),
        requests_per_second=round(_jitter(overrides.get("rps", baseline["rps"])), 1),
        timestamp=_now_iso(),
    )
    return metrics.model_dump_json(indent=2)


@mcp.tool()
def get_logs(service: str, severity: str = "error", minutes: int = 15) -> str:
    """Get recent log entries for a specific service filtered by severity.

    Args:
        service: Service name
        severity: Log level filter — 'info', 'warn', 'error', or 'fatal'
        minutes: How far back to look (default 15)

    Returns:
        JSON array of log entries with timestamps.
    """
    if service not in BASELINES:
        available = ", ".join(sorted(BASELINES.keys()))
        return json.dumps({"error": f"Unknown service '{service}'. Available: {available}"})

    scenarios = _load_scenarios()
    scenario = scenarios.get(ACTIVE_SCENARIO.get("name", ""), {})
    scenario_logs = scenario.get("affected_services", {}).get(service, {}).get("logs", [])

    # Generate contextual logs based on scenario
    logs: list[dict] = []
    now = datetime.now(timezone.utc)

    if scenario_logs:
        for i, msg in enumerate(scenario_logs):
            entry = LogEntry(
                timestamp=(now - timedelta(minutes=minutes - i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                service=service,
                severity=severity,
                message=msg,
                trace_id=f"trace-{random.randint(100000, 999999)}",
            )
            logs.append(entry.model_dump())
    else:
        # Healthy baseline logs
        healthy_messages = {
            "info": [
                f"{service}: Health check passed",
                f"{service}: Request processed successfully",
                f"{service}: Connection pool refreshed",
            ],
            "warn": [
                f"{service}: Response time slightly elevated (p95: 120ms)",
                f"{service}: Connection pool utilization at 70%",
            ],
            "error": [],
            "fatal": [],
        }
        for msg in healthy_messages.get(severity, []):
            entry = LogEntry(
                timestamp=(now - timedelta(minutes=random.randint(1, minutes))).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                service=service,
                severity=severity,
                message=msg,
            )
            logs.append(entry.model_dump())

    return json.dumps(logs, indent=2)


@mcp.tool()
def get_traces(service: str, minutes: int = 15) -> str:
    """Get distributed trace spans for a service to analyze request flow and latency.

    Args:
        service: Service name to trace
        minutes: How far back to look (default 15)

    Returns:
        JSON array of trace spans with timing and status.
    """
    if service not in BASELINES:
        available = ", ".join(sorted(BASELINES.keys()))
        return json.dumps({"error": f"Unknown service '{service}'. Available: {available}"})

    scenarios = _load_scenarios()
    scenario = scenarios.get(ACTIVE_SCENARIO.get("name", ""), {})
    scenario_traces = scenario.get("affected_services", {}).get(service, {}).get("traces", [])

    spans: list[dict] = []

    if scenario_traces:
        for t in scenario_traces:
            span = TraceSpan(
                trace_id=f"trace-{random.randint(100000, 999999)}",
                span_id=f"span-{random.randint(1000, 9999)}",
                service=service,
                operation=t["operation"],
                duration_ms=t["duration_ms"],
                status=t.get("status", "OK"),
                parent_span_id=t.get("parent_span_id"),
            )
            spans.append(span.model_dump())
    else:
        # Healthy baseline traces
        baseline = BASELINES[service]
        operations = ["handleRequest", "processPayload", "dbQuery", "cacheCheck", "respond"]
        for op in operations:
            span = TraceSpan(
                trace_id=f"trace-{random.randint(100000, 999999)}",
                span_id=f"span-{random.randint(1000, 9999)}",
                service=service,
                operation=op,
                duration_ms=round(_jitter(baseline["latency"] * 0.3), 1),
                status="OK",
            )
            spans.append(span.model_dump())

    return json.dumps(spans, indent=2)


@mcp.tool()
def get_service_topology() -> str:
    """Get the service dependency map showing how services connect and their current health.

    Returns:
        JSON object with services, their dependencies, and health status.
    """
    topology = {
        "services": {
            "api-gateway": {
                "depends_on": [
                    "payment-service",
                    "order-service",
                    "user-service",
                    "inventory-service",
                ],
                "health": "healthy",
            },
            "payment-service": {
                "depends_on": ["postgres-primary", "redis-cache", "notification-service"],
                "health": "healthy",
            },
            "order-service": {
                "depends_on": ["postgres-primary", "inventory-service", "payment-service"],
                "health": "healthy",
            },
            "inventory-service": {
                "depends_on": ["postgres-primary", "redis-cache"],
                "health": "healthy",
            },
            "user-service": {
                "depends_on": ["postgres-primary", "redis-cache"],
                "health": "healthy",
            },
            "notification-service": {
                "depends_on": ["redis-cache"],
                "health": "healthy",
            },
            "postgres-primary": {
                "depends_on": [],
                "health": "healthy",
            },
            "redis-cache": {
                "depends_on": [],
                "health": "healthy",
            },
        },
        "timestamp": _now_iso(),
    }

    # Apply scenario-based health degradation
    if ACTIVE_SCENARIO["name"]:
        scenarios = _load_scenarios()
        scenario = scenarios.get(ACTIVE_SCENARIO["name"], {})
        for svc, details in scenario.get("affected_services", {}).items():
            if svc in topology["services"]:
                progress = min(_scenario_elapsed_minutes() / scenario.get("duration_minutes", 10), 1.0)
                if progress > 0.7:
                    topology["services"][svc]["health"] = "critical"
                elif progress > 0.3:
                    topology["services"][svc]["health"] = "degraded"

    return json.dumps(topology, indent=2)


@mcp.tool()
def trigger_scenario(scenario_name: str) -> str:
    """Inject a pre-built incident scenario for demo purposes.

    Available scenarios: cpu_spike, memory_leak, cascading_failure, bad_deployment

    Args:
        scenario_name: Name of the scenario to trigger

    Returns:
        Confirmation message with scenario details.
    """
    scenarios = _load_scenarios()
    if scenario_name not in scenarios:
        available = ", ".join(sorted(scenarios.keys()))
        return json.dumps(
            {"error": f"Unknown scenario '{scenario_name}'. Available: {available}"}
        )

    ACTIVE_SCENARIO["name"] = scenario_name
    ACTIVE_SCENARIO["started_at"] = time.time()

    scenario = scenarios[scenario_name]
    return json.dumps(
        {
            "status": "triggered",
            "scenario": scenario_name,
            "title": scenario["title"],
            "description": scenario["description"],
            "affected_services": list(scenario["affected_services"].keys()),
            "duration_minutes": scenario["duration_minutes"],
            "message": f"🔴 INCIDENT TRIGGERED: {scenario['title']}. Metrics will degrade over {scenario['duration_minutes']} minutes.",
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
