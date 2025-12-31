# Story 4.2: Deploy CloudNative-PG Operator and Shared Cluster

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want CNPG operator with a shared PostgreSQL cluster,
so that applications can provision databases without managing individual clusters.

## Acceptance Criteria

1. **AC1**: `kubernetes/apps/databases/cloudnative-pg/` directory exists with proper structure:
   - `app/` directory containing operator HelmRelease
   - `cluster/` directory containing shared PostgreSQL Cluster definition
   - `ks.yaml` Flux Kustomization entry point for the operator
   - Properly structured `kustomization.yaml` files

2. **AC2**: CloudNative-PG Operator HelmRelease is configured with:
   - CNPG latest stable version (v1.28.0 as of December 2025)
   - Proper remediation blocks (install retries: -1 for operators, upgrade strategy: rollback)
   - Interval: 1h (per project standards)
   - CRD handling with `install.crds: CreateReplace` and `upgrade.crds: CreateReplace`

3. **AC3**: Shared PostgreSQL Cluster named `postgres` is deployed in `databases` namespace with:
   - 3 replicas for high availability
   - Storage using `openebs-hostpath` StorageClass (local NVMe performance)
   - superuser credentials stored in `postgres-superuser-secret`
   - Standard Kubernetes recommended labels (`app.kubernetes.io/name`, etc.)

4. **AC4**: Backup configuration to Cloudflare R2 is operational:
   - Barman object store configuration pointing to R2
   - WAL archiving enabled for continuous backup
   - Daily scheduled base backups
   - 30-day retention policy
   - bzip2 compression enabled

5. **AC5**: `kubectl cnpg status postgres -n databases` shows healthy cluster with:
   - All 3 instances in `Running` state
   - Primary and replicas properly synchronized
   - WAL archiving functional

6. **AC6**: Application database provisioning pattern is documented and functional:
   - `${APP}-pguser-secret` for app credentials
   - `${APP}-initdb-secret` for database initialization
   - Host endpoint: `postgres-rw.databases.svc.cluster.local`

7. **AC7**: HealthCheckExprs are configured in Flux Kustomization for proper dependency handling

8. **AC8**: CiliumNetworkPolicy is created for database access patterns (Tier 1 platform service)

## Tasks / Subtasks

