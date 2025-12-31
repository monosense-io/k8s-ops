# Story 5.3: Deploy Business Applications to Apps Cluster

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want business applications deployed to the apps cluster,
so that production workloads run on the appropriate cluster with proper isolation from platform services.

## Acceptance Criteria

1. **AC1**: Odoo ERP is deployed and accessible:
   - `clusters/apps/apps/business/odoo/` directory structure exists with all required files
   - HelmRelease using Bitnami Odoo chart v28.x successfully deployed
   - Odoo accessible via `odoo.monosense.io`
   - Uses shared CNPG cluster via `odoo-pguser-secret` pattern
   - CiliumNetworkPolicy for Tier 2 isolation configured

2. **AC2**: n8n workflow automation is deployed and accessible:
   - `clusters/apps/apps/business/n8n/` directory structure exists with all required files
   - HelmRelease using community-charts/n8n v1.16.x successfully deployed
   - n8n accessible via `n8n.monosense.io`
   - Uses shared CNPG cluster via `n8n-pguser-secret` pattern
   - CiliumNetworkPolicy for Tier 2 isolation configured

3. **AC3**: ArsipQ application deployment is configured:
   - `clusters/apps/apps/business/arsipq/` directory structure exists
   - Flux Kustomization referencing external arsipq-backend manifests configured
   - ArsipQ accessible via `arsipq.monosense.io`
   - Uses shared CNPG cluster via `arsipq-pguser-secret` pattern
   - CiliumNetworkPolicy for Tier 2 isolation configured

4. **AC4**: All apps use shared CNPG cluster pattern:
   - Database credentials stored via ExternalSecret → 1Password
   - Database host: `postgres-rw.databases.svc.cluster.local`
   - Each app uses `${APP}-pguser-secret` naming pattern
   - Each app uses `${APP}-initdb-secret` for database initialization
   - CNPG healthCheckExprs configured in each app's ks.yaml

5. **AC5**: All apps have CiliumNetworkPolicy for Tier 2 isolation:
   - Default-deny policy applied (from cluster-wide policy)
   - App-specific ingress rules allow traffic from Gateway
   - App-specific egress rules allow PostgreSQL, DNS, external APIs
   - Metrics scraping allowed from observability namespace

6. **AC6**: All apps are accessible via Gateway API routing:
   - HTTPRoute resources created for each app
   - Routes reference `envoy-gateway-external` Gateway
   - TLS termination using wildcard certificate
   - External access via Cloudflare Tunnel

7. **AC7**: Authentik SSO (from infra cluster) works for apps cluster applications:
   - Cross-cluster SSO configuration documented
   - Apps configured to use `authentik.monosense.dev` as OIDC provider
   - SSO integration tested for at least one application

8. **AC8**: VolSync backups configured for stateful applications:
   - ReplicationSource created for apps with persistent data
   - Backups target Cloudflare R2
   - Schedule: every 8 hours (default)
   - Retention: 24 hourly, 7 daily snapshots

## Tasks / Subtasks

