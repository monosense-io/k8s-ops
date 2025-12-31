---
stepsCompleted: [1, 2, 3, 4]
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# k8s-ops - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for k8s-ops, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Repository & GitOps Management (FR1-FR12)**

- FR1: Operator can manage both clusters from a single Git repository
- FR2: Operator can define shared infrastructure components in a base directory that applies to all clusters
- FR3: Operator can create cluster-specific overrides without duplicating base configurations
- FR4: Operator can view Flux reconciliation status for all clusters
- FR5: Operator can trigger manual reconciliation when needed
- FR6: Operator can suspend and resume Flux reconciliation per application or cluster
- FR7: Operator can receive consolidated Renovate PRs for shared dependencies
- FR8: Operator can validate Flux manifests via GitHub Actions before merge
- FR9: Operator can configure Renovate to group updates by type (patch/minor/major)
- FR10: Operator can compose applications using reusable Kustomize components
- FR11: Operator can enforce PR reviews before changes apply to clusters
- FR12: Flux can automatically decrypt SOPS-encrypted files during reconciliation

**Cluster Lifecycle Management (FR13-FR20)**

- FR13: Operator can bootstrap a new cluster using documented helmfile sequence
- FR14: Operator can generate Talos machine configurations from templates
- FR15: Operator can apply Talos configurations via API without manual node access
- FR16: Operator can upgrade Talos nodes with rolling updates
- FR17: Operator can add or remove nodes from a cluster via configuration
- FR18: Operator can onboard a new cluster by copying existing cluster structure
- FR19: Operator can decommission a cluster by removing its configuration directory
- FR20: Operator can generate kubeconfig from Talos control plane

**Shared Infrastructure Management (FR21-FR33)**

- FR21: Operator can deploy Cilium CNI with eBPF and native routing
- FR22: Operator can configure network policies with default-deny and explicit allows
- FR23: Operator can temporarily bypass network policies for debugging
- FR24: Operator can audit network policy state against documented baseline
- FR25: Operator can allocate LoadBalancer IPs from defined Cilium IP pools
- FR26: Operator can provision block storage via Rook-Ceph
- FR27: Operator can provision shared storage via NFS
- FR28: Operator can view Ceph cluster health status and OSD state
- FR29: Operator can expand Rook-Ceph storage pool capacity
- FR30: Operator can configure namespace resource quotas and limit ranges
- FR31: Operator can assign workloads to priority classes (system-critical, cluster-services, application)
- FR32: Operator can deploy cert-manager with Let's Encrypt DNS-01 validation
- FR33: Operator can configure wildcard certificates for cluster domains

**Application Deployment (FR34-FR40)**

- FR34: Operator can deploy applications using HelmRelease resources
- FR35: Operator can define application bases with cluster-specific overlays
- FR36: Operator can configure application-specific ingress routes via Gateway API
- FR37: Operator can set application resource requests and limits
- FR38: Operator can configure application dependencies via Flux `dependsOn`
- FR39: Operator can deploy an application to a new cluster by creating overlay directory
- FR40: Operator can view HelmRelease error messages and remediation status

**Observability & Monitoring (FR41-FR51)**

- FR41: Operator can view metrics from both clusters in unified Grafana dashboards
- FR42: Operator can query logs from both clusters via VictoriaLogs
- FR43: Operator can query historical metrics for specific pods, services, or time ranges
- FR44: Operator can receive alerts via VMAlertmanager notifications
- FR45: Operator can view Cluster Overview dashboard showing node health and resource usage
- FR46: Operator can view Flux GitOps dashboard showing reconciliation status
- FR47: Operator can view Application Health dashboard showing pod status and restarts
- FR48: Operator can configure scrape targets for VictoriaMetrics
- FR49: Operator can configure log collection via Fluent-bit
- FR50: Operator can view connectivity test results via CLI or dashboard
- FR51: Operator can automatically create DNS records when Gateway/HTTPRoute resources are created

**Secret & Certificate Management (FR52-FR57)**

- FR52: Operator can store secrets in 1Password as source of truth
- FR53: Operator can sync secrets from 1Password to Kubernetes via External Secrets
- FR54: Operator can encrypt sensitive files in Git using SOPS with AGE
- FR55: Operator can rotate secrets by updating 1Password (auto-sync to cluster)
- FR56: Operator can manage AGE private key securely in 1Password
- FR57: Operator can issue and renew TLS certificates automatically

**Backup & Recovery (FR58-FR63)**

- FR58: Operator can configure PVC backups to Cloudflare R2 via VolSync
- FR59: Operator can set backup schedules per PVC (every 8 hours default)
- FR60: Operator can restore PVCs from VolSync backups
- FR61: Operator can rebuild entire cluster from Git + VolSync + 1Password
- FR62: Operator can verify backup integrity via restore tests
- FR63: Operator can run automated backup validation job on schedule

**Staged Rollout (FR64-FR67)**

- FR64: Operator can configure infra cluster to receive updates immediately
- FR65: Operator can configure apps cluster to receive updates after soak period
- FR66: Operator can override staged rollout for urgent changes
- FR67: Operator can roll back changes by reverting Git commits

**ArsipQ Development Platform - Infra Cluster (FR68-FR76)**

- FR68: Developer can connect to PostgreSQL cluster managed by CloudNativePG
- FR69: Developer can create Kafka topics via KafkaTopic custom resources
- FR70: Developer can register schemas in Apicurio Registry
- FR71: Developer can authenticate via Keycloak OIDC
- FR72: Developer can store application secrets in OpenBao
- FR73: Developer can access S3-compatible storage via external MinIO
- FR74: Developer can view ArsipQ platform health via Gatus dashboard
- FR75: Developer can deploy Spring Boot applications to infra cluster via GitOps
- FR76: Developer can view application logs filtered by namespace/pod in VictoriaLogs

**Operational Tasks & Validation (FR77-FR83)**

- FR77: Operator can run common tasks via unified .taskfiles
- FR78: Operator can access runbooks for major components
- FR79: Operator can perform Cilium connectivity tests to validate networking
- FR80: Operator can test secret rotation end-to-end
- FR81: Operator can validate complete cluster bootstrap within target time
- FR82: Operator can verify secret propagation from 1Password to running pods
- FR83: Operator can verify node upgrade success before proceeding to next node

### NonFunctional Requirements

**Performance (NFR1-NFR7)**

- NFR1: Flux incremental reconciliation < 5 minutes (time from Git push to resources applied)
- NFR2: Flux full cluster bootstrap < 30 minutes (time from empty cluster to all resources Ready)
- NFR3: VictoriaMetrics query response < 2 seconds (95th percentile for dashboard queries)
- NFR4: VictoriaLogs search response < 5 seconds (95th percentile for log searches)
- NFR5: External Secrets sync < 5 minutes (time from 1Password change to Secret update)
- NFR6: Certificate renewal automatic (30+ days before expiry)
- NFR7: Talos node boot < 3 minutes (time from power-on to kubelet Ready)

**Security (NFR8-NFR15)**

- NFR8: No secrets in Git - All sensitive values encrypted with SOPS or stored in 1Password
- NFR9: Network isolation - Default-deny network policies; explicit allow required
- NFR10: Secrets at rest - All Kubernetes Secrets encrypted via Talos encryption provider
- NFR11: Secrets in transit - All internal communication over TLS or mTLS
- NFR12: External TLS - All public endpoints use valid Let's Encrypt certificates
- NFR13: AGE key security - Private key stored only in 1Password; never in Git or filesystem
- NFR14: RBAC enforcement - No cluster-admin bindings for applications
- NFR15: Image provenance - Prefer images from trusted registries (Harbor, ghcr.io)

