# Story 7.1: Deploy VolSync for PVC Backups

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want **VolSync backing up PVCs to Cloudflare R2**,
So that **application data is protected and recoverable from off-site storage**.

## Acceptance Criteria

1. **Given** Rook-Ceph storage is operational
   **When** VolSync operator is deployed via HelmRelease
   **Then** VolSync controller pods are running in `volsync-system` namespace

2. **Given** VolSync operator is running
   **When** R2 credentials ExternalSecret is created
   **Then** Secret `volsync-r2-secret` contains valid AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, RESTIC_REPOSITORY, RESTIC_PASSWORD

3. **Given** credentials are synced
   **When** kubernetes component `volsync/r2` is created
   **Then** component provides ReplicationSource template for R2 backups with:
   - Restic configuration pointing to R2 endpoint
   - Default schedule: every 8 hours (`0 */8 * * *`)
   - Retention: 24 hourly, 7 daily snapshots

4. **Given** component is available
   **When** applications include `volsync/r2` component reference
   **Then** ReplicationSource is created with app-specific PVC reference

5. **Given** ReplicationSource is created
   **When** first backup runs
   **Then** snapshot appears in R2 bucket at path `{APP}/`

6. **Given** backups are running
   **When** `task volsync:list APP=<app>` is executed
   **Then** available snapshots are listed with timestamps

7. **Given** backup exists in R2
   **When** restore is triggered via ReplicationDestination
   **Then** PVC data is recovered from R2 backup

8. **Given** VolSync is operational
   **When** backup job completes
   **Then** success rate is 100% (NFR19)

## Tasks / Subtasks

