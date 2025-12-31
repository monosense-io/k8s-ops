# Story 3.3: Create Reusable Kustomize Components

Status: ready-for-dev

## Story

As a **platform operator**,
I want **reusable Kustomize components for common patterns**,
So that **applications can compose functionality without duplication and maintain consistency across both clusters**.

## Acceptance Criteria

1. **Given** the repository structure with `kubernetes/components/`
   **When** shared components are created
   **Then** the following components exist:
   - `cnpg/` - CNPG database provisioning (ExternalSecret, CronJob for backups)
   - `volsync/r2/` - VolSync backup to Cloudflare R2
   - `volsync/nfs/` - VolSync backup to NFS
   - `gatus/external/` - External health check endpoint
   - `gatus/internal/` - Internal health check endpoint
   - `dragonfly/` - Dragonfly Redis instance
   - `secpol/` - Standard security policies

2. **And** each component has `kustomization.yaml` with configurable replacements

3. **And** components can be referenced via `spec.components` in Flux Kustomization

4. **And** `kustomize build` with component reference produces valid manifests

## Tasks / Subtasks

- [ ] Task 1: Create Component Directory Structure (AC: #1)
  - [ ] Create `kubernetes/components/` directory if not exists
  - [ ] Create subdirectory for each component type
  - [ ] Create `volsync/` with `r2/` and `nfs/` subdirectories

- [ ] Task 2: Create CNPG Database Provisioning Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/cnpg/kustomization.yaml`
  - [ ] Create `externalsecret.yaml` for `${APP}-pguser-secret` pattern
  - [ ] Create `cronjob.yaml` for backup job (`${APP}-pg-backups`)
  - [ ] Add configurable replacements for APP, NAMESPACE
  - [ ] Follow CNPG Shared Cluster Pattern (host: `postgres-rw.databases.svc.cluster.local`)

- [ ] Task 3: Create VolSync R2 Backup Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/volsync/r2/kustomization.yaml`
  - [ ] Create `replicationsource.yaml` with Restic to R2
  - [ ] Configure R2 endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
  - [ ] Set default schedule: every 8 hours (`0 */8 * * *`)
  - [ ] Set retention: 24 hourly, 7 daily
  - [ ] Add configurable replacements for APP, PVC_NAME

- [ ] Task 4: Create VolSync NFS Backup Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/volsync/nfs/kustomization.yaml`
  - [ ] Create `replicationsource.yaml` with Restic to NFS
  - [ ] Configure NFS destination path
  - [ ] Add configurable replacements for APP, PVC_NAME, NFS_PATH

- [ ] Task 5: Create Gatus External Health Check Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/gatus/external/kustomization.yaml`
  - [ ] Create `configmap.yaml` for Gatus endpoint configuration
  - [ ] Configure for external endpoint (HTTPS via Gateway)
  - [ ] Add `gatus.io/enabled: "true"` label
  - [ ] Add configurable replacements for APP, ENDPOINT

- [ ] Task 6: Create Gatus Internal Health Check Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/gatus/internal/kustomization.yaml`
  - [ ] Create `configmap.yaml` for internal service health check
  - [ ] Configure for internal endpoint (ClusterIP service)
  - [ ] Add configurable replacements for APP, SERVICE, PORT

- [ ] Task 7: Create Dragonfly Redis Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/dragonfly/kustomization.yaml`
  - [ ] Create `dragonfly.yaml` CR for Dragonfly Operator
  - [ ] Configure default resource limits
  - [ ] Add configurable replacements for APP, NAMESPACE

- [ ] Task 8: Create Security Policies Component (AC: #1, #2)
  - [ ] Create `kubernetes/components/secpol/kustomization.yaml`
  - [ ] Create `networkpolicy.yaml` with Tier 2 default-deny pattern
  - [ ] Create `podsecuritypolicy.yaml` or equivalent restrictive settings
  - [ ] Configure `readOnlyRootFilesystem: true`, `runAsNonRoot: true`
  - [ ] Add configurable replacements for APP, NAMESPACE

- [ ] Task 9: Verify Component References Work (AC: #3, #4)
  - [ ] Create test kustomization referencing components
  - [ ] Verify `kustomize build` succeeds for each component
  - [ ] Verify relative path references work from app directories
  - [ ] Test component composition (multiple components together)

- [ ] Task 10: Document Component Usage (AC: #3)
  - [ ] Add usage examples in component README or comments
  - [ ] Document required replacements for each component
  - [ ] Add to project-context.md component usage patterns

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **FRs Covered (Epic 3: GitOps Operations):**
   - FR10: Operator can compose applications using reusable Kustomize components

2. **Kustomize Components Pattern (from architecture.md):**
   ```
   components/
   ├── cnpg/           # CloudNative PostgreSQL
   ├── volsync/        # Backup configuration
   │   ├── r2/         # Cloudflare R2 destination
   │   └── nfs/        # NFS destination
   ├── gatus/          # Health checks
   │   ├── external/   # External endpoints
   │   └── internal/   # Internal endpoints
   ├── dragonfly/      # Redis alternative
   └── secpol/         # Security policies
   ```

3. **Component Usage in ks.yaml:**
   ```yaml
   spec:
     components:
       - ../../../../kubernetes/components/cnpg
       - ../../../../kubernetes/components/volsync/r2
       - ../../../../kubernetes/components/gatus/external
   ```

### Critical Implementation Rules

**From project-context.md:**

1. **CNPG Shared Cluster Pattern:**
   - **One `postgres` cluster per Kubernetes cluster** - NOT per-app clusters
   - Database name = `${APP}` (matches application name)
   - Host endpoint: `postgres-rw.databases.svc.cluster.local`
   - Credentials: `${APP}-pguser-secret` (from External Secrets)
   - Init credentials: `${APP}-initdb-secret`
   - Backup CronJob: `${APP}-pg-backups`

2. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`)
   - Kustomization entry: `kustomization.yaml`

3. **ExternalSecret API Version:**
   - Use `external-secrets.io/v1` (NOT v1beta1)
   - ClusterSecretStore: `onepassword-connect`

4. **Backup Destination:**
   - Cloudflare R2 endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
   - NOT MinIO (MinIO is general S3 only)

5. **Security Rules:**
   - ALWAYS set `readOnlyRootFilesystem: true` where possible
   - ALWAYS drop all capabilities: `capabilities: { drop: ["ALL"] }`
   - ALWAYS run as non-root: `runAsNonRoot: true`

6. **Custom Annotations/Labels:**
   - Prefix: `monosense.dev/`
   - Backup annotation: `monosense.dev/backup: "true"`
   - Snapshot schedule: `monosense.dev/snapshot.schedule: "0 */8 * * *"`

### Project Structure Notes

**Component Location:**
```
kubernetes/components/
├── cnpg/
│   ├── kustomization.yaml
│   ├── cronjob.yaml
│   └── externalsecret.yaml
├── volsync/
│   ├── r2/
│   │   ├── kustomization.yaml
│   │   └── replicationsource.yaml
│   └── nfs/
│       ├── kustomization.yaml
│       └── replicationsource.yaml
├── gatus/
│   ├── external/
│   │   ├── kustomization.yaml
│   │   └── configmap.yaml
│   └── internal/
│       ├── kustomization.yaml
│       └── configmap.yaml
├── dragonfly/
│   ├── kustomization.yaml
│   └── dragonfly.yaml
└── secpol/
    ├── kustomization.yaml
    └── networkpolicy.yaml
```

### Component Templates

**cnpg/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
resources:
  - externalsecret.yaml
  - cronjob.yaml
replacements:
  - source:
      kind: ConfigMap
      name: app-config
      fieldPath: data.APP_NAME
    targets:
      - select:
          kind: ExternalSecret
        fieldPaths:
          - metadata.name
          - spec.target.name
      - select:
          kind: CronJob
        fieldPaths:
          - metadata.name
```

**cnpg/externalsecret.yaml:**
```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: ${APP}-pguser-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: ${APP}-pguser-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: ${APP}-pguser
```

**cnpg/cronjob.yaml:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ${APP}-pg-backups
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: ghcr.io/cloudnative-pg/postgresql:17
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgres-rw.databases.svc.cluster.local \
                    -U ${APP} -d ${APP} > /backup/${APP}-$(date +%Y%m%d%H%M%S).sql
              envFrom:
                - secretRef:
                    name: ${APP}-pguser-secret
```

**volsync/r2/replicationsource.yaml:**
```yaml
apiVersion: volsync.backube/v1alpha1
kind: ReplicationSource
metadata:
  name: ${APP}-r2-backup
  labels:
    monosense.dev/backup: "true"
  annotations:
    monosense.dev/snapshot.schedule: "0 */8 * * *"
spec:
  sourcePVC: ${PVC_NAME}
  trigger:
    schedule: "0 */8 * * *"
  restic:
    pruneIntervalDays: 7
    repository: ${APP}-volsync-r2-secret
    retain:
      hourly: 24
      daily: 7
    copyMethod: Snapshot
    storageClassName: ceph-block
    cacheStorageClassName: ceph-block
```

**gatus/external/configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${APP}-gatus
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    endpoints:
      - name: ${APP}
        url: https://${APP}.${CLUSTER_DOMAIN}/health
        interval: 5m
        conditions:
          - "[STATUS] == 200"
```

**dragonfly/dragonfly.yaml:**
```yaml
apiVersion: dragonflydb.io/v1alpha1
kind: Dragonfly
metadata:
  name: ${APP}-dragonfly
spec:
  replicas: 1
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi
```

**secpol/networkpolicy.yaml:**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: ${APP}-default-deny
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: ${APP}
  ingress:
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: networking
  egress:
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
```

### Previous Story Intelligence

**From Story 3.1 (Flux Operational Taskfiles):**
- `.taskfiles/flux/Taskfile.yaml` structure established
- Multi-cluster context handling with CLUSTER variable
- Preconditions for validation
- Detailed summaries with examples

**From Story 3.2 (Renovate Configuration):**
- File matching patterns for Kubernetes manifests
- Flux manager configuration for HelmRelease/HelmRepository
- Automerge and grouping strategies

**Key Learnings Applied:**
- Use `.yaml` extension consistently
- Follow kebab-case naming conventions
- Include comprehensive examples in documentation
- Validate with `kustomize build` before committing

### Kustomize Component API

**Component Definition (v1alpha1):**
```yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
```

**Reference in Application:**
```yaml
# In app's kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - helmrelease.yaml
components:
  - ../../../../kubernetes/components/cnpg
  - ../../../../kubernetes/components/volsync/r2
```

**Flux Kustomization Reference:**
```yaml
# In ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
spec:
  components:
    - ../../../../kubernetes/components/cnpg
```

### Variable Replacement Patterns

**ConfigMap-based Replacement:**
```yaml
replacements:
  - source:
      kind: ConfigMap
      name: app-config
      fieldPath: data.APP_NAME
    targets:
      - select:
          kind: ExternalSecret
        fieldPaths:
          - metadata.name
```

**Flux Substitution:**
- Components work with Flux `postBuild.substituteFrom`
- Use `${VARIABLE}` syntax in component templates
- Variables resolved from `cluster-vars` ConfigMap

### Verification Commands

```bash
# Verify component structure
ls -la kubernetes/components/

# Test kustomize build for each component
kustomize build kubernetes/components/cnpg
kustomize build kubernetes/components/volsync/r2
kustomize build kubernetes/components/gatus/external
kustomize build kubernetes/components/dragonfly
kustomize build kubernetes/components/secpol

# Test component composition with app
cd kubernetes/apps/business/test-app/app
kustomize build .

# Validate YAML syntax
yamllint kubernetes/components/**/*.yaml
```

### Critical Don't-Miss Rules

1. **Component API Version:**
   - Use `apiVersion: kustomize.config.k8s.io/v1alpha1`
   - Kind: `Component` (not Kustomization)

2. **Path References:**
   - Components use relative paths from consuming app
   - Example: `../../../../kubernetes/components/cnpg`

3. **CNPG Host:**
   - ALWAYS use `postgres-rw.databases.svc.cluster.local`
   - NEVER create per-app CNPG clusters

4. **R2 Endpoint:**
   - Use `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
   - NOT MinIO

5. **Gatus Labels:**
   - ALWAYS include `gatus.io/enabled: "true"` label

6. **Security Defaults:**
   - `readOnlyRootFilesystem: true`
   - `runAsNonRoot: true`
   - `capabilities: { drop: ["ALL"] }`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3: Create Reusable Kustomize Components]
- [Source: _bmad-output/planning-artifacts/architecture.md#Kustomize Components Pattern]
- [Source: docs/project-context.md#Component Usage Pattern]
- [Source: docs/project-context.md#CNPG Shared Cluster Pattern]
- [Kustomize Components Documentation](https://kubectl.docs.kubernetes.io/guides/config_management/components/)
- [FluxCD Kustomization Components](https://fluxcd.io/flux/components/kustomize/kustomizations/#components)
- [VolSync Documentation](https://volsync.readthedocs.io/)
- [Dragonfly Operator](https://www.dragonflydb.io/docs/operator)

### Validation Checklist

Before marking complete, verify:
- [ ] `kubernetes/components/cnpg/` with kustomization.yaml, externalsecret.yaml, cronjob.yaml
- [ ] `kubernetes/components/volsync/r2/` with kustomization.yaml, replicationsource.yaml
- [ ] `kubernetes/components/volsync/nfs/` with kustomization.yaml, replicationsource.yaml
- [ ] `kubernetes/components/gatus/external/` with kustomization.yaml, configmap.yaml
- [ ] `kubernetes/components/gatus/internal/` with kustomization.yaml, configmap.yaml
- [ ] `kubernetes/components/dragonfly/` with kustomization.yaml, dragonfly.yaml
- [ ] `kubernetes/components/secpol/` with kustomization.yaml, networkpolicy.yaml
- [ ] All components use `apiVersion: kustomize.config.k8s.io/v1alpha1` with `kind: Component`
- [ ] `kustomize build` succeeds for each component
- [ ] Components can be referenced via relative path in app kustomization
- [ ] ExternalSecret uses `external-secrets.io/v1` API version
- [ ] CNPG host uses `postgres-rw.databases.svc.cluster.local`
- [ ] VolSync R2 uses correct R2 endpoint

### Git Commit Message Format

```
feat(flux): create reusable Kustomize components for app composition

- Add kubernetes/components/cnpg for database provisioning
- Add kubernetes/components/volsync/r2 for R2 backups
- Add kubernetes/components/volsync/nfs for NFS backups
- Add kubernetes/components/gatus/external and internal for health checks
- Add kubernetes/components/dragonfly for Redis instances
- Add kubernetes/components/secpol for security policies
- FR10: Compose applications using reusable Kustomize components
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

