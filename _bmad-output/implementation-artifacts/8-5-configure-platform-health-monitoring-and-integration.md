# Story 8.5: Configure Platform Health Monitoring and Integration

Status: ready-for-dev

## Story

As a **developer**,
I want **platform health visibility and integration documentation**,
So that **I can build applications against a known-healthy platform**.

## Acceptance Criteria

1. **Gatus ConfigMap includes health checks for all platform services:**
   - Kafka bootstrap endpoint (via kafka-health-check sidecar or JMX exporter)
   - Apicurio Registry `/health/ready` endpoint
   - Keycloak `/health/ready` endpoint (management port 9000)
   - OpenBao `/v1/sys/health` endpoint
   - External MinIO S3 API (`s3.monosense.dev`)

2. **Gatus dashboard shows all platform services health:**
   - Dashboard accessible via `gatus.monosense.dev`
   - All ArsipQ platform services visible on single page
   - Clear healthy/unhealthy status indicators

3. **Integration documentation created:**
   - `docs/platform/arsipq-integration.md` documents:
     - Connection endpoints for each service
     - Authentication configuration
     - Spring Boot integration examples
     - Schema registry usage patterns

4. **Flux Kustomization can reference arsipq-backend manifests:**
   - Application deployment path established
   - GitOps pattern for Spring Boot apps documented

## Tasks / Subtasks

