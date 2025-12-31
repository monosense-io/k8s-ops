---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - _bmad-output/planning-artifacts/research/technical-multi-cluster-gitops-architecture-2025-12-28.md
  - docs/index.md
  - docs/home-ops-analysis.md
  - docs/prod-ops-analysis.md
  - docs/integration-analysis.md
workflowType: 'prd'
lastStep: 10
documentCounts:
  briefs: 0
  research: 1
  brainstorming: 0
  projectDocs: 4
---

# Product Requirements Document - k8s-ops

**Author:** monosense
**Date:** 2025-12-28

## Executive Summary

**k8s-ops** is a unified multi-cluster GitOps repository consolidating two existing Kubernetes infrastructure repositories (`home-ops` and `prod-ops`) into a single, well-structured monorepo following FluxCD best practices.

### Vision

Establish a single source of truth for managing multiple Talos Linux Kubernetes clusters with:
- **Reduced duplication** through shared infrastructure components and Kustomize bases
- **Easier maintenance** via unified Renovate configuration and consolidated tooling
- **Better visibility** with cross-cluster observability using VictoriaMetrics stack
- **Modern architecture** aligned with FluxCD community patterns (onedr0p/home-ops style)

### Problem Statement

Managing two separate GitOps repositories (`home-ops` for home lab, `prod-ops` for production) creates:
- Duplicate Helm repository definitions and component configurations
- Inconsistent versions between clusters requiring manual synchronization
- Separate Renovate PR streams for identical dependencies
- No unified view across cluster health and metrics
- Maintenance overhead when updating shared components

### Solution

Consolidate into `k8s-ops` monorepo with:

1. **Cluster-specific directories** (`clusters/infra/`, `clusters/apps/`) following FluxCD monorepo pattern
2. **Shared infrastructure base** (`infrastructure/`) for common CRDs, controllers, and operators
3. **Shared apps base** (`apps/base/`) with cluster overlays for environment-specific configuration
4. **Unified observability stack** - VictoriaMetrics K8s + VictoriaLogs + Fluent-bit replacing Prometheus/Loki
5. **ArsipQ dev platform** (infra cluster only) for Spring Boot development environment
6. **Latest component versions** pinned at migration time with Renovate managing updates

### What Makes This Special

- **Clean-slate rebuild** - Clusters already destroyed, enabling best-practices structure from day one
- **Unified observability** - VictoriaMetrics provides lighter, faster metrics with cross-cluster querying capability
- **Dev platform ready** - ArsipQ stack deployable via GitOps patterns
- **Community-aligned patterns** - Following onedr0p/home-ops and FluxCD official examples

## Project Classification

| Attribute | Value |
|-----------|-------|
| **Technical Type** | Infrastructure-as-Code / GitOps Platform |
| **Domain** | DevOps/Infrastructure |
| **Complexity** | Medium |
| **Project Context** | Brownfield - consolidating existing systems |

## Repository Structure Decision

Adopting **monorepo with cluster directories** pattern:

```
k8s-ops/
├── clusters/
│   ├── infra/                  # Infrastructure cluster - platform services
│   │   ├── apps/               # Infra-specific apps (observability hub, platform services)
│   │   ├── flux/               # Infra cluster Flux config
│   │   └── talos/              # Infra Talos machine configs
│   └── apps/                   # Applications cluster - business workloads
│       ├── apps/               # App-specific workloads (odoo, n8n, arsipq)
│       ├── flux/               # Apps cluster Flux config
│       └── talos/              # Apps Talos machine configs
├── infrastructure/
│   ├── base/                   # Shared CRDs and controllers
│   ├── controllers/            # Shared operators
│   └── configs/                # Cluster-vars ConfigMaps
├── apps/
│   ├── base/                   # Shared app definitions
│   ├── overlays/               # Cluster-specific patches
│   └── components/             # Reusable Kustomize components
├── bootstrap/                  # Helmfile bootstrap
├── terraform/                  # Authentik, shared modules
└── .taskfiles/                 # Unified task automation
```

## Scope Definition

### IN SCOPE

| Category | Items |
|----------|-------|
| **Repository** | Merge home-ops + prod-ops → k8s-ops monorepo |
| **Structure** | FluxCD best practices directory layout |
| **Versions** | Upgrade all components to latest (pinned at migration) |
| **Observability** | Replace Prometheus/Loki with VictoriaMetrics K8s + VictoriaLogs + Fluent-bit (infra cluster) |
| **ArsipQ Platform** | Deploy CNPG, Strimzi, Apicurio, Keycloak, OpenBao (infra cluster only) |
| **Shared Infra** | Cilium, cert-manager, external-secrets, Rook-Ceph, Envoy Gateway |
| **Secrets** | 1Password + External Secrets, SOPS/AGE (existing key) |
| **SSO** | Authentik (infra cluster, serving both) |
| **Container Registry** | Harbor (infra cluster) |

### OUT OF SCOPE

| Category | Rationale |
|----------|-----------|
| Cross-cluster service mesh | Not required; clusters operate independently |
| Shared secrets between clusters | Each cluster has own 1Password vault references |
| Multi-cluster Flux hub-spoke | Using standalone mode (each cluster runs own Flux) |
| Database replication across clusters | Not needed for current workloads |
| Zero-downtime migration | Clusters already destroyed; clean rebuild |

## Observability Architecture

**Major Workstream:** Replacing Prometheus/Loki stack with VictoriaMetrics ecosystem on infra cluster.

| Component | Replaces | Purpose |
|-----------|----------|---------|
| **VictoriaMetrics K8s Operator** | kube-prometheus-stack | Metrics collection, storage, alerting |
| **VMAgent** | Prometheus | Scraping and remote write |
| **VMAlertmanager** | Alertmanager | Alert routing |
| **VictoriaLogs** | Loki | Log aggregation and querying |
| **Fluent-bit** | Promtail | Log collection and forwarding |
| **Grafana** | (retained) | Visualization (with VM datasources) |

**Centralized Strategy:** Observability stack runs on infra cluster only. Apps cluster runs VMAgent + Fluent-bit for collection, remote-writes to infra cluster. Cross-cluster visibility achieved via centralized Grafana.

**Log Collection Pattern (Direct HTTP):**
- Infra cluster: Fluent-bit → VictoriaLogs (internal service)
- Apps cluster: Fluent-bit → VictoriaLogs (via Gateway, HTTPS)
- Fluent-bit memory buffer handles transient failures
- Cluster label added to distinguish log sources

**Migration Impact:**
- Alert rules require conversion from PromQL to MetricsQL (largely compatible)
- Recording rules need migration
- Grafana dashboards need datasource updates
- Existing exporters remain compatible

## Infra/Apps Cluster Architecture

