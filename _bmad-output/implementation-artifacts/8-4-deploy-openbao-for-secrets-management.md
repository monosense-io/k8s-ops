# Story 8.4: Deploy OpenBao for Secrets Management

Status: ready-for-dev

---

## Story

As a **developer**,
I want **OpenBao for application secrets management**,
So that **Spring Boot applications can retrieve secrets at runtime**.

---

## Acceptance Criteria

1. **Given** storage is operational
   **When** OpenBao is deployed
   **Then** `clusters/infra/apps/platform/openbao/` contains:
   - OpenBao deployment (latest version 2.2.0+)
   - Persistent storage for vault data
   - HTTPRoute for API and UI access
   - Auto-unseal configuration (or documented manual unseal)

2. **Given** OpenBao is deployed
   **When** initialization is complete
   **Then** OpenBao is initialized and unsealed

3. **Given** OpenBao is unsealed
   **When** accessing the API
   **Then** secrets can be read/written via CLI and API

4. **Given** OpenBao is operational
   **When** pods need access
   **Then** Kubernetes auth method is configured for pod authentication

5. **Given** OpenBao is accessible
   **When** accessing UI
   **Then** OpenBao UI is accessible via `openbao.monosense.dev`

---

## Tasks / Subtasks

- [ ] **Task 1: Configure Persistent Storage** (AC: #1)
  - [ ] 1.1 Determine storage class: `ceph-block` for RWO volume
  - [ ] 1.2 Configure PVC with 10Gi initial size (data storage)
  - [ ] 1.3 Configure audit log storage (optional, for production audit trails)
  - [ ] 1.4 Verify PVC is bound after deployment

- [ ] **Task 2: Configure OpenBao Secrets in 1Password** (AC: #1)
  - [ ] 2.1 Create 1Password item `openbao` with initial admin token (placeholder until init)
  - [ ] 2.2 Create ExternalSecret `openbao-secret` for any pre-configured credentials
  - [ ] 2.3 Document unseal key storage procedure (store unseal keys securely in 1Password after init)

- [ ] **Task 3: Create OpenBao Deployment** (AC: #1, #2)
  - [ ] 3.1 Create directory structure `clusters/infra/apps/platform/openbao/app/`
  - [ ] 3.2 Create `helmrelease.yaml` using OpenBao Helm chart 0.23.0
  - [ ] 3.3 Configure standalone mode initially (can upgrade to HA later)
  - [ ] 3.4 Configure Raft storage backend for data persistence
  - [ ] 3.5 Configure health check endpoints (`/v1/sys/health`)
  - [ ] 3.6 Set resource requests/limits (CPU: 250m/500m, Memory: 256Mi/512Mi)
  - [ ] 3.7 Create `kustomization.yaml` for app directory
  - [ ] 3.8 Create `ks.yaml` Flux Kustomization entry point with dependencies
  - [ ] 3.9 Verify pod is running: `kubectl get po -n arsipq-platform -l app.kubernetes.io/name=openbao`

- [ ] **Task 4: Initialize and Unseal OpenBao** (AC: #2, #3)
  - [ ] 4.1 Execute `kubectl exec -ti openbao-0 -- bao operator init` to initialize
  - [ ] 4.2 Securely store unseal keys in 1Password vault (5 keys, threshold 3)
  - [ ] 4.3 Store root token securely in 1Password
  - [ ] 4.4 Unseal OpenBao using 3 of 5 unseal keys
  - [ ] 4.5 Verify unsealed status: `bao status`
  - [ ] 4.6 Document manual unseal procedure for pod restarts
  - [ ] 4.7 (Optional) Configure auto-unseal using static key or transit (if external KMS available)

- [ ] **Task 5: Configure External Access** (AC: #5)
  - [ ] 5.1 Create `httproute.yaml` for Gateway API routing
  - [ ] 5.2 Reference Gateway `envoy-external` in namespace `networking`
  - [ ] 5.3 Configure hostname `openbao.${CLUSTER_DOMAIN}` using Flux variable substitution
  - [ ] 5.4 Configure path matching for API (`/v1/*`) and UI (`/ui/*`)
  - [ ] 5.5 Verify external access via `https://openbao.monosense.dev`

- [ ] **Task 6: Configure Kubernetes Auth Method** (AC: #4)
  - [ ] 6.1 Enable Kubernetes auth method: `bao auth enable kubernetes`
  - [ ] 6.2 Configure Kubernetes auth with cluster CA and token reviewer JWT
  - [ ] 6.3 Create policy for ArsipQ applications to read secrets
  - [ ] 6.4 Create role binding `arsipq-app` for service accounts in `arsipq-platform` namespace
  - [ ] 6.5 Test authentication from a pod using service account token
  - [ ] 6.6 Document authentication configuration for developers

- [ ] **Task 7: Configure Network Policy** (AC: related to security)
  - [ ] 7.1 Create `networkpolicy.yaml` with CiliumNetworkPolicy for Tier 2 isolation
  - [ ] 7.2 Allow ingress from Gateway namespace (`networking`)
  - [ ] 7.3 Allow ingress from application namespaces needing secrets (`arsipq-platform`, `business`)
  - [ ] 7.4 Allow ingress from observability namespace for metrics scraping
  - [ ] 7.5 Allow egress for DNS resolution

- [ ] **Task 8: Create Initial Secrets Structure** (AC: #3)
  - [ ] 8.1 Enable KV secrets engine v2: `bao secrets enable -path=secret kv-v2`
  - [ ] 8.2 Create initial secrets structure for ArsipQ apps: `secret/arsipq/<app-name>`
  - [ ] 8.3 Create policy `arsipq-read` allowing read access to `secret/data/arsipq/*`
  - [ ] 8.4 Verify secret read/write operations work
  - [ ] 8.5 Document secret path conventions for developers

- [ ] **Task 9: Configure Monitoring Integration**
  - [ ] 9.1 Verify `/v1/sys/health` endpoint responds correctly (200 for unsealed, 503 for sealed)
  - [ ] 9.2 Configure Prometheus/VictoriaMetrics metrics endpoint if available
  - [ ] 9.3 Add Gatus health check ConfigMap for `openbao.monosense.dev`
  - [ ] 9.4 Add Gatus internal check for `/v1/sys/health` endpoint

---

## Dev Notes

### Latest Version Information (December 2025)

Based on web research:
- **OpenBao latest version:** 2.2.0 (build date: 2025-03-05)
- **Helm chart latest version:** 0.23.0 (released December 30, 2025)
- **Docker image:** `quay.io/openbao/openbao:2.2.0`
- **Helm repo:** `https://openbao.github.io/openbao-helm`
- **OCI registry:** `oci://ghcr.io/openbao/charts/openbao`

**Prerequisites:**
- Kubernetes 1.30+ (earliest tested)
- Helm 3.12+ (earliest tested)

### Deployment Modes

OpenBao Helm chart supports four deployment modes:
1. **Dev mode:** Single server with memory storage (NOT for production)
2. **Standalone (default):** Single server with file storage (acceptable for start)
3. **HA mode:** Three servers with Raft integrated storage (recommended for production)
4. **External mode:** Agent injector only, connects to external OpenBao

**RECOMMENDATION:** Start with **Standalone mode** with Raft storage for this initial deployment. Can upgrade to HA mode later if needed.

### Storage Configuration

```yaml
server:
  dataStorage:
    enabled: true
    size: 10Gi
    storageClass: ceph-block  # Use Rook-Ceph for persistence
    accessMode: ReadWriteOnce
  auditStorage:
    enabled: true
    size: 5Gi
    storageClass: ceph-block
    mountPath: "/openbao/audit"
```

### Auto-Unseal Options

**Available Options:**
1. **Shamir's Secret Sharing (Manual):** Default, requires manual unseal after pod restart
2. **Cloud KMS (AWS/GCP/Azure):** Auto-unseal using cloud provider KMS
3. **Transit Secrets Engine:** Auto-unseal using another Vault/OpenBao instance
4. **Static Key (New in 2.4.0):** Auto-unseal using statically injected secrets (experimental)

**IMPORTANT:** For this home lab deployment without cloud KMS:
- Use **manual Shamir unseal** initially
- Store unseal keys securely in 1Password
- Document the unseal procedure in runbook
- Consider Transit auto-unseal if another secrets manager is available

**Recovery Keys Warning:** Recovery keys cannot decrypt the root key. If auto-unseal mechanism becomes unavailable, there's no way to recover access until mechanism is restored.

### Architecture Constraints

From `docs/project-context.md` and architecture document:

| Constraint | Value |
|------------|-------|
| Location | `clusters/infra/apps/platform/openbao/` (infra cluster only) |
| Namespace | `arsipq-platform` |
| Storage | `ceph-block` StorageClass for persistent data |
| External Domain | `openbao.monosense.dev` |
| Gateway | `envoy-external` in `networking` namespace |
| Functional Requirement | FR72: Developer can store application secrets in OpenBao |

### HelmRelease Template

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: openbao
spec:
  interval: 1h
  chart:
    spec:
      chart: openbao
      version: 0.23.0
      sourceRef:
        kind: HelmRepository
        name: openbao
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
    global:
      openshift: false

    # Standalone mode with Raft storage
    server:
      enabled: true
      image:
        repository: quay.io/openbao/openbao
        tag: "2.2.0"

      # Resource limits
      resources:
        requests:
          cpu: 250m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi

      # Data storage
      dataStorage:
        enabled: true
        size: 10Gi
        storageClass: ceph-block
        accessMode: ReadWriteOnce

      # Audit storage
      auditStorage:
        enabled: true
        size: 5Gi
        storageClass: ceph-block

      # Standalone with Raft
      standalone:
        enabled: true
        config: |
          ui = true
          listener "tcp" {
            tls_disable = 1
            address = "[::]:8200"
            cluster_address = "[::]:8201"
          }
          storage "raft" {
            path = "/openbao/data"
          }
          service_registration "kubernetes" {}

      # Security context
      statefulSet:
        securityContext:
          pod:
            fsGroup: 1000
            runAsGroup: 1000
            runAsNonRoot: true
            runAsUser: 100
          container:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL

      # Service configuration
      service:
        enabled: true
        type: ClusterIP
        port: 8200

      # Readiness and liveness probes
      readinessProbe:
        enabled: true
        path: "/v1/sys/health?standbyok=true"
        initialDelaySeconds: 5
      livenessProbe:
        enabled: true
        path: "/v1/sys/health?standbyok=true"
        initialDelaySeconds: 60

      # Pod annotations
      annotations:
        reloader.stakater.com/auto: "true"

    # Injector disabled for now (can enable later)
    injector:
      enabled: false

    # UI enabled
    ui:
      enabled: true
      serviceType: ClusterIP
```

### Directory Structure

```
clusters/infra/apps/platform/openbao/
├── app/
│   ├── helmrelease.yaml      # OpenBao deployment via Helm chart
│   ├── httproute.yaml        # External access via Gateway API
│   ├── networkpolicy.yaml    # CiliumNetworkPolicy
│   ├── helmrepository.yaml   # OpenBao Helm repo definition
│   └── kustomization.yaml
└── ks.yaml                   # Flux Kustomization entry point
```

### HelmRepository Definition

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: openbao
  namespace: flux-system
spec:
  interval: 24h
  url: https://openbao.github.io/openbao-helm
```

### HTTPRoute Template

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: openbao
  annotations:
    external-dns.alpha.kubernetes.io/target: external.${CLUSTER_DOMAIN}
spec:
  parentRefs:
    - name: envoy-external
      namespace: networking
      sectionName: https
  hostnames:
    - openbao.${CLUSTER_DOMAIN}
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: openbao
          port: 8200
```

### CiliumNetworkPolicy Template

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: openbao
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: openbao
  ingress:
    # Allow from Gateway
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: networking
    # Allow from applications needing secrets
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: arsipq-platform
        - matchLabels:
            io.kubernetes.pod.namespace: business
    # Allow metrics scraping
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: observability
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
            - port: "53"
              protocol: TCP
```

### Gatus Health Check ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: openbao-gatus
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    endpoints:
      - name: OpenBao External
        url: https://openbao.monosense.dev/v1/sys/health
        interval: 5m
        conditions:
          - "[STATUS] == 200"
      - name: OpenBao Internal
        url: http://openbao.arsipq-platform.svc.cluster.local:8200/v1/sys/health
        interval: 2m
        conditions:
          - "[STATUS] == 200"
```

### Flux Kustomization (ks.yaml)

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name openbao
  namespace: flux-system
spec:
  targetNamespace: arsipq-platform
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/infra/apps/platform/openbao/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: external-secrets-stores
      namespace: flux-system
    - name: rook-ceph-cluster
      namespace: flux-system
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Initialization and Unseal Procedure

**Step 1: Initialize OpenBao**
```bash
# Execute on first pod
kubectl exec -ti openbao-0 -n arsipq-platform -- bao operator init

# Output will show:
# Unseal Key 1: xxxxx
# Unseal Key 2: xxxxx
# Unseal Key 3: xxxxx
# Unseal Key 4: xxxxx
# Unseal Key 5: xxxxx
# Initial Root Token: hvs.xxxxxx
```

**Step 2: Store Keys Securely**
Store ALL unseal keys and root token in 1Password vault `k8s-ops`:
- Item name: `openbao-unseal-keys`
- Keys: `key1`, `key2`, `key3`, `key4`, `key5`, `root_token`

**Step 3: Unseal (requires 3 of 5 keys)**
```bash
kubectl exec -ti openbao-0 -n arsipq-platform -- bao operator unseal
# Enter Key 1
kubectl exec -ti openbao-0 -n arsipq-platform -- bao operator unseal
# Enter Key 2
kubectl exec -ti openbao-0 -n arsipq-platform -- bao operator unseal
# Enter Key 3
```

**Step 4: Verify Status**
```bash
kubectl exec -ti openbao-0 -n arsipq-platform -- bao status
# Should show: Sealed: false
```

### Kubernetes Auth Method Configuration

```bash
# Login with root token
bao login

# Enable Kubernetes auth
bao auth enable kubernetes

# Configure Kubernetes auth (auto-detects from pod)
bao write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Create policy for ArsipQ apps
bao policy write arsipq-read - <<EOF
path "secret/data/arsipq/*" {
  capabilities = ["read", "list"]
}
EOF

# Create role for arsipq-platform service accounts
bao write auth/kubernetes/role/arsipq-app \
    bound_service_account_names="*" \
    bound_service_account_namespaces="arsipq-platform" \
    policies="arsipq-read" \
    ttl=1h
```

### Spring Boot Integration

**application.yaml configuration:**
```yaml
spring:
  cloud:
    vault:
      enabled: true
      host: openbao.arsipq-platform.svc.cluster.local
      port: 8200
      scheme: http
      authentication: KUBERNETES
      kubernetes:
        role: arsipq-app
        kubernetes-path: auth/kubernetes
      kv:
        enabled: true
        backend: secret
        application-name: ${spring.application.name}
```

**Add dependency:**
```xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-vault-config</artifactId>
</dependency>
```

### Previous Story Intelligence

From **Story 8.3 (Keycloak)**:
- Namespace `arsipq-platform` exists and is configured
- ExternalSecret pattern established with 1Password ClusterSecretStore
- HTTPRoute pattern using `envoy-external` gateway
- CiliumNetworkPolicy pattern for Tier 2 isolation
- Keycloak available at `keycloak.monosense.dev` for OIDC integration

From **Story 8.2 (Apicurio Registry)** and **Story 8.1 (Strimzi Kafka)**:
- Platform services pattern established
- Dependencies pattern for platform services
- Monitoring integration patterns

### Integration with Other ArsipQ Services

OpenBao provides secrets management for:
- **Spring Boot applications** - Primary use case via Kubernetes auth
- **Keycloak** (Story 8.3) - Can store Keycloak admin credentials
- **Kafka** (Story 8.1) - Can store Kafka credentials
- **Database passwords** - Alternative to External Secrets for runtime secrets

### Project Structure Notes

- **Alignment:** This app is infra-only, correctly placed in `clusters/infra/apps/platform/`
- **Namespace:** `arsipq-platform` - same as other ArsipQ platform services
- **Storage:** Uses Rook-Ceph `ceph-block` for persistent data
- **External access:** Uses `envoy-external` Gateway (infra cluster pattern)
- **Domain:** `openbao.monosense.dev` (infra cluster domain)

### Security Considerations

- Run as non-root user (UID 100)
- Drop all capabilities
- No privilege escalation
- CiliumNetworkPolicy for Tier 2 isolation
- Unseal keys stored separately from OpenBao (in 1Password)
- All secrets encrypted at rest by OpenBao
- TLS terminated at gateway (internal traffic is HTTP)
- Kubernetes auth prevents need for long-lived tokens

### Operational Notes

**Pod Restart Behavior:**
- After pod restart, OpenBao will be in **sealed** state
- Manual unseal required using 3 of 5 unseal keys from 1Password
- Consider implementing alerting for sealed state

**Backup Considerations:**
- Raft storage data is in PVC - backed up by VolSync
- Unseal keys and root token stored in 1Password (separate backup path)
- Test restore procedure periodically

**Health Check States:**
- `200 OK` - Initialized, unsealed, active
- `429` - Unsealed, standby (HA mode)
- `472` - Disaster recovery standby
- `501` - Not initialized
- `503` - Sealed

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 8, Story 8.4]
- [Source: _bmad-output/planning-artifacts/architecture.md - Technology Stack, App Location Rules]
- [Source: docs/project-context.md - Flux HelmRelease Rules, Storage Class Selection]
- [Source: _bmad-output/implementation-artifacts/8-3-deploy-keycloak-for-oidc-authentication.md - Previous Story]
- [OpenBao Helm Chart GitHub](https://github.com/openbao/openbao-helm)
- [OpenBao Kubernetes Documentation](https://openbao.org/docs/platform/k8s/helm/)
- [OpenBao Run on Kubernetes Guide](https://openbao.org/docs/platform/k8s/helm/run/)
- [OpenBao Seal/Unseal Concepts](https://openbao.org/docs/concepts/seal/)
- [Auto Unseal with Transit](https://labs.iximiuz.com/tutorials/openbao-vault-auto-unseal-transit-82d2a212)

---

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Story Completion Notes

Story created by BMAD create-story workflow on 2025-12-31. Ultimate context engine analysis completed - comprehensive developer guide created.