- [ ] Task 1: Create Odoo deployment (AC: #1, #4, #5, #6, #8)
  - [ ] Subtask 1.1: Create directory structure `clusters/apps/apps/business/odoo/`
  - [ ] Subtask 1.2: Create ExternalSecret for `odoo-pguser-secret` and `odoo-initdb-secret`
  - [ ] Subtask 1.3: Create HelmRelease with Bitnami Odoo chart
  - [ ] Subtask 1.4: Create HTTPRoute for `odoo.monosense.io`
  - [ ] Subtask 1.5: Create CiliumNetworkPolicy for Odoo namespace
  - [ ] Subtask 1.6: Create ks.yaml with CNPG healthCheckExprs and dependencies
  - [ ] Subtask 1.7: Configure VolSync ReplicationSource for Odoo PVC
  - [ ] Subtask 1.8: Verify Odoo is accessible and functional

- [ ] Task 2: Create n8n deployment (AC: #2, #4, #5, #6, #8)
  - [ ] Subtask 2.1: Create directory structure `clusters/apps/apps/business/n8n/`
  - [ ] Subtask 2.2: Create ExternalSecret for `n8n-pguser-secret` and `n8n-initdb-secret`
  - [ ] Subtask 2.3: Create HelmRelease with community-charts/n8n chart
  - [ ] Subtask 2.4: Create HTTPRoute for `n8n.monosense.io`
  - [ ] Subtask 2.5: Create CiliumNetworkPolicy for n8n namespace
  - [ ] Subtask 2.6: Create ks.yaml with CNPG healthCheckExprs and dependencies
  - [ ] Subtask 2.7: Configure VolSync ReplicationSource for n8n PVC
  - [ ] Subtask 2.8: Verify n8n is accessible and functional

- [ ] Task 3: Create ArsipQ deployment (AC: #3, #4, #5, #6)
  - [ ] Subtask 3.1: Create directory structure `clusters/apps/apps/business/arsipq/`
  - [ ] Subtask 3.2: Create ExternalSecret for `arsipq-pguser-secret` and `arsipq-initdb-secret`
  - [ ] Subtask 3.3: Create Flux Kustomization referencing arsipq-backend manifests
  - [ ] Subtask 3.4: Create HTTPRoute for `arsipq.monosense.io`
  - [ ] Subtask 3.5: Create CiliumNetworkPolicy for ArsipQ namespace
  - [ ] Subtask 3.6: Create ks.yaml with CNPG healthCheckExprs and dependencies
  - [ ] Subtask 3.7: Verify ArsipQ is accessible and functional

- [ ] Task 4: Configure Authentik SSO integration (AC: #7)
  - [ ] Subtask 4.1: Document cross-cluster SSO configuration
  - [ ] Subtask 4.2: Configure at least one app to use Authentik OIDC
  - [ ] Subtask 4.3: Verify SSO login flow works end-to-end

- [ ] Task 5: Verify all deployments (AC: #1-8)
  - [ ] Subtask 5.1: Run `flux get kustomization -n flux-system` and verify all are Ready
  - [ ] Subtask 5.2: Run `kubectl get hr -A` and verify all HelmReleases are Ready
  - [ ] Subtask 5.3: Test external access to each application via browser
  - [ ] Subtask 5.4: Verify database connectivity for each application
  - [ ] Subtask 5.5: Verify VolSync backup jobs complete successfully

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Deploy the business-critical production applications to the apps cluster. These are the applications that serve actual business needs (ERP, workflow automation, custom apps) and need to be isolated from platform services running on the infra cluster.

**Why Apps Cluster:**
- Business applications isolated from platform infrastructure
- Staged rollout: changes validated on infra cluster 24h before apps cluster
- Resource isolation: business workloads don't compete with observability stack
- Blast radius containment: platform issues don't affect business apps

**Cluster Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                         APPS CLUSTER                             │
│  Network: 10.25.13.0/24 | Branch: release | Cilium ID: 2        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │      ODOO        │  │       N8N        │  │    ARSIPQ      │ │
│  │  (Business ERP)  │  │ (Workflow Auto)  │  │ (Custom App)   │ │
│  │                  │  │                  │  │                │ │
│  │  odoo.monosense  │  │  n8n.monosense   │  │ arsipq.mono    │ │
│  │      .io         │  │      .io         │  │   sense.io     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘ │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                    ┌────────────▼─────────────┐                 │
│                    │   SHARED CNPG CLUSTER    │                 │
│                    │   postgres-rw.databases  │                 │
│                    │      .svc.cluster.local  │                 │
│                    └──────────────────────────┘                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  OBSERVABILITY (Remote-Write to Infra)                    │   │
│  │  VMAgent + Fluent-bit → infra.monosense.dev              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                    Cross-cluster SSO
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                        INFRA CLUSTER                             │
│  Authentik SSO: authentik.monosense.dev                         │
└─────────────────────────────────────────────────────────────────┘
```

### Previous Story Context (Story 5.2)

**Completed Infrastructure:**
- Apps cluster references `release` branch (not `main`)
- 24-hour staged rollout workflow configured
- `task flux:override-staged-rollout` available for emergencies

**Key Configuration from Story 5.2:**
- Apps cluster Flux sources from `release` branch
- Changes on `main` go to infra first, then 24h later to apps
- Manual override available via GitHub Actions workflow_dispatch

### CNPG Shared Cluster Pattern (CRITICAL)

**DO NOT create per-app PostgreSQL clusters!** All apps use the shared cluster:

```yaml
# Database connection pattern for all apps
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: odoo-pguser-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: odoo-pguser-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: cnpg-odoo  # 1Password item for this app
```

**1Password Item Structure:**
Each app needs a 1Password item with fields:
- `host`: `postgres-rw.databases.svc.cluster.local`
- `port`: `5432`
- `database`: `${APP}` (e.g., `odoo`, `n8n`, `arsipq`)
- `username`: `${APP}` (e.g., `odoo`, `n8n`, `arsipq`)
- `password`: (generated secure password)

### Application Directory Structure

**Standard structure for apps-cluster-only apps:**

```
clusters/apps/apps/business/{app}/
├── app/
│   ├── helmrelease.yaml          # HelmRelease definition
│   ├── kustomization.yaml        # Local kustomization
│   ├── externalsecret.yaml       # Secret references
│   ├── networkpolicy.yaml        # CiliumNetworkPolicy
│   └── httproute.yaml            # Gateway API route
└── ks.yaml                       # Flux Kustomization entry point
```

### HelmRelease Configurations

#### Odoo (Bitnami Chart v28.x)

```yaml
# clusters/apps/apps/business/odoo/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: odoo
spec:
  interval: 1h
  chart:
    spec:
      chart: odoo
      version: "28.x.x"  # Pin to specific version
      sourceRef:
        kind: HelmRepository
        name: bitnami
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
    # External PostgreSQL (shared CNPG cluster)
    postgresql:
      enabled: false
    externalDatabase:
      host: postgres-rw.databases.svc.cluster.local
      port: 5432
      user: odoo
      database: odoo
      existingSecret: odoo-pguser-secret
      existingSecretPasswordKey: password

    # Resource configuration (adjust based on worker count)
    resources:
      requests:
        memory: "2Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "2000m"

    # Persistence
    persistence:
      enabled: true
      storageClass: ceph-block
      size: 50Gi

    # Ingress disabled (using Gateway API)
    ingress:
      enabled: false

    # Security context
    podSecurityContext:
      fsGroup: 1001
    containerSecurityContext:
      runAsUser: 1001
      runAsNonRoot: true
```

**Odoo Resource Sizing:**
- Worker formula: `(#CPU_CORES * 2) + 1`
- Memory per worker: 2GB request, 2.5GB limit
- For basic setup: 1 worker = 2GB RAM

#### n8n (Community Chart v1.16.x)

```yaml
# clusters/apps/apps/business/n8n/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: n8n
spec:
  interval: 1h
  chart:
    spec:
      chart: n8n
      version: "1.16.x"  # Pin to specific version
      sourceRef:
        kind: HelmRepository
        name: community-charts
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
    # External PostgreSQL (shared CNPG cluster)
    postgresql:
      enabled: false
    externalPostgresql:
      host: postgres-rw.databases.svc.cluster.local
      port: 5432
      user: n8n
      database: n8n
      existingSecret: n8n-pguser-secret
      existingSecretPasswordKey: password

    # Resource configuration (production basic)
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "2000m"

    # Persistence
    persistence:
      enabled: true
      storageClass: ceph-block
      size: 10Gi

    # Ingress disabled (using Gateway API)
    ingress:
      enabled: false

    # n8n specific
    config:
      executions:
        pruneData: "true"
        pruneDataMaxAge: 336  # 14 days in hours
```

**n8n Resource Notes:**
- Memory is more important than CPU for n8n
- Baseline idle: ~100MB, typical: ~180MB
- Set N8N_PAYLOAD_SIZE_MAX based on memory (4GB = 128MB)

#### ArsipQ (Custom Application)

ArsipQ is a custom Spring Boot application - no Helm chart available. Use Kustomize referencing external manifests:

```yaml
# clusters/apps/apps/business/arsipq/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name arsipq
  namespace: flux-system
spec:
  targetNamespace: business
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/apps/apps/business/arsipq/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  dependsOn:
    - name: cloudnative-pg-cluster
      namespace: flux-system
    - name: authentik
      namespace: flux-system
  healthCheckExprs:
    - apiVersion: postgresql.cnpg.io/v1
      kind: Cluster
      failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

**ArsipQ Deployment Option 1: Reference External Repo**
```yaml
# If arsipq-backend has K8s manifests
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: arsipq-backend
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/arsipq-backend
  ref:
    branch: main
  secretRef:
    name: github-deploy-key
```

**ArsipQ Deployment Option 2: Inline Manifests**
```yaml
# clusters/apps/apps/business/arsipq/app/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arsipq
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: arsipq
  template:
    metadata:
      labels:
        app.kubernetes.io/name: arsipq
      annotations:
        reloader.stakater.com/auto: "true"
    spec:
      containers:
        - name: arsipq
          image: ghcr.io/your-org/arsipq:v1.0.0@sha256:...
          ports:
            - containerPort: 8080
          env:
            - name: SPRING_DATASOURCE_URL
              value: "jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/arsipq"
            - name: SPRING_DATASOURCE_USERNAME
              valueFrom:
                secretKeyRef:
                  name: arsipq-pguser-secret
                  key: username
            - name: SPRING_DATASOURCE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: arsipq-pguser-secret
                  key: password
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          securityContext:
            runAsNonRoot: true
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
```

### Gateway API HTTPRoute Pattern

```yaml
# Standard HTTPRoute template for all apps
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: odoo  # or n8n, arsipq
spec:
  parentRefs:
    - name: envoy-gateway-external  # Apps cluster gateway
      namespace: networking
      sectionName: https
  hostnames:
    - "odoo.${CLUSTER_DOMAIN}"  # Flux substitutes to monosense.io
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: odoo
          port: 8069  # Odoo default port
```

**Gateway Names per Cluster:**
| Cluster | External Gateway | Domain |
|---------|------------------|--------|
| infra | `envoy-external` | `*.monosense.dev` |
| apps | `envoy-gateway-external` | `*.monosense.io` |

### CiliumNetworkPolicy Pattern

```yaml
# clusters/apps/apps/business/odoo/app/networkpolicy.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: odoo
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: odoo

  # Ingress rules
  ingress:
    # Allow from Envoy Gateway
    - fromEndpoints:
        - matchLabels:
            app.kubernetes.io/name: envoy
      toPorts:
        - ports:
            - port: "8069"
              protocol: TCP

    # Allow metrics scraping from observability
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: observability
      toPorts:
        - ports:
            - port: "9090"  # Metrics port if exposed
              protocol: TCP

  # Egress rules
  egress:
    # Allow DNS
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP

    # Allow PostgreSQL
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: databases
            cnpg.io/cluster: postgres
      toPorts:
        - ports:
            - port: "5432"
              protocol: TCP

    # Allow external HTTPS (for SMTP, webhooks, etc.)
    - toCIDR:
        - 0.0.0.0/0
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
```

### Flux Kustomization (ks.yaml) Template

```yaml
# clusters/apps/apps/business/odoo/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name odoo
  namespace: flux-system
spec:
  targetNamespace: business
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  components:
    - ../../../../kubernetes/components/cnpg       # Database component
    - ../../../../kubernetes/components/volsync/r2 # Backup to R2
    - ../../../../kubernetes/components/gatus/external  # Health check
  path: ./clusters/apps/apps/business/odoo/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  dependsOn:
    - name: cloudnative-pg-cluster
      namespace: flux-system
    - name: authentik
      namespace: flux-system
  healthCheckExprs:
    - apiVersion: postgresql.cnpg.io/v1
      kind: Cluster
      failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Cross-Cluster SSO Configuration

Authentik runs on infra cluster but serves both clusters:

```yaml
# Apps on apps cluster configure OIDC to point to infra cluster Authentik
# Example for n8n OAuth2 configuration
config:
  oauth2:
    enable: true
    clientId: ${N8N_OAUTH2_CLIENT_ID}
    clientSecret: ${N8N_OAUTH2_CLIENT_SECRET}
    authorizationUrl: https://authentik.monosense.dev/application/o/authorize/
    tokenUrl: https://authentik.monosense.dev/application/o/token/
    userInfoUrl: https://authentik.monosense.dev/application/o/userinfo/
    scope: openid email profile
```

**SSO Network Flow:**
```
Browser → odoo.monosense.io → redirect to → authentik.monosense.dev
                                                      ↓
                                               (SSO login)
                                                      ↓
                                             redirect back to
                                                      ↓
                                            odoo.monosense.io
```

### VolSync Backup Configuration

```yaml
# Use the volsync/r2 component, configure per-app via replacements
# kubernetes/components/volsync/r2/replicationsource.yaml template

apiVersion: volsync.backube/v1alpha1
kind: ReplicationSource
metadata:
  name: ${APP}-backup
spec:
  sourcePVC: ${APP}-data  # PVC name
  trigger:
    schedule: "0 */8 * * *"  # Every 8 hours
  restic:
    pruneIntervalDays: 1
    repository: ${APP}-restic-secret
    retain:
      hourly: 24
      daily: 7
    copyMethod: Snapshot
    storageClassName: ceph-block
    moverSecurityContext:
      runAsUser: 1001
      fsGroup: 1001
```

### Project Structure Notes

**Files to Create:**

| Path | Purpose |
|------|---------|
| `clusters/apps/apps/business/odoo/ks.yaml` | Flux Kustomization entry point |
| `clusters/apps/apps/business/odoo/app/helmrelease.yaml` | Odoo HelmRelease |
| `clusters/apps/apps/business/odoo/app/kustomization.yaml` | Local kustomization |
| `clusters/apps/apps/business/odoo/app/externalsecret.yaml` | Database secrets |
| `clusters/apps/apps/business/odoo/app/networkpolicy.yaml` | Network isolation |
| `clusters/apps/apps/business/odoo/app/httproute.yaml` | Gateway API route |
| `clusters/apps/apps/business/n8n/...` | Same structure as Odoo |
| `clusters/apps/apps/business/arsipq/...` | Same structure, but with deployment instead of HelmRelease |

**Namespace Organization:**
All business apps deploy to the `business` namespace on apps cluster.

### Critical Technical Details

**Version Requirements:**
| Application | Chart/Version | Notes |
|-------------|---------------|-------|
| Odoo | Bitnami 28.x | PostgreSQL subchart disabled, use external |
| n8n | community-charts 1.16.x | Valkey chart replaced with official (breaking change) |
| ArsipQ | Custom | Pin image with @sha256 digest |

**Image Pinning (Required):**
```yaml
image:
  repository: docker.io/bitnami/odoo
  tag: 18.0.20241217@sha256:abc123...  # Always include digest
```

**ExternalSecret API Version:**
```yaml
apiVersion: external-secrets.io/v1  # NOT v1beta1
```

### Verification Commands

```bash
# Check all business apps Flux Kustomizations
flux get kustomization -n flux-system --context apps | grep -E "odoo|n8n|arsipq"

# Check all HelmReleases in business namespace
kubectl --context apps get hr -n business

# Verify database connectivity for each app
kubectl --context apps exec -n business deploy/odoo -- \
  psql -h postgres-rw.databases.svc.cluster.local -U odoo -d odoo -c "SELECT 1"

# Verify network policies
kubectl --context apps get ciliumnetworkpolicy -n business

# Verify external access
curl -I https://odoo.monosense.io
curl -I https://n8n.monosense.io
curl -I https://arsipq.monosense.io

# Verify VolSync backups
kubectl --context apps get replicationsource -n business
kubectl --context apps get replicationsource -n business -o jsonpath='{.items[*].status.lastSyncTime}'

# Verify Gatus health checks
kubectl --context apps get configmap -n observability -l gatus.io/enabled=true
```

### Anti-Patterns to Avoid

1. **DO NOT** create per-app CNPG clusters - use the shared `postgres` cluster
2. **DO NOT** hardcode domain names - use `${CLUSTER_DOMAIN}` substitution
3. **DO NOT** use `envoy-external` on apps cluster - use `envoy-gateway-external`
4. **DO NOT** skip CiliumNetworkPolicy - all Tier 2 apps need explicit policies
5. **DO NOT** skip healthCheckExprs for CNPG-backed apps
6. **DO NOT** use v1beta1 API versions - use `external-secrets.io/v1` and `helm.toolkit.fluxcd.io/v2`
7. **DO NOT** deploy to infra cluster - business apps go to apps cluster only
8. **DO NOT** forget image digest pinning - always use `@sha256:` suffix

### Edge Cases to Handle

**Scenario: Database not ready when app deploys**
- ks.yaml `dependsOn: cloudnative-pg-cluster` prevents this
- healthCheckExprs provides additional verification

**Scenario: Authentik (infra cluster) unavailable**
- Apps still function for existing sessions
- New logins fail until Authentik recovers
- Consider Authentik HA deployment on infra cluster

**Scenario: Gateway route conflicts**
- Each app has unique hostname - no path-based routing conflicts
- Use `sectionName: https` to ensure TLS

**Scenario: VolSync backup fails**
- Check R2 credentials in ExternalSecret
- Verify PVC exists and is bound
- Check Restic secret configuration

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#App Location Rules (CRITICAL)] - Apps cluster only deployment
- [Source: _bmad-output/planning-artifacts/architecture.md#CNPG Shared Cluster Pattern] - Database pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5: Network Policy Pattern] - Tier 2 isolation
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3] - Original acceptance criteria
- [Source: docs/project-context.md#Gateway API Routing] - Gateway names per cluster
- [Source: docs/project-context.md#CNPG Shared Cluster Pattern] - Database credentials pattern
- [Source: 5-2-implement-branch-based-staged-rollout.md] - Previous story context

### External Documentation

- [Bitnami Odoo Helm Chart](https://artifacthub.io/packages/helm/bitnami/odoo) - v28.x
- [n8n Community Helm Chart](https://artifacthub.io/packages/helm/n8n/n8n) - v1.16.x
- [Flux CD HelmRelease Guide](https://fluxcd.io/flux/components/helm/helmreleases/)
- [Gateway API HTTPRoute](https://gateway-api.sigs.k8s.io/api-types/httproute/)
- [CiliumNetworkPolicy Reference](https://docs.cilium.io/en/stable/network/kubernetes/policy/)
- [VolSync ReplicationSource](https://volsync.readthedocs.io/en/stable/usage/restic/index.html)
- [External Secrets Operator v1](https://external-secrets.io/latest/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
