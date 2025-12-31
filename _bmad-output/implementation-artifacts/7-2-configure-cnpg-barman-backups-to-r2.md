# Story 7.2: Configure CNPG Barman Backups to R2

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want **PostgreSQL databases backed up via Barman to Cloudflare R2**,
So that **I can perform point-in-time recovery for databases with off-site protection**.

## Acceptance Criteria

1. **Given** CNPG shared cluster is operational
   **When** Barman Cloud Plugin is deployed
   **Then** Plugin controller pods are running in `cnpg-system` namespace

2. **Given** Barman Cloud Plugin is installed
   **When** R2 credentials ExternalSecret is created
   **Then** Secret `cnpg-r2-secret` contains valid `ACCESS_KEY_ID`, `ACCESS_SECRET_KEY`

3. **Given** credentials are synced
   **When** ObjectStore CRD is created
   **Then** ObjectStore references R2 bucket at `s3://${CNPG_R2_BUCKET}/` with:
   - R2 endpoint: `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
   - WAL compression: bzip2
   - Data compression: bzip2
   - Retention policy: 30 days

4. **Given** ObjectStore is configured
   **When** CNPG Cluster CR is updated with plugin configuration
   **Then** Cluster references `barman-cloud.cloudnative-pg.io` plugin with:
   - `isWALArchiver: true`
   - `barmanObjectName` pointing to ObjectStore

5. **Given** WAL archiving is enabled
   **When** database write activity occurs
   **Then** WAL files are continuously archived to R2 bucket

6. **Given** WAL archiving is active
   **When** ScheduledBackup is created with daily schedule
   **Then** Base backups run daily at specified time

7. **Given** backups are running
   **When** `kubectl cnpg backup postgres -n databases --method=plugin` is executed
   **Then** On-demand backup completes successfully and appears in R2

8. **Given** backups exist in R2
   **When** recovery is needed
   **Then** Point-in-time recovery to any timestamp within retention period is possible

## Tasks / Subtasks

- [ ] Task 1: Deploy Barman Cloud Plugin (AC: #1)
  - [ ] 1.1 Create `kubernetes/apps/databases/barman-cloud-plugin/` directory structure
  - [ ] 1.2 Create HelmRelease for Barman Cloud Plugin v0.10.0
  - [ ] 1.3 Configure plugin with cluster-aware settings
  - [ ] 1.4 Create Flux Kustomization `ks.yaml` with dependency on `cloudnative-pg`
  - [ ] 1.5 Verify plugin controller pods are running

- [ ] Task 2: Configure R2 Credentials via External Secrets (AC: #2)
  - [ ] 2.1 Create/verify 1Password item `cnpg-r2` with R2 access credentials
  - [ ] 2.2 Create ExternalSecret `cnpg-r2-secret` syncing from 1Password
  - [ ] 2.3 Verify secret contains ACCESS_KEY_ID, ACCESS_SECRET_KEY
  - [ ] 2.4 Deploy to `databases` namespace

- [ ] Task 3: Create ObjectStore Resource (AC: #3)
  - [ ] 3.1 Create `kubernetes/apps/databases/cloudnative-pg/objectstore/` directory
  - [ ] 3.2 Create ObjectStore CRD with:
    - `apiVersion: barmancloud.cnpg.io/v1`
    - `destinationPath: s3://${CNPG_R2_BUCKET}/`
    - `endpointURL: https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
    - WAL compression: bzip2
    - Data compression: bzip2
    - Retention policy: 30d
  - [ ] 3.3 Reference R2 credentials secret
  - [ ] 3.4 Add `serverName` for backup identification

- [ ] Task 4: Update CNPG Cluster with Plugin Configuration (AC: #4, #5)
  - [ ] 4.1 Modify existing CNPG Cluster CR to add `plugins` section
  - [ ] 4.2 Configure plugin with:
    - `name: barman-cloud.cloudnative-pg.io`
    - `isWALArchiver: true`
    - `parameters.barmanObjectName: <objectstore-name>`
  - [ ] 4.3 Apply updated cluster configuration
  - [ ] 4.4 Verify WAL archiving starts (check cluster status)

- [ ] Task 5: Create ScheduledBackup for Daily Base Backups (AC: #6)
  - [ ] 5.1 Create ScheduledBackup resource in `kubernetes/apps/databases/cloudnative-pg/cluster/`
  - [ ] 5.2 Configure:
    - Schedule: `0 0 * * *` (daily at midnight)
    - Method: plugin
    - Plugin name: `barman-cloud.cloudnative-pg.io`
  - [ ] 5.3 Verify scheduled backup appears in cluster status

- [ ] Task 6: Test Backup and Verify (AC: #7, #8)
  - [ ] 6.1 Trigger on-demand backup: `kubectl cnpg backup postgres -n databases --method=plugin --plugin-name=barman-cloud.cloudnative-pg.io`
  - [ ] 6.2 Verify backup appears in R2 bucket
  - [ ] 6.3 Check WAL files are being archived
  - [ ] 6.4 Document recovery procedure for runbook

## Dev Notes

### Architecture Compliance Requirements

**App Location:**
- Barman Cloud Plugin: `kubernetes/apps/databases/barman-cloud-plugin/` (shared - both clusters)
- ObjectStore: `kubernetes/apps/databases/cloudnative-pg/objectstore/`
- ScheduledBackup: `kubernetes/apps/databases/cloudnative-pg/cluster/`

**Directory Structure:**
```
kubernetes/apps/databases/
├── barman-cloud-plugin/
│   ├── app/
│   │   ├── helmrelease.yaml
│   │   └── kustomization.yaml
│   └── ks.yaml
└── cloudnative-pg/
    ├── app/                          # Existing operator
    ├── cluster/
    │   ├── cluster.yaml              # Updated with plugin config
    │   ├── scheduledbackup.yaml      # NEW
    │   └── kustomization.yaml
    ├── objectstore/                  # NEW
    │   ├── objectstore.yaml
    │   ├── externalsecret.yaml
    │   └── kustomization.yaml
    └── ks.yaml
