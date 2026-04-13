# Runbook: Deployment Rollback

## Symptoms
- Error rate spike immediately following a deployment
- New error types appearing in logs that match the deployed code changes
- Canary metrics diverging from baseline (latency, error rate)
- Customer complaints correlating with deploy timestamp

## Diagnostic Steps

1. **Confirm the correlation with deployment**
   ```
   get_deployments() — check if there was a recent deployment (revision change)
   get_current_metrics(<service>) — compare current metrics to pre-deploy baseline
   ```

2. **Identify the breaking change**
   ```
   get_logs(<service>, "error", 15) — look for new error types not seen before the deploy
   get_traces(<service>, 15) — trace failures to specific operations
   ```

3. **Check downstream impact**
   ```
   get_logs(<downstream-service>, "error", 15) — look for errors caused by the changed API
   ```

4. **Verify the rollback target**
   ```
   get_deployments() — confirm the previous revision exists and was stable
   ```

## Remediation

### Immediate (< 5 min)
1. **Rollback**: `rollback_deployment(<service>, <previous_revision>)`
   - Always verify the target revision was previously stable
   - Monitor metrics after rollback for 5 minutes to confirm recovery

### Short-term (< 1 hour)
1. Analyze the breaking change (API schema mismatch, missing migration, etc.)
2. Fix the code and re-deploy with proper testing
3. Update canary analysis rules to catch similar issues

### Long-term
1. Add contract testing between services (prevent schema mismatches)
2. Implement automated canary analysis with automatic rollback
3. Add pre-deployment integration tests
4. Require API versioning for breaking changes

## Escalation Criteria
- Rollback fails or target revision is also broken
- Multiple services need coordinated rollback
- Data corruption suspected from the bad deploy
