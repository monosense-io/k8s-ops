# Story 3.2: Configure Renovate for Dependency Management

Status: ready-for-dev

## Story

As a **platform operator**,
I want **Renovate automatically creating PRs for dependency updates grouped by type**,
So that **I can keep components updated with minimal manual effort and have a unified update strategy across both clusters**.

## Acceptance Criteria

1. **Given** the repository with HelmReleases and container images
   **When** Renovate is configured
   **Then** `renovate.json5` contains:
   - Preset extending `config:recommended`
   - Custom managers for Flux HelmRelease resources
   - Grouping rules: patch updates weekly, minor monthly, major as individual PRs
   - Automerge enabled for patch updates in non-production (infra cluster)
   - Labels for PR categorization (helm, docker, github-actions)

2. **And** Renovate bot has access to the repository

3. **And** PRs include changelog links and release notes

4. **And** shared dependencies in `infrastructure/base/` create single PR affecting both clusters

## Tasks / Subtasks

- [ ] Task 1: Create Renovate Configuration File (AC: #1)
  - [ ] Create `renovate.json5` at repository root
  - [ ] Extend `config:recommended` preset
  - [ ] Configure `config:base` for Dependency Dashboard and monorepo grouping
  - [ ] Set timezone to appropriate value (e.g., `Asia/Jakarta`)
  - [ ] Configure semantic commit messages to match project format

- [ ] Task 2: Configure Flux Manager for HelmRelease Detection (AC: #1, #4)
  - [ ] Enable `flux` manager for HelmRelease/HelmRepository/OCIRepository
  - [ ] Configure file matching patterns for `kubernetes/**/*.yaml`
  - [ ] Configure file matching patterns for `infrastructure/**/*.yaml`
  - [ ] Configure file matching patterns for `clusters/**/*.yaml`
  - [ ] Ensure namespace linking works for HelmRelease → HelmRepository

- [ ] Task 3: Configure Docker/Container Image Updates (AC: #1)
  - [ ] Enable `regex` manager for container images in HelmRelease values
  - [ ] Match image tags with `@sha256:` digest pattern
  - [ ] Configure datasources for Docker Hub, ghcr.io, quay.io

- [ ] Task 4: Configure Package Grouping Rules (AC: #1, #3)
  - [ ] Create package rule for patch updates (weekly schedule, automerge)
  - [ ] Create package rule for minor updates (monthly schedule)
  - [ ] Create package rule for major updates (individual PRs, no automerge)
  - [ ] Group known monorepo packages together
  - [ ] Configure release notes and changelog links in PRs

- [ ] Task 5: Configure Labels and PR Settings (AC: #1, #3)
  - [ ] Add label `renovate` for all Renovate PRs
  - [ ] Add label `helm` for Helm chart updates
  - [ ] Add label `docker` for container image updates
  - [ ] Add label `github-actions` for workflow updates
  - [ ] Configure PR body template with changelog links

- [ ] Task 6: Configure Automerge Strategy (AC: #1)
  - [ ] Enable automerge for patch updates
  - [ ] Disable automerge for major updates
  - [ ] Configure `platformAutomerge: true` for native GitHub automerge
  - [ ] Set `automergeType: "pr"` for PR-based automerge
  - [ ] Exclude critical paths from automerge (e.g., `clusters/apps/`)

- [ ] Task 7: Configure GitHub Actions Manager (AC: #1)
  - [ ] Enable `github-actions` manager for workflow updates
  - [ ] Match `.github/workflows/*.yaml` files
  - [ ] Group GitHub Actions updates together

- [ ] Task 8: Configure Scheduling (AC: #1)
  - [ ] Set schedule for patch updates (weekly, e.g., weekends)
  - [ ] Set schedule for minor updates (monthly, first week)
  - [ ] Configure rate limiting to avoid PR flood

- [ ] Task 9: Verify Renovate Access and Configuration (AC: #2, #4)
  - [ ] Ensure Renovate GitHub App is installed on repository
  - [ ] Run `renovate-config-validator` on configuration
  - [ ] Verify Dependency Dashboard issue is created
  - [ ] Test that PRs are created for known outdated dependencies

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **FRs Covered (Epic 3: GitOps Operations):**
   - FR7: Operator can receive consolidated Renovate PRs for shared dependencies
   - FR8: Operator can validate Flux manifests via GitHub Actions before merge
   - FR9: Operator can configure Renovate to group updates by type (patch/minor/major)

2. **Renovate Multi-Cluster Strategy (Critical Decision from architecture.md):**
   > **Decision 4: Renovate Multi-Cluster Strategy**
   >
   > **Decision:** Single PR for both clusters
   >
   > **Pattern:**
   > - Renovate updates version in `infrastructure/base/` or `apps/base/`
   > - Single PR affects both clusters through base/overlay inheritance
   > - Staged rollout (Decision 3) handles timing between clusters
   >
   > **Rationale:** Matches base/overlay pattern, avoids duplicate PRs, staged rollout ensures safety.

3. **Staged Rollout Integration:**
   - Changes merged to `main` → infra cluster (immediate)
   - GitHub Action fast-forwards `release` branch after 24h → apps cluster
   - Renovate PRs merged to `main` follow same pattern

4. **Git Commit Message Format:**
   ```
   <type>(<scope>): <description>

   Types: feat, fix, refactor, chore, docs, ci
   Scopes: infra, apps, flux, talos, bootstrap, renovate
   ```
   Renovate should use `chore(renovate): <description>` format.

### Project Context Rules (Critical)

**From project-context.md:**

1. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`) for all Kubernetes manifests
   - Renovate config: `renovate.json5` (JSON5 for comments)

2. **Version Pinning Pattern (Critical for Renovate):**
   ```yaml
   image:
     repository: docker.io/cloudflare/cloudflared
     tag: 2025.9.1@sha256:4604b477520dc8322af5427da68b44f0bf814938e9d2e4814f2249ee4b03ffdf
   ```
   Renovate must update both tag AND digest.

3. **OCIRepository Pattern:**
   ```yaml
   chartRef:
     kind: OCIRepository
     name: app-template
     namespace: flux-system
   ```
   Renovate's flux manager handles OCIRepository updates.

4. **HelmRelease API Version:**
   - Use `helm.toolkit.fluxcd.io/v2` (not v2beta1 or v2beta2)

### Renovate Flux Manager Requirements

**From Renovate Documentation (https://docs.renovatebot.com/modules/manager/flux/):**

1. **HelmRelease Detection:**
   - Renovate extracts helm dependencies from HelmRelease resources
   - For proper linking, HelmRelease must have `metadata.namespace` or `spec.chart.spec.sourceRef.namespace` set
   - Referenced HelmRepository resources must have `metadata.namespace` set

2. **Supported Resources:**
   - HelmRelease (linked to HelmRepository or GitRepository)
   - OCIRepository (tag and digest updates)
   - HelmRepository (url updates)
   - GitRepository (git reference updates)

3. **Flux System Manifests:**
   - Renovate can update `gotk-components.yaml` files
   - Identified via naming pattern and comment headers from `flux bootstrap`

### Recommended Renovate Configuration

**Based on FluxCD community best practices:**

```json5
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":semanticCommits",
    "group:monorepos",
    "helpers:pinGitHubActionDigests"
  ],
  "timezone": "Asia/Jakarta",
  "semanticCommitScope": "renovate",
  "semanticCommitType": "chore",
  "flux": {
    "fileMatch": [
      "(^|/)kubernetes/.+\\.ya?ml$",
      "(^|/)infrastructure/.+\\.ya?ml$",
      "(^|/)clusters/.+\\.ya?ml$"
    ]
  },
  "helm-values": {
    "fileMatch": [
      "(^|/)kubernetes/.+\\.ya?ml$",
      "(^|/)clusters/.+\\.ya?ml$"
    ]
  },
  "packageRules": [
    // Patch updates - weekly, automerge
    {
      "matchUpdateTypes": ["patch"],
      "schedule": ["after 10pm on saturday"],
      "automerge": true,
      "automergeType": "pr"
    },
    // Minor updates - monthly
    {
      "matchUpdateTypes": ["minor"],
      "schedule": ["on the first day of the month"],
      "automerge": false
    },
    // Major updates - individual PRs
    {
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "dependencyDashboardApproval": true
    },
    // Disable automerge for apps cluster (production)
    {
      "matchPaths": ["clusters/apps/**"],
      "automerge": false
    },
    // Labels
    {
      "matchManagers": ["flux", "helm-values"],
      "addLabels": ["helm"]
    },
    {
      "matchManagers": ["docker-compose", "dockerfile", "kubernetes"],
      "addLabels": ["docker"]
    },
    {
      "matchManagers": ["github-actions"],
      "addLabels": ["github-actions"]
    }
  ],
  "labels": ["renovate"],
  "platformAutomerge": true,
  "rebaseWhen": "conflicted",
  "dependencyDashboard": true,
  "dependencyDashboardTitle": "Renovate Dashboard - k8s-ops"
}
```

### Previous Story Intelligence

**From Story 3.1 (Create Flux Operational Taskfiles):**
- `.taskfiles/flux/Taskfile.yaml` created with comprehensive Flux operations
- Multi-cluster context handling established (CLUSTER variable)
- Preconditions pattern for validation established
- Integration with Flux CLI commands documented

**Key Learnings:**
- Use `.yaml` extension consistently
- Tasks should be cluster-aware with CLUSTER variable
- Include preconditions for validation
- Provide detailed summaries with examples
- Follow Taskfile v3 patterns

### Technology Stack Requirements

**Required Tools:**
- Renovate GitHub App or Self-hosted Renovate
- `renovate-config-validator` CLI for testing
- GitHub repository with appropriate permissions

**Renovate Version:**
- Latest stable version (self-managed or GitHub App)
- Flux manager requires recent Renovate version for OCIRepository support

### Directory Structure Impact

```
k8s-ops/
├── renovate.json5                          # Renovate configuration (NEW)
├── .github/
│   └── renovate.yaml                       # Alternative config location (if preferred)
├── infrastructure/
│   └── base/
│       └── repositories/                   # Shared HelmRepository/OCIRepository
├── kubernetes/
│   └── apps/                               # Shared app definitions
└── clusters/
    ├── infra/                              # Infra cluster (immediate updates)
    └── apps/                               # Apps cluster (staged updates)
```

### Renovate File Match Patterns

**For Flux Resources:**
```json5
"flux": {
  "fileMatch": [
    "(^|/)kubernetes/.+\\.ya?ml$",
    "(^|/)infrastructure/.+\\.ya?ml$",
    "(^|/)clusters/.+\\.ya?ml$",
    "(^|/)bootstrap/.+\\.ya?ml$"
  ]
}
```

**For Helm Values (container images):**
```json5
"helm-values": {
  "fileMatch": [
    "(^|/)kubernetes/.+\\.ya?ml$",
    "(^|/)clusters/.+\\.ya?ml$"
  ]
}
```

### Automerge Configuration

**Safe Automerge Strategy:**
1. Enable automerge for **patch** updates only
2. Disable for **major** updates (breaking changes)
3. Disable for **apps cluster** paths (production safety)
4. Use `platformAutomerge: true` for GitHub native automerge
5. Require status checks to pass before automerge

**From Renovate Docs:**
> By default, Renovate will not assign reviewers and assignees to an automerge-enabled PR unless it fails status checks.

### Package Grouping Strategy

1. **Monorepo Groups:** Group known monorepos (e.g., Kubernetes, FluxCD)
2. **Type-based Groups:** Group by update type (patch, minor, major)
3. **Manager-based Labels:** Add labels based on manager type
4. **Path-based Rules:** Different rules for different directories

### Validation Commands

```bash
# Validate Renovate configuration
npx renovate-config-validator renovate.json5

# Test Renovate dry-run (if self-hosted)
renovate --platform=github --dry-run=true

# Check GitHub App installation
gh api /repos/OWNER/REPO/installation
```

### Critical Implementation Rules

1. **Configuration Format:**
   - Use `renovate.json5` for JSON5 support (comments)
   - Extend `config:recommended` as base
   - Set timezone for scheduling

2. **Flux Manager:**
   - Enable flux manager with proper fileMatch patterns
   - Ensure HelmRelease has namespace set for proper linking
   - Support both HelmRepository and OCIRepository sources

3. **Commit Message Format:**
   - Use `chore(renovate): <description>` format
   - Enable `semanticCommits: true`
   - Set `semanticCommitScope: "renovate"`

4. **Automerge Safety:**
   - Only automerge patch updates
   - Disable automerge for apps cluster (production)
   - Require status checks to pass

5. **Labels:**
   - Add `renovate` label to all PRs
   - Add manager-specific labels (helm, docker, github-actions)

### Project Structure Notes

- **Location:** `renovate.json5` at repository root
- **Alternative:** `.github/renovate.json5` (if preferred)
- **Naming:** Use `.json5` extension for comment support
- **Validation:** Use `renovate-config-validator` before commit

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2: Configure Renovate for Dependency Management]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 4: Renovate Multi-Cluster Strategy]
- [Source: docs/project-context.md#Version Pinning Pattern]
- [Renovate Flux Manager Documentation](https://docs.renovatebot.com/modules/manager/flux/)
- [Renovate Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Renovate Automerge Configuration](https://docs.renovatebot.com/key-concepts/automerge/)
- [FluxCD HelmRelease Management](https://fluxcd.io/flux/guides/helmreleases/)

### Validation Checklist

Before marking complete, verify:
- [ ] `renovate.json5` created at repository root
- [ ] Configuration extends `config:recommended`
- [ ] Flux manager enabled with correct fileMatch patterns
- [ ] Package rules for patch/minor/major updates
- [ ] Automerge enabled for patch updates only
- [ ] Automerge disabled for apps cluster paths
- [ ] Labels configured (renovate, helm, docker, github-actions)
- [ ] Semantic commit messages configured
- [ ] Dependency Dashboard enabled
- [ ] Configuration validates with `renovate-config-validator`
- [ ] Renovate GitHub App has repository access
- [ ] First PR created for known outdated dependency

### Git Commit Message Format

```
chore(renovate): configure automated dependency management

- Add renovate.json5 with FluxCD manager configuration
- Configure patch/minor/major update grouping rules
- Enable automerge for patch updates (infra cluster only)
- Add labels for PR categorization (helm, docker, github-actions)
- FR7: Consolidated Renovate PRs for shared dependencies
- FR9: Grouped updates by type (patch/minor/major)
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