```

### CRITICAL: Plugin-Based Architecture (Not Legacy barmanObjectStore)

**CloudNativePG v1.26+ deprecates the built-in `.spec.backup.barmanObjectStore` field.**

You MUST use the new plugin-based architecture with:
- Barman Cloud Plugin v0.10.0 (latest as of December 2025)
- ObjectStore CRD (apiVersion: `barmancloud.cnpg.io/v1`)
- Plugin configuration in Cluster CR under `.spec.plugins`

**DO NOT USE the legacy barmanObjectStore pattern - it will be removed in future CNPG releases.**

### Barman Cloud Plugin HelmRelease

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: barman-cloud-plugin
spec:
  interval: 1h
  chart:
    spec:
      chart: cnpg-plugin-barman-cloud
      version: 0.10.0
      sourceRef:
        kind: HelmRepository
        name: cloudnative-pg
        namespace: flux-system
  install:
    remediation:
      retries: -1  # Operator must succeed
    crds: CreateReplace
  upgrade:
    cleanupOnFail: true
    crds: CreateReplace
    remediation:
      strategy: rollback
      retries: 3
  values:
    # Default values usually sufficient
```

### ObjectStore Configuration (R2-Specific)

```yaml
apiVersion: barmancloud.cnpg.io/v1
kind: ObjectStore
metadata:
  name: postgres-r2-backup
  namespace: databases
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
    wal:
      compression: bzip2
      maxParallel: 2
    data:
      compression: bzip2
      jobs: 2
    retentionPolicy: "30d"
    serverName: postgres-${CLUSTER_NAME}  # Unique per cluster
```

### CNPG Cluster Plugin Configuration

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres
  namespace: databases
spec:
  instances: 3
  # ... existing configuration ...

  # NEW: Plugin-based backup configuration
  plugins:
    - name: barman-cloud.cloudnative-pg.io
      isWALArchiver: true
      parameters:
        barmanObjectName: postgres-r2-backup
        serverName: postgres-${CLUSTER_NAME}
```

### ScheduledBackup Configuration

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: postgres-daily-backup
  namespace: databases
spec:
  cluster:
    name: postgres
  schedule: "0 0 * * *"  # Daily at midnight
  backupOwnerReference: self
  method: plugin
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
```

### On-Demand Backup Command