- [ ] Task 1: Create Gatus health check ConfigMap for platform services (AC: #1)
  - [ ] 1.1 Create `clusters/infra/apps/observability/gatus/app/configmap-arsipq.yaml`
  - [ ] 1.2 Configure Kafka health endpoint (use internal bootstrap or metrics endpoint)
  - [ ] 1.3 Configure Apicurio Registry health check on port 8080
  - [ ] 1.4 Configure Keycloak health check on management port 9000
  - [ ] 1.5 Configure OpenBao health check with standby tolerance
  - [ ] 1.6 Configure MinIO S3 health check endpoint
  - [ ] 1.7 Add ConfigMap to kustomization.yaml resources

- [ ] Task 2: Verify Gatus dashboard integration (AC: #2)
  - [ ] 2.1 Ensure ConfigMap has `gatus.io/enabled: "true"` label
  - [ ] 2.2 Validate Gatus picks up new endpoints after deployment
  - [ ] 2.3 Test each health check endpoint responds correctly

- [ ] Task 3: Create integration documentation (AC: #3)
  - [ ] 3.1 Create `docs/platform/arsipq-integration.md`
  - [ ] 3.2 Document CNPG PostgreSQL connection patterns
  - [ ] 3.3 Document Kafka producer/consumer configuration
  - [ ] 3.4 Document Apicurio schema registration workflow
  - [ ] 3.5 Document Keycloak OIDC integration for Spring Security
  - [ ] 3.6 Document OpenBao secrets injection patterns
  - [ ] 3.7 Document MinIO S3 client configuration
  - [ ] 3.8 Add Spring Boot application.yaml examples

- [ ] Task 4: Configure Flux deployment path for arsipq-backend (AC: #4)
  - [ ] 4.1 Create `clusters/infra/apps/platform/arsipq-backend/` directory structure
  - [ ] 4.2 Create ks.yaml with proper dependencies
  - [ ] 4.3 Document GitOps deployment workflow in integration guide

## Dev Notes

### Critical Architecture Requirements

**App Location (CRITICAL):**
- Path: `clusters/infra/apps/observability/gatus/` (Gatus already exists, add ConfigMap)
- Path: `clusters/infra/apps/platform/arsipq-backend/` (new app deployment location)
- Documentation: `docs/platform/arsipq-integration.md`

**Naming Conventions:**
- ConfigMap: `gatus-arsipq-platform` with label `gatus.io/enabled: "true"`
- All resources use kebab-case

**Technology Stack Versions:**
- Gatus: v5.33.1 (latest stable, December 2025)
- Keycloak: Management port 9000 for health checks
- OpenBao: `/v1/sys/health` with configurable status codes
- Apicurio Registry: Quarkus-based `/health/ready` on port 8080

### Health Check Endpoint Specifications

**Keycloak Health Check:**
```yaml
- name: keycloak
  group: arsipq-platform
  url: http://keycloak-http.keycloak.svc.cluster.local:9000/health/ready
  interval: 30s
  conditions:
    - "[STATUS] == 200"
```
- Uses management port 9000 (NOT main HTTP port)
- Requires `KC_HEALTH_ENABLED=true` environment variable on Keycloak

**OpenBao Health Check:**
```yaml
- name: openbao
  group: arsipq-platform
  url: http://openbao.openbao.svc.cluster.local:8200/v1/sys/health?standbyok=true
  interval: 30s
  conditions:
    - "[STATUS] == 200 || [STATUS] == 429"
```
- Status 200 = active node, 429 = standby node (both acceptable)
- `standbyok=true` query param makes standby return 200 if preferred
- Status 503 = sealed, 501 = uninitialized (both indicate problems)

**Apicurio Registry Health Check:**
```yaml
- name: apicurio-registry
  group: arsipq-platform
  url: http://apicurio.arsipq-platform.svc.cluster.local:8080/health/ready
  interval: 30s
  conditions:
    - "[STATUS] == 200"
```
- Standard Quarkus health endpoints: `/health/ready` for readiness
- Port 8080 is the application port

**Kafka Bootstrap Health Check:**
```yaml
- name: kafka-bootstrap
  group: arsipq-platform
  url: tcp://arsipq-kafka-kafka-bootstrap.strimzi-kafka.svc.cluster.local:9092
  interval: 30s
  conditions:
    - "[CONNECTED] == true"
```
- Gatus supports TCP health checks for Kafka bootstrap
- Alternative: Use JMX metrics endpoint if Strimzi Metrics Reporter enabled
- Bootstrap service: `arsipq-kafka-kafka-bootstrap.strimzi-kafka:9092`

**MinIO S3 Health Check:**
```yaml
- name: minio-s3
  group: arsipq-platform
  url: https://s3.monosense.dev/minio/health/live
  interval: 60s
  conditions:
    - "[STATUS] == 200"
```
- External MinIO endpoint
- Health endpoint: `/minio/health/live`

### Gatus ConfigMap Pattern

**Use project standard ConfigMap approach (NOT annotations):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gatus-arsipq-platform
  namespace: observability
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    endpoints:
      # All endpoints defined here
```

### Service Endpoints for Integration Documentation

| Service | Internal Endpoint | External Endpoint | Port |
|---------|-------------------|-------------------|------|
| PostgreSQL | `postgres-rw.databases.svc.cluster.local` | N/A | 5432 |
| Kafka Bootstrap | `arsipq-kafka-kafka-bootstrap.strimzi-kafka.svc.cluster.local` | N/A | 9092 |
| Apicurio Registry | `apicurio.arsipq-platform.svc.cluster.local` | `apicurio.monosense.dev` | 8080 |
| Keycloak | `keycloak-http.keycloak.svc.cluster.local` | `keycloak.monosense.dev` | 8080 |
| OpenBao | `openbao.openbao.svc.cluster.local` | `openbao.monosense.dev` | 8200 |
| MinIO S3 | N/A (external) | `s3.monosense.dev` | 443 |

### Spring Boot Integration Patterns

**PostgreSQL (CNPG Shared Cluster):**
```yaml
spring:
  datasource:
    url: jdbc:postgresql://postgres-rw.databases.svc.cluster.local:5432/${APP_NAME}
    username: ${PGUSER}
    password: ${PGPASSWORD}
```
- Database name = application name
- Credentials from `${APP}-pguser-secret`

**Kafka Configuration:**
```yaml
spring:
  kafka:
    bootstrap-servers: arsipq-kafka-kafka-bootstrap.strimzi-kafka.svc.cluster.local:9092
    properties:
      schema.registry.url: http://apicurio.arsipq-platform.svc.cluster.local:8080/apis/ccompat/v7
```
- Use Apicurio in Confluent compatibility mode (`/apis/ccompat/v7`)

**Keycloak OIDC:**
```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://keycloak.monosense.dev/realms/arsipq
```
- Realm: `arsipq`
- JWKS endpoint auto-discovered from issuer

**OpenBao Secrets:**
```yaml
spring:
  cloud:
    vault:
      uri: http://openbao.openbao.svc.cluster.local:8200
      authentication: KUBERNETES
      kubernetes:
        role: ${APP_NAME}
```
- Use Kubernetes auth method
- Role matches application name

### Dependencies

This story depends on completion of:
- Story 8.1: Strimzi Kafka (provides bootstrap endpoint)
- Story 8.2: Apicurio Registry (provides schema registry)
- Story 8.3: Keycloak (provides OIDC)
- Story 8.4: OpenBao (provides secrets management)

**Flux Kustomization dependencies for arsipq-backend:**
```yaml
dependsOn:
  - name: strimzi-kafka
  - name: apicurio
  - name: keycloak
  - name: openbao
  - name: cloudnative-pg-cluster
```

### Project Structure Notes

**Alignment with unified project structure:**
- Gatus ConfigMaps go in existing Gatus app directory
- New documentation in `docs/platform/`
- arsipq-backend follows standard `clusters/infra/apps/platform/` pattern

**File locations:**
```
clusters/infra/apps/observability/gatus/
├── app/
│   ├── configmap-arsipq.yaml    # NEW: ArsipQ platform health checks
│   └── kustomization.yaml       # UPDATE: Add configmap-arsipq.yaml
├── ks.yaml

clusters/infra/apps/platform/arsipq-backend/
├── app/
│   ├── helmrelease.yaml         # NEW: Application deployment
│   ├── kustomization.yaml       # NEW: Local kustomization
│   ├── externalsecret.yaml      # NEW: Secrets reference
│   └── networkpolicy.yaml       # NEW: Tier 2 network policy
├── ks.yaml                      # NEW: Flux Kustomization

docs/platform/
├── arsipq-integration.md        # NEW: Integration documentation
```

### Anti-Patterns to Avoid

1. **DO NOT** create separate Gatus deployment for ArsipQ - use existing shared Gatus
2. **DO NOT** hardcode endpoints - use service DNS names
3. **DO NOT** expose internal health endpoints externally without authentication
4. **DO NOT** use Keycloak main HTTP port (8080) for health checks - use management port (9000)
5. **DO NOT** check only OpenBao status 200 - allow 429 for standby nodes

### Testing Validation

After deployment, verify:
```bash
# Check Gatus picked up new endpoints
kubectl -n observability get configmap gatus-arsipq-platform -o yaml

# Verify health check responses
kubectl -n observability exec -it deploy/gatus -- curl -s http://localhost:8080/api/v1/endpoints/statuses

# Test individual endpoints
kubectl run test --rm -it --image=curlimages/curl -- \
  curl -s http://keycloak-http.keycloak.svc.cluster.local:9000/health/ready
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-8-Story-8.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns]
- [Source: docs/project-context.md#Gatus-Health-Check-Pattern]
- [Gatus Documentation](https://gatus.io/docs)
- [Keycloak Health Checks](https://www.keycloak.org/observability/health)
- [OpenBao /sys/health API](https://openbao.org/api-docs/system/health/)
- [Strimzi Monitoring](https://strimzi.io/blog/2025/10/01/monitoring-of-custom-resources/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