**Reliability (NFR16-NFR22)**

- NFR16: Flux reconciliation success 99% (percentage of reconciliations without error)
- NFR17: Rook-Ceph availability 99.9% (Ceph cluster HEALTH_OK uptime)
- NFR18: Pod restart frequency < 5/day per cluster (excludes CronJobs and expected restarts)
- NFR19: Backup success rate 100% (VolSync jobs completing without error)
- NFR20: Cluster recovery < 2 hours (full cluster rebuild from Git + VolSync)
- NFR21: Zero drift tolerance 100% (all resources match Git state via Flux enforcement)
- NFR22: Storage redundancy 3 replicas (Rook-Ceph replication factor)

**Maintainability (NFR23-NFR29)**

- NFR23: Pattern consistency - All apps follow base/overlay Kustomize pattern
- NFR24: Documentation coverage - Runbooks exist for all major components
- NFR25: Naming conventions - Consistent resource naming across clusters
- NFR26: Version pinning - All Helm charts and images pinned to specific versions
- NFR27: Renovate automation - Dependency updates automated via Renovate PRs
- NFR28: Code review - All changes require PR review before merge
- NFR29: Taskfile coverage - Common operations available via unified .taskfiles

**Resource Efficiency (NFR30-NFR33)**

- NFR30: Control plane overhead < 2 GB RAM per controller (home lab resource constraints)
- NFR31: Observability overhead < 4 GB RAM total (VictoriaMetrics lighter than Prometheus)
- NFR32: Operator footprint < 500 MB RAM each (CNPG, Strimzi, etc.)
- NFR33: Storage efficiency - Thin provisioning (Rook-Ceph uses only allocated space)

**Integration (NFR34-NFR38)**

- NFR34: 1Password connectivity - External Secrets Operator maintains connection; retry on failure
- NFR35: GitHub connectivity - Flux retries with exponential backoff on failure
- NFR36: Cloudflare DNS - External-DNS updates DNS within 60 seconds of ingress creation
- NFR37: Cloudflare R2 connectivity - VolSync and CNPG Barman connect to R2 for backups; S3 API compatibility verified
- NFR38: Renovate integration - PRs auto-created within 24 hours of new releases

**Operational (NFR39-NFR43)**

- NFR39: Staged rollout - Infra cluster receives updates 24 hours before apps cluster
- NFR40: Rollback capability - Any change reversible via Git revert within 5 minutes
- NFR41: Alert notification - VMAlertmanager delivers notifications within 1 minute of trigger
- NFR42: Log retention - VictoriaLogs retains logs for 30 days minimum
- NFR43: Metric retention - VictoriaMetrics retains metrics for 90 days minimum

### Additional Requirements

**From Architecture Document:**

**Starter Template Requirements:**
- Use existing home-ops/prod-ops patterns merged with community best practices (onedr0p/home-ops style)
- Battle-tested patterns from 140+ combined HelmReleases
- Repository structure follows FluxCD monorepo pattern

**Bootstrap Sequence (CRD-First Pattern):**
- Phase 1 Pre-Flux (Helmfile): CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
- Phase 2 Post-Flux (GitOps): external-secrets → Rook-Ceph → VictoriaMetrics → Applications
- Standardized CRD-first pattern for both clusters

**Cluster Identity Configuration:**
- Infra cluster: cluster.id=1, cluster.name=infra
- Apps cluster: cluster.id=2, cluster.name=apps
- Enables future Cluster Mesh capability

**Branch-Based Staged Rollout:**
- main branch → infra cluster (immediate reconciliation)
- release branch → apps cluster (reconciles from release branch)
- GitHub Action: On merge to main, wait 24 hours, fast-forward release branch to main
- Manual override via workflow_dispatch

**Zero Trust Network Policy Pattern:**
- Tier 0: System Namespaces (kube-system, flux-system, DNS) - Always Allow
- Tier 1: Platform Services (observability, cert-manager, external-secrets) - Controlled Access
- Tier 2: Application Namespaces - Default Deny + Explicit Allow
- CiliumClusterwideNetworkPolicy for default-deny-all, allow-dns, allow-metrics-scraping

**Hub/Spoke Observability Architecture:**
- Infra cluster: Full VictoriaMetrics stack (storage, query, alerting)
- Apps cluster: VMAgent + Fluent-bit (collection only, remote-write to infra)
- Centralized Grafana on infra cluster
- Accepted Risk: SPOF during infra cluster downtime, mitigated by VMAgent buffering

**Technology Stack Versions (December 2025):**
- Talos Linux v1.12.0 (includes K8s 1.35.0)
- Cilium v1.18.5
- Flux CD v2.7.5
- External Secrets Operator v1.0.0
- Rook-Ceph v1.18.8 (Ceph Squid 19.2.3)
- OpenEBS v4.4
- Envoy Gateway v1.6.1 (Gateway API v1.4.1)
- cert-manager v1.19.2
- VictoriaMetrics v1.131.0 (Operator v0.66.1)

**CNPG Shared Cluster Pattern:**
- Single shared PostgreSQL cluster named `postgres` per Kubernetes cluster
- Apps create databases within shared cluster (not separate CNPG clusters)
- Naming: ${APP}-pguser-secret, ${APP}-initdb-secret, ${APP}-pg-backups

**App Location Rules (Critical for Implementation):**
- `kubernetes/apps/` - Shared apps deployed to BOTH clusters
- `clusters/infra/apps/` - Apps ONLY on infra cluster
- `clusters/apps/apps/` - Apps ONLY on apps cluster

**DR Testing Cadence:**
- CNPG Point-in-Time Recovery: Monthly
- CNPG Full Cluster Recovery: Quarterly
- VolSync PVC Restore: Monthly
- Full DR Simulation: Bi-annually
- Backup Verification: Weekly (automated)