| Aspect | Infra Cluster | Apps Cluster |
|--------|---------------|--------------|
| **Purpose** | Platform services, observability, dev tools | Business application workloads |
| **Infrastructure** | Full shared stack | Shared stack (CNI, storage, secrets) |
| **Observability** | Full VictoriaMetrics stack (storage + query) | VMAgent + Fluent-bit (collection only) |
| **CNPG PostgreSQL** | ArsipQ platform databases | Business app databases |
| **ArsipQ Platform** | Strimzi, Apicurio, Keycloak, OpenBao | Not deployed |
| **Business Apps** | Not deployed | Odoo, n8n, ArsipQ |
| **SSO** | Hosts Authentik | Uses infra Authentik |
| **Container Registry** | Hosts Harbor | Uses infra Harbor |
| **Storage** | Rook-Ceph + platform data | Rook-Ceph + app data |

## ArsipQ Platform Stack (Infra Cluster Only)

Platform components deployed to support Spring Boot development:

| Component | Version | Namespace | Purpose |
|-----------|---------|-----------|---------|
| **Strimzi** | v0.47.0 | strimzi-system | Kafka 3.7.0 (KRaft mode) |
| **Envoy Gateway** | v1.6.1 | envoy-gateway-system | Gateway API controller |
| **Apicurio Registry** | latest | arsipq-platform | Schema registry |
| **Keycloak** | Bitnami | arsipq-platform | OIDC/SSO |
| **OpenBao** | latest | arsipq-platform | Secrets management |

**Database:** Uses CNPG PostgreSQL (operator deployed on both clusters, ArsipQ databases on infra cluster).

**S3 Storage:** Uses existing external MinIO server (not operator-managed).

**Integration Pattern:** Flux Kustomization references manifests from arsipq-backend repo (read-only, no modifications to source).

**Dependency Order:**
1. Namespaces → 2. Operator CRDs → 3. Operators → 4. Platform resources → 5. Application manifests

## Success Criteria

### User Success (Operator Experience)

| Success Indicator | Measurement |
|-------------------|-------------|
| **Single-repo workflow** | All cluster changes made in k8s-ops, no context switching between repos |
| **Unified dependency management** | One Renovate PR updates shared components for both clusters |
| **Cross-cluster visibility** | Single Grafana instance (on infra) showing both infra and apps cluster metrics |
| **Faster troubleshooting** | Consistent patterns mean same debugging approach for both clusters |
| **Reduced cognitive load** | New component deployment follows identical pattern regardless of cluster; documented in < 1 page |
| **Predictable operations** | Same directory structure, same Kustomize patterns, same tooling across clusters |

**Success Moment:** Update a shared Helm chart version once → Renovate opens one PR → merge → infra cluster reconciles first, apps cluster follows after soak period.

### Business Success (Operational Efficiency)

| Metric | Before (2 repos) | After (k8s-ops) |
|--------|------------------|-----------------|
| **Repositories to maintain** | 2 | 1 |
| **Renovate PR streams** | 2 separate | 1 unified |
| **Duplicate configurations** | ~60% overlap | 0% (shared base) |
| **Time to update shared component** | 2x (update both repos) | 1x (single update, auto-propagates) |
| **Observability stack complexity** | Prometheus + Loki (heavy) | VictoriaMetrics (40% lighter resource usage) |
| **Context switches per day** | Multiple (different patterns) | Zero (unified patterns) |

### Technical Success

#### Flux Reconciliation

| Scenario | Target |
|----------|--------|
| **Incremental changes** | All Kustomizations `Ready` within 5 minutes of push |
| **Full cluster bootstrap** | Complete reconciliation within 30 minutes |
| **Dependency chains** | All `dependsOn` chains resolve without circular dependencies |
| **Zero drift** | No manual `kubectl` changes required; all state in Git |

#### Infrastructure Health

| Component | Success Criteria |
|-----------|------------------|
| **Cilium CNI** | Connectivity tests pass; no packet drops between pods |
| **Rook-Ceph** | Cluster `HEALTH_OK`; all OSDs up; all PGs `active+clean` |
| **cert-manager** | Certificates issued and renewed automatically |
| **External Secrets** | Sync from 1Password within 5 minutes of vault change |
| **CRD ordering** | All operator CRDs installed before custom resources applied |

#### Observability Health

| Component | Success Criteria |
|-----------|------------------|
| **VMAgent** | 100% of expected scrape targets discovered |
| **Scrape errors** | < 1% error rate per target |
| **VictoriaLogs** | Receiving logs from all Fluent-bit DaemonSet pods |
| **vmalert** | All alert rules evaluating without errors |
| **Grafana** | Dashboards loading with data from both clusters |

#### Operational Resilience

| Scenario | Success Criteria |
|----------|------------------|
| **Rollback** | `flux suspend` + Git revert recovers cluster within 5 minutes |
| **Secret rotation** | External Secrets sync within 5 minutes of 1Password change |
| **Staged rollout** | Infra cluster updates first; 24h soak before apps |
| **Component failure** | Single component failure doesn't cascade to unrelated workloads |

### ArsipQ Platform Success (Infra Cluster)

| Component | Health Check |
|-----------|--------------|
| **CNPG PostgreSQL** | Cluster `Ready`; 3 replicas; primary accepting writes |
| **Strimzi Kafka** | Cluster `Ready`; KRaft quorum healthy; topic creation works |
| **External MinIO** | S3 API accessible from platform pods |
| **Apicurio Registry** | `/health` endpoint returning 200 |
| **Keycloak** | Admin console accessible; realm configuration persisted |
| **OpenBao** | Initialized, unsealed, secrets read/write functional |
| **Gatus monitoring** | Automated health checks for all ArsipQ endpoints |

## Product Scope

### Phase Structure

| Phase | Name | Scope | Done When |
|-------|------|-------|-----------|
| **1** | Foundation | Repo structure + Infra cluster + Shared infra | Infra cluster reconciling; platform services running |
| **2** | Apps Cluster | Apps cluster setup + business workloads | Apps cluster reconciling; all business apps running |
| **3** | Observability | VictoriaMetrics + VictoriaLogs + Fluent-bit | Metrics/logs flowing; Grafana dashboards operational |
| **4** | Dev Platform | ArsipQ stack deployment | All operators + platform components healthy |

### Phase 1: Foundation (MVP)

| Component | Deliverable |
|-----------|-------------|
| **Repository** | k8s-ops with FluxCD best practices structure |
| **Infra cluster** | Talos + Cilium + Flux bootstrap |
| **Shared infrastructure** | cert-manager, external-secrets, Rook-Ceph, CNPG in `infrastructure/base/` |
| **Platform services** | Harbor, Authentik, Mattermost |
| **Tooling** | Unified .taskfiles, Renovate config, GitHub Actions |

**Exit Criteria:**
- [ ] Infra cluster Flux reconciling without errors
- [ ] Platform services accessible via ingress
- [ ] Renovate opening PRs against k8s-ops
- [ ] Secrets syncing from 1Password

### Phase 2: Apps Cluster

| Component | Deliverable |
|-----------|-------------|
| **Apps cluster** | Talos + Cilium + Flux bootstrap |
| **Shared base reuse** | Apps cluster using same `infrastructure/base/` as infra |
| **Business apps** | Odoo, n8n, ArsipQ |
| **Cluster overlays** | `clusters/apps/` with apps-specific configuration |

