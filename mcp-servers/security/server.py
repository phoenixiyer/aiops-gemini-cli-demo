# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=2.0.0", "pydantic>=2.0.0"]
# ///
"""Security MCP Server — Simulated auth anomaly and threat intelligence for NovaMart."""

import json
import random
from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

mcp = FastMCP(
    "NovaMart Security",
    instructions=(
        "Provides security intelligence for NovaMart: auth anomaly detection, "
        "access log analysis, CVE exposure assessment, and overall security posture scoring."
    ),
)

# ---------------------------------------------------------------------------
# Simulated data
# ---------------------------------------------------------------------------

_SERVICE_CVE_MAP: dict[str, list[dict]] = {
    "api-gateway": [
        {
            "cve": "CVE-2025-1234",
            "severity": "medium",
            "component": "express@4.18.2",
            "description": "HTTP header injection via crafted User-Agent",
        },
    ],
    "payment-service": [
        {
            "cve": "CVE-2025-5678",
            "severity": "high",
            "component": "stripe-go@v72",
            "description": "Webhook signature bypass under specific race condition",
        },
        {
            "cve": "CVE-2024-9012",
            "severity": "low",
            "component": "golang/net@v0.19.0",
            "description": "Potential HTTP/2 denial of service",
        },
    ],
    "order-service": [],
    "inventory-service": [
        {
            "cve": "CVE-2025-3344",
            "severity": "medium",
            "component": "log4j@2.20.0",
            "description": "RCE risk under non-default JVM configuration",
        },
    ],
    "user-service": [
        {
            "cve": "CVE-2025-7890",
            "severity": "critical",
            "component": "golang/crypto@v0.17.0",
            "description": "TLS session resumption bypass allowing auth token forgery",
        },
    ],
    "notification-service": [],
    "postgres-primary": [
        {
            "cve": "CVE-2024-4321",
            "severity": "high",
            "component": "postgresql@16.1",
            "description": "Privilege escalation via row security bypass",
        },
    ],
    "redis-cache": [],
}

_SERVICE_SECURITY_SCORES: dict[str, int] = {
    "api-gateway": 82,
    "payment-service": 61,
    "order-service": 95,
    "inventory-service": 74,
    "user-service": 48,  # Critical CVE pulls score down
    "notification-service": 97,
    "postgres-primary": 70,
    "redis-cache": 91,
}

