# Story 8.3: Deploy Keycloak for OIDC Authentication

Status: ready-for-dev

---

## Story

As a **developer**,
I want **Keycloak providing OIDC authentication**,
So that **Spring Boot applications have consistent SSO integration**.

---

## Acceptance Criteria

1. **Given** CNPG shared cluster is operational
   **When** Keycloak is deployed
   **Then** `clusters/infra/apps/platform/keycloak/` contains:
   - Keycloak Bitnami HelmRelease (version 26.x)
   - PostgreSQL database in shared CNPG cluster
   - HTTPRoute for admin console and OIDC endpoints

2. **Given** Keycloak is deployed
   **When** accessing admin console
   **Then** admin console is accessible via `keycloak.monosense.dev`

3. **Given** Keycloak admin console is accessible
   **When** realm configuration is set up
   **Then** realm configuration is persisted in database

4. **Given** Keycloak is operational
   **When** developers configure applications
   **Then** developers can configure OIDC clients for applications

---

## Tasks / Subtasks

- [ ] **Task 1: Configure PostgreSQL Database** (AC: #1)
  - [ ] 1.1 Create ExternalSecret `keycloak-initdb-secret` for database initialization credentials
  - [ ] 1.2 Create ExternalSecret `keycloak-pguser-secret` for application database credentials
  - [ ] 1.3 Configure 1Password items with required PostgreSQL credentials (keycloak-initdb, keycloak-pguser)
  - [ ] 1.4 Verify database creation in shared CNPG cluster: `postgres-rw.databases.svc.cluster.local`

- [ ] **Task 2: Configure Keycloak Admin Credentials** (AC: #1, #2)
  - [ ] 2.1 Create ExternalSecret `keycloak-secret` for admin credentials
  - [ ] 2.2 Configure 1Password item `keycloak` with keys: `admin-username`, `admin-password`
  - [ ] 2.3 Verify secrets sync properly via External Secrets Operator

- [ ] **Task 3: Create Keycloak Deployment** (AC: #1, #2)
  - [ ] 3.1 Create directory structure `clusters/infra/apps/platform/keycloak/app/`
  - [ ] 3.2 Create `helmrelease.yaml` using Bitnami Keycloak Helm chart 25.2.0 (Keycloak 26.x)
  - [ ] 3.3 Configure PostgreSQL external database connection with JDBC URL
  - [ ] 3.4 Configure production mode with HTTP disabled (proxy termination at gateway)
  - [ ] 3.5 Configure health check endpoints (`/health/ready`, `/health/live`)
  - [ ] 3.6 Create `kustomization.yaml` for app directory
  - [ ] 3.7 Create `ks.yaml` Flux Kustomization entry point with dependencies
  - [ ] 3.8 Verify pod health with `kubectl get po -n arsipq-platform -l app.kubernetes.io/name=keycloak`

- [ ] **Task 4: Configure External Access** (AC: #2)
  - [ ] 4.1 Create `httproute.yaml` for Gateway API routing
  - [ ] 4.2 Reference Gateway `envoy-external` in namespace `networking`
  - [ ] 4.3 Configure hostname `keycloak.${CLUSTER_DOMAIN}` using Flux variable substitution
  - [ ] 4.4 Configure path matching for admin console (`/admin/*`) and OIDC endpoints (`/realms/*`)
  - [ ] 4.5 Verify external access via `https://keycloak.monosense.dev`

- [ ] **Task 5: Configure Network Policy** (AC: related to security)
  - [ ] 5.1 Create `networkpolicy.yaml` with CiliumNetworkPolicy for Tier 2 isolation
  - [ ] 5.2 Allow ingress from Gateway namespace (`networking`)
  - [ ] 5.3 Allow egress to PostgreSQL database namespace (`databases`)
  - [ ] 5.4 Allow ingress from application namespaces needing OIDC (e.g., `arsipq-platform`, `business`)
  - [ ] 5.5 Allow ingress from observability namespace for metrics scraping

- [ ] **Task 6: Create ArsipQ Realm Configuration** (AC: #3, #4)
  - [ ] 6.1 Access Keycloak admin console and create `arsipq` realm
  - [ ] 6.2 Configure realm settings (token lifetimes, login settings, brute force protection)
  - [ ] 6.3 Document realm configuration for reproducibility
  - [ ] 6.4 Verify realm persists after pod restart

- [ ] **Task 7: Configure Monitoring Integration**
  - [ ] 7.1 Verify `/health/ready` endpoint responds with 200
  - [ ] 7.2 Create ServiceMonitor for VictoriaMetrics scraping (metrics enabled via Bitnami chart)
  - [ ] 7.3 Add Gatus health check ConfigMap for `keycloak.monosense.dev`

---

## Dev Notes

### Latest Version Information (December 2025)

Based on web research:
- **Keycloak latest version:** 26.4.7 (Quarkus-based)
- **Bitnami Helm chart version:** 25.2.0
- **Official Docker image:** `quay.io/keycloak/keycloak:26.4.7`
- **Bitnami Docker image:** `docker.io/bitnami/keycloak:26`

**IMPORTANT - Keycloak 26 Breaking Changes:**
- Admin environment variables changed:
  - `KC_BOOTSTRAP_ADMIN_USERNAME` (replaces `KEYCLOAK_ADMIN`)
  - `KC_BOOTSTRAP_ADMIN_PASSWORD` (replaces `KEYCLOAK_ADMIN_PASSWORD`)
- Production mode requires explicit configuration
- Health endpoints moved to `/health/ready` and `/health/live`

**RECOMMENDATION:** Use Bitnami Helm chart 25.2.0 which wraps Keycloak 26.x and handles the complexity of production deployment with proper database configuration.

### Database Configuration

Keycloak requires PostgreSQL for production:
- **Database host:** `postgres-rw.databases.svc.cluster.local`
- **Database name:** `keycloak` (matches app name per CNPG pattern)
- **Database port:** 5432
- **Credentials secret:** `keycloak-pguser-secret`

**JDBC URL:** `jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/keycloak`

### Bitnami Chart Configuration

The Bitnami Helm chart provides:
- Built-in PostgreSQL support (external database mode)
- Production-ready security hardening
- Metrics endpoint for Prometheus/VictoriaMetrics
- Configurable proxy settings for reverse proxy (edge termination)

Key Bitnami chart values:
```yaml
# External PostgreSQL
postgresql:
  enabled: false  # Use external CNPG cluster

externalDatabase:
  host: postgres-rw.databases.svc.cluster.local
  port: 5432
  database: keycloak
  user: keycloak
  existingSecret: keycloak-pguser-secret
  existingSecretPasswordKey: password

# Production mode
production: true
proxy: edge  # TLS terminated at gateway

# Admin credentials
auth:
  adminUser: admin
  existingSecret: keycloak-secret
  passwordSecretKey: admin-password

# Health probes
customLivenessProbe:
  httpGet:
    path: /health/live
    port: http
customReadinessProbe:
  httpGet:
    path: /health/ready
    port: http

# Metrics
metrics:
  enabled: true
  service:
    ports:
      http: 8080

# Resources
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    memory: 1Gi
```

### Architecture Constraints

From `docs/project-context.md` and architecture document:

| Constraint | Value |
|------------|-------|
| Location | `clusters/infra/apps/platform/keycloak/` (infra cluster only) |
| Namespace | `arsipq-platform` |
| Database | Shared CNPG `postgres` cluster in `databases` namespace |
| Database Name | `keycloak` |
| External Domain | `keycloak.monosense.dev` |
| Gateway | `envoy-external` in `networking` namespace |

### CNPG Shared Cluster Pattern

From project-context.md:
- **Database host:** `postgres-rw.databases.svc.cluster.local`
- **Database name:** `keycloak` (matches app name)
- **Credentials secret:** `keycloak-pguser-secret`
- **Init secret:** `keycloak-initdb-secret`

### Required Dependencies

Add to `ks.yaml`:
```yaml
spec:
  dependsOn:
    - name: cloudnative-pg-cluster
      namespace: flux-system
    - name: external-secrets-stores
      namespace: flux-system
  healthCheckExprs:
    - apiVersion: postgresql.cnpg.io/v1
      kind: Cluster
      failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
```

### HelmRelease Template

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: keycloak
spec:
  interval: 1h
  chart:
    spec:
      chart: keycloak
      version: 25.2.0
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
    # Production mode
    production: true
    proxy: edge

    # External PostgreSQL
    postgresql:
      enabled: false
    externalDatabase:
      host: postgres-rw.databases.svc.cluster.local
      port: 5432
      database: keycloak
      user: keycloak
      existingSecret: keycloak-pguser-secret
      existingSecretPasswordKey: password

    # Admin credentials
    auth:
      adminUser: admin
      existingSecret: keycloak-secret
      passwordSecretKey: admin-password

    # Logging
    logging:
      output: default
      level: INFO

    # Metrics
    metrics:
      enabled: true
      serviceMonitor:
        enabled: true
        namespace: arsipq-platform

    # Resources
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        memory: 1Gi

    # Security context
    podSecurityContext:
      fsGroup: 1000
    containerSecurityContext:
      runAsUser: 1000
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL

    # Pod annotations for Reloader
    podAnnotations:
      reloader.stakater.com/auto: "true"
```

### Directory Structure

```
clusters/infra/apps/platform/keycloak/
├── app/
│   ├── helmrelease.yaml      # Keycloak deployment via Bitnami chart
│   ├── externalsecret.yaml   # PostgreSQL and admin credentials
│   ├── httproute.yaml        # External access via Gateway API
│   ├── networkpolicy.yaml    # CiliumNetworkPolicy
│   └── kustomization.yaml
└── ks.yaml                   # Flux Kustomization entry point
```

### ExternalSecret Template

```yaml
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: keycloak-pguser-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: keycloak-pguser-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: keycloak-pguser
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: keycloak-initdb-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: keycloak-initdb-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: keycloak-initdb
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: keycloak-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: keycloak-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: keycloak
```

### 1Password Items Required

Create in 1Password vault `k8s-ops`:

1. **keycloak-pguser** - with keys:
   - `username`: `keycloak`
   - `password`: (generate secure password)

2. **keycloak-initdb** - with keys:
   - `POSTGRES_USER`: `keycloak`
   - `POSTGRES_PASSWORD`: (same as pguser password)
   - `POSTGRES_DB`: `keycloak`

3. **keycloak** - with keys:
   - `admin-username`: `admin`
   - `admin-password`: (generate secure password)

### HTTPRoute Template

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: keycloak
  annotations:
    external-dns.alpha.kubernetes.io/target: external.${CLUSTER_DOMAIN}
spec:
  parentRefs:
    - name: envoy-external
      namespace: networking
      sectionName: https
  hostnames:
    - keycloak.${CLUSTER_DOMAIN}
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: keycloak
          port: 80
```

### CiliumNetworkPolicy Template

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: keycloak
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: keycloak
  ingress:
    # Allow from Gateway
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: networking
    # Allow from applications needing OIDC
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
    # Allow to PostgreSQL
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: databases
      toPorts:
        - ports:
            - port: "5432"
              protocol: TCP
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
  name: keycloak-gatus
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    endpoints:
      - name: Keycloak
        url: https://keycloak.monosense.dev/health/ready
        interval: 5m
        conditions:
          - "[STATUS] == 200"
```

### OIDC Configuration for Spring Boot

After Keycloak is deployed, developers can configure Spring Boot applications:

**application.yaml:**
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          keycloak:
            client-id: ${KEYCLOAK_CLIENT_ID}
            client-secret: ${KEYCLOAK_CLIENT_SECRET}
            scope: openid,profile,email
        provider:
          keycloak:
            issuer-uri: https://keycloak.monosense.dev/realms/arsipq
      resourceserver:
        jwt:
          issuer-uri: https://keycloak.monosense.dev/realms/arsipq
```

### Previous Story Intelligence

From **Story 8.2 (Apicurio Registry)**:
- Namespace `arsipq-platform` already exists from previous platform deployments
- ExternalSecret pattern established with 1Password ClusterSecretStore
- HTTPRoute pattern using `envoy-external` gateway
- CiliumNetworkPolicy pattern for Tier 2 isolation
- App-template and Bitnami chart patterns both demonstrated

From **Story 8.1 (Strimzi Kafka)**:
- Kafka cluster deployed at: `arsipq-kafka-kafka-bootstrap.arsipq-platform:9092`
- Dependencies pattern established for platform services
- Namespace `arsipq-platform` created and configured

### Project Structure Notes

- **Alignment:** This app is infra-only, correctly placed in `clusters/infra/apps/platform/`
- **Namespace:** `arsipq-platform` - same as other ArsipQ platform services
- **Database:** Uses shared CNPG cluster in `databases` namespace following project patterns
- **External access:** Uses `envoy-external` Gateway (infra cluster pattern)
- **Domain:** `keycloak.monosense.dev` (infra cluster domain)

### Security Considerations

- Run as non-root user (UID 1000)
- Read-only root filesystem not possible with Keycloak (requires writable temp)
- Drop all capabilities
- No privilege escalation
- CiliumNetworkPolicy for Tier 2 isolation
- Production mode enabled (HTTP disabled, requires reverse proxy)
- Admin credentials stored in 1Password, never in Git

### Integration with Other ArsipQ Services

Keycloak will provide OIDC authentication for:
- **Apicurio Registry** (Story 8.2) - Can configure OIDC login
- **OpenBao** (Story 8.4) - Will use Keycloak for OIDC auth
- **Spring Boot applications** - Primary use case for ArsipQ platform

### Realm Configuration Notes

The `arsipq` realm should be configured with:
- Appropriate token lifetimes (access token: 5 min, refresh token: 30 min)
- Brute force detection enabled
- Password policy (minimum length, complexity)
- Required OIDC flows (authorization code, client credentials)
- Groups and roles for ArsipQ applications

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 8, Story 8.3]
- [Source: _bmad-output/planning-artifacts/architecture.md - Technology Stack, App Location Rules]
- [Source: docs/project-context.md - CNPG Shared Cluster Pattern, Flux HelmRelease Rules]
- [Source: _bmad-output/implementation-artifacts/8-2-deploy-apicurio-schema-registry.md - Previous Story]
- [Bitnami Keycloak Helm Chart](https://artifacthub.io/packages/helm/bitnami/keycloak)
- [Bitnami Keycloak GitHub](https://github.com/bitnami/charts/tree/main/bitnami/keycloak)
- [Keycloak Docker Image](https://hub.docker.com/r/keycloak/keycloak)
- [Keycloak Official Docker Guide](https://www.keycloak.org/getting-started/getting-started-docker)
- [Keycloak 26.4.0 Release Notes](https://www.keycloak.org/2025/09/keycloak-2640-released)
- [Keycloak Downloads](https://www.keycloak.org/downloads)

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
