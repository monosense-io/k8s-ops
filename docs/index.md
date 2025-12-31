# k8s-ops Project Documentation

## Overview

This project consolidates two existing Kubernetes GitOps repositories into a unified multi-cluster management solution:

| Source Repo | Cluster | Purpose | Network |
|-------------|---------|---------|---------|
| `home-ops` | k8s | Home lab / Media services | 10.25.11.0/24 |
| `prod-ops` | prod | Production / Business apps | 10.25.13.0/24 |

## Quick Reference

### Shared Infrastructure

| Component | Details |
|-----------|---------|
| **OS** | Talos Linux v1.11.2 |
| **CNI** | Cilium (eBPF) |
| **GitOps** | Flux CD |
| **Secrets** | 1Password + External Secrets |
| **Encryption** | SOPS with AGE |
| **Storage** | Rook-Ceph, OpenEBS, NFS |
| **Domains** | monosense.io (public), monosense.dev (private) |

### SOPS AGE Key (Shared)
```
age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
```

## Documentation Index

- [home-ops Analysis](./home-ops-analysis.md) - Detailed home lab cluster documentation
- [prod-ops Analysis](./prod-ops-analysis.md) - Detailed production cluster documentation
- [Integration Analysis](./integration-analysis.md) - Comparison and merge strategy

## Repository Statistics

| Metric | home-ops | prod-ops | Combined |
|--------|----------|----------|----------|
| HelmReleases | 80 | 60 | 140 |
| Namespaces | 16 | 16 | 32 (with overlaps) |
| ExternalSecrets | 37 | ~30 | ~67 |
| OCI Repositories | 11 | 85 | ~90 (deduplicated) |
| GitHub Workflows | 8 | 8 | 16 |

## Common Namespaces (Both Clusters)

| Namespace | Purpose |
|-----------|---------|
| kube-system | Core K8s infrastructure |
| flux-system | GitOps automation |
| cert-manager | TLS certificate management |
| external-secrets | Secrets from 1Password |
| networking | Ingress, DNS, tunnels |
| observability | Monitoring stack |
| databases | PostgreSQL, Dragonfly |
| storage/rook-ceph | Distributed storage |
| security | Authentik SSO |
| volsync-system | Backup/recovery |

## Unique to Each Cluster

### home-ops Only
- downloads (Plex, Sonarr, Radarr, qBittorrent)
- selfhosted/harbor (Container registry)
- selfhosted/mattermost (Team chat)

### prod-ops Only (migrating to apps cluster)
- business/arsipq (Spring Boot platform - replaces pilar)
- business/odoo (ERP)
- business/n8n (Workflow automation)

---

Generated: 2025-12-28
