# Story 5.4: Create Multi-Cluster Operational Validation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want validation tasks for multi-cluster operations,
so that I can verify cross-cluster functionality works correctly and confirm disaster recovery procedures are reliable.

## Acceptance Criteria

1. **AC1**: DR Taskfile contains backup verification tasks:
   - `.taskfiles/dr/Taskfile.yaml` exists with properly structured tasks
   - `dr:verify-backups` task checks R2 backup accessibility for both clusters
   - Task accepts CLUSTER variable (infra/apps) for cluster-specific verification
   - Task validates both VolSync and CNPG Barman backup accessibility

2. **AC2**: CNPG restore test task is functional:
   - `dr:test-cnpg-restore` task exists and performs point-in-time recovery to test namespace
   - Restore creates temporary cluster in `test-restore` namespace
   - Data integrity is verified after restore
   - Cleanup of test resources occurs after verification
   - RTO measurement captured (target: <30 min)

3. **AC3**: Smoke test scripts exist for automated DR testing:
   - `tests/smoke/dr-cnpg-restore.sh` automates CNPG restore verification
   - `tests/smoke/dr-volsync-restore.sh` automates VolSync restore verification
   - Scripts are executable and return proper exit codes
   - Scripts output clear success/failure messages with timing information

4. **AC4**: VolSync restore test task is functional:
   - Task restores a PVC from latest or specified snapshot
   - Verification that application starts with restored data
   - Task cleans up test resources after verification
   - Task works for any app with VolSync backup configured

5. **AC5**: Secret rotation validation is testable:
   - Secret rotation test procedure documented
   - Update 1Password → verify pod picks up new value within 10 minutes
   - External Secrets refresh interval verified
   - End-to-end rotation test can be performed manually

6. **AC6**: Multi-cluster connectivity validation exists:
   - Verification that apps cluster VMAgent successfully remote-writes to infra VictoriaMetrics
   - Verification that apps cluster Fluent-bit successfully ships logs to infra VictoriaLogs
   - Cross-cluster SSO (Authentik) connectivity can be validated
   - Network path validation between clusters documented

7. **AC7**: All validation tasks are cluster-aware:
   - Tasks accept CLUSTER variable (infra/apps)
   - Tasks use correct kubeconfig context for target cluster
   - Tasks report which cluster they're operating on
   - Multi-cluster operations can run against both clusters sequentially

## Tasks / Subtasks

