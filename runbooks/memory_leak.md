# Runbook: Memory Leak

## Symptoms
- Memory usage growing linearly over time (not plateauing)
- Frequent full GC cycles with increasing pause times
- Pod OOMKilled events (exit code 137)
- Gradual latency increase as GC pressure grows

## Diagnostic Steps

1. **Confirm the leak pattern**
   ```
   get_current_metrics(<service>) — check if memory is above baseline and trending up
   ```

2. **Check for known leak patterns in logs**
   ```
   get_logs(<service>, "error", 30) — look for:
     - "cursor leak" / "connection leak"
     - "OOM" / "OutOfMemoryError"
     - GC warnings with increasing pause times
   ```

3. **Identify the leaking operation**
   ```
   get_traces(<service>, 15) — look for operations that succeed but never close resources
   ```

4. **Check pod history**
   ```
   list_pods() — look for pods with high restart counts (OOMKilled pattern)
   ```

## Remediation

### Immediate (< 5 min)
1. **Restart affected pods**: This is a temporary fix — the leak will recur
2. **Scale horizontally**: `scale_deployment(<service>, <current + 2>)` to buy time

### Short-term (< 1 hour)
1. Identify unclosed resources (database cursors, file handles, HTTP connections)
2. Deploy hotfix closing the resource leak
3. If hotfix is not ready, set up a periodic pod restart (cron-based rolling restart)

### Long-term
1. Add resource cleanup in `finally` blocks / context managers
2. Set memory limits with proper OOM handling
3. Add memory leak detection to CI (e.g., tracemalloc, pprof)
4. Implement connection pool monitoring dashboards

## Escalation Criteria
- Memory above 90% and climbing
- Multiple pods OOMKilled within 30 minutes
- Service is on the critical payment/checkout path
