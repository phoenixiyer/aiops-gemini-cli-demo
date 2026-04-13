# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=2.0.0", "pydantic>=2.0.0"]
# ///
"""Kubernetes MCP Server — Simulated K8s cluster management for NovaMart."""

import json
import random
import time
from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

mcp = FastMCP(
    "NovaMart Kubernetes",
    instructions="Provides Kubernetes cluster management for the NovaMart platform. Supports pod listing, deployment management, scaling, and rollback.",
)

# ---------------------------------------------------------------------------
# Simulated cluster state (in-memory, persists within a session)
# ---------------------------------------------------------------------------

_DEPLOYMENTS: dict[str, dict] = {
    "api-gateway": {
        "namespace": "production",
        "replicas": 3,
        "available_replicas": 3,
        "image": "novamart/api-gateway:v3.1.2",
        "revision": 12,
        "revision_history": [
            {"revision": 10, "image": "novamart/api-gateway:v3.0.8", "date": "2026-03-28"},
            {"revision": 11, "image": "novamart/api-gateway:v3.1.0", "date": "2026-04-01"},
            {"revision": 12, "image": "novamart/api-gateway:v3.1.2", "date": "2026-04-05"},
        ],
    },
    "payment-service": {
        "namespace": "production",
        "replicas": 2,
        "available_replicas": 2,
        "image": "novamart/payment-service:v2.8.1",
        "revision": 8,
        "revision_history": [
            {"revision": 6, "image": "novamart/payment-service:v2.7.0", "date": "2026-03-20"},
            {"revision": 7, "image": "novamart/payment-service:v2.8.0", "date": "2026-03-30"},
            {"revision": 8, "image": "novamart/payment-service:v2.8.1", "date": "2026-04-06"},
        ],
    },
    "order-service": {
        "namespace": "production",
        "replicas": 3,
        "available_replicas": 3,
        "image": "novamart/order-service:v4.2.0",
        "revision": 15,
        "revision_history": [
            {"revision": 13, "image": "novamart/order-service:v4.0.3", "date": "2026-03-25"},
            {"revision": 14, "image": "novamart/order-service:v4.1.0", "date": "2026-04-01"},
            {"revision": 15, "image": "novamart/order-service:v4.2.0", "date": "2026-04-04"},
        ],
    },
    "inventory-service": {
        "namespace": "production",
        "replicas": 2,
        "available_replicas": 2,
        "image": "novamart/inventory-service:v2.4.0",
        "revision": 9,
        "revision_history": [
            {"revision": 7, "image": "novamart/inventory-service:v2.2.0", "date": "2026-03-18"},
            {"revision": 8, "image": "novamart/inventory-service:v2.3.1", "date": "2026-03-29"},
            {"revision": 9, "image": "novamart/inventory-service:v2.4.0", "date": "2026-04-06"},
        ],
    },
    "user-service": {
        "namespace": "production",
        "replicas": 3,
        "available_replicas": 3,
        "image": "novamart/user-service:v1.9.4",
        "revision": 6,
        "revision_history": [
            {"revision": 4, "image": "novamart/user-service:v1.8.0", "date": "2026-03-10"},
            {"revision": 5, "image": "novamart/user-service:v1.9.0", "date": "2026-03-22"},
            {"revision": 6, "image": "novamart/user-service:v1.9.4", "date": "2026-04-03"},
        ],
    },
    "notification-service": {
        "namespace": "production",
        "replicas": 2,
        "available_replicas": 2,
        "image": "novamart/notification-service:v1.3.0",
        "revision": 4,
        "revision_history": [
            {"revision": 2, "image": "novamart/notification-service:v1.1.0", "date": "2026-03-05"},
            {"revision": 3, "image": "novamart/notification-service:v1.2.0", "date": "2026-03-20"},
            {"revision": 4, "image": "novamart/notification-service:v1.3.0", "date": "2026-04-02"},
        ],
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_pod_name(deployment: str, index: int) -> str:
    suffix = f"{random.randint(1000, 9999)}"
    return f"{deployment}-{suffix}-pod{index}"


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_pods(namespace: str = "production") -> str:
    """List all pods in a Kubernetes namespace with their status, restarts, and age.

    Args:
        namespace: Kubernetes namespace (default 'production')

    Returns:
        JSON array of pod details.
    """
    pods = []
    now = datetime.now(timezone.utc)

    for deploy_name, deploy in _DEPLOYMENTS.items():
        if deploy["namespace"] != namespace:
            continue
        for i in range(deploy["replicas"]):
            age_hours = random.randint(2, 720)
            restarts = random.choice([0, 0, 0, 0, 1, 2])
            pod = {
                "name": _generate_pod_name(deploy_name, i + 1),
                "deployment": deploy_name,
                "namespace": namespace,
                "status": "Running",
                "ready": "1/1",
                "restarts": restarts,
                "age": f"{age_hours}h",
                "node": f"gke-novamart-pool-{random.choice(['a', 'b', 'c'])}-{random.randint(1, 5)}",
                "ip": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(2, 254)}",
                "image": deploy["image"],
            }
            pods.append(pod)

    return json.dumps({"namespace": namespace, "pods": pods, "total": len(pods)}, indent=2)


@mcp.tool()
def describe_pod(pod_name: str) -> str:
    """Get detailed information about a specific pod including events and resource usage.

    Args:
        pod_name: The pod name (e.g. 'payment-service-4821-pod1')

    Returns:
        JSON object with pod details, conditions, resource usage, and recent events.
    """
    # Extract deployment name from pod name
    parts = pod_name.rsplit("-", 2)
    deploy_name = parts[0] if len(parts) >= 3 else pod_name

    deploy = _DEPLOYMENTS.get(deploy_name)
    if not deploy:
        return json.dumps({"error": f"Pod '{pod_name}' not found. Check pod name with list_pods()."})

    now = datetime.now(timezone.utc)
    pod_detail = {
        "name": pod_name,
        "namespace": deploy["namespace"],
        "deployment": deploy_name,
        "image": deploy["image"],
        "status": "Running",
        "conditions": [
            {"type": "Ready", "status": "True", "since": (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")},
            {"type": "ContainersReady", "status": "True", "since": (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")},
            {"type": "PodScheduled", "status": "True", "since": (now - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        ],
        "resources": {
            "requests": {"cpu": "250m", "memory": "512Mi"},
            "limits": {"cpu": "1000m", "memory": "2Gi"},
            "current_usage": {
                "cpu": f"{random.randint(100, 800)}m",
                "memory": f"{random.randint(256, 1800)}Mi",
            },
        },
        "events": [
            {
                "type": "Normal",
                "reason": "Pulled",
                "message": f"Successfully pulled image '{deploy['image']}'",
                "age": "5h",
            },
            {
                "type": "Normal",
                "reason": "Started",
                "message": "Started container main",
                "age": "5h",
            },
        ],
    }
    return json.dumps(pod_detail, indent=2)


@mcp.tool()
def get_deployments(namespace: str = "production") -> str:
    """List all deployments with replica counts, images, and revision history.

    Args:
        namespace: Kubernetes namespace (default 'production')

    Returns:
        JSON array of deployment details including rollback targets.
    """
    deployments = []
    for name, deploy in _DEPLOYMENTS.items():
        if deploy["namespace"] != namespace:
            continue
        deployments.append({
            "name": name,
            "namespace": namespace,
            "replicas": f"{deploy['available_replicas']}/{deploy['replicas']}",
            "image": deploy["image"],
            "current_revision": deploy["revision"],
            "revision_history": deploy["revision_history"],
            "strategy": "RollingUpdate",
            "max_surge": "25%",
            "max_unavailable": "25%",
        })

    return json.dumps({"namespace": namespace, "deployments": deployments}, indent=2)


@mcp.tool()
def scale_deployment(deployment_name: str, replicas: int) -> str:
    """Scale a deployment to the specified number of replicas.

    ⚠️ Safety: Minimum 2 replicas enforced for high availability.

    Args:
        deployment_name: Name of the deployment to scale
        replicas: Target replica count (minimum 2)

    Returns:
        Confirmation of scaling action with before/after state.
    """
    deploy = _DEPLOYMENTS.get(deployment_name)
    if not deploy:
        available = ", ".join(sorted(_DEPLOYMENTS.keys()))
        return json.dumps({"error": f"Deployment '{deployment_name}' not found. Available: {available}"})

    if replicas < 2:
        return json.dumps({
            "error": "SAFETY VIOLATION: Cannot scale below 2 replicas. High availability requires minimum 2 replicas.",
            "requested": replicas,
            "minimum_allowed": 2,
        })

    if replicas > 20:
        return json.dumps({
            "error": "SAFETY VIOLATION: Cannot scale above 20 replicas without SRE lead approval.",
            "requested": replicas,
            "maximum_allowed": 20,
        })

    old_replicas = deploy["replicas"]
    deploy["replicas"] = replicas
    deploy["available_replicas"] = replicas

    return json.dumps({
        "status": "success",
        "deployment": deployment_name,
        "action": "scale",
        "previous_replicas": old_replicas,
        "new_replicas": replicas,
        "message": f"✅ Deployment '{deployment_name}' scaled from {old_replicas} to {replicas} replicas.",
        "timestamp": _now_iso(),
        "note": "New pods will be ready within 30-60 seconds.",
    }, indent=2)


@mcp.tool()
def rollback_deployment(deployment_name: str, target_revision: int) -> str:
    """Rollback a deployment to a specific previous revision.

    Args:
        deployment_name: Name of the deployment to rollback
        target_revision: The revision number to rollback to

    Returns:
        Confirmation of rollback with old and new image versions.
    """
    deploy = _DEPLOYMENTS.get(deployment_name)
    if not deploy:
        available = ", ".join(sorted(_DEPLOYMENTS.keys()))
        return json.dumps({"error": f"Deployment '{deployment_name}' not found. Available: {available}"})

    target_entry = None
    for rev in deploy["revision_history"]:
        if rev["revision"] == target_revision:
            target_entry = rev
            break

    if not target_entry:
        available_revisions = [r["revision"] for r in deploy["revision_history"]]
        return json.dumps({
            "error": f"Revision {target_revision} not found for '{deployment_name}'.",
            "available_revisions": available_revisions,
        })

    if target_revision == deploy["revision"]:
        return json.dumps({
            "error": f"Revision {target_revision} is already the current revision.",
            "current_revision": deploy["revision"],
        })

    old_image = deploy["image"]
    old_revision = deploy["revision"]
    deploy["image"] = target_entry["image"]
    deploy["revision"] = deploy["revision"] + 1  # New revision for rollback

    return json.dumps({
        "status": "success",
        "deployment": deployment_name,
        "action": "rollback",
        "previous_image": old_image,
        "previous_revision": old_revision,
        "new_image": target_entry["image"],
        "rollback_to_revision": target_revision,
        "new_revision": deploy["revision"],
        "message": f"✅ Deployment '{deployment_name}' rolled back from {old_image} to {target_entry['image']}.",
        "timestamp": _now_iso(),
        "note": "Rolling update in progress. ETA: 60-90 seconds.",
    }, indent=2)


@mcp.tool()
def get_pod_logs(pod_name: str, lines: int = 50) -> str:
    """Get container stdout/stderr logs from a specific pod.

    Args:
        pod_name: The pod name
        lines: Number of recent log lines to retrieve (default 50)

    Returns:
        Array of log lines from the pod.
    """
    parts = pod_name.rsplit("-", 2)
    deploy_name = parts[0] if len(parts) >= 3 else pod_name

    if deploy_name not in _DEPLOYMENTS:
        return json.dumps({"error": f"Pod '{pod_name}' not found."})

    now = datetime.now(timezone.utc)
    log_lines = []
    for i in range(min(lines, 20)):
        ts = (now - timedelta(seconds=i * 30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        level = random.choice(["INFO", "INFO", "INFO", "DEBUG", "WARN"])
        messages = [
            f"Request processed in {random.randint(10, 200)}ms",
            f"Health check: OK (uptime: {random.randint(1, 720)}h)",
            f"Connection pool: {random.randint(5, 50)}/{random.randint(50, 100)} active",
            f"Cache hit ratio: {random.uniform(85, 99):.1f}%",
            f"Goroutines: {random.randint(20, 150)} active",
        ]
        log_lines.append(f"{ts} [{level}] {random.choice(messages)}")

    return json.dumps({"pod": pod_name, "lines": log_lines}, indent=2)


if __name__ == "__main__":
    mcp.run()