**Implementation Enforcement Guidelines (12 rules for AI agents):**
1. Use `kustomization.yaml` (not `.yml`) for all Kustomize files
2. Follow the application directory structure exactly as specified
3. Include `install.remediation.retries: 3` and `upgrade.remediation.strategy: rollback` in all HelmReleases
4. Use `external-secrets.io/v1beta1` API version for ExternalSecrets
5. Reference `cluster-vars` ConfigMap via `postBuild.substituteFrom`
6. Use kebab-case for all Kubernetes resource names
7. Use `monosense.dev/` prefix for custom annotations and labels
8. Follow commit message format: `<type>(<scope>): <description>`
9. Include CiliumNetworkPolicy for Tier 2 applications
10. Use `${VARIABLE_NAME}` syntax for Flux substitution
11. Declare dependencies for database-backed and SSO apps
12. Use ConfigMap approach for Gatus health checks

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 0 | Single Git repository management |
| FR2 | Epic 0 | Shared infrastructure base directory |
| FR3 | Epic 0 | Cluster-specific overrides |
| FR4 | Epic 3 | View Flux reconciliation status |
| FR5 | Epic 3 | Trigger manual reconciliation |
| FR6 | Epic 3 | Suspend/resume Flux reconciliation |
| FR7 | Epic 3 | Consolidated Renovate PRs |
| FR8 | Epic 3 | GitHub Actions validation |
| FR9 | Epic 3 | Renovate grouping configuration |
| FR10 | Epic 3 | Reusable Kustomize components |
| FR11 | Epic 3 | PR review enforcement |
| FR12 | Epic 0 | SOPS decryption in Flux |
| FR13 | Epic 1 | Helmfile bootstrap sequence |
| FR14 | Epic 1 | Talos machine configuration generation |
| FR15 | Epic 1 | Talos API configuration |
| FR16 | Epic 5 | Rolling Talos upgrades |
| FR17 | Epic 5 | Node addition/removal |
| FR18 | Epic 5 | New cluster onboarding |
| FR19 | Epic 5 | Cluster decommissioning |
| FR20 | Epic 1 | Kubeconfig generation |
| FR21 | Epic 1 | Cilium CNI deployment |
| FR22 | Epic 2 | Network policy configuration |
| FR23 | Epic 2 | Network policy bypass for debugging |
| FR24 | Epic 2 | Network policy audit |
| FR25 | Epic 2 | LoadBalancer IP allocation |
| FR26 | Epic 2 | Rook-Ceph block storage |
| FR27 | Epic 2 | NFS shared storage |
| FR28 | Epic 2 | Ceph health monitoring |
| FR29 | Epic 2 | Ceph pool expansion |
| FR30 | Epic 2 | Namespace resource quotas |
| FR31 | Epic 2 | Priority class assignment |
| FR32 | Epic 2 | cert-manager with DNS-01 |
| FR33 | Epic 2 | Wildcard certificates |
| FR34 | Epic 4 | HelmRelease deployment |
| FR35 | Epic 4 | Application base/overlay pattern |
| FR36 | Epic 4 | Gateway API ingress routes |
| FR37 | Epic 4 | Resource requests/limits |
| FR38 | Epic 4 | Flux dependsOn configuration |
| FR39 | Epic 4 | Application overlay deployment |
| FR40 | Epic 4 | HelmRelease error visibility |
| FR41 | Epic 6 | Unified Grafana dashboards |
| FR42 | Epic 6 | VictoriaLogs log queries |
| FR43 | Epic 6 | Historical metrics queries |
| FR44 | Epic 6 | VMAlertmanager notifications |
| FR45 | Epic 6 | Cluster Overview dashboard |
| FR46 | Epic 6 | Flux GitOps dashboard |
| FR47 | Epic 6 | Application Health dashboard |
| FR48 | Epic 6 | VictoriaMetrics scrape targets |
| FR49 | Epic 6 | Fluent-bit log collection |
| FR50 | Epic 6 | Connectivity test results |
| FR51 | Epic 6 | Automatic DNS record creation |
| FR52 | Epic 1 | 1Password secret storage |
| FR53 | Epic 1 | External Secrets sync |
| FR54 | Epic 0 | SOPS/AGE encryption |
| FR55 | Epic 1 | Secret rotation via 1Password |
| FR56 | Epic 0 | AGE key management |
| FR57 | Epic 2 | Automatic TLS certificate renewal |
| FR58 | Epic 7 | VolSync PVC backups to R2 |
| FR59 | Epic 7 | Backup schedule configuration |
| FR60 | Epic 7 | PVC restore from VolSync |
| FR61 | Epic 7 | Full cluster rebuild |
| FR62 | Epic 7 | Backup integrity verification |
| FR63 | Epic 7 | Automated backup validation |
| FR64 | Epic 5 | Infra cluster immediate updates |
| FR65 | Epic 5 | Apps cluster soak period |
| FR66 | Epic 5 | Staged rollout override |
| FR67 | Epic 5 | Git revert rollback |
| FR68 | Epic 8 | CNPG PostgreSQL access |
| FR69 | Epic 8 | Kafka topic creation |
| FR70 | Epic 8 | Apicurio schema registration |
| FR71 | Epic 8 | Keycloak OIDC authentication |
| FR72 | Epic 8 | OpenBao secrets storage |
| FR73 | Epic 8 | MinIO S3 access |
| FR74 | Epic 8 | Gatus health dashboard |
| FR75 | Epic 8 | Spring Boot GitOps deployment |
| FR76 | Epic 8 | VictoriaLogs log filtering |
| FR77 | Epic 4 | Unified .taskfiles |
| FR78 | Epic 4 | Component runbooks |
| FR79 | Epic 4 | Cilium connectivity tests |
| FR80 | Epic 5 | Secret rotation testing |
| FR81 | Epic 5 | Bootstrap time validation |
| FR82 | Epic 5 | Secret propagation verification |
| FR83 | Epic 5 | Node upgrade verification |

## Epic List

- Epic 0: Repository Foundation (5 stories)
- Epic 1: Infra Cluster Bootstrap (5 stories)
- Epic 2: Shared Infrastructure Services (6 stories)
- Epic 3: GitOps Operations (4 stories)
- Epic 4: Application Deployment Patterns (5 stories)
- Epic 5: Apps Cluster & Staged Rollout (5 stories)
- Epic 6: Centralized Observability (5 stories)
- Epic 7: Backup & Disaster Recovery (4 stories)
- Epic 8: ArsipQ Development Platform (5 stories)

---

## Epic 0: Repository Foundation

**Goal:** Operator has a properly structured GitOps repository with encryption configured, ready for cluster bootstrap.

**FRs Covered:** FR1, FR2, FR3, FR12, FR54, FR56

### Story 0.1: Initialize Repository Structure

**As a** platform operator,
**I want** a properly structured k8s-ops repository following FluxCD best practices,
**So that** I have a clear, organized foundation for managing multiple clusters.

**Acceptance Criteria:**

**Given** a new GitHub repository named `k8s-ops`
**When** the directory structure is initialized
**Then** the following directories exist:
- `clusters/infra/` and `clusters/apps/` with `flux/`, `talos/`, and `apps/` subdirectories
- `infrastructure/base/` for shared infrastructure components
- `kubernetes/apps/` for shared application definitions
- `kubernetes/components/` for reusable Kustomize components
- `bootstrap/infra/` and `bootstrap/apps/` with `helmfile.d/` subdirectories
- `.taskfiles/` for unified task automation
- `terraform/` for infrastructure modules
- `docs/` for documentation and runbooks
**And** a root `Taskfile.yaml` exists referencing `.taskfiles/`
**And** `.gitignore` excludes sensitive files and build artifacts
**And** `renovate.json5` is configured for dependency management

---

### Story 0.2: Create Shared Infrastructure Base

**As a** platform operator,
**I want** shared infrastructure component definitions in a base directory,
**So that** both clusters can reference common CRDs, controllers, and repositories.

**Acceptance Criteria:**

**Given** the repository structure from Story 0.1
**When** shared infrastructure base is created
**Then** `infrastructure/base/repositories/` contains:
- `kustomization.yaml` listing all repository sources
- `helm/` directory with HelmRepository definitions (bitnami, cilium, jetstack, etc.)
- `oci/` directory with OCIRepository definitions (ghcr-flux, ghcr-sidero, etc.)
**And** repository definitions are valid Flux v2 resources
**And** `kustomize build infrastructure/base/repositories` succeeds without errors

---

### Story 0.3: Configure Cluster-Specific Flux Entry Points

**As a** platform operator,
**I want** cluster-specific Flux configuration directories,
**So that** each cluster can reference shared bases while maintaining its own configuration.

**Acceptance Criteria:**

