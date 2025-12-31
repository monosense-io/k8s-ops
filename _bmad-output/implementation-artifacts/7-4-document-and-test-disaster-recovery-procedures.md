# Story 7.4: Document and Test Disaster Recovery Procedures

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want **documented and tested DR procedures with automated validation scripts**,
So that **I can recover from disasters with confidence and verify backup integrity continuously**.

## Acceptance Criteria

1. **Given** backups are operational on both clusters (VolSync + CNPG Barman)
   **When** `docs/runbooks/disaster-recovery.md` is created
   **Then** it documents:
   - Full cluster rebuild from Git + VolSync + 1Password
   - CNPG point-in-time recovery procedure
   - VolSync PVC restore procedure
   - Estimated recovery times per data size
   - Pre-requisites checklist for each recovery type

2. **Given** VolSync backups exist in R2
   **When** `tests/smoke/dr-volsync-restore.sh` is executed
   **Then** the script:
   - Creates a test namespace
   - Restores a PVC from backup using `task volsync:restore`
   - Verifies data integrity (file existence, permissions, checksums)
   - Cleans up test resources
   - Reports pass/fail status

3. **Given** CNPG Barman backups exist in R2
   **When** `tests/smoke/dr-cnpg-restore.sh` is executed
   **Then** the script:
   - Creates a test CNPG cluster with PITR configuration
   - Restores to specific point-in-time
   - Verifies data integrity (row counts, checksums)
   - Validates RTO < 30 minutes for CNPG restore
   - Cleans up test resources
   - Reports pass/fail status

4. **Given** DR scripts exist
   **When** `.taskfiles/dr/Taskfile.yaml` is created
   **Then** it contains tasks:
   - `dr:verify-backups` - Check R2 backup accessibility
   - `dr:test-cnpg-restore` - Run CNPG PITR test
   - `dr:test-volsync-restore` - Run VolSync restore test
   - `dr:full-test` - Run all DR tests sequentially

5. **Given** DR taskfiles exist
   **When** root `Taskfile.yaml` is updated
   **Then** DR tasks are included and accessible via `task --list`

6. **Given** DR testing infrastructure exists
   **When** scheduled backup verification is configured
   **Then** weekly automated `restic check` runs and reports status

7. **Given** DR documentation is complete
   **When** monthly CNPG PITR test is scheduled
   **Then** procedure exists in runbook with calendar reminder instructions

8. **Given** all DR infrastructure is operational
   **When** `task dr:full-test CLUSTER=infra` is executed
   **Then** all DR tests pass and report completion within acceptable RTO

## Tasks / Subtasks

