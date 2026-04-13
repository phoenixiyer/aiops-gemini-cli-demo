# Runbook: Cascading Failure

## Symptoms
- Multiple services reporting elevated error rates simultaneously
- Database or shared dependency showing high latency
- Connection pool exhaustion across multiple services
- Error rate climbing progressively through the service graph

## Diagnostic Steps

1. **Map the blast radius**
   ```
   get_service_topology() — identify which services are degraded and their dependencies
   ```

2. **Find the root dependency**
   ```
   get_current_metrics(<database/shared-service>) — check the bottom of the dependency tree first
   ```

3. **Check the root cause in logs**
   ```
   get_logs(<root-service>, "error", 30) — look for:
     - Lock contention / long-running queries
     - Connection pool exhaustion
     - Disk I/O issues
   ```

4. **Verify upstream impact**
   ```
   get_current_metrics(<upstream-service>) — for each service depending on the root
   get_logs(<upstream-service>, "error", 15)
   ```

5. **Check for retry storms**
   ```
   Look for "retry" patterns in logs — retries amplify cascading failures
   ```

## Remediation

### Immediate (< 5 min)
1. **Kill the root cause**: If it's a long-running query, identify and terminate it
2. **Enable circuit breakers**: If upstream services are retrying into a dead dependency, break the circuit
3. **Shed load**: If the gateway is overwhelmed, enable rate limiting

### Short-term (< 1 hour)
1. Scale the bottleneck service/database
2. Increase connection pool limits on the root dependency
3. Add query timeouts to prevent future long-running queries

### Long-term
1. Implement bulkhead pattern (isolate connection pools per service)
2. Add query cost analysis before allowing analytical queries on prod
3. Set up separate read replicas for analytics workloads
4. Implement backpressure mechanisms

## Escalation Criteria
- More than 3 services affected
- Customer-facing error rate > 10%
- Database is unresponsive (not just slow)
- Revenue impact confirmed