**Exit Criteria:**
- [ ] Apps cluster Flux reconciling without errors
- [ ] All business apps accessible via ingress
- [ ] Authentik SSO (from infra) functional for apps cluster
- [ ] Shared component update propagates to both clusters

### Phase 3: Observability

| Component | Deliverable |
|-----------|-------------|
| **VictoriaMetrics Operator** | Full stack on infra cluster |
| **VMAgent** | On both clusters (apps cluster remote-writes to infra) |
| **VMSingle/VMCluster** | On infra cluster (centralized storage) |
| **VictoriaLogs** | On infra cluster, receiving logs from both clusters |
| **Fluent-bit** | DaemonSet on all nodes (both clusters) |
| **Grafana** | On infra cluster with multi-cluster datasources |
| **Dashboards** | 3 specific dashboards migrated |

**Specific Dashboard Deliverables:**
1. **Cluster Overview** - Node health, pod counts, resource usage (both clusters)
2. **Flux GitOps** - Reconciliation status, sync times, error rates
3. **Application Health** - Per-namespace pod status, restart counts, ingress latency

**Exit Criteria:**
- [ ] Prometheus/Loki completely removed
- [ ] VictoriaMetrics scraping 100% of targets (both clusters)
- [ ] VictoriaLogs receiving logs from all pods (both clusters)
- [ ] All 3 dashboards functional with live data
- [ ] Alert rules migrated and evaluating

### Phase 4: Dev Platform (Infra Cluster)

| Component | Deliverable |
|-----------|-------------|
| **Operators** | Strimzi, Envoy Gateway (CNPG already in Phase 1) |
| **Platform resources** | ArsipQ PostgreSQL cluster, Kafka cluster |
| **Applications** | Apicurio Registry, Keycloak, OpenBao |
| **Integration** | Flux Kustomization referencing arsipq-backend manifests |
| **Monitoring** | Gatus health checks for all ArsipQ endpoints |

**Exit Criteria:**
- [ ] All operators CRDs installed and healthy
- [ ] ArsipQ PostgreSQL cluster accepting connections
- [ ] Kafka cluster producing/consuming messages
- [ ] External MinIO S3 accessible from platform
- [ ] Keycloak admin console accessible
- [ ] OpenBao initialized and unsealed
- [ ] Gatus showing green for all endpoints

### Growth Features (Post-Phase 4)

| Feature | Priority | Description |
|---------|----------|-------------|
| **Cross-cluster comparison dashboard** | High | Side-by-side resource usage, costs, performance |
| **Unified alerting runbooks** | Medium | Documented response procedures for common alerts |
| **Automated cluster health reports** | Medium | Weekly summary of reconciliation status, drift, issues |
| **Kustomize component library** | Low | Reusable components for common patterns (cnpg, volsync, etc.) |

### Vision (Future)

| Capability | Description |
|------------|-------------|
| **Third cluster support** | New cluster onboarded in < 1 day using established patterns |
| **Shared app catalog** | Pre-configured apps deployable via single Kustomization reference |
| **Self-service platform** | Developers deploy workloads via PR without deep K8s knowledge |
| **Multi-tenant isolation** | Namespace-based isolation with RBAC for different teams |

### Reference Strategy

Original repositories (`home-ops`, `prod-ops`) will be archived (read-only) as reference for:
- Historical configuration decisions
- Troubleshooting if issues arise
- Version comparison during migration

## Technology Stack

| Layer | Components |
|-------|------------|
| **OS** | Talos Linux v1.12.0 |
| **Kubernetes** | v1.35.0 (included in Talos 1.12.0) |
| **GitOps** | Flux CD (latest) |
| **CNI** | Cilium (eBPF) |
| **Secrets** | 1Password + External Secrets, SOPS/AGE |
| **Storage** | Rook-Ceph, OpenEBS, NFS |
| **Observability** | VictoriaMetrics K8s, VictoriaLogs, Fluent-bit, Grafana |
| **Ingress** | Envoy Gateway (Gateway API) |
| **SSO** | Authentik |

## Target Clusters

| Cluster | Purpose | Network | Nodes |
|---------|---------|---------|-------|
| **infra** | Platform services, observability, ArsipQ dev | 10.25.11.0/24 | 10.25.11.11-16 |
| **apps** | Business application workloads | 10.25.13.0/24 | 10.25.13.11-16 |

## User Journeys

### Journey 1: Daily Operations - The Unified Update

**Persona: Alex (Platform Operator)**

Alex manages the k8s-ops infrastructure and has just received a Renovate PR indicating that Cilium v1.18.3 is available. In the old days with two separate repos, this would have meant reviewing two PRs, merging them separately, and hoping both clusters updated without issues.

This morning is different. Alex opens the single Renovate PR in k8s-ops that updates `infrastructure/base/cilium/` - a shared component used by both clusters. The PR shows the Cilium changelog and the files affected. Alex reviews the changes, runs the Flux validation workflow in GitHub Actions, and merges with confidence.

Within minutes, Alex watches the Flux dashboard as the infra cluster picks up the change first. The staged rollout gives a 24-hour soak period before apps cluster updates automatically. By tomorrow, both clusters will be running the new Cilium version from a single merge. Alex spends the saved time actually improving the platform instead of doing duplicate work.

**Journey Reveals Requirements For:**
- Shared infrastructure base (`infrastructure/base/`)
- Unified Renovate configuration
- Staged rollout (infra → apps)
- Flux reconciliation monitoring
- GitHub Actions validation workflow

---

### Journey 2: Incident Response - The 3AM Alert

**Persona: Alex (Platform Operator)**

At 3:14 AM, Alex's phone buzzes with a VMAlertmanager notification: "Pod CrashLooping: arsipq-backend in apps cluster." Half-asleep, Alex opens the Grafana mobile app and navigates to the unified Application Health dashboard.

The cross-cluster view immediately shows the issue is isolated to apps cluster - infra cluster is healthy. Alex drills into the arsipq-backend metrics and sees memory usage spiked right before the crash. The VictoriaLogs panel shows the fatal error: "java.lang.OutOfMemoryError: Java heap space."

Alex SSHs into the environment, runs `task flux:suspend app=arsipq cluster=apps` to stop reconciliation, then opens a quick PR to increase the memory limit in `clusters/apps/apps/business/arsipq/`. After merging, `task flux:resume app=arsipq cluster=apps` brings the app back with the new limits.

The whole incident takes 12 minutes. The unified observability stack and consistent patterns meant Alex didn't waste time figuring out which cluster, which repo, or which observability tool to use.

**Journey Reveals Requirements For:**
- VMAlertmanager notification routing
- Cross-cluster Grafana dashboards (centralized on infra)
- VictoriaLogs for log analysis
- Unified .taskfiles for common operations
- Flux suspend/resume capability
- Cluster-specific app overrides (`clusters/apps/apps/`)

---

### Journey 3: New Application Deployment - Adding a Business App

**Persona: Alex (Platform Operator)**

A new internal tool needs to be deployed to the apps cluster. Alex opens the k8s-ops repo and examines how existing apps are structured.

