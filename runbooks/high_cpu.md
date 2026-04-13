# Runbook: CPU Saturation

## Symptoms
- CPU usage > 85% sustained for 5+ minutes
- P95 latency increasing proportionally to CPU usage
- Thread/goroutine pool exhaustion
- Liveness probe failures

## Diagnostic Steps

1. **Identify the hot service**
   ```
   get_current_metrics(<service>) — check CPU across all services
   ```

2. **Check for code-level causes**
   ```
   get_logs(<service>, "error", 30) — look for regex timeouts, infinite loops, excessive GC
   ```

3. **Trace the slow path**
   ```
   get_traces(<service>, 15) — identify which operation is consuming CPU
   ```

4. **Check recent deployments**
   ```
   get_deployments() — was a new version recently deployed?
   ```

5. **Check pod restarts**
   ```
   list_pods() — are pods restarting due to OOM or liveness failures?
   ```

## Remediation

### Immediate (< 5 min)
1. **Scale horizontally**: `scale_deployment(<service>, <current + 2>)` to distribute load
2. **If caused by bad deploy**: `rollback_deployment(<service>, <previous_revision>)`

### Short-term (< 1 hour)
1. Profile the hot code path (CPU flame graph)
2. Add rate limiting if the spike is traffic-driven
3. Add circuit breaker if the spike is caused by a downstream dependency

### Long-term
1. Set up CPU-based HPA (Horizontal Pod Autoscaler)
2. Add load testing to CI/CD pipeline
3. Review regex patterns for catastrophic backtracking

## Escalation Criteria
- CPU > 95% for 10+ minutes after scaling
- Multiple services affected (cascading)
- Revenue-impacting (payment, checkout path)
