---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Multi-Cluster Kubernetes GitOps Architecture Patterns'
research_goals: 'Determine optimal repository structure for managing 2 clusters (home/prod) in one repo; Identify Flux-specific patterns for multi-cluster management; Learn from community implementations'
user_name: 'monosense'
date: '2025-12-28'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2025-12-28
**Author:** monosense
**Research Type:** Technical

---

## Research Overview

**Topic:** Multi-Cluster Kubernetes GitOps Architecture Patterns

**Coverage Areas:**
1. Multi-cluster GitOps repository structures
2. Flux CD multi-cluster management patterns
3. Kubernetes GitOps monorepo vs polyrepo strategies
4. Multi-environment Kubernetes configuration management

**Application:** Direct application to k8s-ops integration project (merging home-ops + prod-ops)

---

## Technical Research Scope Confirmation

**Research Topic:** Multi-Cluster Kubernetes GitOps Architecture Patterns

**Research Goals:**
- Determine optimal repository structure for managing 2 clusters (home/prod) in one repo
- Identify Flux-specific patterns for multi-cluster management
- Learn from community implementations

**Technical Research Scope:**
- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**
- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2025-12-28

---

## Technology Stack Analysis

### Core GitOps Tooling

**Flux CD** is the primary GitOps operator for multi-cluster Kubernetes management. It supports syncing from multiple Git sources into multiple clusters, providing consistent, declarative control for complex environments.

_Key Capabilities:_
- Native multi-cluster support via Remote Apply feature
- Kustomize and Helm integration
- Built-in multi-tenancy lockdown features
- Path and ref-specific sources for environment separation