- [ ] Task 1: Create DR Taskfile structure (AC: #1, #7)
  - [ ] Subtask 1.1: Create `.taskfiles/dr/Taskfile.yaml` with proper structure
  - [ ] Subtask 1.2: Implement `dr:verify-backups` task for R2 accessibility check
  - [ ] Subtask 1.3: Add cluster-awareness with CLUSTER variable support
  - [ ] Subtask 1.4: Implement VolSync backup status verification
  - [ ] Subtask 1.5: Implement CNPG Barman backup status verification
  - [ ] Subtask 1.6: Add output formatting for clear status reporting

- [ ] Task 2: Create CNPG restore test task (AC: #2, #3)
  - [ ] Subtask 2.1: Implement `dr:test-cnpg-restore` task using kubectl cnpg plugin
  - [ ] Subtask 2.2: Create test namespace provisioning logic
  - [ ] Subtask 2.3: Implement restore from latest backup to test namespace
  - [ ] Subtask 2.4: Add data integrity verification queries
  - [ ] Subtask 2.5: Implement cleanup of test resources
  - [ ] Subtask 2.6: Add timing measurement for RTO validation
  - [ ] Subtask 2.7: Create `tests/smoke/dr-cnpg-restore.sh` script

- [ ] Task 3: Create VolSync restore test task (AC: #4, #3)
  - [ ] Subtask 3.1: Implement `dr:test-volsync-restore` task
  - [ ] Subtask 3.2: Create ReplicationDestination for restore testing
  - [ ] Subtask 3.3: Implement snapshot selection (latest or specified)
  - [ ] Subtask 3.4: Add verification that restored PVC is accessible
  - [ ] Subtask 3.5: Implement cleanup of test resources
  - [ ] Subtask 3.6: Create `tests/smoke/dr-volsync-restore.sh` script

- [ ] Task 4: Create secret rotation validation (AC: #5)
  - [ ] Subtask 4.1: Document secret rotation test procedure
  - [ ] Subtask 4.2: Create `dr:test-secret-rotation` task
  - [ ] Subtask 4.3: Implement 1Password update detection
  - [ ] Subtask 4.4: Add pod secret value verification
  - [ ] Subtask 4.5: Verify External Secrets refresh interval compliance

- [ ] Task 5: Create cross-cluster connectivity validation (AC: #6)
  - [ ] Subtask 5.1: Implement VMAgent remote-write verification
  - [ ] Subtask 5.2: Implement Fluent-bit log shipping verification
  - [ ] Subtask 5.3: Implement Authentik SSO connectivity check
  - [ ] Subtask 5.4: Document network path validation procedures

- [ ] Task 6: Integration and testing (AC: #1-7)
  - [ ] Subtask 6.1: Verify all tasks work on both clusters
  - [ ] Subtask 6.2: Run full DR validation suite
  - [ ] Subtask 6.3: Document task usage in runbooks
  - [ ] Subtask 6.4: Verify smoke tests are executable and return proper codes

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Create comprehensive operational validation tooling that enables the platform operator to verify:
1. Disaster recovery readiness (backups are accessible and restorable)
2. Cross-cluster integrations work correctly (observability, SSO)
3. Secret management is functioning (External Secrets + 1Password)

**Multi-Cluster Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION TASKS                                │
│  .taskfiles/dr/Taskfile.yaml                                            │
│  tests/smoke/*.sh                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    INFRA CLUSTER (cluster.id=1)                     │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │ │
│  │  │ VictoriaMetrics │  │  VictoriaLogs   │  │    Authentik      │  │ │
│  │  │   (Hub)         │←─│    (Hub)        │  │    (SSO)          │  │ │
│  │  │                 │  │                 │  │                   │  │ │
│  │  └────────▲────────┘  └────────▲────────┘  └────────▲──────────┘  │ │
│  │           │                    │                    │             │ │
│  │  ┌────────┴────────────────────┴────────────────────┴───────────┐ │ │
│  │  │               CNPG Cluster + VolSync Backups                 │ │ │
│  │  │               → Cloudflare R2 (eca0833...r2.cloudflarestorage)│ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                          ↑ remote-write                                  │
│                          │ SSO via HTTPS                                 │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    APPS CLUSTER (cluster.id=2)                      │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │ │
│  │  │    VMAgent      │  │   Fluent-bit    │  │  Business Apps    │  │ │
│  │  │  (Spoke)        │──│    (Spoke)      │  │ (Odoo, n8n, etc.) │  │ │
│  │  │                 │  │                 │  │                   │  │ │
│  │  └─────────────────┘  └─────────────────┘  └───────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │               CNPG Cluster + VolSync Backups                 │ │ │
│  │  │               → Cloudflare R2 (same endpoint)                 │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Previous Story Context (Story 5.3)

**Completed Work:**
- Business applications (Odoo, n8n, ArsipQ) deployed to apps cluster
- CNPG shared cluster pattern implemented with `${APP}-pguser-secret` naming
- VolSync backups configured for stateful applications
- CiliumNetworkPolicy Tier 2 isolation configured
- Cross-cluster SSO via Authentik established

**Relevant Patterns from Story 5.3:**
- Database host: `postgres-rw.databases.svc.cluster.local`
- VolSync schedule: every 8 hours, retention 24 hourly + 7 daily
- Authentik endpoint: `authentik.monosense.dev`
- Apps cluster domain: `*.monosense.io`

### Taskfile Structure

**DR Taskfile Location:** `.taskfiles/dr/Taskfile.yaml`

```yaml
# .taskfiles/dr/Taskfile.yaml
version: "3"

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  KUBECONFIG_CONTEXT: '{{.CLUSTER}}'

tasks:
  verify-backups:
    desc: Verify backup accessibility for cluster
    vars:
      CLUSTER: '{{.CLUSTER | default "infra"}}'
    cmds:
      - echo "Verifying backups for cluster {{.CLUSTER}}..."
      - task: verify-volsync
        vars: { CLUSTER: "{{.CLUSTER}}" }
      - task: verify-cnpg
        vars: { CLUSTER: "{{.CLUSTER}}" }

  verify-volsync:
    desc: Verify VolSync ReplicationSource status
    vars:
      CLUSTER: '{{.CLUSTER | default "infra"}}'
    cmds:
      - |
        echo "📦 VolSync Backup Status ({{.CLUSTER}}):"
        kubectl --context {{.CLUSTER}} get replicationsource -A \
          -o custom-columns=\
          "NAMESPACE:.metadata.namespace,\
          NAME:.metadata.name,\
          LAST_SYNC:.status.lastSyncTime,\
          NEXT_SYNC:.status.nextSyncTime"

  verify-cnpg:
    desc: Verify CNPG Barman backup status
    vars:
      CLUSTER: '{{.CLUSTER | default "infra"}}'
    cmds:
      - |
        echo "🐘 CNPG Backup Status ({{.CLUSTER}}):"
        kubectl --context {{.CLUSTER}} cnpg status postgres -n databases \
          --timeout 30s 2>/dev/null || \
        kubectl --context {{.CLUSTER}} get cluster postgres -n databases \
          -o jsonpath='{.status.firstRecoverabilityPoint}{"\n"}'

  test-cnpg-restore:
    desc: Test CNPG point-in-time recovery to test namespace
    vars:
      CLUSTER: '{{.CLUSTER | default "infra"}}'
      TIMESTAMP: '{{now | date "2006-01-02T15:04:05Z"}}'
    cmds:
      - echo "🔄 Starting CNPG restore test for cluster {{.CLUSTER}}..."
      - kubectl --context {{.CLUSTER}} create namespace test-restore --dry-run=client -o yaml | kubectl --context {{.CLUSTER}} apply -f -
      - task: _cnpg-restore-cluster
        vars: { CLUSTER: "{{.CLUSTER}}" }
      - task: _cnpg-verify-restore
        vars: { CLUSTER: "{{.CLUSTER}}" }
      - task: _cnpg-cleanup-restore
        vars: { CLUSTER: "{{.CLUSTER}}" }

  test-volsync-restore:
    desc: Test VolSync restore for an application
    vars:
      CLUSTER: '{{.CLUSTER | default "apps"}}'
      APP: '{{.APP | default ""}}'
    preconditions:
      - sh: '[ -n "{{.APP}}" ]'
        msg: "APP variable is required. Usage: task dr:test-volsync-restore CLUSTER=apps APP=odoo"
    cmds:
      - echo "🔄 Starting VolSync restore test for {{.APP}} on cluster {{.CLUSTER}}..."
      - task: _volsync-restore
        vars: { CLUSTER: "{{.CLUSTER}}", APP: "{{.APP}}" }
      - task: _volsync-verify
        vars: { CLUSTER: "{{.CLUSTER}}", APP: "{{.APP}}" }
      - task: _volsync-cleanup
        vars: { CLUSTER: "{{.CLUSTER}}", APP: "{{.APP}}" }

  test-secret-rotation:
    desc: Test External Secrets refresh and pod secret propagation
    vars:
      CLUSTER: '{{.CLUSTER | default "infra"}}'
      SECRET: '{{.SECRET | default ""}}'
      NAMESPACE: '{{.NAMESPACE | default "default"}}'
    cmds:
      - echo "🔐 Testing secret rotation for {{.SECRET}} in {{.NAMESPACE}}..."
      - |
        # Get current secret value hash
        BEFORE=$(kubectl --context {{.CLUSTER}} get secret {{.SECRET}} -n {{.NAMESPACE}} -o jsonpath='{.data}' | md5sum)
        echo "Before hash: $BEFORE"

        # Trigger External Secrets refresh
        kubectl --context {{.CLUSTER}} annotate externalsecret {{.SECRET}} -n {{.NAMESPACE}} \
          force-sync=$(date +%s) --overwrite

        # Wait and check
        echo "Waiting for refresh (up to 5 minutes)..."
        for i in {1..30}; do
          sleep 10
          AFTER=$(kubectl --context {{.CLUSTER}} get secret {{.SECRET}} -n {{.NAMESPACE}} -o jsonpath='{.data}' | md5sum)
          if [ "$BEFORE" != "$AFTER" ]; then
            echo "✅ Secret updated after $((i*10)) seconds"
            exit 0
          fi
        done
        echo "⚠️ Secret not updated within 5 minutes - check 1Password and ESO logs"

  verify-cross-cluster:
    desc: Verify cross-cluster connectivity (observability, SSO)
    cmds:
      - task: _verify-vmagent
      - task: _verify-fluentbit
      - task: _verify-authentik

  _verify-vmagent:
    internal: true
    cmds:
      - |
        echo "📊 Verifying VMAgent remote-write (apps → infra)..."
        kubectl --context apps logs -n observability deploy/vmagent --tail=10 2>/dev/null | \
          grep -q "successfully sent" && echo "✅ VMAgent remote-write working" || \
          echo "⚠️ Check VMAgent logs for remote-write status"

  _verify-fluentbit:
    internal: true
    cmds:
      - |
        echo "📋 Verifying Fluent-bit log shipping (apps → infra)..."
        kubectl --context apps logs -n observability ds/fluent-bit --tail=10 2>/dev/null | \
          grep -qE "(output:|flushed)" && echo "✅ Fluent-bit shipping logs" || \
          echo "⚠️ Check Fluent-bit logs for shipping status"

  _verify-authentik:
    internal: true
    cmds:
      - |
        echo "🔑 Verifying Authentik SSO connectivity..."
        curl -sf -o /dev/null -w "%{http_code}" \
          https://authentik.monosense.dev/-/health/ready/ && \
          echo " ✅ Authentik healthy" || echo " ⚠️ Authentik not reachable"
```

### CNPG Restore Test Details

**Using kubectl cnpg plugin:**
The `kubectl cnpg` plugin provides specialized commands for managing CloudNativePG clusters. Key commands for restore testing:

```bash
# Check cluster status with extended timeout for large clusters
kubectl cnpg status postgres -n databases --timeout 45s

# View backup information
kubectl cnpg backup list postgres -n databases

# Create on-demand backup before testing
kubectl cnpg backup postgres -n databases

# For restore testing, create a recovery cluster
```

**Recovery Cluster Manifest:**
```yaml
# test-restore-cluster.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-restore-test
  namespace: test-restore
spec:
  instances: 1

  # Use same storage as production but smaller
  storage:
    size: 10Gi
    storageClass: openebs-hostpath

  # Bootstrap from backup
  bootstrap:
    recovery:
      source: postgres-backup

  # Reference the backup cluster
  externalClusters:
    - name: postgres-backup
      barmanObjectStore:
        destinationPath: s3://cnpg-${CLUSTER}/
        endpointURL: https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com
        s3Credentials:
          accessKeyId:
            name: cnpg-r2-secret
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: cnpg-r2-secret
            key: SECRET_ACCESS_KEY
```

**RTO Measurement:**
- Target: <30 minutes for CNPG point-in-time recovery
- Timing starts when restore command issued
- Timing ends when cluster reports Ready and data verification passes

### VolSync Restore Test Details

**ReplicationDestination for Restore:**
```yaml
# test-restore-destination.yaml
apiVersion: volsync.backube/v1alpha1
kind: ReplicationDestination
metadata:
  name: ${APP}-restore-test
  namespace: test-restore
spec:
  trigger:
    manual: restore-test-$(date +%s)
  restic:
    repository: ${APP}-restic-secret
    destinationPVC: ${APP}-test-restore
    copyMethod: Snapshot
    storageClassName: ceph-block
    accessModes:
      - ReadWriteOnce
    capacity: 10Gi  # Adjust based on app
    # Optional: restore from specific point in time
    # restoreAsOf: "2025-12-30T00:00:00Z"
```

**VolSync Restore Verification:**
```bash
# Check restore status
kubectl get replicationdestination ${APP}-restore-test -n test-restore \
  -o jsonpath='{.status.lastManualSync}'

# Verify PVC is bound
kubectl get pvc ${APP}-test-restore -n test-restore

# List available snapshots
restic -r s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/${BUCKET}/${APP} snapshots
```

### Smoke Test Scripts

**tests/smoke/dr-cnpg-restore.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail

CLUSTER="${1:-infra}"
TIMEOUT="${2:-1800}"  # 30 minutes default
START_TIME=$(date +%s)

echo "=== CNPG Restore Test for cluster: ${CLUSTER} ==="

# Create test namespace
kubectl --context "${CLUSTER}" create namespace test-restore --dry-run=client -o yaml | \
  kubectl --context "${CLUSTER}" apply -f -

# Apply restore cluster manifest
# ... (apply the recovery cluster YAML)

# Wait for cluster to be ready
echo "Waiting for restore cluster to be ready..."
kubectl --context "${CLUSTER}" wait --for=condition=Ready \
  cluster/postgres-restore-test -n test-restore --timeout="${TIMEOUT}s"

# Verify data
echo "Verifying data integrity..."
kubectl --context "${CLUSTER}" exec -n test-restore \
  postgres-restore-test-1 -- psql -U postgres -c "SELECT count(*) FROM pg_database;"

# Calculate RTO
END_TIME=$(date +%s)
RTO=$((END_TIME - START_TIME))
echo "✅ CNPG restore test passed. RTO: ${RTO} seconds"

# Cleanup
kubectl --context "${CLUSTER}" delete namespace test-restore --wait=false

exit 0
```

**tests/smoke/dr-volsync-restore.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail

CLUSTER="${1:-apps}"
APP="${2:-}"

if [ -z "${APP}" ]; then
  echo "Usage: $0 <cluster> <app>"
  exit 1
fi

echo "=== VolSync Restore Test for ${APP} on cluster: ${CLUSTER} ==="

# Create test namespace
kubectl --context "${CLUSTER}" create namespace test-restore --dry-run=client -o yaml | \
  kubectl --context "${CLUSTER}" apply -f -

# Copy restic secret to test namespace
kubectl --context "${CLUSTER}" get secret "${APP}-restic-secret" -n business -o yaml | \
  sed 's/namespace: business/namespace: test-restore/' | \
  kubectl --context "${CLUSTER}" apply -f -

# Create ReplicationDestination
cat <<EOF | kubectl --context "${CLUSTER}" apply -f -
apiVersion: volsync.backube/v1alpha1
kind: ReplicationDestination
metadata:
  name: ${APP}-restore-test
  namespace: test-restore
spec:
  trigger:
    manual: restore-$(date +%s)
  restic:
    repository: ${APP}-restic-secret
    destinationPVC: ${APP}-test-restore
    copyMethod: Snapshot
    storageClassName: ceph-block
    accessModes:
      - ReadWriteOnce
    capacity: 10Gi
EOF

# Wait for restore to complete
echo "Waiting for restore to complete..."
for i in {1..60}; do
  SYNC=$(kubectl --context "${CLUSTER}" get replicationdestination "${APP}-restore-test" \
    -n test-restore -o jsonpath='{.status.lastManualSync}' 2>/dev/null || echo "")
  if [ -n "${SYNC}" ]; then
    echo "✅ VolSync restore completed"
    break
  fi
  sleep 10
done

# Verify PVC
kubectl --context "${CLUSTER}" get pvc "${APP}-test-restore" -n test-restore

echo "✅ VolSync restore test passed for ${APP}"

# Cleanup
kubectl --context "${CLUSTER}" delete namespace test-restore --wait=false

exit 0
```

### Secret Rotation Test Procedure

**Manual Testing Steps:**
1. Identify a test secret (e.g., `gatus-secret` in `observability` namespace)
2. Update the value in 1Password
3. Monitor External Secrets sync:
   ```bash
   kubectl get externalsecret gatus-secret -n observability -w
   ```
4. Verify pod receives new value:
   ```bash
   kubectl exec -n observability deploy/gatus -- printenv | grep -i password
   ```
5. Expected timing: <5 minutes (based on ESO refreshInterval: 1h, but force-sync should be immediate)

**Automated Test:**
```bash
task dr:test-secret-rotation CLUSTER=infra SECRET=test-secret NAMESPACE=default
```

### Cross-Cluster Validation

**VMAgent Remote-Write Verification:**
```bash
# Check VMAgent logs for successful remote-write
kubectl --context apps logs -n observability deploy/vmagent --tail=50 | grep -E "(sent|success|error)"

# Query infra VictoriaMetrics for apps cluster metrics
curl -s "http://vmsingle.observability.svc:8429/api/v1/query?query=up{cluster='apps'}" | jq .
```

**Fluent-bit Log Shipping Verification:**
```bash
# Check Fluent-bit output stats
kubectl --context apps logs -n observability ds/fluent-bit --tail=50 | grep -E "(output|flushed|retry)"

# Query VictoriaLogs for apps cluster logs
curl -s "http://victorialogs.observability.svc:9428/select/logsql/query?query=cluster:apps" | head
```

**Authentik SSO Verification:**
```bash
# Health check
curl -sf https://authentik.monosense.dev/-/health/ready/

# Verify OIDC endpoint
curl -sf https://authentik.monosense.dev/application/o/.well-known/openid-configuration | jq .issuer
```

### Project Structure Notes

**Files to Create:**

| Path | Purpose |
|------|---------|
| `.taskfiles/dr/Taskfile.yaml` | DR validation tasks |
| `tests/smoke/dr-cnpg-restore.sh` | CNPG restore automation |
| `tests/smoke/dr-volsync-restore.sh` | VolSync restore automation |
| `tests/smoke/test-restore-cluster.yaml` | CNPG recovery cluster template |
| `tests/smoke/test-restore-destination.yaml` | VolSync destination template |

**Directory Structure:**
```
.taskfiles/
└── dr/
    └── Taskfile.yaml

tests/
└── smoke/
    ├── dr-cnpg-restore.sh
    ├── dr-volsync-restore.sh
    ├── test-restore-cluster.yaml
    └── test-restore-destination.yaml
```

### Critical Technical Details

**Version Requirements:**
| Component | Version | Notes |
|-----------|---------|-------|
| kubectl cnpg plugin | Latest | Required for CNPG operations |
| VolSync | v0.9+ | For cleanupTempPVC and enableFileDeletion options |
| restic | v0.16+ | For improved restore performance |
| Taskfile | v3 | For task orchestration |

**Cloudflare R2 Endpoint:**
```
https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com
```

**Cluster Contexts:**
- `infra` - kubectl context for infra cluster
- `apps` - kubectl context for apps cluster

### Verification Commands

```bash
# Run full DR validation suite
task dr:verify-backups CLUSTER=infra
task dr:verify-backups CLUSTER=apps

# Test CNPG restore
task dr:test-cnpg-restore CLUSTER=infra

# Test VolSync restore for specific app
task dr:test-volsync-restore CLUSTER=apps APP=odoo

# Test secret rotation
task dr:test-secret-rotation CLUSTER=infra SECRET=gatus-secret NAMESPACE=observability

# Verify cross-cluster connectivity
task dr:verify-cross-cluster

# Run smoke tests
./tests/smoke/dr-cnpg-restore.sh infra
./tests/smoke/dr-volsync-restore.sh apps odoo
```

### Anti-Patterns to Avoid

1. **DO NOT** run restore tests against production namespaces - always use `test-restore`
2. **DO NOT** skip cleanup - test resources consume storage
3. **DO NOT** hardcode cluster names - use `${CLUSTER}` variable
4. **DO NOT** forget to check for `kubectl cnpg` plugin availability
5. **DO NOT** run VolSync restores without verifying restic secret exists
6. **DO NOT** assume cross-cluster connectivity - always verify network paths
7. **DO NOT** skip timeout handling - DR operations can be slow
8. **DO NOT** forget proper exit codes in smoke test scripts

### Edge Cases to Handle

**Scenario: CNPG plugin not installed**
- Check for plugin existence before running CNPG tasks
- Provide installation instructions if missing
- Fallback to kubectl-based status checks where possible

**Scenario: R2 connectivity issues**
- Tasks should timeout gracefully
- Provide clear error messages about connectivity
- Suggest checking External Secrets for R2 credentials

**Scenario: Test namespace already exists**
- Use `--dry-run=client -o yaml | apply` pattern for idempotency
- Clean up before starting new test

**Scenario: Large database restore**
- Use `--timeout` flag for kubectl cnpg commands
- Document expected timing based on data size
- Consider incremental restore testing for very large DBs

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#DR Testing Cadence] - Monthly/quarterly schedule
- [Source: _bmad-output/planning-artifacts/architecture.md#Backup Architecture] - R2 backup configuration
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4] - Original acceptance criteria
- [Source: docs/project-context.md#Observability Pattern] - Hub/spoke architecture
- [Source: 5-3-deploy-business-applications-to-apps-cluster.md] - Previous story context

### External Documentation

- [CloudNativePG kubectl Plugin](https://cloudnative-pg.io/documentation/current/kubectl-plugin/) - v1.28+
- [VolSync Restic Documentation](https://volsync.readthedocs.io/en/stable/usage/restic/index.html) - Backup and restore
- [Taskfile Documentation](https://taskfile.dev/) - Task runner
- [External Secrets Operator](https://external-secrets.io/latest/) - Secret management
- [VictoriaMetrics vmagent](https://docs.victoriametrics.com/vmagent/) - Remote-write verification

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