**Given** the shared infrastructure base from Story 0.2
**When** cluster Flux entry points are configured
**Then** `clusters/infra/flux/` contains:
- `kustomization.yaml` as root Flux entry point
- `cluster-vars.yaml` ConfigMap with CLUSTER_NAME=infra, CLUSTER_ID=1, CLUSTER_DOMAIN=monosense.dev
- `config/` directory with `cluster-infrastructure.yaml`, `cluster-apps.yaml`, `cluster-local.yaml`
- `repositories/kustomization.yaml` referencing `infrastructure/base/repositories`
**And** `clusters/apps/flux/` contains equivalent structure with CLUSTER_NAME=apps, CLUSTER_ID=2
**And** `kustomize build clusters/infra/flux` succeeds
**And** `kustomize build clusters/apps/flux` succeeds

---

### Story 0.4: Configure SOPS/AGE Encryption

**As a** platform operator,
**I want** SOPS encryption configured with my existing AGE key,
**So that** I can encrypt sensitive files in Git while Flux can decrypt them during reconciliation.

**Acceptance Criteria:**

**Given** the repository structure with cluster directories
**When** SOPS/AGE encryption is configured
**Then** `.sops.yaml` exists at repository root with:
- Creation rules for `*.sops.yaml` and `*.sops.yml` files
- AGE public key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
- Path-specific rules for cluster secrets
**And** a test secret file can be encrypted with `sops -e`
**And** the encrypted file can be decrypted with `sops -d` using the private key from 1Password
**And** `bootstrap/infra/github-deploy-key.sops.yaml` template exists for GitHub deploy key

---

### Story 0.5: Create GitHub Workflows for Validation

**As a** platform operator,
**I want** GitHub Actions workflows to validate changes before merge,
**So that** I can catch manifest errors and security issues in PRs.

**Acceptance Criteria:**

**Given** the configured repository structure
**When** GitHub workflows are created
**Then** `.github/workflows/` contains:
- `validate-kustomize.yaml` that runs `kustomize build` for affected paths
- `kubeconform.yaml` for schema validation against CRDs
- `gitleaks.yaml` for secret detection in code
- `flux-diff.yaml` to show Flux resource changes in PRs
**And** workflows trigger on pull requests to main branch
**And** `CODEOWNERS` file exists requiring review for changes
**And** `dependabot.yaml` is configured for GitHub Actions updates

---

## Epic 1: Infra Cluster Bootstrap

**Goal:** Operator can bootstrap the infra cluster with Talos, deploy the bootstrap sequence, and have secrets management operational.

**FRs Covered:** FR13, FR14, FR15, FR20, FR21, FR52, FR53, FR55

### Story 1.1: Create Talos Machine Configurations

**As a** platform operator,
**I want** Talos machine configurations generated from templates using talhelper,
**So that** I can provision consistent, reproducible cluster nodes.

**Acceptance Criteria:**

**Given** the repository structure from Epic 0
**When** Talos configurations are created for infra cluster
**Then** `clusters/infra/talos/` contains:
- `talconfig.yaml` with cluster settings (name: infra, endpoint: 10.25.11.10, nodes: 10.25.11.11-16)
- `clusterconfig/` directory with generated machine configs (encrypted with SOPS)
- `patches/` directory for node-specific customizations
**And** talconfig.yaml specifies Talos v1.12.0, Kubernetes v1.35.0
**And** network configuration includes MTU 9000, LACP bonding
**And** `talhelper genconfig` produces valid machine configurations
**And** secrets are encrypted in `talsecret.sops.yaml`

---

### Story 1.2: Create Helmfile Bootstrap Configuration

**As a** platform operator,
**I want** a helmfile-based bootstrap sequence for pre-Flux components,
**So that** I can install critical infrastructure before Flux takes over.

**Acceptance Criteria:**

**Given** Talos machine configurations from Story 1.1
**When** helmfile bootstrap is configured
**Then** `bootstrap/infra/helmfile.d/` contains:
- `00-crds.yaml` installing CRDs separately (Cilium, cert-manager, Gateway API)
- `01-apps.yaml` with dependency chain: Cilium → CoreDNS → Spegel → cert-manager → Flux
**And** `bootstrap/infra/templates/values.yaml.gotmpl` extracts values from HelmRelease pattern
**And** `bootstrap/infra/secrets.yaml.tpl` references 1Password secrets
**And** Cilium configured with cluster.id=1, cluster.name=infra, eBPF native routing
**And** `.taskfiles/bootstrap/Taskfile.yaml` contains `bootstrap:infra` task

---

### Story 1.3: Bootstrap Infra Cluster

**As a** platform operator,
**I want** to bootstrap the infra cluster using documented taskfile commands,
**So that** my cluster is running with Flux GitOps managing all resources.

**Acceptance Criteria:**

**Given** Talos nodes are provisioned and helmfile bootstrap is configured
**When** `task bootstrap:infra` is executed
**Then** Talos control plane is bootstrapped via `talosctl bootstrap`
**And** kubeconfig is generated via `talosctl kubeconfig`
**And** helmfile installs components in order: CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
**And** Flux connects to GitHub repository using deploy key
**And** `flux check` passes with all components healthy
**And** Cilium connectivity tests pass (`cilium connectivity test`)
**And** bootstrap completes within 30 minutes (NFR2)

---

### Story 1.4: Deploy External Secrets Operator with 1Password

**As a** platform operator,
**I want** External Secrets Operator syncing secrets from 1Password,
**So that** applications can access secrets without storing them in Git.

**Acceptance Criteria:**

**Given** Flux is operational from Story 1.3
**When** External Secrets Operator is deployed
**Then** `kubernetes/apps/external-secrets/` contains:
- Operator HelmRelease with ESO v1.0.0
- ClusterSecretStore referencing 1Password Connect
**And** 1Password Connect is deployed with credentials from SOPS-encrypted secret
**And** a test ExternalSecret successfully syncs a secret from 1Password
**And** secret sync completes within 5 minutes (NFR5)
**And** operator uses < 500MB RAM (NFR32)

---

### Story 1.5: Create Operational Taskfiles for Talos

**As a** platform operator,
**I want** unified taskfiles for common Talos operations,
**So that** I can manage nodes consistently without remembering complex commands.

**Acceptance Criteria:**

**Given** a running infra cluster from Story 1.3
**When** Talos taskfiles are created
**Then** `.taskfiles/talos/Taskfile.yaml` contains tasks:
- `talos:apply-node` - Apply machine config to a node
- `talos:upgrade-node` - Upgrade Talos on a node with rolling strategy
- `talos:upgrade-k8s` - Upgrade Kubernetes version
- `talos:reset-cluster` - Reset cluster (with confirmation prompt)
- `talos:generate-iso` - Generate installer ISO
**And** `.taskfiles/op/Taskfile.yaml` contains:
- `op:push` - Push kubeconfig to 1Password
- `op:pull` - Pull kubeconfig from 1Password
**And** tasks are cluster-aware (accept CLUSTER variable)
**And** `task talos:apply-node CLUSTER=infra NODE=10.25.11.11` works correctly

---

## Epic 2: Shared Infrastructure Services

**Goal:** Operator can provision storage, configure network policies, and manage TLS certificates across the cluster.

**FRs Covered:** FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR57

### Story 2.1: Deploy Rook-Ceph Storage Cluster

**As a** platform operator,
**I want** Rook-Ceph providing block storage with 3-replica redundancy,
**So that** applications have reliable, persistent storage.

**Acceptance Criteria:**