The app base definitions live in `apps/base/` with HelmRelease, values, and Kustomization. The apps cluster configuration is in `clusters/apps/apps/` with overlays. Alex realizes deploying is straightforward: create the base in `apps/base/newtool/` and overlay in `clusters/apps/apps/newtool/` with cluster-specific values.

Alex creates the directories, defines the HelmRelease with the app's Helm chart, adds the reference to `clusters/apps/flux/apps.yaml`. A quick PR, passing validation, merge, and Flux reconciles the new app within 5 minutes.

No new Helm repository definitions needed (shared repos in infrastructure). No researching how to structure it. The pattern was already established and documented.

**Journey Reveals Requirements For:**
- Apps base/overlay pattern (`apps/base/`, `clusters/*/apps/`)
- Consistent HelmRelease structure
- Cluster-specific Flux entry points
- Pattern documentation
- Reusable component library

---

### Journey 4: ArsipQ Development - Kafka Integration Testing

**Persona: Dani (Backend Developer)**

Dani is developing a new event-driven feature for ArsipQ that publishes domain events to Kafka. The local development environment doesn't have Kafka, and setting it up locally would take hours.

Dani connects to the infra cluster where the ArsipQ platform is running. Using the Strimzi-managed Kafka cluster, Dani creates a new KafkaTopic CR for the feature and a KafkaUser for authentication. The Gatus dashboard confirms all platform services are healthy.

For the Spring Boot service, Dani uses the internal Kafka bootstrap address (`arsipq-kafka-kafka-bootstrap.arsipq-platform:9092`). The schema gets registered in Apicurio Registry, and Keycloak provides the JWT tokens for service authentication. Dani's feature works against real infrastructure without any local setup complexity.

When the feature is ready, the same Kafka topic definitions will work in any environment - the infrastructure is consistent and production-like from day one.

**Journey Reveals Requirements For:**
- Strimzi Kafka with self-service topic creation (infra cluster)
- Apicurio Registry for schemas
- Keycloak for authentication
- Gatus health monitoring
- Production-like dev environment
- Internal service discovery

---

### Journey 5: Cluster Onboarding - The Third Cluster

**Persona: Alex (Platform Operator - Future Scenario)**

Six months from now, the homelab has grown and Alex needs a third cluster for staging. Thanks to the k8s-ops patterns, this is a straightforward process.

Alex creates `clusters/staging/` by copying the structure from `clusters/apps/`. The Talos configs get adjusted for the new node IPs (10.25.12.0/24). The `flux/` directory references the same `infrastructure/base/` that infra and apps clusters use. For apps, Alex selects which ones staging needs by creating appropriate overlay references.

The helmfile bootstrap sequence is identical: Cilium → CoreDNS → cert-manager → Flux. Within 30 minutes, the new cluster is reconciling from k8s-ops. VMAgent starts sending metrics to infra cluster's VictoriaMetrics, and the unified Grafana dashboard now shows three clusters.

The pattern that started with two clusters scales effortlessly. Alex's documentation from the k8s-ops consolidation becomes the onboarding guide.

**Journey Reveals Requirements For:**
- Cluster directory template structure
- Reusable bootstrap sequence
- Shared infrastructure references
- Flexible app overlay selection
- Multi-cluster observability scaling (centralized on infra)
- Onboarding documentation

---

### Journey Requirements Summary

| Capability Area | Revealed By Journey |
|-----------------|---------------------|
| **Shared Infrastructure Base** | Daily Operations, New App Deployment |
| **Unified Renovate** | Daily Operations |
| **Staged Rollout (infra→apps)** | Daily Operations |
| **Cross-cluster Observability (centralized)** | Daily Operations, Incident Response |
| **VMAlertmanager Notifications** | Incident Response |
| **VictoriaLogs Integration** | Incident Response |
| **Unified .taskfiles** | Incident Response |
| **Flux Suspend/Resume** | Incident Response |
| **Apps Base/Overlay Pattern** | New App Deployment, Cluster Onboarding |
| **Cluster-specific Overrides** | Incident Response, New App Deployment |
| **Strimzi Kafka Self-service (infra)** | ArsipQ Development |
| **Apicurio Schema Registry** | ArsipQ Development |
| **Keycloak Authentication** | ArsipQ Development |
| **Gatus Health Monitoring** | ArsipQ Development |
| **Cluster Template Structure** | Cluster Onboarding |
| **Bootstrap Sequence** | Cluster Onboarding |
| **Onboarding Documentation** | Cluster Onboarding |

## Innovation & Novel Patterns

### Detected Innovation Areas

k8s-ops incorporates three differentiated patterns that go beyond standard GitOps implementations:

| Innovation | Description |
|------------|-------------|
| **Centralized Observability** | VictoriaMetrics on infra cluster with remote-write from apps |
| **GitOps Dev Platform** | Full Spring Boot infrastructure managed via Flux on infra cluster |
| **Staged Rollout** | Automated infra→apps promotion with soak time |

---

### Innovation 1: Centralized Observability with VictoriaMetrics

**What's Different:**
Rather than the typical per-cluster Prometheus + Loki stack, k8s-ops adopts a **centralized observability pattern** with VictoriaMetrics K8s Operator and VictoriaLogs on the infra cluster:

- Full VictoriaMetrics stack runs only on infra cluster (storage, query, alerting)
- Apps cluster runs lightweight VMAgent + Fluent-bit (collection only)
- Remote-write pattern sends metrics/logs to centralized storage
- Single Grafana instance provides cross-cluster visibility
- 40% reduction in resource usage compared to per-cluster Prometheus stacks

**Why It Matters:**
- Lighter footprint on apps cluster (no storage overhead)
- Single pane of glass for all clusters
- Simpler architecture (no federation complexity)
- MetricsQL compatibility means existing knowledge transfers
- VictoriaLogs provides unified logging without Loki's complexity

**Validation Approach:**
- Compare resource usage: VictoriaMetrics vs previous Prometheus
- Measure query latency for cross-cluster queries
- Validate remote-write reliability from apps cluster

**Risk Mitigation:**
- VictoriaMetrics has strong community adoption and commercial backing
- Fallback: PromQL compatibility means Prometheus could be restored
- Apps cluster can cache locally if infra cluster unreachable

---

### Innovation 2: GitOps-Managed Dev Platform

**What's Different:**
Most development platforms are either:
- Local (Docker Compose) - not production-like
- Managed services (AWS RDS, Confluent) - expensive, different from prod
- Manually deployed - configuration drift, inconsistency

k8s-ops deploys a **full Spring Boot development platform via GitOps** on infra cluster:
- CloudNativePG PostgreSQL (3-replica HA cluster)
- Strimzi Kafka (KRaft mode, 3 controllers + 3 brokers)
- Existing MinIO (S3-compatible storage on internal network)
- Keycloak (OIDC/SSO)
- OpenBao (secrets management)
- Apicurio Registry (schema registry)

All managed through FluxCD with the same patterns as production infrastructure.