```bash
# Using cnpg kubectl plugin
kubectl cnpg backup postgres -n databases \
  --method=plugin \
  --plugin-name=barman-cloud.cloudnative-pg.io

# Verify backup status
kubectl cnpg status postgres -n databases
```

### Cloudflare R2 Configuration

**R2 Endpoint:** `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
**Bucket Structure:** Each cluster gets unique serverName prefix within the CNPG bucket

**Secret Format (1Password -> ExternalSecret):**
```yaml
ACCESS_KEY_ID: <r2-access-key>
ACCESS_SECRET_KEY: <r2-secret-key>
```

**ExternalSecret Template:**
```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: cnpg-r2-secret
  namespace: databases
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: cnpg-r2-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: cnpg-r2
```

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR19 | Backup success rate 100% | Monitor ScheduledBackup status, alert on failure |
| NFR37 | Cloudflare R2 connectivity | Verify endpoint connectivity before deployment |
| NFR20 | Cluster recovery < 2 hours | Document PITR procedure in runbooks |
| NFR42 | Log retention 30 days | WAL retention matches via retentionPolicy |

### Dependencies

- **Hard Dependencies:**
  - `cloudnative-pg` operator - CNPG must be deployed first
  - `external-secrets-stores` - 1Password credentials
  - Story 7.1 (VolSync) - Not directly, but same R2 bucket infrastructure

- **Soft Dependencies:**
  - `rook-ceph-cluster` - Storage for PostgreSQL PVCs

### Previous Story Intelligence (7.1 - VolSync)

From Story 7.1 implementation patterns:
- R2 endpoint: `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
- Same 1Password vault pattern for R2 credentials
- ExternalSecret pattern: `external-secrets.io/v1` API version
- HelmRelease remediation pattern: `install.remediation.retries: 3`

**Key Learnings to Apply:**
- Use `external-secrets.io/v1` (not v1beta1)
- R2 credentials in separate secret per service (cnpg-r2-secret)
- Operators should use `retries: -1` for install remediation

### Project Structure Notes

- Alignment with unified project structure: Barman Cloud Plugin follows shared app pattern in `kubernetes/apps/`
- ObjectStore is part of CNPG configuration, placed alongside cluster
- No detected conflicts with architecture patterns
- Follow `monosense.dev/` prefix for custom annotations

### Security Considerations

- R2 credentials stored ONLY in 1Password, synced via ExternalSecret
- Barman encrypts data before upload (optional: add `encryption: AES256` if desired)
- Cloudflare R2 provides at-rest encryption
- No credentials in Git repository
- WAL files contain database content - treat backup bucket as sensitive

### Testing Considerations

**Manual Test Procedure:**
1. Verify plugin is installed: `kubectl get pods -n cnpg-system`
2. Verify ObjectStore is ready: `kubectl get objectstores -n databases`
3. Check cluster WAL archiving: `kubectl cnpg status postgres -n databases`
4. Trigger manual backup and verify in R2
5. Test PITR to a new cluster (documented in Story 7.4)

**Automated Validation (tests/smoke/):**
- `dr-cnpg-restore.sh` - CNPG PITR test (created in Story 7.4)

### DR Testing Cadence (From Architecture)

| Test Type | Frequency | Scope |
|-----------|-----------|-------|
| CNPG Point-in-Time Recovery | Monthly | Restore to test namespace |
| CNPG Full Cluster Recovery | Quarterly | Restore to separate cluster |
| Backup Verification | Weekly (automated) | Verify R2 accessibility |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2] - Epic and story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#Backup Architecture] - R2 endpoint and bucket structure
- [Source: docs/project-context.md#CNPG Shared Cluster Pattern] - Shared postgres cluster pattern
- [Source: _bmad-output/implementation-artifacts/7-1-deploy-volsync-for-pvc-backups.md] - Previous story patterns
- [Barman Cloud Plugin Documentation](https://cloudnative-pg.io/plugin-barman-cloud/docs/usage/) - Official plugin usage guide
- [Barman Cloud Plugin GitHub](https://github.com/cloudnative-pg/plugin-barman-cloud) - Plugin releases and source
- [CloudNativePG WAL Archiving](https://cloudnative-pg.io/documentation/1.27/wal_archiving/) - WAL archiving concepts

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

