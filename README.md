# k8s-ops

GitOps repository for managing multi-cluster Kubernetes infrastructure using Flux CD.

## Overview

This repository manages two Kubernetes clusters:

| Cluster | Purpose | Domain |
|---------|---------|--------|
| **infra** | Infrastructure services, observability hub | `monosense.dev` |
| **apps** | Business applications | `monosense.io` |

## Technology Stack

- **Talos Linux v1.12.0** - Immutable Kubernetes OS
- **Cilium v1.18.5** - CNI with eBPF datapath
- **Flux CD v2.7.5** - GitOps with Kustomize + Helm
- **SOPS + AGE** - Secret encryption

## Repository Structure

```
k8s-ops/
├── clusters/           # Cluster-specific configurations
│   ├── infra/          # Infra cluster (formerly home-ops)
│   │   ├── apps/       # Cluster-specific apps
│   │   ├── flux/       # Flux configuration
│   │   └── talos/      # Talos machine configs
│   └── apps/           # Apps cluster (formerly prod-ops)
├── infrastructure/     # Shared infrastructure
│   └── base/           # CRDs, controllers, repositories
├── kubernetes/         # Shared Kubernetes resources
│   ├── apps/           # Apps deployed to BOTH clusters
│   └── components/     # Reusable Kustomize components
├── bootstrap/          # Cluster bootstrap configurations
│   ├── infra/          # Helmfile for infra cluster
│   └── apps/           # Helmfile for apps cluster
├── .taskfiles/         # Task automation
├── terraform/          # Infrastructure modules
├── tests/              # Integration and smoke tests
└── docs/               # Documentation and runbooks
```

## Quick Start

### Prerequisites

- [talosctl](https://www.talos.dev/latest/talos-guides/install/talosctl/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [flux](https://fluxcd.io/flux/installation/)
- [task](https://taskfile.dev/installation/)
- [sops](https://github.com/getsops/sops)
- [age](https://github.com/FiloSottile/age)
- [helmfile](https://helmfile.readthedocs.io/en/latest/#installation) - for bootstrap operations
- [kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/) - for manifest validation
- [yamllint](https://yamllint.readthedocs.io/en/stable/quickstart.html#installing-yamllint) - for YAML linting (`pip install yamllint`)

> **Note:** This repository must be cloned via `git clone` or initialized with `git init` before running tasks. The Taskfile uses `git rev-parse` to determine the repository root.

### Working with Clusters

```bash
# Set target cluster (default: infra)
export CLUSTER=infra  # or 'apps'

# List available tasks
task --list

# Validate YAML and Kustomize builds
task validate

# Bootstrap a cluster (placeholder - see Story 1.3)
task bootstrap:talos

# Reconcile Flux (placeholder - see Story 1.5)
task flux:reconcile
```

> **Note:** Bootstrap and operational tasks are placeholders until the corresponding stories are implemented.

## Documentation

- [Architecture Decision Records](docs/adr/)
- [Runbooks](docs/runbooks/)
- [Architecture Documentation](docs/architecture/)

## License

MIT
