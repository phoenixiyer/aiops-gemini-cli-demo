"""NovaMart Topology Dashboard — FastAPI server that bridges the MCP simulation servers."""

import json
import sys
from pathlib import Path

# Make the mcp-servers importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Dynamically import the in-process MCP server modules so we share state
# with whatever scenario was triggered via the gemini CLI in the same process.
# In standalone mode (dashboard only), we fall back to importing them fresh.
# ---------------------------------------------------------------------------


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ROOT = Path(__file__).parent.parent
_obs_mod = _load_module("observability", _ROOT / "mcp-servers" / "observability" / "server.py")
_alert_mod = _load_module("alerting", _ROOT / "mcp-servers" / "alerting" / "server.py")

app = FastAPI(title="NovaMart Topology Dashboard", version="1.0.0")

# ---------------------------------------------------------------------------
# Static files (dashboard UI)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ---------------------------------------------------------------------------
# REST API — topology, metrics, alerts
# ---------------------------------------------------------------------------


@app.get("/api/topology")
async def get_topology():
    """Return service topology with current health status."""
    raw = _obs_mod.get_service_topology()
    return JSONResponse(content=json.loads(raw))


@app.get("/api/metrics/{service}")
async def get_metrics(service: str):
    """Return real-time metrics for a specific service."""
    raw = _obs_mod.get_current_metrics(service)
    return JSONResponse(content=json.loads(raw))


@app.get("/api/metrics")
async def get_all_metrics():
    """Return real-time metrics for all services."""
    services = list(_obs_mod.BASELINES.keys())
    results = {}
    for svc in services:
        raw = _obs_mod.get_current_metrics(svc)
        results[svc] = json.loads(raw)
    return JSONResponse(content=results)


@app.get("/api/alerts")
async def get_alerts():
    """Return currently active alerts."""
    raw = _alert_mod.get_active_alerts()
    return JSONResponse(content=json.loads(raw))


@app.get("/api/scenario")
async def get_scenario():
    """Return the currently active scenario name, if any."""
    return JSONResponse(
        content={
            "active_scenario": _obs_mod.ACTIVE_SCENARIO.get("name"),
            "started_at": _obs_mod.ACTIVE_SCENARIO.get("started_at"),
        }
    )


@app.post("/api/scenario/{scenario_name}")
async def trigger_scenario(scenario_name: str):
    """Trigger a scenario from the dashboard."""
    raw = _obs_mod.trigger_scenario(scenario_name)
    return JSONResponse(content=json.loads(raw))


@app.delete("/api/scenario")
async def clear_scenario():
    """Clear the active scenario and return to baseline."""
    _obs_mod.ACTIVE_SCENARIO["name"] = None
    _obs_mod.ACTIVE_SCENARIO["started_at"] = None
    return JSONResponse(
        content={
            "status": "cleared",
            "message": "✅ Scenario cleared. Services returning to baseline.",
        }
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import threading
    import webbrowser

    import uvicorn

    port = int(os.getenv("DASHBOARD_PORT", "8080"))

    print("\n  🌐  NovaMart Topology Dashboard")
    print("  ─────────────────────────────────")
    print(f"  URL: http://localhost:{port}")
    print("  Press Ctrl+C to stop\n")

    def _open_browser():
        import time

        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