_Source: [Flux Documentation](https://fluxcd.io/flux/)_

**Kustomize** serves as the operator-agnostic configuration management layer. Both Flux and Argo CD understand kustomization.yaml, making it a portable foundation for GitOps structures.

_Key Features:_
- Base and overlay patterns for environment configuration
- No templating language required (pure YAML patching)
- Native Kubernetes integration
- Component reusability across clusters

_Source: [Flux Kustomization Guide](https://fluxcd.io/flux/components/kustomize/kustomizations/)_

### Repository Structure Patterns

**Monorepo Approach:**
All Kubernetes manifests stored in a single Git repository. Typical structure includes `apps/`, `infrastructure/`, and `clusters/` directories with base and overlay patterns.

_Advantages:_
- Simplified dependency management
- Atomic updates across services
- Single source of truth

_Disadvantages:_
- Difficult per-folder authorization
- Performance issues with large repos
- Unintentional production changes harder to spot

_Source: [Flux Repository Structure Guide](https://fluxcd.io/flux/guides/repository-structure/)_

**Polyrepo Approach:**
Separate repositories per team, environment, or application. More scalable and resilient for larger organizations.

_Patterns:_
- Repo per Team/Tenant
- Repo per Application
- Repo per Environment

_Source: [GitOps Repository Patterns - Cloudogu](https://platform.cloudogu.com/en/blog/gitops-repository-patterns-part-3-repository-patterns/)_

### Multi-Cluster Deployment Modes

**Standalone Mode:**
Each Kubernetes cluster runs its own Flux controllers, reconciling independently from the same or different bootstrap repositories.

_Benefits:_
- Reduced attack surface (no exposed API servers)
- Reduced blast radius (self-sufficient clusters)
- Suitable for air-gapped environments

_Drawbacks:_
- Operational overhead (separate bootstrap per cluster)
- Maintenance overhead (independent updates)
- Monitoring overhead (separate observability)

_Source: [FluxCD Multi-cluster Architecture - Stefan Prodan](https://stefanprodan.com/blog/2024/fluxcd-multi-cluster-architecture/)_

**Hub and Spoke Mode:**
Central cluster acts as GitOps hub, managing continuous delivery for multiple spoke clusters by connecting to their Kubernetes API servers.

_Benefits:_
- Reduced operational overhead (single bootstrap)
- Single pane of glass monitoring
- Suitable for Cluster API provisioning

_Drawbacks:_
- Single point of failure
- Security concerns if hub compromised

_Source: [FluxCD Multi-cluster Architecture - Medium](https://medium.com/@stefanprodan/fluxcd-multi-cluster-architecture-e426fb2bca0f)_

### Configuration Management Tools

**SOPS (Secrets OPerationS):**
Encryption tool supporting AGE, GPG, and cloud KMS. Encrypts only values in YAML/JSON, keeping keys readable for version control.

**External Secrets Operator:**
Kubernetes operator that syncs secrets from external providers (1Password, Vault, AWS Secrets Manager) into native Kubernetes secrets.

**Renovate:**
Automated dependency update tool that monitors repositories for outdated dependencies and creates PRs automatically.

_Source: [Flux Multi-Tenancy Example](https://github.com/fluxcd/flux2-multi-tenancy)_

### Community Reference Implementations

**onedr0p/home-ops:**
Popular mono repository pattern for home infrastructure using Talos, Flux, and GitOps practices. Structure:
```
kubernetes/
├── main/           # main cluster
│   ├── apps/       # applications
│   ├── bootstrap/  # bootstrap procedures
│   ├── flux/       # core flux configuration
│   └── templates/  # re-useable components
```

_Source: [onedr0p/home-ops](https://github.com/onedr0p/home-ops)_

**bjw-s-labs/home-ops:**
Similar pattern using Ansible, Terraform, Kubernetes, Flux, Renovate, and GitHub Actions for infrastructure automation.

_Source: [bjw-s-labs/home-ops](https://github.com/bjw-s-labs/home-ops)_

**flux2-kustomize-helm-example:**
Official Flux example demonstrating multi-environment deployments using Kustomize overlays and Helm releases.

_Source: [flux2-kustomize-helm-example](https://github.com/fluxcd/flux2-kustomize-helm-example)_

### Key Best Practices Identified

1. **Separate application code from configuration** - Keep source code in app repos, manifests in GitOps repos
2. **Use DRY principles** - "Don't Repeat YAML" via Kustomize bases/overlays or Helm
3. **All environments in same branch** - Different folders, not branches, for environments
4. **Limit folder depth to 3 levels** - Deeper structures become hard to navigate
5. **Organize around workflows and people** - Reduce friction between activities and folders

_Sources: [Red Hat GitOps Structure](https://developers.redhat.com/articles/2022/09/07/how-set-your-gitops-directory-structure), [Cloudogu GitOps Patterns](https://github.com/cloudogu/gitops-patterns)_

### Approved Repository Structure for k8s-ops

Based on analysis and user requirements, the following structure is approved:

```
k8s-ops/
├── clusters/
│   ├── infra/              # Infrastructure cluster (formerly home-ops)
│   │   ├── apps/           # Infra-only apps (observability hub, platform services)
│   │   ├── flux/           # Flux configuration + cluster-vars
│   │   └── talos/          # Talos machine configs
│   └── apps/               # Applications cluster (formerly prod-ops)
│       ├── apps/           # Apps-only apps (business workloads)
│       ├── flux/           # Flux configuration + cluster-vars
│       └── talos/          # Talos machine configs
├── bootstrap/
│   ├── infra/              # Infra cluster bootstrap (helmfile)
│   └── apps/               # Apps cluster bootstrap (helmfile)
├── infrastructure/
│   └── base/               # Shared CRDs, controllers, repositories
├── kubernetes/
│   ├── apps/               # Shared app definitions (both clusters)
│   └── components/         # Reusable Kustomize components
├── terraform/              # Cloudflare, R2, shared modules
└── .taskfiles/             # Unified task automation
```

**Cluster Mapping:**
- home-ops → `clusters/infra/` (cluster name: infra, CLUSTER_ID: 1)
- prod-ops → `clusters/apps/` (cluster name: apps, CLUSTER_ID: 2)

**Key Decisions:**
- Talos configs kept within cluster directories for locality
- Shared infrastructure and app bases at top level
- Unified bootstrap, terraform, and taskfiles
- Observability: infra=hub (full stack), apps=spoke (remote-write only)

---

## Integration Patterns Analysis

### Kustomize Base and Overlay Patterns

**Base/Overlay Architecture:**
Kustomize supports bases (shared configurations) and overlays (environment-specific customizations). Overlays inherit from bases or other overlays, enabling configuration inheritance without duplication.

_Pattern for k8s-ops:_
```
kubernetes/apps/              # Shared app definitions (deployed to BOTH clusters)
├── databases/cloudnative-pg/
├── security/authentik/
├── observability/gatus/
└── ...

clusters/infra/apps/          # Infra-only apps
├── observability/victoria-metrics/  # Hub - metrics storage
├── observability/victoria-logs/     # Hub - log storage
└── platform/strimzi-kafka/

clusters/apps/apps/           # Apps-only apps
├── observability/vmagent/    # Spoke - remote-write to infra
└── business/odoo/
```

_Source: [Kustomize Multibases Example](https://github.com/kubernetes-sigs/kustomize/blob/master/examples/multibases/README.md)_

**Kustomize Components (v3.7.0+):**
Components (`kind: Component`) allow reusable configuration logic across multiple overlays. Define a change once as a component, then reference it from multiple overlays.

_Your existing components (cnpg, volsync, gatus) fit this pattern perfectly._

_Source: [Using Kustomize Components - Scott Lowe](https://blog.scottlowe.org/2021/11/01/using-kustomize-components-with-cluster-api/)_

### Flux Dependency Management

**dependsOn Feature:**
Flux allows defining reconciliation order between Kustomizations. Essential for ensuring CRDs exist before custom resources are applied.

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
spec:
  dependsOn:
    - name: infrastructure
    - name: cert-manager
```

_Key Rules:_
- Avoid circular dependencies (never applied)
- Use `readyExpr` for custom readiness logic
- Platform team defines order between infrastructure and tenant apps

_Source: [Flux Kustomization Docs](https://fluxcd.io/flux/components/kustomize/kustomizations/)_

### Variable Substitution for Multi-Environment

**postBuild.substitute:**
Flux provides post-build variable substitution for templating manifests without full Helm complexity.

```yaml
spec:
  postBuild:
    substitute:
      cluster_name: "dev"
      cluster_domain: "monosense.dev"
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
      - kind: Secret
        name: cluster-secrets
```

_Use Cases:_
- Cluster-specific domain names
- Environment labels
- Resource sizing per cluster
- Secret references

_Limitation: Variables don't cascade to child Kustomizations automatically._

_Source: [Variable Substitution in Flux - Budiman JoJo](https://budimanjojo.com/2021/10/27/variable-substitution-in-flux-gitops/)_

### Helm Values Inheritance

**Hierarchical Values Pattern:**
For Helm-based apps, use value file hierarchies:
```
values/
├── base.values.yaml         # Shared defaults
├── dev.values.yaml          # Dev overrides
└── prod.values.yaml         # Prod overrides
```

_Override chain: `base → environment → cluster-specific`_

_Source: [Helm GitOps Adventure - Medium](https://medium.com/@percenuage/my-adventure-with-helm-as-gitops-in-a-distributed-architecture-6a6fdc6f11bd)_

### Shared Repository Patterns for k8s-ops

**Recommended Integration Structure:**

```
k8s-ops/
├── infrastructure/
│   └── base/                        # Shared infra (CRDs, controllers, repos)
│       ├── repositories/            # Shared HelmRepository/OCIRepository
│       ├── cert-manager/
│       ├── external-secrets/
│       └── cilium/
├── kubernetes/
│   ├── apps/                        # Shared app definitions (BOTH clusters)
│   │   ├── databases/cloudnative-pg/
│   │   ├── security/authentik/
│   │   └── observability/gatus/
│   └── components/                  # Reusable Kustomize components
│       ├── cnpg/
│       └── volsync/
└── clusters/
    ├── infra/
    │   ├── flux/
    │   │   ├── kustomization.yaml   # Entry point
    │   │   └── cluster-vars.yaml    # CLUSTER_NAME=infra, CLUSTER_ID=1
    │   └── apps/                    # Infra-only apps
    │       └── observability/victoria-metrics/
    └── apps/
        ├── flux/
        │   ├── kustomization.yaml   # Entry point
        │   └── cluster-vars.yaml    # CLUSTER_NAME=apps, CLUSTER_ID=2
        └── apps/                    # Apps-only apps
            └── business/odoo/
```

### Cross-Cluster Dependency Strategy

**For your infra/apps clusters:**

| Layer | Infra Cluster | Apps Cluster | Location |
|-------|---------------|--------------|----------|
| CRDs | Sync first | Sync first | infrastructure/base/ |
| Controllers | dependsOn CRDs | dependsOn CRDs | infrastructure/base/ |
| Shared Apps | dependsOn controllers | dependsOn controllers | kubernetes/apps/ |
| Cluster Apps | dependsOn shared apps | dependsOn shared apps | clusters/{cluster}/apps/ |

**Staged Rollout:**
- Infra cluster reconciles from `main` branch (immediate)
- Apps cluster reconciles from `release` branch (24h delayed promotion)

_Source: [Flux Multi-Cluster Architecture - Stefan Prodan](https://medium.com/@stefanprodan/fluxcd-multi-cluster-architecture-e426fb2bca0f)_

---

## Executive Summary

### Research Objective
Determine the optimal repository structure and patterns for consolidating two existing Kubernetes GitOps repositories (`home-ops` and `prod-ops`) into a unified `k8s-ops` repository while maintaining operational independence and enabling shared configuration.

### Key Findings

1. **Standalone Mode is Optimal**: Each cluster should run its own Flux controllers, reconciling independently from the shared repository. This provides reduced blast radius, self-sufficiency, and matches your current operational model.

2. **Monorepo with Cluster Directories**: The community standard for multi-cluster GitOps is a single repository with cluster-specific directories. This aligns with onedr0p/home-ops and bjw-s-labs/home-ops patterns you're already following.

3. **Your Existing Patterns are Best Practice**: Talos + Flux + Kustomize + SOPS + 1Password + Renovate is the proven stack for home lab and production GitOps.

4. **Kustomize Components Enable Reuse**: Your existing components (cnpg, volsync, gatus) are the correct abstraction for cross-cluster configuration sharing.

### Strategic Recommendations

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| 1 | Adopt `clusters/{dev,prod}/` structure | Standard pattern, clear separation |
| 2 | Keep Talos configs within cluster dirs | Locality, easier maintenance |
| 3 | Create shared `infrastructure/base/` | Deduplicate common CRDs/controllers |
| 4 | Use `apps/base/` + `apps/overlays/` | DRY principle for shared apps |
| 5 | Implement cluster-vars ConfigMaps | postBuild substitution for env differences |

---

## Final Approved Repository Structure

```
k8s-ops/
├── clusters/
│   ├── infra/                       # Infrastructure cluster (formerly home-ops)
│   │   ├── apps/                    # Infra-only apps
│   │   │   ├── observability/       # VictoriaMetrics hub, VictoriaLogs, Grafana
│   │   │   ├── platform/            # Strimzi Kafka, Apicurio, Keycloak, OpenBao
│   │   │   └── selfhosted/          # Harbor, Mattermost
│   │   ├── flux/
│   │   │   ├── cluster-vars.yaml    # CLUSTER_NAME=infra, CLUSTER_ID=1
│   │   │   └── kustomization.yaml   # Entry point
│   │   └── talos/                   # Infra Talos machine configs
│   │       ├── talconfig.yaml
│   │       ├── clusterconfig/
│   │       └── patches/
│   └── apps/                        # Applications cluster (formerly prod-ops)
│       ├── apps/                    # Apps-only apps
│       │   ├── observability/       # VMAgent, Fluent-bit (remote-write to infra)
│       │   └── business/            # Odoo, n8n, ArsipQ
│       ├── flux/
│       │   ├── cluster-vars.yaml    # CLUSTER_NAME=apps, CLUSTER_ID=2
│       │   └── kustomization.yaml   # Entry point
│       └── talos/                   # Apps Talos machine configs
│           ├── talconfig.yaml
│           ├── clusterconfig/
│           └── patches/
├── infrastructure/
│   └── base/                        # Shared infrastructure
│       ├── repositories/            # Shared HelmRepository/OCIRepository
│       ├── cert-manager/
│       ├── external-secrets/
│       ├── cilium/
│       ├── rook-ceph/
│       ├── openebs/
│       └── envoy-gateway/
├── kubernetes/
│   ├── apps/                        # Shared app definitions (BOTH clusters)
│   │   ├── databases/cloudnative-pg/
│   │   ├── security/authentik/
│   │   ├── observability/gatus/
│   │   └── networking/external-dns/
│   └── components/                  # Reusable Kustomize components
│       ├── cnpg/
│       ├── volsync/
│       ├── gatus/
│       └── dragonfly/
├── bootstrap/
│   ├── infra/                       # Infra cluster bootstrap (helmfile)
│   │   └── helmfile.d/
│   └── apps/                        # Apps cluster bootstrap (helmfile)
│       └── helmfile.d/
├── terraform/
│   ├── cloudflare/                  # DNS and R2 configuration
│   └── modules/
├── .github/
│   └── workflows/                   # Unified CI/CD
├── .taskfiles/                      # Unified task automation
├── .sops.yaml                       # SOPS config (AGE key)
├── renovate.json5                   # Renovate config
└── docs/
```

---

## Implementation Checklist

### Phase 1: Repository Setup (Epic 0)
- [ ] Create k8s-ops directory structure per architecture
- [ ] Create `.sops.yaml` with AGE key
- [ ] Create `renovate.json5` for dependency automation
- [ ] Set up `.github/workflows/` (validate, flux-diff, gitleaks)
- [ ] Create `.taskfiles/` structure
- [ ] Create `Taskfile.yaml` root entry point

### Phase 2: Infra Cluster Migration (home-ops → clusters/infra/)
- [ ] Copy Talos configs to `clusters/infra/talos/`
- [ ] Create `clusters/infra/flux/cluster-vars.yaml` (CLUSTER_NAME=infra, CLUSTER_ID=1)
- [ ] Move shared infrastructure to `infrastructure/base/`
- [ ] Move shared apps to `kubernetes/apps/`
- [ ] Configure infra-only apps in `clusters/infra/apps/` (VictoriaMetrics hub)
- [ ] Create bootstrap/infra/helmfile.d/ with CRD-first pattern
- [ ] Update Flux GitRepository to point to k8s-ops
- [ ] Test reconciliation

### Phase 3: Apps Cluster Migration (prod-ops → clusters/apps/)
- [ ] Copy Talos configs to `clusters/apps/talos/`
- [ ] Create `clusters/apps/flux/cluster-vars.yaml` (CLUSTER_NAME=apps, CLUSTER_ID=2)
- [ ] Configure apps-only apps in `clusters/apps/apps/` (business workloads)
- [ ] Configure VMAgent + Fluent-bit to remote-write to infra cluster
- [ ] Create bootstrap/apps/helmfile.d/ with CRD-first pattern
- [ ] Update Flux GitRepository to point to k8s-ops
- [ ] Test reconciliation
- [ ] Validate cross-cluster observability

### Phase 4: Optimization & Staged Rollout
- [ ] Deduplicate Helm repositories to `infrastructure/base/repositories/`
- [ ] Consolidate Kustomize components to `kubernetes/components/`
- [ ] Set up GitHub workflow for main → release branch promotion (24h delay)
- [ ] Update Renovate groups for unified repo
- [ ] Archive old repositories (home-ops, prod-ops)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Flux path changes break reconciliation | Test in branch first, gradual rollout |
| Secrets/SOPS issues | Same AGE key, verify decrypt before migration |
| Cluster downtime during migration | Keep old repos as fallback, migrate one cluster at a time |
| Renovate PR conflicts | Separate Renovate runs per cluster initially |

---

## Sources

### Official Documentation
- [Flux Repository Structure Guide](https://fluxcd.io/flux/guides/repository-structure/)
- [Flux Kustomization Docs](https://fluxcd.io/flux/components/kustomize/kustomizations/)
- [Flux Multi-Tenancy](https://fluxcd.io/flux/installation/configuration/multitenancy/)

### Architecture References
- [FluxCD Multi-cluster Architecture - Stefan Prodan](https://stefanprodan.com/blog/2024/fluxcd-multi-cluster-architecture/)
- [Multi-Cluster GitOps with EKS and Flux - AWS](https://aws.amazon.com/blogs/containers/part-1-build-multi-cluster-gitops-using-amazon-eks-flux-cd-and-crossplane/)

### Community Examples
- [onedr0p/home-ops](https://github.com/onedr0p/home-ops)
- [bjw-s-labs/home-ops](https://github.com/bjw-s-labs/home-ops)
- [flux2-kustomize-helm-example](https://github.com/fluxcd/flux2-kustomize-helm-example)
- [flux2-multi-tenancy](https://github.com/fluxcd/flux2-multi-tenancy)

### Best Practices
- [GitOps Repository Patterns - Cloudogu](https://platform.cloudogu.com/en/blog/gitops-repository-patterns-part-6-examples/)
- [Red Hat GitOps Directory Structure](https://developers.redhat.com/articles/2022/09/07/how-set-your-gitops-directory-structure)
- [Kustomize Best Practices](https://www.openanalytics.eu/blog/2021/02/23/kustomize-best-practices/)

---

**Research Completed:** 2025-12-28
**Confidence Level:** High - Based on official Flux documentation, community patterns, and your existing infrastructure
**Next Step:** Create PRD for k8s-ops implementation