**Why It Matters:**
- Dev environment matches production patterns exactly
- Infrastructure-as-code means reproducible, version-controlled dev platform
- Developers get production-grade services without local setup complexity
- Same deployment patterns for dev platform as business applications

**Validation Approach:**
- ArsipQ backend successfully connects to all platform services
- Platform survives cluster rebuild (all state in Git + persistent volumes)
- Developer onboarding time for platform access < 15 minutes

**Risk Mitigation:**
- Operators are production-grade (CNPG, Strimzi widely used)
- Gatus health monitoring provides early warning
- Platform is on infra cluster (doesn't affect apps cluster workloads)

---

### Innovation 3: Staged Rollout with Automated Soak Time

**What's Different:**
Standard GitOps applies changes to all clusters simultaneously or requires manual promotion. k8s-ops implements **automated staged rollout with soak time**:

```
Git Push → Infra Cluster (immediate) → 24h Soak → Apps Cluster (automatic)
```

**Implementation Pattern:**
- Shared components in `infrastructure/base/` and `apps/base/`
- Infra cluster Kustomization has no delay
- Apps cluster Kustomization has `dependsOn` relationship with infra
- Flux interval configured for 24-hour propagation delay

**Why It Matters:**
- Changes validated in real environment before apps cluster
- Automated promotion reduces manual toil
- Single merge triggers both deployments with safety gap
- Easy to adjust soak time (1h for hotfixes, 48h for major changes)

**Validation Approach:**
- Track time-to-apps-cluster for shared component updates
- Measure incidents caught in infra soak period before apps impact
- Validate manual override works (force immediate apps update when needed)

**Risk Mitigation:**
- `flux suspend` immediately stops apps cluster propagation
- Git revert rolls back both clusters
- Apps cluster can diverge temporarily with cluster-specific overlay

---

### Innovation Summary

| Innovation | Risk Level | Validation Method |
|------------|------------|-------------------|
| VictoriaMetrics Observability | Low | Resource comparison, query latency |
| GitOps Dev Platform | Medium | Service connectivity, rebuild survival |
| Staged Rollout | Low | Time tracking, incident prevention |

## Infrastructure-Specific Requirements

### Project-Type Overview

k8s-ops is an Infrastructure-as-Code platform managing multiple Talos Linux Kubernetes clusters via FluxCD GitOps. Unlike traditional application projects, the "product" is the infrastructure itself - the patterns, automation, and operational capabilities that enable workload deployment.

### Cluster Architecture

| Component | Specification |
|-----------|---------------|
| **Operating System** | Talos Linux v1.12.0 (immutable, API-driven) |
| **Kubernetes Version** | v1.35.0 (included in Talos 1.12.0) |
| **Cluster Topology** | Multi-node HA (control plane + workers) |
| **Node Count** | 6 nodes per cluster (10.25.11.11-16, 10.25.13.11-16) |
| **Network MTU** | 9000 (jumbo frames) |
| **Bonding** | LACP 802.3ad |

### Network Topology

| Cluster/Service | Subnet | Gateway | VLAN |
|-----------------|--------|---------|------|
| **infra** | 10.25.11.0/24 | 10.25.11.1 | 2511 |
| **apps** | 10.25.13.0/24 | 10.25.13.1 | 2513 |
| **MinIO (existing)** | Internal network | Direct access | - |

**Note:** MinIO is a pre-existing service on the internal network, accessible from both clusters via `s3.monosense.dev`.

### Networking Stack

| Layer | Technology | Version | Configuration |
|-------|------------|---------|---------------|
| **CNI** | Cilium | v1.16+ | eBPF native routing, no overlay |
| **Ingress** | Envoy Gateway | v1.6+ | Gateway API v1.0+ |
| **Load Balancer** | Cilium BGP Control Plane | - | BGP peering with upstream router |
| **Upstream Router** | Juniper SRX 320 | JUNOS 21.4R3-S4.9 | BGP peer for service IPs |
| **Service Mesh** | None | - | Out of scope; clusters operate independently |
| **DNS (Internal)** | CoreDNS | latest | Cluster DNS resolution |
| **DNS (External)** | External-DNS | latest | Cloudflare + bind9 (split DNS) |
| **Tunnel** | Cloudflare Tunnel | latest | Secure external access without public IPs |

**BGP Configuration:**
- Cilium BGP Control Plane announces LoadBalancer service IPs to Juniper SRX
- Each cluster has dedicated ASN for BGP peering
- Upstream router redistributes service IPs to network

**DNS Strategy (Split DNS):**
- **External**: External-DNS updates Cloudflare for public DNS
- **Internal**: External-DNS updates bind9 for internal DNS resolution
- **Cloudflare Tunnel**: Secure ingress for external access without exposing public IPs
- **Domains**: `*.monosense.dev` (infra), `*.monosense.io` (apps)

**Key Decision: Envoy Gateway vs Cilium Gateway**

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Gateway Controller | Envoy Gateway | More mature Gateway API implementation; ArsipQ requires advanced routing (rate limiting, header manipulation) |
| Alternative Considered | Cilium Gateway API | Less mature; would simplify stack but lacks features needed |

### Network Policies

Cilium NetworkPolicies enforced for pod-to-pod isolation:

| Policy Type | Scope |
|-------------|-------|
| **Default Deny** | All namespaces (explicit allow required) |
| **Namespace Isolation** | Pods can only communicate within namespace by default |
| **Ingress Allow** | Explicit policies for ingress controller access |
| **Monitoring Allow** | VictoriaMetrics scraping permitted across namespaces |
| **System Namespaces** | kube-system, flux-system exempt for operations |

**Debug Bypass (Emergency Use Only):**
```bash
# Temporarily disable policies for a namespace (debugging only)
kubectl annotate ns <namespace> policy.cilium.io/enforce=false

# Re-enable after debugging
kubectl annotate ns <namespace> policy.cilium.io/enforce-
```

**Policy Validation:**
- Cilium connectivity tests run post-deployment
- `cilium connectivity test` validates policy enforcement

### Resource Management

| Resource | Configuration |
|----------|---------------|
| **Namespace Quotas** | Enforced per-namespace to prevent resource starvation |
| **LimitRanges** | Default requests/limits for pods without explicit settings |
| **Priority Classes** | System-critical, cluster-services, application (default) |

### Storage Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Block Storage** | Rook-Ceph | Persistent volumes (RWO) |
| **Shared Storage** | NFS | ReadWriteMany volumes |
| **Object Storage** | MinIO (infra cluster) | S3-compatible, general storage (NOT backups) |
| **Backup Storage** | Cloudflare R2 | VolSync + CNPG Barman backup destination |
| **Local Storage** | OpenEBS | Node-local volumes, CNPG PostgreSQL (local NVMe) |

### Backup Strategy

| Component | Method | Destination |
|-----------|--------|-------------|
| **PVC Backups** | VolSync (Restic) | Cloudflare R2 |
| **Database Backups** | CNPG Barman | Cloudflare R2 |
| **Cluster State** | Git (FluxCD) | GitHub repository |
| **Secrets** | 1Password | External vault (source of truth) |
| **Talos Config** | Git + SOPS | Encrypted in repository |

**Cloudflare R2 Backup Target:**

| Setting | Value |
|---------|-------|
| **Endpoint** | `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com` |
| **VolSync Bucket** | Per-app buckets |
| **CNPG Buckets** | `cnpg-infra/`, `cnpg-apps/` |
| **Retention** | VolSync: 24 hourly, 7 daily; CNPG: 30 days |

**VolSync Configuration:**
- Restic-based incremental backups to Cloudflare R2
- Schedule: every 8 hours for stateful apps
- Ceph block snapshots for local quick recovery

**CNPG Barman Configuration:**
- Continuous WAL archiving to R2
- Daily scheduled base backups
- bzip2 compression
- 30-day retention

**Note:** MinIO (on infra cluster) is for general S3 storage needs only, NOT backup destination.

**Data Restore Time Estimate:**

| Data Size | Estimated Restore Time |
|-----------|------------------------|
| < 10 GB | < 15 minutes |
| 10-50 GB | 15-60 minutes |
| 50-200 GB | 1-4 hours |
| > 200 GB | 4+ hours (network dependent) |

### Secrets Management

| Layer | Technology | Scope |
|-------|------------|-------|
| **External Vault** | 1Password | Source of truth for all secrets |
| **Kubernetes Sync** | External Secrets Operator | Pulls from 1Password to K8s Secrets |
| **Git Encryption** | SOPS + AGE | Encrypts sensitive files in repo |
| **Runtime Secrets** | Kubernetes Secrets | Created by External Secrets |

**AGE Key Storage:**

| Key Type | Location |
|----------|----------|
| **Private Key** | 1Password vault (never in Git) |
| **Public Key** | Repository `.sops.yaml` |

**Secret Flow:**
```
1Password → External Secrets Operator → Kubernetes Secret → Pod
```

### TLS & Certificate Management

| Component | Configuration |
|-----------|---------------|
| **Issuer** | cert-manager with Let's Encrypt |
| **ACME Challenge** | DNS-01 via Cloudflare |
| **Wildcard Certs** | `*.monosense.io`, `*.monosense.dev` |
| **Internal Certs** | Self-signed CA for internal services |
| **Renewal** | Automatic (30 days before expiry) |

### Domain Configuration

| Pattern | Example | Cluster |
|---------|---------|---------|
| **`{app}.monosense.dev`** | `grafana.monosense.dev` | Infra |
| **`{app}.monosense.io`** | `odoo.monosense.io` | Apps |

**Subdomain Naming Convention:**
- Infra cluster (platform services): `{service}.monosense.dev`
- Apps cluster (business apps): `{service}.monosense.io`

### Talos API Access

| Method | Use Case |
|--------|----------|
| **talosctl** | Node management, upgrades, troubleshooting |
| **Kubeconfig** | Generated via `talosctl kubeconfig` |
| **Endpoint** | Control plane VIP or individual node IPs |

**Bootstrap Access Pattern:**
1. Generate Talos secrets with `talhelper`
2. Apply machine configs via `talosctl apply-config`
3. Bootstrap first control plane node
4. Retrieve kubeconfig for kubectl access
5. Additional nodes join via machine config

### GitOps Configuration

| Aspect | Configuration |
|--------|---------------|
| **Git Provider** | GitHub |
| **Repository** | k8s-ops (monorepo) |
| **Branch Strategy** | main (single branch, PR-based changes) |
| **Reconciliation Interval** | 5 minutes (default) |
| **Drift Detection** | Enabled (Flux auto-remediation) |

### Bootstrap Sequence

**Phase 1: Helmfile Bootstrap (Pre-Flux)**
```
1. Cilium CNI        → Cluster networking
2. CoreDNS           → DNS resolution
3. cert-manager      → TLS certificates (CRDs only)
4. Flux              → GitOps controller
```

**Phase 2: Flux Reconciliation (Post-Bootstrap)**
```
5. External Secrets  → 1Password integration
6. Rook-Ceph         → Storage provisioning (uses OpenEBS for monitors initially)
7. VictoriaMetrics   → Observability
8. Applications      → All remaining workloads
```

**Note:** Rook-Ceph monitors use OpenEBS/hostPath initially, then migrate to Ceph once cluster is healthy.

### Operational Validation

| Test | Frequency | Success Criteria |
|------|-----------|------------------|
| **Cilium connectivity** | Post-deploy, post-upgrade | All connectivity tests pass |
| **VolSync restore** | Monthly | PVC restored, data verified, app functional |
| **Bootstrap smoke** | Per release | Fresh cluster to Flux Ready < 30 min |
| **Secret rotation** | Quarterly | 1Password change → pod picks up new value < 10 min |
| **Network policy audit** | Monthly | Policies match documented baseline |

### Runbook References

| Component | Runbook Location |
|-----------|------------------|
| **Rook-Ceph** | `docs/runbooks/rook-ceph.md` |
| **Cilium** | `docs/runbooks/cilium.md` |
| **Flux** | `docs/runbooks/flux.md` |
| **Talos** | `docs/runbooks/talos.md` |
| **VictoriaMetrics** | `docs/runbooks/victoria-metrics.md` |
| **Disaster Recovery** | `docs/runbooks/disaster-recovery.md` |

### Implementation Considerations

| Consideration | Approach |
|---------------|----------|
| **Cluster Rebuild** | Full rebuild from Git: < 1 hour (+ data restore time per table above) |
| **Node Replacement** | Talos machine config in Git, join via API |
| **Upgrade Strategy** | Rolling updates via Talos API, staged (dev 24h → prod) |
| **Disaster Recovery** | Git + VolSync + 1Password = full state recovery |
| **Multi-cluster Management** | Independent Flux per cluster, shared repo |

## Project Scoping & Risk Management

### MVP Strategy & Philosophy

**MVP Approach:** Platform MVP - Build the foundation for multi-cluster management with immediate operational value.

**Rationale:** k8s-ops is infrastructure, not a product with users to acquire. The "MVP" is the minimum infrastructure that:
1. Replaces the previous two-repo workflow
2. Runs all existing workloads
3. Provides unified observability
4. Enables ArsipQ development

### Resource Requirements by Phase

| Phase | Effort | Primary Skills | Dependencies |
|-------|--------|----------------|--------------|
| **1: Foundation** | ~40 hours | Talos, FluxCD, Kustomize | None |
| **2: Apps Cluster** | ~20 hours | Same as Phase 1 | Phase 1 complete |
| **3: Observability** | ~30 hours | VictoriaMetrics, Grafana, Fluent-bit | Phases 1-2 complete |
| **4: Dev Platform** | ~25 hours | Strimzi, Keycloak, OpenBao | Phase 1 complete (infra cluster) |

**Total Estimated Effort:** ~115 hours (single operator)

**Note:** Phases 3 and 4 can run in parallel after Phase 1 is complete.

### Phase Dependencies

```
Phase 1 (Foundation)
    ├── Phase 2 (Production) ──────────────────┐
    │                                          │
    ├── Phase 3 (Observability) ───────────────┼── All Complete
    │                                          │
    └── Phase 4 (Dev Platform) ────────────────┘
```

**Critical Path:** Phase 1 → Phase 2 → Done (core functionality)
**Parallel Tracks:** Phase 3 and Phase 4 can proceed independently after Phase 1

### Risk Assessment & Mitigation

#### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Rook-Ceph bootstrap failure** | Medium | High | OpenEBS fallback for initial storage; documented recovery procedure |
| **VictoriaMetrics migration issues** | Low | Medium | PromQL compatibility; can revert to Prometheus if needed |
| **Cilium version incompatibility** | Low | High | Pin to tested version; test in dev before prod |
| **ArsipQ operator conflicts** | Medium | Low | Dev cluster only; doesn't affect core infrastructure |
| **SOPS/AGE key issues** | Low | Critical | Key in 1Password; documented recovery; test decrypt before bootstrap |

#### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Extended downtime during rebuild** | Medium | Low | Downtime accepted; no SLA for home lab |
| **Data loss during migration** | Low | High | VolSync backups verified before starting; MinIO on separate infra |
| **Configuration drift after go-live** | Low | Medium | Flux drift detection; GitOps enforcement |
| **Single operator bottleneck** | High | Medium | Comprehensive documentation; runbooks for common tasks |

#### External Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **1Password outage** | Low | Medium | Secrets cached in cluster; don't delete existing secrets during outage |
| **GitHub outage** | Low | Medium | Flux continues with last-known state; local git clone as backup |
| **Upstream component deprecation** | Low | Low | Renovate tracks updates; community-supported projects only |

### Contingency Plans

#### If Phase 1 Fails
- **Symptom:** Infra cluster won't bootstrap or reconcile
- **Action:** Restore home-ops repo; debug k8s-ops in isolation
- **Recovery:** Fix issues, retry bootstrap

#### If Phase 2 Fails
- **Symptom:** Apps cluster issues after migration
- **Action:** Apps cluster can run independently; restore prod-ops if critical
- **Recovery:** Infra cluster validates changes before apps retry

#### If Phase 3 Fails
- **Symptom:** VictoriaMetrics not scraping or dashboards broken
- **Action:** Clusters still functional; observability is enhancement
- **Recovery:** Revert to kube-prometheus-stack temporarily; debug VM issues

#### If Phase 4 Fails
- **Symptom:** ArsipQ platform components not healthy
- **Action:** Infra cluster still works for other workloads
- **Recovery:** Debug operator issues; ArsipQ development can use local Docker Compose temporarily

### Scope Boundaries

#### Explicitly IN Scope
- Repository consolidation and restructuring
- Both clusters operational with all existing apps
- VictoriaMetrics observability stack
- ArsipQ development platform
- Unified Renovate and tooling
- Comprehensive documentation

#### Explicitly OUT of Scope (Deferred)
- Cross-cluster service mesh
- Multi-cluster Flux federation
- Automated cluster provisioning (Cluster API)
- Cost optimization/resource right-sizing
- Comprehensive alerting runbooks (Growth feature)
- Self-service developer portal (Vision feature)

### Success Criteria Alignment

| Phase | Maps to Success Criteria |
|-------|-------------------------|
| **Phase 1** | Dev cluster Flux reconciling; Renovate PRs; Secrets syncing |
| **Phase 2** | Prod cluster reconciling; Shared component propagation |
| **Phase 3** | VictoriaMetrics scraping 100%; Dashboards functional |
| **Phase 4** | All ArsipQ operators healthy; Gatus green |

## Functional Requirements

### Repository & GitOps Management

- **FR1:** Operator can manage both clusters from a single Git repository
- **FR2:** Operator can define shared infrastructure components in a base directory that applies to all clusters
- **FR3:** Operator can create cluster-specific overrides without duplicating base configurations
- **FR4:** Operator can view Flux reconciliation status for all clusters
- **FR5:** Operator can trigger manual reconciliation when needed
- **FR6:** Operator can suspend and resume Flux reconciliation per application or cluster
- **FR7:** Operator can receive consolidated Renovate PRs for shared dependencies
- **FR8:** Operator can validate Flux manifests via GitHub Actions before merge
- **FR9:** Operator can configure Renovate to group updates by type (patch/minor/major)
- **FR10:** Operator can compose applications using reusable Kustomize components
- **FR11:** Operator can enforce PR reviews before changes apply to clusters
- **FR12:** Flux can automatically decrypt SOPS-encrypted files during reconciliation

### Cluster Lifecycle Management

- **FR13:** Operator can bootstrap a new cluster using documented helmfile sequence
- **FR14:** Operator can generate Talos machine configurations from templates
- **FR15:** Operator can apply Talos configurations via API without manual node access
- **FR16:** Operator can upgrade Talos nodes with rolling updates
- **FR17:** Operator can add or remove nodes from a cluster via configuration
- **FR18:** Operator can onboard a new cluster by copying existing cluster structure
- **FR19:** Operator can decommission a cluster by removing its configuration directory
- **FR20:** Operator can generate kubeconfig from Talos control plane

### Shared Infrastructure Management

- **FR21:** Operator can deploy Cilium CNI with eBPF and native routing
- **FR22:** Operator can configure network policies with default-deny and explicit allows
- **FR23:** Operator can temporarily bypass network policies for debugging
- **FR24:** Operator can audit network policy state against documented baseline
- **FR25:** Operator can allocate LoadBalancer IPs from defined Cilium IP pools
- **FR26:** Operator can provision block storage via Rook-Ceph
- **FR27:** Operator can provision shared storage via NFS
- **FR28:** Operator can view Ceph cluster health status and OSD state
- **FR29:** Operator can expand Rook-Ceph storage pool capacity
- **FR30:** Operator can configure namespace resource quotas and limit ranges
- **FR31:** Operator can assign workloads to priority classes (system-critical, cluster-services, application)
- **FR32:** Operator can deploy cert-manager with Let's Encrypt DNS-01 validation
- **FR33:** Operator can configure wildcard certificates for cluster domains

### Application Deployment

- **FR34:** Operator can deploy applications using HelmRelease resources
- **FR35:** Operator can define application bases with cluster-specific overlays
- **FR36:** Operator can configure application-specific ingress routes via Gateway API
- **FR37:** Operator can set application resource requests and limits
- **FR38:** Operator can configure application dependencies via Flux `dependsOn`
- **FR39:** Operator can deploy an application to a new cluster by creating overlay directory
- **FR40:** Operator can view HelmRelease error messages and remediation status

### Observability & Monitoring

- **FR41:** Operator can view metrics from both clusters in unified Grafana dashboards
- **FR42:** Operator can query logs from both clusters via VictoriaLogs
- **FR43:** Operator can query historical metrics for specific pods, services, or time ranges
- **FR44:** Operator can receive alerts via VMAlertmanager notifications
- **FR45:** Operator can view Cluster Overview dashboard showing node health and resource usage
- **FR46:** Operator can view Flux GitOps dashboard showing reconciliation status
- **FR47:** Operator can view Application Health dashboard showing pod status and restarts
- **FR48:** Operator can configure scrape targets for VictoriaMetrics
- **FR49:** Operator can configure log collection via Fluent-bit
- **FR50:** Operator can view connectivity test results via CLI or dashboard
- **FR51:** Operator can automatically create DNS records when Gateway/HTTPRoute resources are created

### Secret & Certificate Management

- **FR52:** Operator can store secrets in 1Password as source of truth
- **FR53:** Operator can sync secrets from 1Password to Kubernetes via External Secrets
- **FR54:** Operator can encrypt sensitive files in Git using SOPS with AGE
- **FR55:** Operator can rotate secrets by updating 1Password (auto-sync to cluster)
- **FR56:** Operator can manage AGE private key securely in 1Password
- **FR57:** Operator can issue and renew TLS certificates automatically

### Backup & Recovery

- **FR58:** Operator can configure PVC backups to Cloudflare R2 via VolSync
- **FR59:** Operator can set backup schedules per PVC (every 8 hours default)
- **FR60:** Operator can restore PVCs from VolSync backups
- **FR61:** Operator can rebuild entire cluster from Git + VolSync + 1Password
- **FR62:** Operator can verify backup integrity via restore tests
- **FR63:** Operator can run automated backup validation job on schedule

### Staged Rollout

- **FR64:** Operator can configure infra cluster to receive updates immediately
- **FR65:** Operator can configure apps cluster to receive updates after soak period
- **FR66:** Operator can override staged rollout for urgent changes
- **FR67:** Operator can roll back changes by reverting Git commits

### ArsipQ Development Platform (Infra Cluster)

- **FR68:** Developer can connect to PostgreSQL cluster managed by CloudNativePG
- **FR69:** Developer can create Kafka topics via KafkaTopic custom resources
- **FR70:** Developer can register schemas in Apicurio Registry
- **FR71:** Developer can authenticate via Keycloak OIDC
- **FR72:** Developer can store application secrets in OpenBao
- **FR73:** Developer can access S3-compatible storage via external MinIO
- **FR74:** Developer can view ArsipQ platform health via Gatus dashboard
- **FR75:** Developer can deploy Spring Boot applications to infra cluster via GitOps
- **FR76:** Developer can view application logs filtered by namespace/pod in VictoriaLogs

### Operational Tasks & Validation

- **FR77:** Operator can run common tasks via unified .taskfiles
- **FR78:** Operator can access runbooks for major components
- **FR79:** Operator can perform Cilium connectivity tests to validate networking
- **FR80:** Operator can test secret rotation end-to-end
- **FR81:** Operator can validate complete cluster bootstrap within target time
- **FR82:** Operator can verify secret propagation from 1Password to running pods
- **FR83:** Operator can verify node upgrade success before proceeding to next node

## Non-Functional Requirements

### Performance

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **NFR1:** Flux incremental reconciliation | < 5 minutes | Time from Git push to resources applied |
| **NFR2:** Flux full cluster bootstrap | < 30 minutes | Time from empty cluster to all resources Ready |
| **NFR3:** VictoriaMetrics query response | < 2 seconds | 95th percentile for dashboard queries |
| **NFR4:** VictoriaLogs search response | < 5 seconds | 95th percentile for log searches |
| **NFR5:** External Secrets sync | < 5 minutes | Time from 1Password change to Secret update |
| **NFR6:** Certificate renewal | Automatic | 30+ days before expiry |
| **NFR7:** Talos node boot | < 3 minutes | Time from power-on to kubelet Ready |

### Security

| Requirement | Specification |
|-------------|---------------|
| **NFR8:** No secrets in Git | All sensitive values encrypted with SOPS or stored in 1Password |
| **NFR9:** Network isolation | Default-deny network policies; explicit allow required |
| **NFR10:** Secrets at rest | All Kubernetes Secrets encrypted via Talos encryption provider |
| **NFR11:** Secrets in transit | All internal communication over TLS or mTLS |
| **NFR12:** External TLS | All public endpoints use valid Let's Encrypt certificates |
| **NFR13:** AGE key security | Private key stored only in 1Password; never in Git or filesystem |
| **NFR14:** RBAC enforcement | No cluster-admin bindings for applications |
| **NFR15:** Image provenance | Prefer images from trusted registries (Harbor, ghcr.io) |

### Reliability

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **NFR16:** Flux reconciliation success | 99% | Percentage of reconciliations without error |
| **NFR17:** Rook-Ceph availability | 99.9% | Ceph cluster HEALTH_OK uptime |
| **NFR18:** Pod restart frequency | < 5/day per cluster | Excludes CronJobs and expected restarts |
| **NFR19:** Backup success rate | 100% | VolSync jobs completing without error |
| **NFR20:** Cluster recovery | < 2 hours | Full cluster rebuild from Git + VolSync |
| **NFR21:** Zero drift tolerance | 100% | All resources match Git state (Flux enforcement) |
| **NFR22:** Storage redundancy | 3 replicas | Rook-Ceph replication factor |

### Maintainability

| Requirement | Specification |
|-------------|---------------|
| **NFR23:** Pattern consistency | All apps follow base/overlay Kustomize pattern |
| **NFR24:** Documentation coverage | Runbooks exist for all major components |
| **NFR25:** Naming conventions | Consistent resource naming across clusters |
| **NFR26:** Version pinning | All Helm charts and images pinned to specific versions |
| **NFR27:** Renovate automation | Dependency updates automated via Renovate PRs |
| **NFR28:** Code review | All changes require PR review before merge |
| **NFR29:** Taskfile coverage | Common operations available via unified .taskfiles |

### Resource Efficiency

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR30:** Control plane overhead | < 2 GB RAM per controller | Home lab resource constraints |
| **NFR31:** Observability overhead | < 4 GB RAM total | VictoriaMetrics lighter than Prometheus |
| **NFR32:** Operator footprint | < 500 MB RAM each | CNPG, Strimzi, etc. |
| **NFR33:** Storage efficiency | Thin provisioning | Rook-Ceph uses only allocated space |

### Integration

| Requirement | Specification |
|-------------|---------------|
| **NFR34:** 1Password connectivity | External Secrets Operator maintains connection; retry on failure |
| **NFR35:** GitHub connectivity | Flux retries with exponential backoff on failure |
| **NFR36:** Cloudflare DNS | External-DNS updates DNS within 60 seconds of ingress creation |
| **NFR37:** Cloudflare R2 connectivity | VolSync and CNPG Barman connect to R2 for backups; S3 API compatibility verified |
| **NFR38:** Renovate integration | PRs auto-created within 24 hours of new releases |

### Operational

| Requirement | Specification |
|-------------|---------------|
| **NFR39:** Staged rollout | Infra cluster receives updates 24 hours before apps cluster |
| **NFR40:** Rollback capability | Any change reversible via Git revert within 5 minutes |
| **NFR41:** Alert notification | VMAlertmanager delivers notifications within 1 minute of trigger |
| **NFR42:** Log retention | VictoriaLogs retains logs for 30 days minimum |
| **NFR43:** Metric retention | VictoriaMetrics retains metrics for 90 days minimum |