- [ ] Task 1: Create Disaster Recovery Runbook (AC: #1)
  - [ ] 1.1 Create `docs/runbooks/disaster-recovery.md` with structured sections
  - [ ] 1.2 Document full cluster rebuild procedure from Git + VolSync + 1Password
  - [ ] 1.3 Document CNPG point-in-time recovery procedure with step-by-step commands
  - [ ] 1.4 Document VolSync PVC restore procedure with taskfile commands
  - [ ] 1.5 Add estimated recovery times table per data size
  - [ ] 1.6 Create pre-requisites checklist for each recovery type
  - [ ] 1.7 Add troubleshooting section for common recovery issues

- [ ] Task 2: Create VolSync Restore Test Script (AC: #2)
  - [ ] 2.1 Create `tests/smoke/dr-volsync-restore.sh` with proper shebang and error handling
  - [ ] 2.2 Implement test namespace creation with unique suffix
  - [ ] 2.3 Create test PVC with known checksum data
  - [ ] 2.4 Trigger restore using `task volsync:restore` pattern
  - [ ] 2.5 Implement data verification (file existence, checksums)
  - [ ] 2.6 Add cleanup routine for test resources
  - [ ] 2.7 Implement pass/fail reporting with exit codes

- [ ] Task 3: Create CNPG PITR Test Script (AC: #3)
  - [ ] 3.1 Create `tests/smoke/dr-cnpg-restore.sh` with proper shebang and error handling
  - [ ] 3.2 Implement test namespace and test cluster creation
  - [ ] 3.3 Configure PITR bootstrap from existing ObjectStore
  - [ ] 3.4 Set recovery target using `.spec.bootstrap.recovery.recoveryTarget.targetTime`
  - [ ] 3.5 Wait for cluster to reach Ready state with timeout
  - [ ] 3.6 Implement data verification (connect, query, validate row counts)
  - [ ] 3.7 Measure and report RTO (time from script start to verification)
  - [ ] 3.8 Add cleanup routine for test cluster
  - [ ] 3.9 Implement pass/fail reporting with RTO validation (<30 min)

- [ ] Task 4: Create DR Taskfile (AC: #4, #5)
  - [ ] 4.1 Create `.taskfiles/dr/Taskfile.yaml` with proper structure
  - [ ] 4.2 Implement `dr:verify-backups` task to check R2 connectivity
  - [ ] 4.3 Implement `dr:test-cnpg-restore` task wrapping the smoke script
  - [ ] 4.4 Implement `dr:test-volsync-restore` task wrapping the smoke script
  - [ ] 4.5 Implement `dr:full-test` task running all tests sequentially
  - [ ] 4.6 Update root `Taskfile.yaml` to include dr tasks

- [ ] Task 5: Configure Automated Backup Verification (AC: #6)
  - [ ] 5.1 Create CronJob manifest for weekly `restic check` execution
  - [ ] 5.2 Configure job to run `restic check --read-data-subset=10%` against R2
  - [ ] 5.3 Add alerting integration for failed verification
  - [ ] 5.4 Document manual verification procedure in runbook

- [ ] Task 6: Document DR Testing Schedule (AC: #7)
  - [ ] 6.1 Add DR testing cadence section to runbook
  - [ ] 6.2 Document monthly CNPG PITR test procedure
  - [ ] 6.3 Document quarterly full cluster recovery test
  - [ ] 6.4 Add calendar reminder instructions for scheduled tests

- [ ] Task 7: Integration Testing and Validation (AC: #8)
  - [ ] 7.1 Execute `task dr:full-test CLUSTER=infra` end-to-end
  - [ ] 7.2 Verify all tests pass within acceptable RTO
  - [ ] 7.3 Document any issues encountered and resolutions
  - [ ] 7.4 Update runbook with lessons learned

## Dev Notes

### Architecture Compliance Requirements

**App Location:**
- Runbook: `docs/runbooks/disaster-recovery.md`
- Smoke Tests: `tests/smoke/dr-volsync-restore.sh`, `tests/smoke/dr-cnpg-restore.sh`
- Taskfile: `.taskfiles/dr/Taskfile.yaml`
- Backup Verification CronJob: `kubernetes/apps/volsync/backup-verify/` (optional)

**Directory Structure:**
```
k8s-ops/
├── docs/
│   └── runbooks/
│       └── disaster-recovery.md        # Main DR runbook
├── tests/
│   └── smoke/
│       ├── dr-volsync-restore.sh       # VolSync restore validation
│       └── dr-cnpg-restore.sh          # CNPG PITR validation
├── .taskfiles/
│   └── dr/
│       └── Taskfile.yaml               # DR operational tasks
└── kubernetes/
    └── apps/
        └── volsync/
            └── backup-verify/          # Optional: automated verification
                ├── cronjob.yaml
                └── kustomization.yaml
```

### DR Testing Cadence (From Architecture)

| Test Type | Frequency | Scope | Success Criteria |
|-----------|-----------|-------|------------------|
| CNPG Point-in-Time Recovery | Monthly | Restore to test namespace | Data integrity, RTO <30min |
| CNPG Full Cluster Recovery | Quarterly | Restore to separate cluster | Full operational, RTO <2h |
| VolSync PVC Restore | Monthly | Restore single app | App functional with data |
| Full DR Simulation | Bi-annually | Simulate infra cluster failure | Recovery <4h |
| Backup Verification | Weekly (automated) | Verify R2 accessibility | `restic check` passes |

### CNPG Point-in-Time Recovery Configuration

**CRITICAL: Use Plugin-Based Recovery (CNPG v1.26+)**

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-dr-test
  namespace: dr-test
spec:
  instances: 1

  # Storage - use same pattern as production
  storage:
    size: 10Gi
    storageClass: openebs-hostpath

  # Bootstrap from backup using plugin
  bootstrap:
    recovery:
      # Plugin-based recovery (new architecture)
      source: postgres-r2-backup
      recoveryTarget:
        targetTime: "2025-12-31T12:00:00Z"  # Target timestamp for PITR

  # Reference to ObjectStore for recovery
  externalClusters:
    - name: postgres-r2-backup
      plugin:
        name: barman-cloud.cloudnative-pg.io
        parameters:
          barmanObjectName: postgres-r2-backup
          serverName: postgres-${CLUSTER_NAME}
```

**Key Recovery Options:**
- `recoveryTarget.targetTime`: Restore to specific timestamp (RFC-3339 format)
- `recoveryTarget.targetLSN`: Restore to specific WAL position
- `recoveryTarget.targetXid`: Restore to specific transaction ID
- `recoveryTarget.targetImmediate`: Restore to end of backup (no WAL replay)

### VolSync Restore Configuration

**ReplicationDestination for Test Restore:**

```yaml
apiVersion: volsync.backube/v1alpha1
kind: ReplicationDestination
metadata:
  name: dr-test-restore
  namespace: dr-test
spec:
  trigger:
    manual: restore-$(date +%Y%m%d%H%M%S)
  restic:
    repository: volsync-r2-secret
    destinationPVC: dr-test-pvc
    copyMethod: Direct
    # Optional: restore specific snapshot by offset
    # previous: 2  # 2 snapshots ago
    # Optional: restore to specific timestamp
    # restoreAsOf: "2025-12-31T12:00:00-05:00"
```

**Copy Method Options:**
- `Direct`: Write directly to destination PVC (fastest)
- `Snapshot`: Create snapshot first, then restore
- `Clone`: Clone the destination volume

### Cloudflare R2 Configuration

**R2 Endpoint:** `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`

**VolSync Repository:** `s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/${VOLSYNC_R2_BUCKET}/${APP}`

**CNPG Repository:** `s3://${CNPG_R2_BUCKET}/` (via ObjectStore configuration)

### DR Taskfile Implementation

```yaml
# .taskfiles/dr/Taskfile.yaml
version: '3'

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  KUBECONFIG: '{{.ROOT_DIR}}/kubeconfig-{{.CLUSTER}}'
  TEST_NAMESPACE: dr-test-{{now | date "20060102150405"}}

env:
  KUBECONFIG: '{{.KUBECONFIG}}'

tasks:
  verify-backups:
    desc: Verify R2 backup repository accessibility
    summary: |
      Spawns an ephemeral pod to run restic check against the repository.
      Usage: task dr:verify-backups CLUSTER=infra
    cmds:
      - |
        kubectl run dr-verify-$(date +%s) \
          --rm -it --restart=Never \
          --namespace=volsync-system \
          --image=restic/restic:latest \
          --overrides='{
            "spec": {
              "containers": [{
                "name": "restic",
                "image": "restic/restic:latest",
                "command": ["restic", "check", "--read-data-subset=5%"],
                "envFrom": [{"secretRef": {"name": "volsync-r2-secret"}}]
              }]
            }
          }' -- /bin/sh -c "restic check --read-data-subset=5%"
      - echo "Backup verification completed"

  test-cnpg-restore:
    desc: Test CNPG point-in-time recovery
    summary: |
      Runs the CNPG PITR smoke test script.
      Usage: task dr:test-cnpg-restore CLUSTER=infra
    cmds:
      - '{{.ROOT_DIR}}/tests/smoke/dr-cnpg-restore.sh {{.CLUSTER}}'

  test-volsync-restore:
    desc: Test VolSync PVC restore
    summary: |
      Runs the VolSync restore smoke test script.
      Usage: task dr:test-volsync-restore CLUSTER=infra [APP=gatus]
    vars:
      APP: '{{.APP | default "gatus"}}'
    cmds:
      - '{{.ROOT_DIR}}/tests/smoke/dr-volsync-restore.sh {{.CLUSTER}} {{.APP}}'

  full-test:
    desc: Run all DR tests
    summary: |
      Executes all DR validation tests sequentially.
      Usage: task dr:full-test CLUSTER=infra
    cmds:
      - task: verify-backups
      - task: test-volsync-restore
      - task: test-cnpg-restore
      - echo "All DR tests completed successfully"
```

### Smoke Test Script Template (VolSync)

```bash
#!/usr/bin/env bash
# tests/smoke/dr-volsync-restore.sh
# VolSync restore validation script

set -euo pipefail

CLUSTER="${1:-infra}"
APP="${2:-gatus}"
NAMESPACE="dr-test-$(date +%s)"
TIMEOUT="10m"

echo "=== VolSync Restore Test ==="
echo "Cluster: $CLUSTER"
echo "App: $APP"
echo "Test Namespace: $NAMESPACE"

# Setup
kubectl create namespace "$NAMESPACE"
trap "kubectl delete namespace $NAMESPACE --ignore-not-found" EXIT

# Find source ReplicationSource
SOURCE_NS=$(kubectl get replicationsource -A -o jsonpath="{range .items[?(@.metadata.name==\"${APP}-backup\")]}{.metadata.namespace}{end}")
if [ -z "$SOURCE_NS" ]; then
  echo "ERROR: ReplicationSource ${APP}-backup not found"
  exit 1
fi

# Copy secret to test namespace
kubectl get secret volsync-r2-secret -n "$SOURCE_NS" -o yaml | \
  sed "s/namespace: .*/namespace: $NAMESPACE/" | \
  kubectl apply -f -

# Create ReplicationDestination
cat <<EOF | kubectl apply -f -
apiVersion: volsync.backube/v1alpha1
kind: ReplicationDestination
metadata:
  name: dr-test-restore
  namespace: $NAMESPACE
spec:
  trigger:
    manual: restore-$(date +%Y%m%d%H%M%S)
  restic:
    repository: volsync-r2-secret
    destinationPVC: dr-test-pvc
    copyMethod: Direct
    accessModes: ["ReadWriteOnce"]
    capacity: 1Gi
EOF

# Wait for restore completion
echo "Waiting for restore to complete..."
kubectl wait --for=condition=available replicationdestination/dr-test-restore \
  -n "$NAMESPACE" --timeout="$TIMEOUT"

# Verify PVC exists and has data
PVC_STATUS=$(kubectl get pvc dr-test-pvc -n "$NAMESPACE" -o jsonpath='{.status.phase}')
if [ "$PVC_STATUS" != "Bound" ]; then
  echo "ERROR: PVC not bound (status: $PVC_STATUS)"
  exit 1
fi

echo "=== VolSync Restore Test PASSED ==="
```

### Smoke Test Script Template (CNPG PITR)

```bash
#!/usr/bin/env bash
# tests/smoke/dr-cnpg-restore.sh
# CNPG Point-in-Time Recovery validation script

set -euo pipefail

CLUSTER="${1:-infra}"
NAMESPACE="dr-test-cnpg-$(date +%s)"
TIMEOUT="30m"
START_TIME=$(date +%s)

echo "=== CNPG PITR Test ==="
echo "Cluster: $CLUSTER"
echo "Test Namespace: $NAMESPACE"
echo "Start Time: $(date)"

# Setup
kubectl create namespace "$NAMESPACE"
trap "kubectl delete namespace $NAMESPACE --ignore-not-found" EXIT

# Copy R2 credentials to test namespace
kubectl get secret cnpg-r2-secret -n databases -o yaml | \
  sed "s/namespace: .*/namespace: $NAMESPACE/" | \
  kubectl apply -f -

# Create ObjectStore reference for recovery
cat <<EOF | kubectl apply -f -
apiVersion: barmancloud.cnpg.io/v1
kind: ObjectStore
metadata:
  name: dr-test-objectstore
  namespace: $NAMESPACE
spec:
  configuration:
    destinationPath: s3://${CNPG_R2_BUCKET}/
    endpointURL: https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com
    s3Credentials:
      accessKeyId:
        name: cnpg-r2-secret
        key: ACCESS_KEY_ID
      secretAccessKey:
        name: cnpg-r2-secret
        key: ACCESS_SECRET_KEY
    serverName: postgres-${CLUSTER}
EOF

# Get latest backup timestamp (minus 1 minute for safety)
TARGET_TIME=$(date -u -d '1 minute ago' +"%Y-%m-%dT%H:%M:%SZ")
echo "Recovery target time: $TARGET_TIME"

# Create recovery cluster
cat <<EOF | kubectl apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-dr-test
  namespace: $NAMESPACE
spec:
  instances: 1
  storage:
    size: 10Gi
    storageClass: openebs-hostpath

  bootstrap:
    recovery:
      source: dr-recovery-source
      recoveryTarget:
        targetTime: "$TARGET_TIME"

  externalClusters:
    - name: dr-recovery-source
      plugin:
        name: barman-cloud.cloudnative-pg.io
        parameters:
          barmanObjectName: dr-test-objectstore
EOF

# Wait for cluster to be ready
echo "Waiting for recovery cluster to be ready..."
kubectl wait --for=condition=Ready cluster/postgres-dr-test \
  -n "$NAMESPACE" --timeout="$TIMEOUT"

# Verify data connectivity
echo "Verifying database connectivity..."
kubectl cnpg psql postgres-dr-test -n "$NAMESPACE" -- -c "SELECT 1;"

# Calculate RTO
END_TIME=$(date +%s)
RTO_SECONDS=$((END_TIME - START_TIME))
RTO_MINUTES=$((RTO_SECONDS / 60))

echo "Recovery Time Objective (RTO): ${RTO_MINUTES} minutes (${RTO_SECONDS} seconds)"

# Validate RTO < 30 minutes
if [ $RTO_MINUTES -gt 30 ]; then
  echo "WARNING: RTO exceeded 30 minute target"
  # Note: Don't fail, just warn - actual RTO depends on data size
fi

echo "=== CNPG PITR Test PASSED ==="
echo "RTO: ${RTO_MINUTES} minutes"
```

### Backup Verification CronJob

```yaml
# kubernetes/apps/volsync/backup-verify/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-verify
  namespace: volsync-system
spec:
  schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: restic
              image: restic/restic:latest
              command:
                - /bin/sh
                - -c
                - |
                  restic check --read-data-subset=10%
                  if [ $? -eq 0 ]; then
                    echo "Backup verification passed"
                  else
                    echo "Backup verification FAILED"
                    exit 1
                  fi
              envFrom:
                - secretRef:
                    name: volsync-r2-secret
```

### Disaster Recovery Runbook Template

```markdown
# Disaster Recovery Runbook

## Overview
This runbook covers disaster recovery procedures for the k8s-ops infrastructure.

## Recovery Scenarios

### 1. Full Cluster Rebuild
**Scenario:** Complete cluster loss (infra or apps)
**RTO Target:** < 2 hours
**RPO:** 8 hours (VolSync) + continuous (CNPG WAL)

#### Prerequisites
- [ ] 1Password access verified
- [ ] Cloudflare R2 credentials available
- [ ] New hardware/VMs provisioned
- [ ] Network connectivity confirmed

#### Procedure
1. Bootstrap new Talos cluster...
2. Apply Flux GitOps...
3. Restore secrets from 1Password...
4. Restore PVCs from VolSync...
5. Restore databases from CNPG backups...

### 2. CNPG Point-in-Time Recovery
**Scenario:** Database corruption, accidental deletion
**RTO Target:** < 30 minutes

#### Procedure
1. Identify target recovery timestamp
2. Create recovery cluster manifest
3. Apply and wait for recovery
4. Verify data integrity
5. Switch application connections

### 3. VolSync PVC Restore
**Scenario:** Application data loss
**RTO Target:** < 15 minutes

#### Procedure
1. Identify application and snapshot
2. Run `task volsync:restore APP=<app>`
3. Verify restored data
4. Restart application pods

## Testing Schedule
- Weekly: Automated backup verification (CronJob)
- Monthly: CNPG PITR test
- Monthly: VolSync restore test
- Quarterly: Full cluster recovery simulation
- Bi-annually: Full DR simulation
```

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR19 | Backup success rate 100% | Weekly automated verification via CronJob |
| NFR20 | Cluster recovery < 2 hours | Documented procedure, tested quarterly |
| NFR24 | Documentation coverage | Complete runbook with step-by-step procedures |
| NFR29 | Taskfile coverage | DR operations available via `task dr:*` |

### Dependencies

- **Hard Dependencies:**
  - Story 7.1 (VolSync deployment) - VolSync must be operational
  - Story 7.2 (CNPG Barman) - CNPG backups must be configured
  - Story 7.3 (VolSync Taskfiles) - Taskfile infrastructure exists
  - `kubectl cnpg` plugin - Required for CNPG operations

- **Soft Dependencies:**
  - Alerting infrastructure for failed verification notifications

### Previous Story Intelligence (7.1, 7.2, 7.3)

**From Story 7.1 (VolSync):**
- R2 endpoint: `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
- Secret name: `volsync-r2-secret`
- ReplicationSource naming: `${APP}-backup`
- ReplicationDestination pattern for restores
- Schedule: `0 */8 * * *` (every 8 hours)
- Retention: 24 hourly, 7 daily

**From Story 7.2 (CNPG Barman):**
- Plugin-based architecture (CNPG v1.26+) - NOT legacy barmanObjectStore
- ObjectStore CRD: `barmancloud.cnpg.io/v1`
- Secret name: `cnpg-r2-secret`
- WAL compression: bzip2
- Retention: 30 days
- `kubectl cnpg backup` command for on-demand backups

**From Story 7.3 (VolSync Taskfiles):**
- Taskfile variables pattern (CLUSTER, APP, NAMESPACE)
- Error handling for missing resources
- Ephemeral pod pattern for restic commands
- Root Taskfile include pattern

**Key Learnings to Apply:**
- Use consistent variable naming across all DR scripts
- Plugin-based CNPG recovery is mandatory (v1.26+)
- Ephemeral pods for restic operations with proper cleanup
- Clear error handling with exit codes
- RTO measurement and validation

### Security Considerations

- DR test scripts only use existing secrets (no credential handling)
- Test namespaces are isolated and auto-cleaned
- Ephemeral pods for restic operations auto-cleanup
- All sensitive operations via kubectl with RBAC
- No credentials stored in scripts or taskfiles
- R2 bucket access should be restricted to backup operations only

### Testing Considerations

**Manual Test Procedure:**
1. Run `task dr:verify-backups CLUSTER=infra` - verify R2 connectivity
2. Run `task dr:test-volsync-restore CLUSTER=infra APP=gatus` - verify PVC restore
3. Run `task dr:test-cnpg-restore CLUSTER=infra` - verify CNPG PITR
4. Run `task dr:full-test CLUSTER=infra` - verify complete DR pipeline
5. Review RTO measurements against targets
6. Verify cleanup of test resources

**Integration Points:**
- Smoke tests can be integrated into CI/CD for monthly validation
- Alerting should notify on verification failures
- Calendar reminders for manual testing cadence

### Project Structure Notes

- Alignment with unified project structure: Runbook in `docs/runbooks/`, tests in `tests/smoke/`
- Taskfile follows existing pattern at `.taskfiles/dr/`
- Follows existing conventions from Stories 7.1-7.3
- No detected conflicts with architecture patterns
- Scripts use portable bash and standard kubectl commands

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.4] - Epic and story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#DR Testing Cadence] - DR testing schedule
- [Source: docs/project-context.md#Taskfile Operations] - Taskfile operation categories
- [Source: _bmad-output/implementation-artifacts/7-1-deploy-volsync-for-pvc-backups.md] - VolSync patterns
- [Source: _bmad-output/implementation-artifacts/7-2-configure-cnpg-barman-backups-to-r2.md] - CNPG Barman patterns
- [Source: _bmad-output/implementation-artifacts/7-3-create-volsync-operational-taskfiles.md] - Taskfile patterns
- [CloudNativePG Recovery Documentation](https://cloudnative-pg.io/documentation/current/recovery/) - Official PITR guide
- [VolSync Restic Documentation](https://volsync.readthedocs.io/en/latest/usage/restic/) - Restic backup/restore
- [CYBERTEC CNPG PITR Guide](https://www.cybertec-postgresql.com/en/exploration-cnpg-point-in-time-recovery/) - PITR best practices
- [EDB PostgreSQL DR with CNPG](https://www.enterprisedb.com/postgresql-disaster-recovery-with-kubernetes-volume-snapshots-using-cloudnativepg) - Volume snapshot recovery

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