**Given** a running infra cluster with Flux operational
**When** Rook-Ceph is deployed
**Then** `infrastructure/base/rook-ceph/` contains:
- Operator HelmRelease with Rook v1.18.8
- CephCluster CR with 3 replicas, Ceph Squid 19.2.3
- StorageClass `ceph-block` for RWO volumes
**And** Ceph cluster reaches `HEALTH_OK` status
**And** all OSDs are up and PGs are `active+clean`
**And** `kubectl get cephcluster -n rook-ceph` shows Ready state
**And** a test PVC using `ceph-block` StorageClass provisions successfully

---

### Story 2.2: Configure OpenEBS Local Storage

**As a** platform operator,
**I want** OpenEBS providing local NVMe storage for databases,
**So that** CNPG PostgreSQL clusters get optimal I/O performance.

**Acceptance Criteria:**

**Given** Rook-Ceph is operational from Story 2.1
**When** OpenEBS is deployed
**Then** `infrastructure/base/openebs/` contains:
- Operator HelmRelease with OpenEBS v4.4
- StorageClass `openebs-hostpath` for local volumes
**And** LocalPV provisioner is running on all nodes
**And** a test PVC using `openebs-hostpath` provisions on local NVMe
**And** operator uses < 500MB RAM (NFR32)

---

### Story 2.3: Implement Zero Trust Network Policies

**As a** platform operator,
**I want** default-deny network policies with tiered exceptions,
**So that** pod-to-pod communication is secure by default.

**Acceptance Criteria:**

**Given** Cilium CNI is operational
**When** Zero Trust network policies are deployed
**Then** `kubernetes/apps/security/network-policies/` contains:
- CiliumClusterwideNetworkPolicy `default-deny-all` (excludes kube-system, flux-system)
- CiliumClusterwideNetworkPolicy `allow-dns` (UDP/53 to kube-dns)
- CiliumClusterwideNetworkPolicy `allow-metrics-scraping` (from observability namespace)
**And** Tier 0 namespaces (kube-system, flux-system) have unrestricted access
**And** Tier 1 namespaces (observability, cert-manager) have controlled access
**And** Tier 2 namespaces have default-deny requiring explicit CiliumNetworkPolicy
**And** `cilium connectivity test` passes after policies are applied
**And** debug bypass annotation `policy.cilium.io/enforce=false` works for troubleshooting

---

### Story 2.4: Deploy cert-manager with DNS-01 Validation

**As a** platform operator,
**I want** cert-manager automatically issuing Let's Encrypt certificates via DNS-01,
**So that** all ingress endpoints have valid TLS without manual intervention.

**Acceptance Criteria:**

**Given** External Secrets is syncing Cloudflare API credentials
**When** cert-manager is deployed
**Then** `kubernetes/apps/cert-manager/` contains:
- Operator installed via bootstrap (Story 1.2)
- `issuers/` directory with ClusterIssuer for Let's Encrypt (staging and production)
- Cloudflare DNS-01 solver configuration
**And** ClusterIssuer `letsencrypt-production` is Ready
**And** wildcard Certificate for `*.monosense.dev` is issued successfully
**And** Certificate renewal triggers automatically 30+ days before expiry (NFR6)
**And** certificate issuance completes within 5 minutes

---

### Story 2.5: Configure Cilium LoadBalancer IP Pools

**As a** platform operator,
**I want** Cilium BGP Control Plane announcing LoadBalancer IPs,
**So that** services are accessible via predictable IP addresses.

**Acceptance Criteria:**

**Given** Cilium with BGP Control Plane enabled
**When** IP pools are configured
**Then** `infrastructure/base/cilium/` contains:
- CiliumLoadBalancerIPPool for infra cluster IP range
- CiliumBGPPeeringPolicy for Juniper SRX 320 peering
**And** BGP session establishes with upstream router (ASN configured)
**And** creating a LoadBalancer Service allocates IP from pool
**And** IP is announced via BGP and reachable from network
**And** `cilium bgp peers` shows established session

---

### Story 2.6: Configure Resource Management Policies

**As a** platform operator,
**I want** namespace quotas, limit ranges, and priority classes,
**So that** workloads don't starve resources and critical services are prioritized.

**Acceptance Criteria:**

**Given** a running cluster with storage and networking
**When** resource management is configured
**Then** `kubernetes/apps/` contains resource policies:
- PriorityClass definitions: `system-critical`, `cluster-services`, `application` (default)
- LimitRange template for namespaces without explicit settings
- ResourceQuota template for namespace resource limits
**And** kube-system pods use `system-critical` priority
**And** infrastructure operators use `cluster-services` priority
**And** application pods default to `application` priority
**And** pods without resource requests get defaults from LimitRange

---

## Epic 3: GitOps Operations

**Goal:** Operator can manage Flux reconciliation, receive dependency updates via Renovate, and validate changes before merge with GitHub Actions.

**FRs Covered:** FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11

### Story 3.1: Create Flux Operational Taskfiles

**As a** platform operator,
**I want** taskfile commands for common Flux operations,
**So that** I can manage reconciliation without memorizing kubectl commands.

**Acceptance Criteria:**

**Given** a running cluster with Flux operational
**When** Flux taskfiles are created
**Then** `.taskfiles/flux/Taskfile.yaml` contains tasks:
- `flux:reconcile` - Trigger reconciliation for a Kustomization or HelmRelease
- `flux:suspend` - Suspend reconciliation for an app or namespace
- `flux:resume` - Resume reconciliation for an app or namespace
- `flux:logs` - Stream Flux controller logs
- `flux:events` - Show recent Flux events
- `flux:diff` - Preview changes before reconciliation
**And** tasks accept APP and CLUSTER variables
**And** `task flux:suspend APP=odoo CLUSTER=apps` correctly suspends the HelmRelease
**And** `task flux:reconcile APP=odoo CLUSTER=apps` triggers immediate reconciliation

---

### Story 3.2: Configure Renovate for Dependency Management

**As a** platform operator,
**I want** Renovate automatically creating PRs for dependency updates grouped by type,
**So that** I can keep components updated with minimal manual effort.

**Acceptance Criteria:**

**Given** the repository with HelmReleases and container images
**When** Renovate is configured
**Then** `renovate.json5` contains:
- Preset extending `config:recommended`
- Custom managers for Flux HelmRelease resources
- Grouping rules: patch updates weekly, minor monthly, major as individual PRs
- Automerge enabled for patch updates in non-production
- Labels for PR categorization (helm, docker, github-actions)
**And** Renovate bot has access to the repository
**And** PRs include changelog links and release notes
**And** shared dependencies in `infrastructure/base/` create single PR affecting both clusters

---

### Story 3.3: Create Reusable Kustomize Components

**As a** platform operator,
**I want** reusable Kustomize components for common patterns,
**So that** applications can compose functionality without duplication.

**Acceptance Criteria:**

**Given** the repository structure with `kubernetes/components/`
**When** shared components are created
**Then** the following components exist:
- `cnpg/` - CNPG database provisioning (ExternalSecret, CronJob for backups)
- `volsync/r2/` - VolSync backup to Cloudflare R2
- `volsync/nfs/` - VolSync backup to NFS
- `gatus/external/` - External health check endpoint
- `gatus/internal/` - Internal health check endpoint
- `dragonfly/` - Dragonfly Redis instance
- `secpol/` - Standard security policies
**And** each component has `kustomization.yaml` with configurable replacements
**And** components can be referenced via `spec.components` in Flux Kustomization
**And** `kustomize build` with component reference produces valid manifests

