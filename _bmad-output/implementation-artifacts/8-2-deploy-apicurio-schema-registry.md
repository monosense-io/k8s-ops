# Story 8.2: Deploy Apicurio Schema Registry

Status: ready-for-dev

---

## Story

As a **developer**,
I want **a schema registry for Kafka message schemas**,
So that **I can enforce schema compatibility for event-driven services**.

---

## Acceptance Criteria

1. **Given** Strimzi Kafka is operational (Story 8.1)
   **When** Apicurio Registry is deployed
   **Then** `clusters/infra/apps/platform/apicurio/` contains:
   - Apicurio Registry deployment (latest 3.x version)
   - PostgreSQL database in shared CNPG cluster
   - HTTPRoute for external access

2. **Given** Apicurio Registry is deployed
   **When** querying health endpoint
   **Then** `/q/health` endpoint returns 200

3. **Given** Apicurio Registry is accessible
   **When** developers register schemas
   **Then** Avro/JSON schemas can be registered via REST API

4. **Given** Apicurio Registry is configured
   **When** accessing externally
   **Then** Apicurio is accessible via `apicurio.monosense.dev`

---

## Tasks / Subtasks

- [ ] **Task 1: Configure PostgreSQL Database** (AC: #1)
  - [ ] 1.1 Create ExternalSecret `apicurio-initdb-secret` for database initialization credentials
  - [ ] 1.2 Create ExternalSecret `apicurio-pguser-secret` for application database credentials
  - [ ] 1.3 Configure 1Password items with required PostgreSQL credentials
  - [ ] 1.4 Verify database creation in shared CNPG cluster: `postgres-rw.databases.svc.cluster.local`

- [ ] **Task 2: Create Apicurio Registry Deployment** (AC: #1, #2)
  - [ ] 2.1 Create directory structure `clusters/infra/apps/platform/apicurio/app/`
  - [ ] 2.2 Create `helmrelease.yaml` using community Helm chart from `oci://ghcr.io/eshepelyuk/helm/apicurio-registry`
  - [ ] 2.3 Configure PostgreSQL persistence with JDBC URL: `jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/apicurio`
  - [ ] 2.4 Create `kustomization.yaml` for app directory
  - [ ] 2.5 Create `ks.yaml` Flux Kustomization entry point with dependencies
  - [ ] 2.6 Verify pod health with `kubectl get po -n arsipq-platform -l app.kubernetes.io/name=apicurio-registry`

- [ ] **Task 3: Configure External Access** (AC: #4)
  - [ ] 3.1 Create `httproute.yaml` for Gateway API routing
  - [ ] 3.2 Reference Gateway `envoy-external` in namespace `networking`
  - [ ] 3.3 Configure hostname `apicurio.${CLUSTER_DOMAIN}` using Flux variable substitution
  - [ ] 3.4 Verify external access via `https://apicurio.monosense.dev`

- [ ] **Task 4: Configure Network Policy** (AC: related to security)
  - [ ] 4.1 Create `networkpolicy.yaml` with CiliumNetworkPolicy for Tier 2 isolation
  - [ ] 4.2 Allow ingress from Gateway namespace (`networking`)
  - [ ] 4.3 Allow egress to PostgreSQL database namespace (`databases`)
  - [ ] 4.4 Allow egress to Kafka namespace (`arsipq-platform`) if Kafka storage used
  - [ ] 4.5 Allow ingress from observability namespace for metrics scraping

- [ ] **Task 5: Validate Schema Registration** (AC: #3)
  - [ ] 5.1 Test schema registration via curl to REST API endpoint `/apis/registry/v3/groups/default/artifacts`
  - [ ] 5.2 Create test Avro schema and verify it appears in UI
  - [ ] 5.3 Test schema compatibility rules

- [ ] **Task 6: Configure Monitoring Integration**
  - [ ] 6.1 Verify `/q/health` endpoint responds with 200
  - [ ] 6.2 Create ServiceMonitor for VictoriaMetrics scraping (if metrics endpoint available)
  - [ ] 6.3 Add Gatus health check ConfigMap for `apicurio.monosense.dev`

---

## Dev Notes

### Latest Version Information (December 2025)

Based on web research:
- **Latest stable version:** 3.0.7 (or 3.1.6 for latest-release tag)
- **Docker image:** `quay.io/apicurio/apicurio-registry:latest-release` or specific version tag
- **Community Helm chart:** `oci://ghcr.io/eshepelyuk/helm/apicurio-registry` (version 3.8.0)

**NOTE:** The community Helm chart repository (eshepelyuk/apicurio-registry-helm) was archived in November 2024. Consider:
1. Using the Helm chart as-is (still functional but no updates)
2. Using app-template chart with raw container deployment
3. Using the official Apicurio Registry Operator (Quarkus-based for v3)

**RECOMMENDATION:** Use the community Helm chart 3.8.0 for initial deployment, which supports Apicurio Registry 2.5.8.Final. For Apicurio 3.x, consider using app-template or raw manifests with the `quay.io/apicurio/apicurio-registry:3.0.7` image.

### Storage Configuration

Apicurio Registry 3.0 supports multiple storage backends:
- **PostgreSQL (SQL)** - Recommended for production (our choice)
- **Kafka** - For Kafka-centric deployments
- **In-Memory** - Development only

**PostgreSQL JDBC Configuration:**
```yaml
env:
  APICURIO_STORAGE_KIND: sql
  APICURIO_STORAGE_SQL_KIND: postgresql
  APICURIO_DATASOURCE_URL: jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/apicurio
  APICURIO_DATASOURCE_USERNAME: apicurio
  APICURIO_DATASOURCE_PASSWORD: <from-secret>
```

### Health Endpoints

Apicurio Registry 3.x is built on Quarkus and exposes:
- `/q/health` - Combined health check (200 = healthy)
- `/q/health/live` - Liveness probe
- `/q/health/ready` - Readiness probe

### REST API Endpoints

- **Base API path:** `/apis/registry/v3`
- **Schema groups:** `/apis/registry/v3/groups`
- **Artifacts:** `/apis/registry/v3/groups/{groupId}/artifacts`
- **UI path:** `/` (root)

### Architecture Constraints

From `docs/project-context.md` and architecture document:

| Constraint | Value |
|------------|-------|
| Location | `clusters/infra/apps/platform/apicurio/` (infra cluster only) |
| Namespace | `arsipq-platform` |
| Database | Shared CNPG `postgres` cluster in `databases` namespace |
| Database Name | `apicurio` |
| External Domain | `apicurio.monosense.dev` |
| Gateway | `envoy-external` in `networking` namespace |

### CNPG Shared Cluster Pattern

From project-context.md:
- **Database host:** `postgres-rw.databases.svc.cluster.local`
- **Database name:** `apicurio` (matches app name)
- **Credentials secret:** `apicurio-pguser-secret`
- **Init secret:** `apicurio-initdb-secret`

### Required Dependencies

Add to `ks.yaml`:
```yaml
spec:
  dependsOn:
    - name: cloudnative-pg-cluster
      namespace: flux-system
    - name: strimzi-kafka-cluster  # If using Kafka storage
      namespace: flux-system
  healthCheckExprs:
    - apiVersion: postgresql.cnpg.io/v1
      kind: Cluster
      failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
```

### HelmRelease Template (Using App-Template for v3)

Since the community Helm chart is archived and targets v2.x, recommend using bjw-s app-template:

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: apicurio-registry
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: app-template
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
    controllers:
      apicurio:
        containers:
          main:
            image:
              repository: quay.io/apicurio/apicurio-registry
              tag: 3.0.7
            env:
              APICURIO_STORAGE_KIND: sql
              APICURIO_STORAGE_SQL_KIND: postgresql
              APICURIO_DATASOURCE_URL: jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/apicurio
              APICURIO_DATASOURCE_USERNAME:
                valueFrom:
                  secretKeyRef:
                    name: apicurio-pguser-secret
                    key: username
              APICURIO_DATASOURCE_PASSWORD:
                valueFrom:
                  secretKeyRef:
                    name: apicurio-pguser-secret
                    key: password
            probes:
              liveness:
                enabled: true
                custom: true
                spec:
                  httpGet:
                    path: /q/health/live
                    port: 8080
              readiness:
                enabled: true
                custom: true
                spec:
                  httpGet:
                    path: /q/health/ready
                    port: 8080
            resources:
              requests:
                cpu: 100m
                memory: 512Mi
              limits:
                memory: 1Gi
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop: ["ALL"]
    defaultPodOptions:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
    service:
      main:
        controller: apicurio
        ports:
          http:
            port: 8080
```

### Directory Structure

```
clusters/infra/apps/platform/apicurio/
├── app/
│   ├── helmrelease.yaml      # Apicurio Registry deployment
│   ├── externalsecret.yaml   # PostgreSQL credentials
│   ├── httproute.yaml        # External access via Gateway API
│   ├── networkpolicy.yaml    # CiliumNetworkPolicy
│   └── kustomization.yaml
└── ks.yaml                   # Flux Kustomization entry point
```

### ExternalSecret Template

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: apicurio-pguser-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: apicurio-pguser-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: apicurio-pguser
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: apicurio-initdb-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: apicurio-initdb-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: apicurio-initdb
```

### 1Password Items Required

Create in 1Password vault `k8s-ops`:
1. **apicurio-pguser** - with keys: `username`, `password`
2. **apicurio-initdb** - with keys: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB=apicurio`

### HTTPRoute Template

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: apicurio-registry
  annotations:
    external-dns.alpha.kubernetes.io/target: external.${CLUSTER_DOMAIN}
spec:
  parentRefs:
    - name: envoy-external
      namespace: networking
      sectionName: https
  hostnames:
    - apicurio.${CLUSTER_DOMAIN}
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: apicurio-registry
          port: 8080
```

### Gatus Health Check ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apicurio-gatus
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    endpoints:
      - name: Apicurio Registry
        url: https://apicurio.monosense.dev/q/health
        interval: 5m
        conditions:
          - "[STATUS] == 200"
```

### Previous Story Intelligence

From **Story 8.1 (Strimzi Kafka)**:
- Kafka cluster deployed at: `arsipq-kafka-kafka-bootstrap.arsipq-platform:9092`
- Namespace: `arsipq-platform` - already exists from Kafka deployment
- Dependencies pattern established for platform services
- OCIRepository pattern used for operators
- CiliumNetworkPolicy pattern established for Tier 2 apps

### Project Structure Notes

- **Alignment:** This app is infra-only, correctly placed in `clusters/infra/apps/platform/`
- **Namespace:** `arsipq-platform` - same as Strimzi Kafka (shared platform namespace)
- **Database:** Uses shared CNPG cluster in `databases` namespace following project patterns
- **External access:** Uses `envoy-external` Gateway (infra cluster pattern)

### Security Considerations

- Run as non-root user (UID 1000)
- Read-only root filesystem
- Drop all capabilities
- No privilege escalation
- CiliumNetworkPolicy for Tier 2 isolation

### Integration with Kafka

Apicurio Registry can be configured to work with Kafka for:
1. **Schema storage** (alternative to PostgreSQL) - Not used in this deployment
2. **Confluent compatibility** - For Kafka producers/consumers using schema registry

Kafka clients can use Apicurio Registry with:
- Confluent Schema Registry compatibility mode
- Native Apicurio client serializers/deserializers

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 8, Story 8.2]
- [Source: _bmad-output/planning-artifacts/architecture.md - Technology Stack, App Location Rules]
- [Source: docs/project-context.md - CNPG Shared Cluster Pattern, Flux HelmRelease Rules]
- [Source: _bmad-output/implementation-artifacts/8-1-deploy-strimzi-kafka-operator-and-cluster.md - Previous Story]
- [GitHub - eshepelyuk/apicurio-registry-helm](https://github.com/eshepelyuk/apicurio-registry-helm)
- [Apicurio Registry Documentation](https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/index.html)
- [Apicurio Registry Docker Installation](https://www.apicur.io/registry/docs/apicurio-registry/3.1.x/getting-started/assembly-installing-registry-docker.html)
- [Apicurio Registry GitHub Releases](https://github.com/Apicurio/apicurio-registry/releases/tag/3.0.7)

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
