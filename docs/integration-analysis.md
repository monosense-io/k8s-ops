# Integration Analysis: home-ops + prod-ops → k8s-ops

## Executive Summary

Merging `home-ops` and `prod-ops` into a unified `k8s-ops` repository will create a multi-cluster GitOps management solution. Both repositories share significant infrastructure patterns, making integration straightforward with proper planning.

## Compatibility Assessment

### Highly Compatible (No Changes Needed)

| Component | Status | Notes |
|-----------|--------|-------|
| SOPS AGE Key | Identical | Same key used in both repos |
| 1Password Integration | Compatible | Same provider, different vaults |
| Talos Linux | Compatible | Same version, similar configs |
| Cilium CNI | Compatible | Minor version difference (v1.18.1 vs v1.18.2) |
| Flux CD | Compatible | Similar structure, minor version diff |
| Renovate | Compatible | Same group structure and presets |
| GitHub Actions | Compatible | Identical workflow patterns |

### Requires Harmonization

| Component | Issue | Resolution |
|-----------|-------|------------|
| Directory Structure | Different flux paths | Standardize to common layout |
| Cluster Names | k8s vs prod | Use cluster-specific folders |
| Version Differences | Minor helm chart versions | Align to latest versions |
| Helm Repositories | Overlapping definitions | Deduplicate with shared repos |

## Proposed Repository Structure

```
k8s-ops/
├── clusters/
│   ├── infra/                   # Infrastructure cluster (formerly home-ops)
│   │   ├── apps/               # Cluster-specific apps (observability hub, platform services)
│   │   ├── flux/               # Cluster flux config
│   │   └── talos/              # Talos machine configs
│   └── apps/                    # Applications cluster (formerly prod-ops)
│       ├── apps/               # Cluster-specific apps (business workloads)
│       ├── flux/               # Cluster flux config
│       └── talos/              # Talos machine configs
├── infrastructure/
│   └── base/                    # Shared infrastructure (CRDs, controllers)
│       ├── repositories/       # Helm/OCI repos (deduplicated)
│       └── ...                 # cert-manager, cilium, external-secrets, etc.
├── kubernetes/
│   ├── apps/                    # Shared app definitions
│   └── components/              # Reusable Kustomize components
├── bootstrap/
│   ├── infra/                   # Infra cluster bootstrap (helmfile)
│   └── apps/                    # Apps cluster bootstrap (helmfile)
├── terraform/
│   ├── cloudflare/              # DNS and R2 configuration
│   └── modules/                # Shared TF modules
├── docs/                        # Unified documentation
├── .github/                     # Shared GitHub Actions
├── .renovate/                   # Shared Renovate config
└── .taskfiles/                  # Unified task automation
```

## Namespace Comparison

### Identical Namespaces (Merge Application Lists)

| Namespace | home-ops Apps | prod-ops Apps |
|-----------|--------------|---------------|
| kube-system | 9 apps | 9 apps |
| flux-system | 4 apps | 4 apps |
| cert-manager | 1 app | 1 app |
| external-secrets | 1 app | 1 app |
| networking | 7 apps | 7 apps |
| observability | 16 apps | 9 apps |
| databases | 3 apps | 3 apps |
| rook-ceph | 1 app | 1 app |
| openebs-system | 1 app | 1 app |
| volsync-system | 2 apps | 2 apps |
| system-upgrade | 1 app | 1 app |
| actions-runner-system | 3 apps | 1 app |
| security | 1 app | 1 app |

### Cluster-Specific Namespaces

**Infra Cluster Only (formerly home-ops):**
- downloads (6 apps: plex, sonarr, radarr, qbittorrent, prowlarr, overseerr)
- selfhosted/harbor (container registry)
- selfhosted/mattermost (team chat)
- storage/minio (S3-compatible storage - NOT backup destination)
- observability (full VictoriaMetrics stack - hub role)
- platform (Strimzi Kafka, Apicurio, Keycloak, OpenBao)

**Apps Cluster Only (formerly prod-ops):**
- business/odoo (ERP)
- business/n8n (workflow automation)
- business/arsipq (Spring Boot platform)
- observability (VMAgent + Fluent-bit only - spoke role)