_AUTH_ANOMALY_TEMPLATES = {
    "payment-service": [
        "Multiple failed JWT validation attempts from IP 185.220.101.{i} (Tor exit node)",
        "Unusual service account token reuse: sa-payment-processor used from 3 distinct pod IPs",
        "API key rotation overdue: payment-stripe-key-prod has not rotated in 187 days",
    ],
    "user-service": [
        (
            "Credential stuffing pattern detected: "
            "1,240 failed logins in 5 min from subnet 91.108.x.x"
        ),
        (
            "Suspicious session: user_id=48291 authenticated from "
            "New York and Singapore within 4 minutes"
        ),
        "OAuth token leaked: access_token beginning with 'ya29.A0A' detected in error log",
    ],
    "api-gateway": [
        (
            "Rate limit bypass attempt: 3x normal traffic from "
            "IP 23.129.64.{i} using rotating user-agents"
        ),
        "Scanner fingerprint detected: responses consistent with Shodan crawler pattern",
    ],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time_ago(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def check_auth_anomalies(service: str, minutes: int = 30) -> str:
    """Scan for authentication and authorization anomalies on a service.

    Args:
        service: Service name to analyze
        minutes: Lookback window in minutes (default 30)

    Returns:
        JSON list of anomalies found, each with severity and recommended action.
    """
    templates = _AUTH_ANOMALY_TEMPLATES.get(service, [])

    if not templates:
        return json.dumps(
            {
                "service": service,
                "period_minutes": minutes,
                "anomaly_count": 0,
                "anomalies": [],
                "summary": (
                    f"✅ No auth anomalies detected for {service} in the last {minutes} minutes."
                ),
            },
            indent=2,
        )

    anomalies = []
    for msg in templates:
        is_critical = "credential stuffing" in msg or "token leaked" in msg
        anomalies.append(
            {
                "id": f"SEC-A{random.randint(1000, 9999)}",
                "timestamp": _time_ago(random.randint(1, minutes)),
                "service": service,
                "type": "auth_anomaly",
                "severity": "critical" if is_critical else "medium",
                "description": msg.format(i=random.randint(1, 254)),
                "recommended_action": (
                    "Investigate and block offending IPs. Rotate affected credentials immediately."
                ),
            }
        )

    return json.dumps(
        {
            "service": service,
            "period_minutes": minutes,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "summary": (
                f"⚠️ {len(anomalies)} auth anomaly/anomalies detected "
                f"on {service}. Immediate review recommended."
            ),
        },
        indent=2,
    )


@mcp.tool()
def scan_access_logs(service: str, minutes: int = 60) -> str:
    """Scan access logs for suspicious patterns: geolocation anomalies, scrapers, exfiltration.

    Args:
        service: Service name to scan
        minutes: Lookback window in minutes (default 60)

    Returns:
        JSON with traffic anomaly summary and suspicious request patterns.
    """
    normal_rps = {
        "api-gateway": 850,
        "payment-service": 320,
        "order-service": 450,
        "inventory-service": 200,
        "user-service": 600,
        "notification-service": 100,
        "postgres-primary": 0,
        "redis-cache": 0,
    }
    base_rps = normal_rps.get(service, 0)

    suspicious = []
    if base_rps > 0:
        suspicious = [
            {
                "pattern": "Geo-velocity anomaly",
                "description": (
                    f"3 requests to {service} from US/EU/APAC within 90 seconds — impossible travel"
                ),
                "request_count": 3,
                "severity": "medium",
            },
            {
                "pattern": "Unusually high payload size",
                "description": (
                    f"POST requests to {service} averaging 450KB vs normal 2KB "
                    "— potential data exfiltration probe"
                ),
                "request_count": random.randint(5, 40),
                "severity": "high" if service in ("payment-service", "user-service") else "low",
            },
        ]

    top_ips = [
        {
            "ip": f"185.220.101.{random.randint(1, 254)}",
            "requests": random.randint(200, 2000),
            "flag": "Tor exit node",
        },
        {
            "ip": f"91.108.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "requests": random.randint(50, 500),
            "flag": "Known scanner subnet",
        },
    ]

    return json.dumps(
        {
            "service": service,
            "period_minutes": minutes,
            "total_requests_analyzed": base_rps * minutes * 60,
            "suspicious_patterns": suspicious,
            "top_source_ips": top_ips,
            "summary": f"Found {len(suspicious)} suspicious traffic pattern(s) on {service}.",
        },
        indent=2,
    )


@mcp.tool()
def evaluate_cve_exposure(service: str) -> str:
    """Check known CVE exposure for a service based on its current image version.

    Args:
        service: Service name to check

    Returns:
        JSON list of CVEs affecting this service, with severity and remediation advice.
    """
    cves = _SERVICE_CVE_MAP.get(service, [])
    critical = sum(1 for c in cves if c["severity"] == "critical")
    high = sum(1 for c in cves if c["severity"] == "high")

    if critical > 0:
        risk_level = "CRITICAL"
        recommendation = (
            "🔴 IMMEDIATE action required: "
            "patch or mitigate critical CVEs before next deployment window."
        )
    elif high > 0:
        risk_level = "HIGH"
        recommendation = "🟡 Schedule patching in next maintenance window."
    elif cves:
        risk_level = "MEDIUM"
        recommendation = "🟡 Schedule patching in next maintenance window."
    else:
        risk_level = "LOW"
        recommendation = "🟢 No known CVEs. Keep dependencies updated."

    return json.dumps(
        {
            "service": service,
            "cve_count": len(cves),
            "critical": critical,
            "high": high,
            "cves": cves,
            "risk_level": risk_level,
            "recommendation": recommendation,
        },
        indent=2,
    )


@mcp.tool()
def get_security_posture() -> str:
    """Get the overall security posture score and risk summary across all NovaMart services.

    Returns:
        JSON with per-service security scores, overall score, and top risks.
    """
    scores = _SERVICE_SECURITY_SCORES
    overall = round(sum(scores.values()) / len(scores), 1)

    if overall < 60:
        score_band = "POOR"
    elif overall < 75:
        score_band = "FAIR"
    elif overall < 90:
        score_band = "GOOD"
    else:
        score_band = "EXCELLENT"

    top_risks = []
    for svc, cves in _SERVICE_CVE_MAP.items():
        for cve in cves:
            if cve["severity"] in ("critical", "high"):
                top_risks.append(
                    {
                        "service": svc,
                        "cve": cve["cve"],
                        "severity": cve["severity"],
                        "component": cve["component"],
                    }
                )

    top_risks.sort(key=lambda r: 0 if r["severity"] == "critical" else 1)

    critical_cves = sum(
        1 for cves in _SERVICE_CVE_MAP.values() for c in cves if c["severity"] == "critical"
    )

    return json.dumps(
        {
            "overall_security_score": overall,
            "score_band": score_band,
            "service_scores": scores,
            "highest_risk_service": min(scores, key=scores.get),
            "top_risks": top_risks[:5],
            "total_cves": sum(len(v) for v in _SERVICE_CVE_MAP.values()),
            "critical_cves": critical_cves,
            "timestamp": _now_iso(),
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