- [ ] Task 1: Create CloudNative-PG Operator directory structure (AC: #1)
  - [ ] Subtask 1.1: Create `kubernetes/apps/databases/cloudnative-pg/app/` directory
  - [ ] Subtask 1.2: Create `kubernetes/apps/databases/cloudnative-pg/cluster/` directory
  - [ ] Subtask 1.3: Create `kubernetes/apps/databases/cloudnative-pg/ks.yaml` Flux Kustomization for operator
  - [ ] Subtask 1.4: Create `kubernetes/apps/databases/cloudnative-pg/app/kustomization.yaml`
  - [ ] Subtask 1.5: Create separate `ks.yaml` for cluster deployment (cloudnative-pg-cluster)

- [ ] Task 2: Deploy CloudNative-PG Operator (AC: #2)
  - [ ] Subtask 2.1: Create HelmRelease for cloudnative-pg operator
  - [ ] Subtask 2.2: Configure using OCIRepository with `chartRef` pattern (preferred)
  - [ ] Subtask 2.3: Ensure CRD handling with `install.crds: CreateReplace` and `upgrade.crds: CreateReplace`
  - [ ] Subtask 2.4: Set install remediation retries to -1 (operators must succeed)
  - [ ] Subtask 2.5: Set namespace to `databases`

- [ ] Task 3: Create OCIRepository for CNPG Helm chart (AC: #2)
  - [ ] Subtask 3.1: Create OCIRepository in `infrastructure/base/repositories/oci/`
  - [ ] Subtask 3.2: Configure `layerSelector` for Helm chart content type
  - [ ] Subtask 3.3: Reference ghcr.io/cloudnative-pg/charts registry

- [ ] Task 4: Create Shared PostgreSQL Cluster (AC: #3)
  - [ ] Subtask 4.1: Create Cluster CR named `postgres` in `cluster/` directory
  - [ ] Subtask 4.2: Configure 3 replicas with `openebs-hostpath` StorageClass
  - [ ] Subtask 4.3: Set appropriate resource requests and limits
  - [ ] Subtask 4.4: Add standard Kubernetes recommended labels

- [ ] Task 5: Configure Backup to Cloudflare R2 (AC: #4)
  - [ ] Subtask 5.1: Create ExternalSecret for R2 credentials (`cnpg-r2-credentials`)
  - [ ] Subtask 5.2: Configure `backup.barmanObjectStore` with R2 endpoint
  - [ ] Subtask 5.3: Enable WAL archiving with continuous backup
  - [ ] Subtask 5.4: Set daily scheduled backup and 30-day retention
  - [ ] Subtask 5.5: Configure bzip2 compression

- [ ] Task 6: Create Flux Kustomization for Cluster (AC: #7)
  - [ ] Subtask 6.1: Create `cluster/ks.yaml` for cloudnative-pg-cluster
  - [ ] Subtask 6.2: Add dependsOn for cloudnative-pg operator
  - [ ] Subtask 6.3: Add dependsOn for rook-ceph-cluster (storage) and external-secrets (credentials)
  - [ ] Subtask 6.4: Configure healthCheckExprs for Cluster ready status

- [ ] Task 7: Configure Network Policies (AC: #8)
  - [ ] Subtask 7.1: Create CiliumNetworkPolicy allowing ingress from application namespaces
  - [ ] Subtask 7.2: Allow egress to R2 for backups
  - [ ] Subtask 7.3: Allow internal cluster replication traffic

- [ ] Task 8: Document Application Database Provisioning (AC: #6)
  - [ ] Subtask 8.1: Document `${APP}-pguser-secret` pattern
  - [ ] Subtask 8.2: Document `${APP}-initdb-secret` pattern
  - [ ] Subtask 8.3: Ensure pattern is referenceable from `kubernetes/components/cnpg/`

- [ ] Task 9: Validate Deployment (AC: #5)
  - [ ] Subtask 9.1: Verify `kubectl cnpg status postgres -n databases` shows healthy cluster
  - [ ] Subtask 9.2: Verify all 3 instances are running and synchronized
  - [ ] Subtask 9.3: Verify WAL archiving is functional
  - [ ] Subtask 9.4: Verify `kustomize build kubernetes/apps/databases/cloudnative-pg --enable-helm` succeeds

## Dev Notes

### Architecture Context

**Technology Stack:**
- CloudNative-PG v1.28.0 (latest stable as of December 2025)
- PostgreSQL 17.2 (recommended version for CNPG 1.28)
- OpenEBS v4.4 LocalPV Hostpath for storage
- Cloudflare R2 for backups (endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`)

**CNPG v1.28.0 Key Features:**
- Least-privileged reporting capabilities
- TLS for operator metrics (via `METRICS_CERT_DIR`)
- Simultaneous image and config changes support
- Replica auto-recreation with `alpha.cnpg.io/unrecoverable=true` annotation
- Standard Kubernetes labels (`app.kubernetes.io/name`, etc.)
- Postgres 13 no longer supported (minimum is now Postgres 14)

**CNPG Shared Cluster Pattern (CRITICAL - from project-context.md):**
- **One `postgres` cluster per Kubernetes cluster** - NOT per-app clusters
- Database name = `${APP}` (matches application name)
- Host endpoint: `postgres-rw.databases.svc.cluster.local`
- Credentials: `${APP}-pguser-secret` (from External Secrets)
- Init credentials: `${APP}-initdb-secret`
- Backup CronJob: `${APP}-pg-backups`

### Previous Story Context (Story 4.1)

Story 4.1 deployed Envoy Gateway for ingress. Key learnings:
- Uses OCIRepository with `chartRef` pattern (preferred for new apps)
- Follows shared app structure in `kubernetes/apps/`
- Includes proper remediation blocks
- Uses `${CLUSTER_DOMAIN}` variable substitution

### Implementation Patterns

**Directory Structure:**
```
kubernetes/apps/databases/cloudnative-pg/
├── app/
│   ├── helmrelease.yaml          # CNPG operator
│   ├── kustomization.yaml        # Local kustomization
│   └── networkpolicy.yaml        # CiliumNetworkPolicy for operator
├── cluster/
│   ├── cluster.yaml              # PostgreSQL Cluster CR
│   ├── kustomization.yaml        # Local kustomization
│   ├── externalsecret.yaml       # R2 backup credentials
│   ├── scheduledbackup.yaml      # Daily scheduled backup
│   └── networkpolicy.yaml        # CiliumNetworkPolicy for cluster
└── ks.yaml                       # Flux Kustomization for operator
```

**Separate Flux Kustomizations (Required):**
- `cloudnative-pg` - Deploys the operator
- `cloudnative-pg-cluster` - Deploys the shared PostgreSQL cluster (depends on operator)

**OCIRepository Configuration:**
```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: cloudnative-pg
  namespace: flux-system
spec:
  interval: 5m
  url: oci://ghcr.io/cloudnative-pg/charts/cloudnative-pg
  layerSelector:
    mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
    operation: copy
  ref:
    tag: 0.24.0  # Operator chart version (deploys CNPG 1.28.0)
```

**HelmRelease Pattern (REQUIRED for Operator):**
```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: cloudnative-pg
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: cloudnative-pg
    namespace: flux-system
  install:
    crds: CreateReplace
    remediation:
      retries: -1  # Operators must succeed
  upgrade:
    crds: CreateReplace
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
```

**PostgreSQL Cluster Pattern:**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres
  namespace: databases
  labels:
    app.kubernetes.io/name: postgres
    app.kubernetes.io/instance: postgres
    app.kubernetes.io/component: database
    app.kubernetes.io/part-of: k8s-ops
spec:
  instances: 3
  imageName: ghcr.io/cloudnative-pg/postgresql:17.2

  storage:
    storageClass: openebs-hostpath
    size: 20Gi

  postgresql:
    parameters:
      shared_buffers: "256MB"
      max_connections: "200"

  superuserSecret:
    name: postgres-superuser-secret

  backup:
    barmanObjectStore:
      destinationPath: s3://cnpg-${CLUSTER_NAME}/
      endpointURL: https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com
      s3Credentials:
        accessKeyId:
          name: cnpg-r2-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: cnpg-r2-credentials
          key: SECRET_ACCESS_KEY
      wal:
        compression: bzip2
        maxParallel: 2
      data:
        compression: bzip2
    retentionPolicy: "30d"
```

**Flux Kustomization with healthCheckExprs (ks.yaml for cluster):**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name cloudnative-pg-cluster
  namespace: flux-system
spec:
  targetNamespace: databases
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/databases/cloudnative-pg/cluster
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 10m  # Cluster creation can take time
  dependsOn:
    - name: cloudnative-pg
      namespace: flux-system
    - name: external-secrets-stores
      namespace: flux-system
  healthCheckExprs:
    - apiVersion: postgresql.cnpg.io/v1
      kind: Cluster
      failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Critical Implementation Rules

**From project-context.md - MUST FOLLOW:**
1. Use `kustomization.yaml` (not `.yml`) for all Kustomize files
2. Use `helm.toolkit.fluxcd.io/v2` API version (not v2beta1 or v2beta2)
3. Use `external-secrets.io/v1` API version (ESO v1.0.0+)
4. Include remediation blocks in all HelmReleases
5. Use `${VARIABLE_NAME}` syntax for Flux substitution (NOT `$VAR` or `{{VAR}}`)
6. Use OCIRepository with `chartRef` for new apps (preferred pattern)
7. Pin images with `@sha256:` digest where possible
8. Use kebab-case for all resource names
9. Use `monosense.dev/` prefix for custom annotations

**Storage Class Selection:**
- **CNPG PostgreSQL MUST use `openebs-hostpath`** for local NVMe performance
- NOT `ceph-block` - Ceph is for general stateful apps

**Backup Destination:**
- **Backups go to Cloudflare R2** - NOT MinIO
- R2 endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
- Bucket naming: `s3://cnpg-${CLUSTER_NAME}/` (cnpg-infra, cnpg-apps)

**Variable Substitution:**
- `${CLUSTER_NAME}` - `infra` or `apps`
- `${CLUSTER_DOMAIN}` - `monosense.dev` for infra, `monosense.io` for apps

### App Location Rules

- **Location**: `kubernetes/apps/databases/cloudnative-pg/` (shared app for BOTH clusters)
- **Namespace**: `databases`
- Each cluster gets its own `postgres` Cluster instance
- Applications create databases within this shared cluster

### Dependency Chain

```
external-secrets-stores → cloudnative-pg (operator) → cloudnative-pg-cluster
                       ↑
              rook-ceph-cluster (for general storage)
              openebs (for CNPG local storage)
```

### Project Structure Notes

- **Location**: `kubernetes/apps/databases/cloudnative-pg/` (shared app)
- **Namespace**: `databases`
- **Dependencies**: external-secrets (for R2 credentials), openebs (for storage)
- **Dependents**: All database-backed applications (odoo, n8n, authentik, etc.)

### References

- [Source: docs/project-context.md#CNPG Shared Cluster Pattern] - Database naming conventions
- [Source: docs/project-context.md#Storage Class Selection] - openebs-hostpath for CNPG
- [Source: docs/project-context.md#Dependency Rules] - Database-backed apps depend on cloudnative-pg-cluster
- [Source: _bmad-output/planning-artifacts/architecture.md#CNPG Shared Cluster Pattern] - Detailed pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Backup Architecture] - R2 backup configuration
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2] - Original acceptance criteria

### External Documentation

- [CloudNativePG Official Docs](https://cloudnative-pg.io/docs/)
- [CloudNativePG 1.28.0 Release](https://cloudnative-pg.io/releases/cloudnative-pg-1-28.0-released/)
- [CNPG GitHub Releases](https://github.com/cloudnative-pg/cloudnative-pg/releases)
- [OpenEBS Local PV Hostpath](https://openebs.io/docs/user-guides/local-storage-user-guide/local-pv-hostpath/hostpath-overview)
- [CNPG Backup to S3/R2](https://cloudnative-pg.io/docs/1.28/backup_recovery/)

### Latest Version Information (December 2025)

- **CloudNative-PG Operator**: v1.28.0 (released ~3 weeks ago)
- **CNPG Helm Chart**: v0.24.0 (deploys operator 1.28.0)
- **PostgreSQL**: 17.2 (recommended for CNPG 1.28)
- **Key Features in v1.28.0**:
  - Least-privileged reporting
  - TLS for operator metrics
  - Simultaneous image and config changes
  - Replica auto-recreation annotation
  - Standard Kubernetes labels support
  - Postgres 13 deprecated (minimum is Postgres 14)

### Component Integration

**kubernetes/components/cnpg/ Usage:**
Applications using CNPG should reference this component:
```yaml
components:
  - ../../../../kubernetes/components/cnpg
```

The component provides:
- ExternalSecret template for `${APP}-pguser-secret`
- ExternalSecret template for `${APP}-initdb-secret`
- CronJob template for `${APP}-pg-backups`

### Verification Commands

```bash
# Check operator deployment
kubectl get pods -n databases -l app.kubernetes.io/name=cloudnative-pg

# Check cluster status
kubectl cnpg status postgres -n databases

# Verify backup configuration
kubectl get scheduledbackup -n databases

# Check WAL archiving
kubectl cnpg backup postgres -n databases  # Trigger manual backup

# Validate kustomize build
kustomize build kubernetes/apps/databases/cloudnative-pg --enable-helm
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