---

### Story 3.4: Implement PR Review and Branch Protection

**As a** platform operator,
**I want** branch protection requiring PR reviews and passing CI,
**So that** changes are validated before affecting clusters.

**Acceptance Criteria:**

**Given** GitHub workflows from Story 0.5
**When** branch protection is configured
**Then** `main` branch has protection rules:
- Require PR reviews (minimum 1 approval)
- Require status checks to pass (validate-kustomize, kubeconform, gitleaks)
- Require branches to be up to date
- Dismiss stale reviews when new commits pushed
**And** `CODEOWNERS` assigns reviewers for critical paths
**And** direct pushes to main are blocked
**And** PRs cannot merge until all checks pass
**And** `.github/workflows/flux-hr-sync.yaml` reports HelmRelease sync status

---

## Epic 4: Application Deployment Patterns

**Goal:** Operator can deploy applications using HelmRelease, Kustomize components, and Gateway API patterns with unified operational tooling.

**FRs Covered:** FR34, FR35, FR36, FR37, FR38, FR39, FR40, FR77, FR78, FR79

### Story 4.1: Deploy Envoy Gateway for Ingress

**As a** platform operator,
**I want** Envoy Gateway managing ingress via Gateway API,
**So that** applications can expose HTTP routes with consistent configuration.

**Acceptance Criteria:**

**Given** a running cluster with cert-manager issuing certificates
**When** Envoy Gateway is deployed
**Then** `kubernetes/apps/networking/envoy-gateway/` contains:
- Operator HelmRelease with Envoy Gateway v1.6.1
- GatewayClass `envoy-gateway`
- Gateway resource for cluster domain (`*.monosense.dev` or `*.monosense.io`)
**And** Gateway references wildcard TLS certificate from cert-manager
**And** Gateway is Ready and accepting connections
**And** HTTPRoute resources can reference the Gateway

---

### Story 4.2: Deploy CloudNative-PG Operator and Shared Cluster

**As a** platform operator,
**I want** CNPG operator with a shared PostgreSQL cluster,
**So that** applications can provision databases without managing individual clusters.

**Acceptance Criteria:**

**Given** OpenEBS local storage from Story 2.2
**When** CNPG is deployed
**Then** `kubernetes/apps/databases/cloudnative-pg/` contains:
- `app/` with operator HelmRelease
- `cluster/` with shared PostgreSQL Cluster named `postgres` in `databases` namespace
**And** Cluster has 3 replicas using `openebs-hostpath` StorageClass
**And** superuser credentials stored in `postgres-superuser-secret`
**And** `kubectl cnpg status postgres -n databases` shows healthy cluster
**And** applications create databases via `${APP}-initdb-secret` pattern

---

### Story 4.3: Create Reference Application Deployment

**As a** platform operator,
**I want** a reference application demonstrating all deployment patterns,
**So that** future applications follow consistent structure.

**Acceptance Criteria:**

**Given** CNPG, Envoy Gateway, and Kustomize components are operational
**When** Gatus is deployed as reference application
**Then** `kubernetes/apps/observability/gatus/` demonstrates:
- `app/` directory with HelmRelease, kustomization.yaml
- `ks.yaml` with Flux Kustomization referencing components
- ExternalSecret for credentials
- HTTPRoute for external access
- CiliumNetworkPolicy for Tier 2 security
**And** HelmRelease includes `install.remediation.retries: 3` and `upgrade.remediation.strategy: rollback`
**And** ks.yaml uses `postBuild.substituteFrom` for cluster-vars
**And** dependencies declared via `spec.dependsOn`
**And** Gatus is accessible via `gatus.monosense.dev`

---

### Story 4.4: Create Kubernetes Operational Taskfiles

**As a** platform operator,
**I want** unified taskfiles for common Kubernetes operations,
**So that** I can manage workloads efficiently across clusters.

**Acceptance Criteria:**

**Given** running clusters with applications deployed
**When** Kubernetes taskfiles are created
**Then** `.taskfiles/kubernetes/Taskfile.yaml` contains tasks:
- `k8s:sync-secrets` - Force External Secrets sync
- `k8s:hr-restart` - Restart a HelmRelease
- `k8s:cleanse-pods` - Delete failed/evicted pods
- `k8s:browse-pvc` - Browse PVC contents via ephemeral pod
- `k8s:exec` - Exec into a pod
- `k8s:logs` - Stream pod logs
**And** tasks accept CLUSTER, NAMESPACE, and APP variables
**And** `task k8s:hr-restart APP=gatus CLUSTER=infra` restarts the HelmRelease

---

### Story 4.5: Create Runbooks for Major Components

**As a** platform operator,
**I want** runbooks documenting operational procedures,
**So that** I can troubleshoot and recover from issues efficiently.

**Acceptance Criteria:**

**Given** operational clusters with all infrastructure components
**When** runbooks are created
**Then** `docs/runbooks/` contains:
- `bootstrap.md` - Full cluster bootstrap procedure
- `disaster-recovery.md` - DR procedures and recovery steps
- `cnpg-restore.md` - CNPG backup and restore procedures
- `cluster-upgrade.md` - Talos and Kubernetes upgrade procedures
- `rook-ceph.md` - Ceph troubleshooting and maintenance
- `cilium.md` - Network policy debugging and connectivity tests
- `flux.md` - Flux troubleshooting and common operations
**And** each runbook includes symptoms, diagnosis, and resolution steps
**And** runbooks reference taskfile commands where applicable
**And** `docs/index.md` links to all runbooks

---

## Epic 5: Apps Cluster & Staged Rollout

**Goal:** Operator can bootstrap the apps cluster, configure staged rollout (infra-first with 24h soak), and manage multi-cluster operations.

**FRs Covered:** FR16, FR17, FR18, FR19, FR64, FR65, FR66, FR67, FR80, FR81, FR82, FR83

### Story 5.1: Bootstrap Apps Cluster

**As a** platform operator,
**I want** the apps cluster bootstrapped using the same patterns as infra,
**So that** I have a consistent second cluster for business applications.

**Acceptance Criteria:**

**Given** infra cluster is operational and repository patterns are established
**When** apps cluster is bootstrapped
**Then** `clusters/apps/talos/` contains machine configs for nodes 10.25.13.11-16
**And** `bootstrap/apps/` mirrors infra bootstrap with cluster.id=2, cluster.name=apps
**And** `task bootstrap:apps` successfully bootstraps the cluster
**And** Flux connects to repository using `release` branch (not `main`)
**And** `flux check` passes on apps cluster
**And** shared infrastructure from `infrastructure/base/` is deployed
**And** bootstrap completes within 30 minutes (NFR2)

---

### Story 5.2: Implement Branch-Based Staged Rollout

**As a** platform operator,
**I want** automated staged rollout with 24h soak time,
**So that** changes are validated on infra before affecting apps cluster.

**Acceptance Criteria:**

**Given** both clusters are operational with Flux
**When** staged rollout is configured
**Then** infra cluster Flux references `main` branch
**And** apps cluster Flux references `release` branch
**And** `.github/workflows/release-promote.yaml` exists with:
- Trigger on merge to main
- 24-hour delay (using scheduled workflow or wait)
- Fast-forward `release` branch to `main`
- Manual override via `workflow_dispatch`
**And** merging to main updates infra cluster immediately
**And** apps cluster updates 24 hours later automatically
**And** `task flux:override-staged-rollout` forces immediate apps update

