# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=2.0.0", "pydantic>=2.0.0", "markdown-pdf>=1.3.0"]
# ///
"""Alerting & Incident Management MCP Server — Simulated alerting for NovaMart."""

import json
import random
from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

mcp = FastMCP(
    "NovaMart Alerting",
    instructions="Provides alert management and incident tracking for the NovaMart platform. Supports viewing, acknowledging, creating, and resolving incidents.",
)

# ---------------------------------------------------------------------------
# Simulated alert & incident state (in-memory)
# ---------------------------------------------------------------------------

_ALERT_COUNTER = 1000
_INCIDENT_COUNTER = 100


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time_ago(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


_ACTIVE_ALERTS: list[dict] = [
    {
        "id": "ALT-1001",
        "title": "High P95 Latency on payment-service",
        "severity": "critical",
        "service": "payment-service",
        "metric": "latency_p95",
        "threshold": "1000ms",
        "current_value": "5200ms",
        "fired_at": _time_ago(12),
        "acknowledged": False,
        "acknowledged_by": None,
    },
    {
        "id": "ALT-1002",
        "title": "Error Rate Elevated on api-gateway",
        "severity": "warning",
        "service": "api-gateway",
        "metric": "error_rate",
        "threshold": "5%",
        "current_value": "12.3%",
        "fired_at": _time_ago(8),
        "acknowledged": False,
        "acknowledged_by": None,
    },
    {
        "id": "ALT-1003",
        "title": "Memory Usage Critical on order-service",
        "severity": "critical",
        "service": "order-service",
        "metric": "memory_percent",
        "threshold": "85%",
        "current_value": "91%",
        "fired_at": _time_ago(5),
        "acknowledged": False,
        "acknowledged_by": None,
    },
]

_INCIDENTS: list[dict] = [
    {
        "id": "INC-101",
        "title": "Redis Cache Failover",
        "severity": "high",
        "status": "resolved",
        "created_at": _time_ago(1440),  # 24h ago
        "resolved_at": _time_ago(1410),
        "duration_minutes": 30,
        "services_affected": ["redis-cache", "user-service", "payment-service"],
        "root_cause": "Redis primary node failed health check, sentinel triggered failover",
        "resolution": "Automatic failover to replica succeeded. Increased sentinel quorum monitoring.",
        "created_by": "AlertManager",
    },
    {
        "id": "INC-102",
        "title": "Certificate Expiry on api-gateway",
        "severity": "medium",
        "status": "resolved",
        "created_at": _time_ago(4320),  # 3 days ago
        "resolved_at": _time_ago(4290),
        "duration_minutes": 30,
        "services_affected": ["api-gateway"],
        "root_cause": "TLS certificate expired, automated renewal failed due to DNS propagation delay",
        "resolution": "Manual certificate renewal and DNS verification. Added cert-manager alerts for 30-day pre-expiry.",
        "created_by": "SRE-On-Call",
    },
]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_active_alerts() -> str:
    """Get all currently firing alerts with severity, affected service, and timing.

    Returns:
        JSON array of active alerts sorted by severity.
    """
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    sorted_alerts = sorted(_ACTIVE_ALERTS, key=lambda a: severity_order.get(a["severity"], 3))

    summary = {
        "total_alerts": len(sorted_alerts),
        "critical": sum(1 for a in sorted_alerts if a["severity"] == "critical"),
        "warning": sum(1 for a in sorted_alerts if a["severity"] == "warning"),
        "info": sum(1 for a in sorted_alerts if a["severity"] == "info"),
        "alerts": sorted_alerts,
        "timestamp": _now_iso(),
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def acknowledge_alert(alert_id: str) -> str:
    """Acknowledge an active alert to indicate it is being investigated.

    Args:
        alert_id: The alert ID (e.g. 'ALT-1001')

    Returns:
        Confirmation of acknowledgment.
    """
    for alert in _ACTIVE_ALERTS:
        if alert["id"] == alert_id:
            if alert["acknowledged"]:
                return json.dumps({
                    "status": "already_acknowledged",
                    "alert_id": alert_id,
                    "acknowledged_by": alert["acknowledged_by"],
                })
            alert["acknowledged"] = True
            alert["acknowledged_by"] = "Apollo (AI SRE Agent)"
            alert["acknowledged_at"] = _now_iso()
            return json.dumps({
                "status": "acknowledged",
                "alert_id": alert_id,
                "message": f"✅ Alert {alert_id} acknowledged by Apollo.",
                "timestamp": _now_iso(),
            }, indent=2)

    return json.dumps({"error": f"Alert '{alert_id}' not found."})


@mcp.tool()
def create_incident(title: str, severity: str, description: str = "") -> str:
    """Create a new incident record for tracking and post-incident analysis.

    Args:
        title: Incident title
        severity: Severity level — 'low', 'medium', 'high', or 'critical'
        description: Optional detailed description

    Returns:
        The created incident with tracking ID.
    """
    global _INCIDENT_COUNTER
    _INCIDENT_COUNTER += 1
    incident_id = f"INC-{_INCIDENT_COUNTER}"

    incident = {
        "id": incident_id,
        "title": title,
        "severity": severity,
        "description": description,
        "status": "open",
        "created_at": _now_iso(),
        "resolved_at": None,
        "duration_minutes": None,
        "services_affected": [],
        "root_cause": None,
        "resolution": None,
        "timeline": [
            {"time": _now_iso(), "event": f"Incident created: {title}"},
        ],
        "created_by": "Apollo (AI SRE Agent)",
    }
    _INCIDENTS.append(incident)

    return json.dumps({
        "status": "created",
        "incident": incident,
        "message": f"🔴 Incident {incident_id} created: {title}",
    }, indent=2)


@mcp.tool()
def resolve_incident(incident_id: str, resolution_summary: str) -> str:
    """Resolve an open incident and generate a timeline summary.

    Args:
        incident_id: The incident ID (e.g. 'INC-103')
        resolution_summary: Description of how the incident was resolved

    Returns:
        Post-incident summary with timeline, duration, and next steps.
    """
    for incident in _INCIDENTS:
        if incident["id"] == incident_id:
            if incident["status"] == "resolved":
                return json.dumps({
                    "error": f"Incident {incident_id} is already resolved.",
                    "resolved_at": incident["resolved_at"],
                })

            incident["status"] = "resolved"
            incident["resolved_at"] = _now_iso()
            incident["resolution"] = resolution_summary
            incident["timeline"].append(
                {"time": _now_iso(), "event": f"Resolved: {resolution_summary}"}
            )

            # Calculate duration
            created = datetime.fromisoformat(incident["created_at"].replace("Z", "+00:00"))
            resolved = datetime.now(timezone.utc)
            incident["duration_minutes"] = round((resolved - created).total_seconds() / 60, 1)

            report = {
                "status": "resolved",
                "post_incident_report": {
                    "incident_id": incident_id,
                    "title": incident["title"],
                    "severity": incident["severity"],
                    "duration_minutes": incident["duration_minutes"],
                    "timeline": incident["timeline"],
                    "root_cause": incident.get("root_cause", "To be determined in post-mortem"),
                    "resolution": resolution_summary,
                    "impact": f"Services affected during the {incident['duration_minutes']} minute incident window.",
                    "prevention_recommendations": [
                        "Add automated canary analysis before full rollout",
                        "Implement circuit breaker patterns for critical paths",
                        "Add pre-deployment load testing for new code paths",
                        "Review and update relevant runbooks",
                    ],
                },
                "message": f"✅ Incident {incident_id} resolved. Duration: {incident['duration_minutes']} minutes.",
            }
            return json.dumps(report, indent=2)

    return json.dumps({"error": f"Incident '{incident_id}' not found."})


@mcp.tool()
def get_incident_history(hours: int = 72) -> str:
    """Get past incidents for pattern analysis and trend detection.

    Args:
        hours: How far back to look (default 72 hours)

    Returns:
        JSON array of past incidents with resolution details.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for inc in _INCIDENTS:
        created = datetime.fromisoformat(inc["created_at"].replace("Z", "+00:00"))
        if created >= cutoff:
            recent.append(inc)

    return json.dumps({
        "period_hours": hours,
        "total_incidents": len(recent),
        "incidents": recent,
        "summary": {
            "by_severity": {
                "critical": sum(1 for i in recent if i["severity"] == "critical"),
                "high": sum(1 for i in recent if i["severity"] == "high"),
                "medium": sum(1 for i in recent if i["severity"] == "medium"),
                "low": sum(1 for i in recent if i["severity"] == "low"),
            },
            "resolved": sum(1 for i in recent if i["status"] == "resolved"),
            "open": sum(1 for i in recent if i["status"] == "open"),
        },
    }, indent=2)


@mcp.tool()
def export_post_mortem_report(incident_id: str, markdown_content: str) -> str:
    """Export a generated post-mortem report to both Markdown and PDF files on the local disk.

    Args:
        incident_id: The incident ID (e.g. 'INC-103')
        markdown_content: The full formatted markdown content of the report

    Returns:
        Confirmation message with the file paths where the reports were saved.
    """
    import os
    try:
        from markdown_pdf import Section, MarkdownPdf
    except ImportError:
        pass # In case not installed somehow, but uv should handle it

    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. Save the Markdown version
    md_path = os.path.join(reports_dir, f"{incident_id}_post_mortem.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    # 2. Convert and save the PDF version
    pdf_path = os.path.join(reports_dir, f"{incident_id}_post_mortem.pdf")
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(markdown_content))
        pdf.save(pdf_path)
    except Exception as e:
        return json.dumps({
            "error": f"Markdown saved to {md_path}, but PDF generation failed: {e}"
        })
        
    return json.dumps({
        "status": "success",
        "md_file_path": md_path,
        "pdf_file_path": pdf_path,
        "message": f"✅ Post-mortem saved as BOTH Markdown and PDF to {reports_dir}",
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