## Version Alignment

### Core Components (Align to Latest)

| Component | home-ops | prod-ops | Target |
|-----------|----------|----------|--------|
| Cilium | 1.18.2 | 1.18.1 | 1.18.2 |
| CoreDNS | 1.44.3 | 1.43.3 | 1.44.3 |
| Cert-Manager | 1.19.0 | 1.18.2 | 1.19.0 |
| External-Secrets | 0.20.2 | 0.19.2 | 0.20.2 |
| Flux Operator | 0.31.0 | 0.28.0 | 0.31.0 |
| app-template | 4.3.0 | 4.2.0 | 4.3.0 |

## Integration Strategy

### Phase 1: Foundation
1. Create unified repository structure
2. Set up shared Helm/OCI repository definitions in `infrastructure/base/repositories/`
3. Create shared kustomize components library in `kubernetes/components/`
4. Establish common Renovate configuration
5. Create bootstrap helmfile configs for both clusters

### Phase 2: Infra Cluster Migration
1. Move home-ops cluster configs to `clusters/infra/`
2. Create `clusters/infra/flux/cluster-vars.yaml` with CLUSTER_NAME=infra, CLUSTER_ID=1
3. Update Flux kustomizations for new paths
4. Deploy observability hub (VictoriaMetrics full stack)
5. Test infra cluster reconciliation

### Phase 3: Apps Cluster Migration
1. Move prod-ops cluster configs to `clusters/apps/`
2. Create `clusters/apps/flux/cluster-vars.yaml` with CLUSTER_NAME=apps, CLUSTER_ID=2
3. Configure VMAgent + Fluent-bit to remote-write to infra cluster
4. Test apps cluster reconciliation
5. Validate cross-cluster observability

### Phase 4: Optimization
1. Deduplicate common applications to `kubernetes/apps/` base definitions
2. Create cluster overlays for environment differences
3. Consolidate GitHub Actions workflows
4. Unify task automation
5. Set up staged rollout (main → release branch promotion)

## Shared Resources

### Helm Repositories (Deduplicated)
```yaml
# Total unique repositories: ~90
# Shared between clusters: ~60
# Cluster-specific: ~30
```

### Kustomize Components (Reusable)
- cnpg (CloudNative PostgreSQL)
- volsync (Backup configuration)
- gatus (Health checks)
- dragonfly (Redis)
- secpol (Security policies)

### External Secrets Pattern
Both clusters use identical pattern:
```yaml
spec:
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  dataFrom:
    - extract:
        key: {1password-item}
```

## Network Considerations

| Cluster | Network | Gateway | VLAN | Domain |
|---------|---------|---------|------|--------|
| infra | 10.25.11.0/24 | 10.25.11.1 | 2511 | monosense.dev |
| apps | 10.25.13.0/24 | 10.25.13.1 | 2513 | monosense.io |

### Cross-Cluster Connectivity
- Same VLAN structure (2512)
- Same MTU (9000)
- Same bonding (LACP 802.3ad)
- Potential for service mesh integration

## Risk Assessment

### Low Risk
- Repository structure changes (no runtime impact)
- Renovate configuration consolidation
- Documentation merge

### Medium Risk
- Flux path changes (requires careful testing)
- Version upgrades during migration
- GitHub Actions runner configuration

### Mitigation Strategies
1. Test in staging/branch first
2. Migrate one cluster at a time
3. Keep rollback capability
4. Monitor Flux reconciliation status

## Benefits of Unification

1. **Single Source of Truth** - All cluster configs in one repo
2. **Reduced Duplication** - Shared components and repositories
3. **Consistent Tooling** - Unified Renovate, Actions, Tasks
4. **Easier Maintenance** - One place to update shared components
5. **Better Visibility** - Cross-cluster comparison and monitoring
6. **Simplified Onboarding** - Single repo to understand

## Next Steps

1. **PRD Creation** - Define detailed requirements for merged repo
2. **Architecture Design** - Finalize folder structure and patterns
3. **Migration Plan** - Create step-by-step migration checklist
4. **Testing Strategy** - Define validation criteria for each phase