---

### Story 5.3: Deploy Business Applications to Apps Cluster

**As a** platform operator,
**I want** business applications deployed to the apps cluster,
**So that** production workloads run on the appropriate cluster.

**Acceptance Criteria:**

**Given** apps cluster is operational with shared infrastructure
**When** business applications are deployed
**Then** `clusters/apps/apps/business/` contains:
- `odoo/` with HelmRelease, ExternalSecret, HTTPRoute, NetworkPolicy
- `n8n/` with HelmRelease, ExternalSecret, HTTPRoute, NetworkPolicy
- `arsipq/` with application deployment (references external manifests)
**And** each app uses shared CNPG cluster via `${APP}-pguser-secret` pattern
**And** each app has CiliumNetworkPolicy for Tier 2 isolation
**And** apps are accessible via `*.monosense.io` domain
**And** Authentik SSO (from infra cluster) works for apps cluster applications

---

### Story 5.4: Create Multi-Cluster Operational Validation

**As a** platform operator,
**I want** validation tasks for multi-cluster operations,
**So that** I can verify cross-cluster functionality works correctly.

**Acceptance Criteria:**

**Given** both clusters are operational
**When** validation tasks are created
**Then** `.taskfiles/dr/Taskfile.yaml` contains:
- `dr:verify-backups` - Check R2 backup accessibility
- `dr:test-cnpg-restore` - Test CNPG point-in-time recovery to test namespace
**And** `tests/smoke/` contains validation scripts:
- `dr-cnpg-restore.sh` - Automated CNPG restore test
- `dr-volsync-restore.sh` - Automated VolSync restore test
**And** `task dr:verify-backups CLUSTER=infra` verifies R2 connectivity
**And** secret rotation test: update 1Password → verify pod picks up new value < 10 min

---

### Story 5.5: Document Cluster Lifecycle Operations

**As a** platform operator,
**I want** documented procedures for cluster lifecycle management,
**So that** I can onboard new clusters and manage existing ones efficiently.

**Acceptance Criteria:**

**Given** operational multi-cluster environment
**When** lifecycle documentation is created
**Then** `docs/runbooks/cluster-lifecycle.md` documents:
- New cluster onboarding (copy structure, configure, bootstrap)
- Cluster decommissioning (remove config, archive, cleanup)
- Node addition and removal procedures
- Rolling Talos upgrade procedure with verification steps
**And** `task talos:upgrade-node` includes pre/post verification
**And** upgrade waits for node health before proceeding to next
**And** `task cluster:onboard` template task is documented

---

## Epic 6: Centralized Observability

**Goal:** Operator has unified visibility across all clusters with centralized metrics, logs, dashboards, and alerting.

**FRs Covered:** FR41, FR42, FR43, FR44, FR45, FR46, FR47, FR48, FR49, FR50, FR51

### Story 6.1: Deploy VictoriaMetrics Stack on Infra Cluster

**As a** platform operator,
**I want** VictoriaMetrics providing centralized metrics storage and alerting,
**So that** I have a single source for all cluster metrics.

**Acceptance Criteria:**

**Given** infra cluster is operational with storage
**When** VictoriaMetrics stack is deployed
**Then** `clusters/infra/apps/observability/victoria-metrics/` contains:
- VictoriaMetrics Operator HelmRelease v0.66.1
- VMSingle or VMCluster for metrics storage (90d retention per NFR43)
- VMAgent for local scraping (no remote-write)
- VMAlertmanager for alert routing
- VMAlert with migrated alert rules
**And** VMAgent discovers all scrape targets
**And** metrics are queryable via VictoriaMetrics API
**And** total observability RAM < 4GB (NFR31)
**And** query response < 2 seconds for 95th percentile (NFR3)

---

### Story 6.2: Deploy VictoriaLogs for Centralized Logging

**As a** platform operator,
**I want** VictoriaLogs aggregating logs from all clusters,
**So that** I can search and analyze logs from a single location.

**Acceptance Criteria:**

**Given** VictoriaMetrics stack is operational
**When** VictoriaLogs is deployed
**Then** `clusters/infra/apps/observability/victoria-logs/` contains:
- VictoriaLogs deployment with 30d retention (NFR42)
- Ingestion endpoint for Fluent-bit
**And** `clusters/infra/apps/observability/fluent-bit/` contains:
- Fluent-bit DaemonSet shipping logs to VictoriaLogs locally
- Cluster label added to distinguish log sources
**And** logs are searchable via VictoriaLogs query API
**And** search response < 5 seconds for 95th percentile (NFR4)

---

### Story 6.3: Configure Apps Cluster Observability Agents

**As a** platform operator,
**I want** apps cluster metrics and logs forwarded to infra cluster,
**So that** I have unified cross-cluster visibility.

**Acceptance Criteria:**

**Given** infra cluster observability is operational
**When** apps cluster agents are configured
**Then** `clusters/apps/apps/observability/vmagent/` contains:
- VMAgent with remote-write to infra VictoriaMetrics
- ServiceMonitor for scrape target discovery
- Memory buffer for transient failures
**And** `clusters/apps/apps/observability/fluent-bit/` contains:
- Fluent-bit DaemonSet with remote-write to infra VictoriaLogs (via Gateway, HTTPS)
- Cluster label `apps` added to all logs
**And** apps cluster metrics appear in infra cluster queries
**And** apps cluster logs appear in infra VictoriaLogs searches

---

### Story 6.4: Deploy Grafana with Multi-Cluster Dashboards

**As a** platform operator,
**I want** Grafana dashboards showing metrics from both clusters,
**So that** I have visual insight into cluster and application health.

**Acceptance Criteria:**

**Given** VictoriaMetrics and VictoriaLogs are receiving data from both clusters
**When** Grafana is deployed
**Then** `clusters/infra/apps/observability/grafana/` contains:
- Grafana HelmRelease with SSO via Authentik
- VictoriaMetrics datasource configured
- VictoriaLogs datasource configured
**And** the following dashboards are deployed:
- **Cluster Overview**: Node health, pod counts, resource usage (both clusters)
- **Flux GitOps**: Reconciliation status, sync times, error rates
- **Application Health**: Per-namespace pod status, restart counts, ingress latency
**And** dashboards load with data within 10 seconds
**And** Grafana is accessible via `grafana.monosense.dev`

---

### Story 6.5: Configure External-DNS and Alerting

**As a** platform operator,
**I want** automatic DNS records and alert notifications,
**So that** services are discoverable and I'm notified of issues.

**Acceptance Criteria:**

**Given** Grafana and observability stack are operational
**When** External-DNS and alerting are configured
**Then** `kubernetes/apps/networking/external-dns/` contains:
- External-DNS deployment with Cloudflare + bind9 providers
- Annotation-based DNS record creation from Gateway/HTTPRoute
**And** creating an HTTPRoute automatically creates DNS record within 60 seconds (NFR36)
**And** VMAlertmanager is configured with notification channels (webhook, email, etc.)
**And** test alert triggers notification delivery within 1 minute (NFR41)
**And** `kubernetes/apps/networking/cloudflared/` deploys Cloudflare Tunnel for external access

---

## Epic 7: Backup & Disaster Recovery

**Goal:** Operator can backup all stateful data to Cloudflare R2 and recover from disasters using Git + VolSync + 1Password.