- [ ] Task 1: Deploy VolSync Operator (AC: #1)
  - [ ] 1.1 Create `kubernetes/apps/volsync/` directory structure following app pattern
  - [ ] 1.2 Create HelmRelease for VolSync operator v0.14.0 (latest) from backube/volsync chart
  - [ ] 1.3 Configure operator with cluster-aware settings
  - [ ] 1.4 Create Flux Kustomization `ks.yaml` with dependency on `rook-ceph-cluster`
  - [ ] 1.5 Verify controller pods are running

- [ ] Task 2: Configure R2 Credentials via External Secrets (AC: #2)
  - [ ] 2.1 Create 1Password item `volsync-r2` with R2 access credentials
  - [ ] 2.2 Create ExternalSecret `volsync-r2-secret` syncing from 1Password
  - [ ] 2.3 Verify secret contains RESTIC_REPOSITORY, RESTIC_PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  - [ ] 2.4 Repository URL format: `s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/{VOLSYNC_R2_BUCKET}`

- [ ] Task 3: Create Reusable VolSync R2 Component (AC: #3, #4)
  - [ ] 3.1 Create `kubernetes/components/volsync/r2/kustomization.yaml`
  - [ ] 3.2 Create ReplicationSource template with configurable:
    - sourcePVC replacement
    - copyMethod: Snapshot (preferred) or Clone
    - trigger.schedule: `0 */8 * * *` (every 8 hours)
    - restic.repository: reference to volsync-r2-secret
    - restic.retain: { hourly: 24, daily: 7 }
    - restic.pruneIntervalDays: 7
    - restic.cacheCapacity: 2Gi
  - [ ] 3.3 Create ReplicationDestination template for restores
  - [ ] 3.4 Document component usage with variable replacements

- [ ] Task 4: Create VolSync Operational Taskfiles (AC: #6)
  - [ ] 4.1 Create `.taskfiles/volsync/Taskfile.yaml` with tasks:
    - `volsync:list` - List snapshots for an app
    - `volsync:snapshot` - Trigger immediate backup
    - `volsync:restore` - Restore PVC from snapshot
    - `volsync:unlock` - Unlock stuck Restic repository
    - `volsync:status` - Show ReplicationSource status
  - [ ] 4.2 Tasks accept APP, CLUSTER, and optional SNAPSHOT variables
  - [ ] 4.3 Update root `Taskfile.yaml` to include volsync tasks

- [ ] Task 5: Test Backup and Restore Flow (AC: #5, #7, #8)
  - [ ] 5.1 Create test PVC with sample data
  - [ ] 5.2 Apply volsync/r2 component to test PVC
  - [ ] 5.3 Verify backup appears in R2 bucket
  - [ ] 5.4 Test restore to new PVC using ReplicationDestination
  - [ ] 5.5 Verify restored data matches original
  - [ ] 5.6 Clean up test resources

## Dev Notes

### Architecture Compliance Requirements

**App Location:**
- VolSync operator: `kubernetes/apps/volsync/` (shared - both clusters)
- VolSync R2 component: `kubernetes/components/volsync/r2/`

**Directory Structure:**
```
kubernetes/
├── apps/
│   └── volsync/
│       ├── app/
│       │   ├── helmrelease.yaml
│       │   ├── kustomization.yaml
│       │   └── externalsecret.yaml
│       └── ks.yaml
└── components/
    └── volsync/
        ├── r2/
        │   ├── kustomization.yaml
        │   ├── replicationsource.yaml
        │   └── replicationdestination.yaml
        └── nfs/                         # Future: NFS backup target
            └── kustomization.yaml
```

### HelmRelease Requirements

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: volsync
spec:
  interval: 1h
  chart:
    spec:
      chart: volsync
      version: 0.14.0
      sourceRef:
        kind: HelmRepository
        name: backube
        namespace: flux-system
  install:
    remediation:
      retries: 3
  upgrade:
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
  values:
    manageCRDs: true
```

### Cloudflare R2 Configuration

**R2 Endpoint:** `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
**Bucket Structure:** Each app gets its own path prefix within the volsync bucket

**Secret Format (1Password → ExternalSecret):**
```yaml
RESTIC_REPOSITORY: s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/${VOLSYNC_R2_BUCKET}/${APP}
RESTIC_PASSWORD: <strong-encryption-key>
AWS_ACCESS_KEY_ID: <r2-access-key>
AWS_SECRET_ACCESS_KEY: <r2-secret-key>
```

### ReplicationSource Template Pattern

```yaml
apiVersion: volsync.backube/v1alpha1
kind: ReplicationSource
metadata:
  name: ${APP}-backup
  labels:
    app.kubernetes.io/name: ${APP}
    monosense.dev/backup: "true"
  annotations:
    monosense.dev/snapshot.schedule: "0 */8 * * *"
spec:
  sourcePVC: ${APP}-data   # Replaced via Kustomize
  trigger:
    schedule: "0 */8 * * *"
  restic:
    repository: volsync-r2-secret
    copyMethod: Snapshot   # Preferred - uses CSI snapshots
    pruneIntervalDays: 7
    cacheCapacity: 2Gi
    retain:
      hourly: 24
      daily: 7
```

### ReplicationDestination for Restores

```yaml
apiVersion: volsync.backube/v1alpha1
kind: ReplicationDestination
metadata:
  name: ${APP}-restore
spec:
  trigger:
    manual: restore-${TIMESTAMP}
  restic:
    repository: volsync-r2-secret
    destinationPVC: ${APP}-data-restored
    copyMethod: Direct
    # Optional: restore specific snapshot
    # previous: 2  # 2 snapshots ago
```

### Component Usage in Applications

Applications include the volsync component via ks.yaml:

```yaml
# clusters/apps/apps/business/odoo/ks.yaml
spec:
  components:
    - ../../../../kubernetes/components/volsync/r2
```

With Kustomize replacements:
```yaml
# app/kustomization.yaml
replacements:
  - source:
      kind: HelmRelease
      name: odoo
      fieldPath: metadata.name
    targets:
      - select:
          kind: ReplicationSource
        fieldPaths:
          - spec.sourcePVC
        options:
          delimiter: '-'
          index: 0
```

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR19 | Backup success rate 100% | Monitor ReplicationSource status, alert on failure |
| NFR37 | Cloudflare R2 connectivity | Verify endpoint connectivity before deployment |
| NFR20 | Cluster recovery < 2 hours | Document restore procedure in runbooks |

### Dependencies

- **Hard Dependencies:**
  - `rook-ceph-cluster` - Storage for source PVCs
  - `external-secrets-stores` - 1Password credentials

- **Soft Dependencies:**
  - CSI snapshot controller (usually included with Rook-Ceph)

### Security Considerations

- R2 credentials stored ONLY in 1Password, synced via ExternalSecret
- Restic encrypts all data client-side before sending to R2
- Cloudflare R2 provides at-rest encryption
- No credentials in Git repository

### Project Structure Notes

- Alignment with unified project structure: VolSync follows shared app pattern in `kubernetes/apps/`
- Component follows existing component pattern at `kubernetes/components/volsync/r2/`
- No detected conflicts with architecture patterns

### Testing Considerations

**Manual Test Procedure:**
1. Create test PVC with known data checksum
2. Apply ReplicationSource, wait for backup
3. Verify snapshot in R2 via `task volsync:list`
4. Delete source PVC
5. Apply ReplicationDestination for restore
6. Verify restored data checksum matches

**Automated Validation (tests/smoke/):**
- `dr-volsync-restore.sh` - Scripted restore test (created in Story 7.4)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 7] - Epic and story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#Backup Architecture] - R2 endpoint and bucket structure
- [Source: docs/project-context.md#Storage Class Selection] - StorageClass patterns
- [Source: docs/project-context.md#Naming Patterns] - Backup annotation patterns
- [VolSync Documentation](https://volsync.readthedocs.io/en/stable/usage/restic/index.html) - Restic backup configuration
- [VolSync Helm Chart v0.14.0](https://artifacthub.io/packages/helm/backube-helm-charts/volsync) - Latest chart version
- [GitHub - backube/volsync](https://github.com/backube/volsync) - VolSync project repository

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