**FRs Covered:** FR58, FR59, FR60, FR61, FR62, FR63

### Story 7.1: Deploy VolSync for PVC Backups

**As a** platform operator,
**I want** VolSync backing up PVCs to Cloudflare R2,
**So that** application data is protected and recoverable.

**Acceptance Criteria:**

**Given** Rook-Ceph storage is operational
**When** VolSync is deployed
**Then** `kubernetes/apps/volsync/` contains:
- VolSync operator HelmRelease
- R2 credentials via ExternalSecret
**And** `kubernetes/components/volsync/r2/` component provides:
- ReplicationSource template for R2 backups
- Restic configuration with R2 endpoint
- Default schedule: every 8 hours (NFR59)
- Retention: 24 hourly, 7 daily
**And** applications can include `volsync/r2` component for backup
**And** backup jobs complete with 100% success rate (NFR19)

---

### Story 7.2: Configure CNPG Barman Backups to R2

**As a** platform operator,
**I want** PostgreSQL databases backed up via Barman to Cloudflare R2,
**So that** I can perform point-in-time recovery for databases.

**Acceptance Criteria:**

**Given** CNPG shared cluster is operational
**When** Barman backup is configured
**Then** CNPG Cluster CR includes:
- `backup.barmanObjectStore` pointing to Cloudflare R2
- WAL archiving enabled for continuous backup
- Daily scheduled base backups
- bzip2 compression
- 30-day retention
**And** R2 credentials stored in ExternalSecret
**And** `kubectl cnpg backup postgres -n databases` creates on-demand backup
**And** WAL files are archived continuously to R2

---

### Story 7.3: Create VolSync Operational Taskfiles

**As a** platform operator,
**I want** taskfile commands for backup and restore operations,
**So that** I can manage backups without complex kubectl commands.

**Acceptance Criteria:**

**Given** VolSync is operational with backups running
**When** VolSync taskfiles are created
**Then** `.taskfiles/volsync/Taskfile.yaml` contains tasks:
- `volsync:snapshot` - Trigger immediate snapshot for an app
- `volsync:restore` - Restore PVC from latest or specific snapshot
- `volsync:unlock` - Unlock Restic repository if locked
- `volsync:list` - List available snapshots for an app
- `volsync:status` - Show backup status for all ReplicationSources
**And** tasks accept APP, CLUSTER, and SNAPSHOT variables
**And** `task volsync:restore APP=odoo CLUSTER=apps` restores the PVC

---

### Story 7.4: Document and Test Disaster Recovery Procedures

**As a** platform operator,
**I want** documented and tested DR procedures,
**So that** I can recover from disasters with confidence.

**Acceptance Criteria:**

**Given** backups are operational on both clusters
**When** DR documentation and tests are created
**Then** `docs/runbooks/disaster-recovery.md` documents:
- Full cluster rebuild from Git + VolSync + 1Password
- CNPG point-in-time recovery procedure
- VolSync PVC restore procedure
- Estimated recovery times per data size
**And** `tests/smoke/dr-cnpg-restore.sh` validates:
- Restore to test namespace succeeds
- Data integrity verified
- RTO < 30 minutes for CNPG
**And** `tests/smoke/dr-volsync-restore.sh` validates:
- PVC restore succeeds
- Application starts with restored data
**And** monthly CNPG PITR test is scheduled
**And** weekly automated backup verification (restic check) runs

---

## Epic 8: ArsipQ Development Platform

**Goal:** Developers have a complete, production-like platform for Spring Boot development on the infra cluster.

**FRs Covered:** FR68, FR69, FR70, FR71, FR72, FR73, FR74, FR75, FR76

### Story 8.1: Deploy Strimzi Kafka Operator and Cluster

**As a** developer,
**I want** a Kafka cluster managed via GitOps,
**So that** I can build event-driven applications without managing Kafka infrastructure.

**Acceptance Criteria:**

**Given** infra cluster is operational with storage
**When** Strimzi Kafka is deployed
**Then** `clusters/infra/apps/platform/strimzi-kafka/` contains:
- Strimzi Operator HelmRelease v0.47.0
- Kafka cluster CR with KRaft mode (no ZooKeeper)
- 3 controllers + 3 brokers configuration
- Storage using Rook-Ceph
**And** Kafka cluster reaches Ready state
**And** developers can create KafkaTopic CRs to provision topics
**And** `kubectl get kafkatopics -n arsipq-platform` lists created topics
**And** internal bootstrap address: `arsipq-kafka-kafka-bootstrap.arsipq-platform:9092`

---

### Story 8.2: Deploy Apicurio Schema Registry

**As a** developer,
**I want** a schema registry for Kafka message schemas,
**So that** I can enforce schema compatibility for event-driven services.

**Acceptance Criteria:**

**Given** Strimzi Kafka is operational
**When** Apicurio Registry is deployed
**Then** `clusters/infra/apps/platform/apicurio/` contains:
- Apicurio Registry deployment (latest version)
- PostgreSQL database in shared CNPG cluster
- HTTPRoute for external access
**And** `/health` endpoint returns 200
**And** developers can register Avro/JSON schemas via API
**And** Apicurio is accessible via `apicurio.monosense.dev`

---

### Story 8.3: Deploy Keycloak for OIDC Authentication

**As a** developer,
**I want** Keycloak providing OIDC authentication,
**So that** Spring Boot applications have consistent SSO integration.

**Acceptance Criteria:**

**Given** CNPG shared cluster is operational
**When** Keycloak is deployed
**Then** `clusters/infra/apps/platform/keycloak/` contains:
- Keycloak Bitnami HelmRelease
- PostgreSQL database in shared CNPG cluster
- HTTPRoute for admin console and OIDC endpoints
- Realm configuration for ArsipQ
**And** admin console is accessible via `keycloak.monosense.dev`
**And** realm configuration is persisted in database
**And** developers can configure OIDC clients for applications

---

### Story 8.4: Deploy OpenBao for Secrets Management

**As a** developer,
**I want** OpenBao for application secrets management,
**So that** Spring Boot applications can retrieve secrets at runtime.

**Acceptance Criteria:**

**Given** storage is operational
**When** OpenBao is deployed
**Then** `clusters/infra/apps/platform/openbao/` contains:
- OpenBao deployment (latest version)
- Persistent storage for vault data
- HTTPRoute for API and UI access
- Auto-unseal configuration (or documented manual unseal)
**And** OpenBao is initialized and unsealed
**And** secrets can be read/written via CLI and API
**And** Kubernetes auth method is configured for pod authentication
**And** OpenBao UI is accessible via `openbao.monosense.dev`

---

### Story 8.5: Configure Platform Health Monitoring and Integration

**As a** developer,
**I want** platform health visibility and integration documentation,
**So that** I can build applications against a known-healthy platform.

**Acceptance Criteria:**

**Given** all platform components are deployed
**When** health monitoring is configured
**Then** Gatus ConfigMap includes health checks for:
- Kafka bootstrap endpoint
- Apicurio Registry `/health`
- Keycloak `/health/ready`
- OpenBao `/v1/sys/health`
- External MinIO S3 API (`s3.monosense.dev`)
**And** Gatus dashboard shows all platform services health
**And** `docs/platform/arsipq-integration.md` documents:
- Connection endpoints for each service
- Authentication configuration
- Spring Boot integration examples
- Schema registry usage patterns
**And** Flux Kustomization can reference arsipq-backend manifests for application deployment
