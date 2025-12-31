# Story 0.1: Initialize Repository Structure

Status: done

## Story

As a **platform operator**,
I want **a properly structured k8s-ops repository following FluxCD best practices**,
So that **I have a clear, organized foundation for managing multiple clusters**.

## Acceptance Criteria

1. **Given** a new GitHub repository named `k8s-ops`
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

2. **And** a root `Taskfile.yaml` exists referencing `.taskfiles/`

3. **And** `.gitignore` excludes sensitive files and build artifacts

4. **And** `renovate.json5` is configured for dependency management

## Tasks / Subtasks

- [x] Task 1: Create core directory structure (AC: #1)
  - [x] Create `clusters/infra/{flux,talos,apps}` directories
  - [x] Create `clusters/apps/{flux,talos,apps}` directories
  - [x] Create `infrastructure/base/repositories/{helm,oci}` directories
  - [x] Create `kubernetes/apps/` directory
  - [x] Create `kubernetes/components/` directory
  - [x] Create `bootstrap/{infra,apps}/helmfile.d` directories
  - [x] Create `bootstrap/{infra,apps}/templates` directories
  - [x] Create `.taskfiles/{bootstrap,talos,kubernetes,flux,volsync,dr,op}` directories
  - [x] Create `terraform/{cloudflare,modules}` directories
  - [x] Create `docs/{runbooks,adr,architecture}` directories
  - [x] Create `tests/{integration,smoke}` directories

- [x] Task 2: Create root Taskfile.yaml (AC: #2)
  - [x] Create `Taskfile.yaml` with includes for all `.taskfiles/` subdirectories
  - [x] Define standard task variables (CLUSTER, etc.)
  - [x] Include basic documentation in task descriptions

- [x] Task 3: Create .gitignore file (AC: #3)
  - [x] Add SOPS decrypted file patterns (`*.dec.yaml`, `*.dec.yml`)
  - [x] Add Talos generated files (`clusterconfig/*.yaml` except encrypted)
  - [x] Add IDE/editor files (`.idea/`, `.vscode/settings.json`, `*.swp`)
  - [x] Add OS files (`.DS_Store`, `Thumbs.db`)
  - [x] Add temporary and build files (`*.tmp`, `build/`, `dist/`)
  - [x] Add kubeconfig patterns
  - [x] Add terraform state files (`.terraform/`, `*.tfstate*`)

- [x] Task 4: Create renovate.json5 configuration (AC: #4)
  - [x] Extend `config:recommended` preset
  - [x] Configure custom managers for Flux HelmRelease resources
  - [x] Configure regexManagers for container images in HelmRelease values
  - [x] Set up grouping rules (patch weekly, minor monthly, major individual)
  - [x] Configure labels for PR categorization (`helm`, `docker`, `github-actions`)
  - [x] Set automerge for patch updates
  - [x] Add Flux-specific patterns for chart version detection

- [x] Task 5: Create essential placeholder files (AC: #1-4)
  - [x] Create `.sops.yaml` with AGE public key and path rules
  - [x] Create `README.md` with project overview
  - [x] Create `.github/CODEOWNERS` file
  - [x] Create `.github/dependabot.yaml` for GitHub Actions updates

### Review Follow-ups (AI)

- [x] [AI-Review][HIGH] Fix .gitignore excluding _bmad-output/ - story files should be tracked [.gitignore:3-4]
- [x] [AI-Review][MEDIUM] Add Renovate regex pattern for chartRef/OCIRepository style HelmReleases [renovate.json5:26]
- [x] [AI-Review][MEDIUM] Add .editorconfig for YAML consistency (2-space indent, UTF-8, LF)
- [x] [AI-Review][MEDIUM] Add validation tasks to root Taskfile (validate:kustomize, validate:yaml)
- [x] [AI-Review][MEDIUM] Add .yamllint.yaml configuration for YAML linting
- [x] [AI-Review][LOW] Fix README.md task examples to match actual Taskfile task names [README.md:66]
- [x] [AI-Review][LOW] Update dependabot.yaml commit prefix to use defined scope [.github/dependabot.yaml:12]
- [x] [AI-Review][LOW] Use story names instead of numbers in Taskfile TODO comments

### Review Follow-ups Round 2 (AI)

- [x] [AI-Review][HIGH] Add git precondition check to Taskfile ROOT_DIR variable [Taskfile.yaml:9-11]
- [x] [AI-Review][HIGH] Add missing prerequisites to README: helmfile, yamllint, kustomize [README.md:48-54]
- [x] [AI-Review][HIGH] Fix renovate OCIRepository regex to avoid cross-matching multiple resources [renovate.json5:73-83]
- [x] [AI-Review][HIGH] Disable or configure renovate kubernetes section to prevent duplicate PRs [renovate.json5:174-179]
- [x] [AI-Review][MEDIUM] Improve validate:kustomize task to report per-cluster status [Taskfile.yaml:59-69]
- [x] [AI-Review][MEDIUM] Add note to README that bootstrap tasks are placeholders [README.md:69-72]
- [x] [AI-Review][MEDIUM] Broaden renovate kubernetes package disable pattern [renovate.json5:166-170]
- [x] [AI-Review][LOW] Add .gitattributes for Git line ending enforcement
- [x] [AI-Review][LOW] Simplify redundant SOPS catch-all rule [.sops.yaml:33-35]

### Review Follow-ups Round 3 (AI)

- [x] [AI-Review][HIGH] Fix Renovate HelmRelease customManager regex - wrong structure and missing registryUrl [renovate.json5:27-28]
- [x] [AI-Review][MEDIUM] Show kustomize error output on validation failure instead of suppressing [Taskfile.yaml:73]
- [x] [AI-Review][MEDIUM] Remove yes/no from yamllint truthy allowed-values - Kubernetes uses only true/false [.yamllint.yaml:56]
- [x] [AI-Review][MEDIUM] Add resource-boundary anchoring to OCIRepository regex to prevent cross-matching [renovate.json5:79]
- [x] [AI-Review][MEDIUM] Add registryUrlTemplate to first HelmRelease matchString or remove broken matcher [renovate.json5:27]
- [x] [AI-Review][LOW] Verify op:push/pull story reference accuracy - currently says Story 1.5 [.taskfiles/op/Taskfile.yaml:10-11]
- [x] [AI-Review][LOW] Fix README bootstrap story reference - says Story 1.1 but should be Story 1.3 [README.md:72]
- [x] [AI-Review][LOW] Consider adding git preconditions to sub-Taskfiles for direct invocation [.taskfiles/*/Taskfile.yaml]
- [x] [AI-Review][LOW] Remove dead Taskfile.yml line from .gitattributes - project uses .yaml only [.gitattributes:19]

## Dev Notes

### Architecture Patterns & Constraints

**Repository Structure Pattern (from Architecture doc):**
```
k8s-ops/
├── clusters/
│   ├── infra/                    # Formerly home-ops
│   │   ├── apps/                 # Cluster-specific apps
│   │   ├── flux/                 # Flux configuration
│   │   └── talos/                # Talos machine configs
│   └── apps/                     # Formerly prod-ops
│       ├── apps/
│       ├── flux/
│       └── talos/
├── infrastructure/
│   └── base/                     # Shared infrastructure (CRDs, controllers)
│       └── repositories/         # Shared HelmRepository/OCIRepository
│           ├── helm/
│           └── oci/
├── kubernetes/
│   ├── apps/                     # SHARED apps (deployed to BOTH clusters)
│   └── components/               # SHARED Kustomize components
├── bootstrap/
│   ├── infra/                    # Infra cluster bootstrap
│   │   └── helmfile.d/
│   └── apps/                     # Apps cluster bootstrap
│       └── helmfile.d/
├── terraform/
├── .taskfiles/
├── tests/
└── docs/
```

**Critical Implementation Rules:**
1. Use `kustomization.yaml` (not `.yml`) for ALL Kustomize files
2. Use `.yaml` extension consistently for all YAML files
3. Follow kebab-case for all directory and file names
4. Maintain exact structure as specified in architecture document

**SOPS Configuration (from project-context.md):**
- AGE public key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
- Encrypted file patterns: `*.sops.yaml`, `*.sops.yml`

**Renovate Configuration Requirements:**
- Must detect Flux HelmRelease version fields
- Must handle container image references in Helm values
- Follow onedr0p/home-ops patterns for Renovate managers
- Group updates by type for manageable PR streams

### Project Structure Notes

**App Location Rules (CRITICAL - from Architecture doc):**
| Deployment Target | Directory |
|-------------------|-----------|
| Both clusters | `kubernetes/apps/{category}/{app}/` |
| Infra cluster only | `clusters/infra/apps/{category}/{app}/` |
| Apps cluster only | `clusters/apps/apps/{category}/{app}/` |

**Component Structure:**
```
kubernetes/components/
├── cnpg/           # CloudNative PostgreSQL
├── volsync/        # Backup configuration
│   ├── r2/         # Cloudflare R2 backups
│   └── nfs/        # NFS backups
├── gatus/          # Health checks
│   ├── external/
│   └── internal/
├── dragonfly/      # Redis alternative
└── secpol/         # Security policies
```

### References

- [Source: docs/project-context.md#Technology Stack & Versions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- [Source: _bmad-output/planning-artifacts/prd.md#Repository Structure Decision]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 0.1: Initialize Repository Structure]

### Technology Stack Reference

| Component | Version | Notes |
|-----------|---------|-------|
| Talos Linux | v1.12.0 | Immutable K8s OS |
| Cilium | v1.18.5 | eBPF CNI |
| Flux CD | v2.7.5 | GitOps |
| Renovate | Latest | Dependency management |
| SOPS | Latest | AGE encryption |
| Task (go-task) | Latest | Task automation |

### Taskfile Categories (from Architecture doc)

| Category | Purpose |
|----------|---------|
| `bootstrap:*` | Talos bootstrap, K8s apps bootstrap (cluster-aware) |
| `talos:*` | apply-node, upgrade-node, upgrade-k8s, reset-cluster, generate-iso |
| `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods, browse-pvc |
| `flux:*` | reconcile, suspend, resume, logs, events, diff |
| `volsync:*` | snapshot, restore, unlock, list, status |
| `dr:*` | verify-backups, test-cnpg-restore |
| `op:*` | push/pull kubeconfig to 1Password (multi-cluster) |

### Git Commit Message Format

```
<type>(<scope>): <description>

Types: feat, fix, refactor, chore, docs, ci
Scopes: infra, apps, flux, talos, bootstrap, renovate

Examples:
feat(bootstrap): initialize repository structure
chore(renovate): add Renovate configuration
docs(readme): add project overview
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation completed without errors

### Completion Notes List

- **Task 1:** Created complete directory structure matching architecture spec with `.gitkeep` placeholders for empty directories
- **Task 2:** Created root `Taskfile.yaml` with CLUSTER variable support, includes for all taskfile categories, and placeholder taskfiles for each category (bootstrap, talos, kubernetes, flux, volsync, dr, op)
- **Task 3:** Updated existing `.gitignore` with comprehensive patterns: SOPS decrypted files, Talos configs, IDE files, OS files, temp/build files, kubeconfigs, terraform state
- **Task 4:** Created `renovate.json5` with custom regex managers for Flux HelmRelease charts, container images, GitHub releases, and Talos images; configured patch/minor/major grouping and automerge for patches
- **Task 5:** Created `.sops.yaml` with AGE encryption rules, `README.md` with project overview, `.github/CODEOWNERS`, and `.github/dependabot.yaml`

**Review Follow-up Resolution (2025-12-31):**
- ✅ Resolved [HIGH]: Verified .gitignore does NOT exclude _bmad-output/ - pattern `_bmad/` only matches exact directory, not `_bmad-output/`
- ✅ Resolved [MEDIUM]: Added OCIRepository regex pattern to renovate.json5 for chartRef style HelmReleases
- ✅ Resolved [MEDIUM]: Created `.editorconfig` with 2-space YAML indent, UTF-8 encoding, LF line endings
- ✅ Resolved [MEDIUM]: Added `validate`, `validate:yaml`, and `validate:kustomize` tasks to root Taskfile.yaml
- ✅ Resolved [MEDIUM]: Created `.yamllint.yaml` with Kubernetes-friendly rules (150 char line limit, truthy values allowed)
- ✅ Resolved [LOW]: Updated README.md with new `task validate` example (existing task names were correct)
- ✅ Resolved [LOW]: Updated dependabot.yaml commit prefix from `ci(deps)` to `ci(github-actions)`
- ✅ Resolved [LOW]: Updated all Taskfile TODO comments to include story names (e.g., "Story 1.5: Create Operational Taskfiles for Talos")

**Review Follow-up Resolution Round 2 (2025-12-31):**
- ✅ Resolved [HIGH]: Added git precondition check to `default`, `init`, and `validate` tasks in Taskfile.yaml
- ✅ Resolved [HIGH]: Added helmfile, kustomize, and yamllint to README.md prerequisites section
- ✅ Resolved [HIGH]: Fixed OCIRepository regex to use line-limited matching (10 lines max between url and tag)
- ✅ Resolved [HIGH]: Disabled kubernetes manager in renovate.json5 to prevent duplicate PRs with customManagers
- ✅ Resolved [MEDIUM]: Improved validate:kustomize task with per-cluster status reporting (✓ OK / ✗ FAILED / ○ skipped)
- ✅ Resolved [MEDIUM]: Added note to README that bootstrap tasks are placeholders until corresponding stories are implemented
- ✅ Resolved [MEDIUM]: Broadened kubernetes package disable pattern to include `^kubernetes/` and `^registry\.k8s\.io/`
- ✅ Resolved [LOW]: Created `.gitattributes` with LF line ending enforcement for all text files
- ✅ Resolved [LOW]: Simplified `.sops.yaml` to single catch-all rule with documented expected file locations in comments

**Review Round 3 (2025-12-31):**
- Code review performed by Claude Opus 4.5
- Found 9 issues: 1 HIGH, 4 MEDIUM, 4 LOW
- Critical finding: Renovate HelmRelease regex has wrong structure - won't detect chart versions
- Action items added to story for next dev iteration
- Status set to in-progress pending fixes

**Review Round 3 Resolution (2025-12-31):**
- ✅ Resolved [HIGH]: Fixed Renovate HelmRelease regex - removed broken matchString, improved comment-based pattern with quote handling
- ✅ Resolved [MEDIUM]: Added kustomize error output display on validation failure - now captures and shows actual errors
- ✅ Resolved [MEDIUM]: Removed yes/no from yamllint truthy allowed-values - enforces Kubernetes standard true/false only
- ✅ Resolved [MEDIUM]: Added resource-boundary anchoring to OCIRepository regex - prevents cross-matching with negative lookahead
- ✅ Resolved [MEDIUM]: Removed broken HelmRelease matchString (same fix as HIGH priority item)
- ✅ Resolved [LOW]: Verified op:push/pull story references are accurate - Story 1.5 is correct
- ✅ Resolved [LOW]: Fixed README bootstrap story reference from 1.1 to 1.3
- ✅ Resolved [LOW]: Considered git preconditions for sub-Taskfiles - deferred until tasks implemented in future stories
- ✅ Resolved [LOW]: Removed dead Taskfile.yml line from .gitattributes - project uses .yaml only

**Review Round 4 (2025-12-31):**
- Code review performed by Claude Opus 4.5
- Found 7 issues: 0 HIGH, 3 MEDIUM, 4 LOW
- All issues fixed automatically

**Review Round 4 Resolution (2025-12-31):**
- ✅ Resolved [MEDIUM]: Added git init prerequisite note to README.md Quick Start section
- ✅ Resolved [MEDIUM]: Created .github/workflows/ci.yaml for automated PR validation (yamllint + kustomize)
- ✅ Resolved [MEDIUM]: Fixed renovate docker image regex to handle quoted repository values
- ✅ Resolved [LOW]: Noted CODEOWNERS @trosvald may differ from config user_name - verified as GitHub username
- ✅ Resolved [LOW]: Removed .yml pattern from .yamllint.yaml - project standardizes on .yaml
- ✅ Resolved [LOW]: Removed .yml pattern from .sops.yaml regex - project standardizes on .yaml
- ✅ Resolved [LOW]: Created .pre-commit-config.yaml with yamllint, check-yaml, and SOPS hooks
- ✅ Resolved [LOW]: Made .gitignore log patterns more specific (logs/*.log, debug.log, error.log)

### File List

**New Files:**
- `Taskfile.yaml`
- `.taskfiles/bootstrap/Taskfile.yaml`
- `.taskfiles/talos/Taskfile.yaml`
- `.taskfiles/kubernetes/Taskfile.yaml`
- `.taskfiles/flux/Taskfile.yaml`
- `.taskfiles/volsync/Taskfile.yaml`
- `.taskfiles/dr/Taskfile.yaml`
- `.taskfiles/op/Taskfile.yaml`
- `renovate.json5`
- `.sops.yaml`
- `README.md`
- `.github/CODEOWNERS`
- `.github/dependabot.yaml`
- `.editorconfig` (Review follow-up)
- `.yamllint.yaml` (Review follow-up)
- `clusters/infra/flux/.gitkeep`
- `clusters/infra/talos/.gitkeep`
- `clusters/infra/apps/.gitkeep`
- `clusters/apps/flux/.gitkeep`
- `clusters/apps/talos/.gitkeep`
- `clusters/apps/apps/.gitkeep`
- `infrastructure/base/repositories/helm/.gitkeep`
- `infrastructure/base/repositories/oci/.gitkeep`
- `kubernetes/apps/.gitkeep`
- `kubernetes/components/.gitkeep`
- `bootstrap/infra/helmfile.d/.gitkeep`
- `bootstrap/infra/templates/.gitkeep`
- `bootstrap/apps/helmfile.d/.gitkeep`
- `bootstrap/apps/templates/.gitkeep`
- `terraform/cloudflare/.gitkeep`
- `terraform/modules/.gitkeep`
- `docs/runbooks/.gitkeep`
- `docs/adr/.gitkeep`
- `docs/architecture/.gitkeep`
- `tests/integration/.gitkeep`
- `tests/smoke/.gitkeep`

**Modified Files (Review follow-up Round 1):**
- `renovate.json5` - Added OCIRepository regex pattern
- `Taskfile.yaml` - Added validate, validate:yaml, validate:kustomize tasks
- `README.md` - Added task validate example
- `.github/dependabot.yaml` - Updated commit prefix
- `.taskfiles/bootstrap/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/talos/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/kubernetes/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/flux/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/volsync/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/dr/Taskfile.yaml` - Added story names to TODO comments
- `.taskfiles/op/Taskfile.yaml` - Added story names to TODO comments

**New Files (Review follow-up Round 2):**
- `.gitattributes` - Git line ending enforcement

**Modified Files (Review follow-up Round 2):**
- `Taskfile.yaml` - Added git preconditions, improved validate:kustomize output
- `README.md` - Added helmfile/kustomize/yamllint prerequisites, bootstrap placeholder note
- `renovate.json5` - Fixed OCIRepository regex, disabled kubernetes manager, broadened disable patterns
- `.sops.yaml` - Simplified to single catch-all rule with documentation

**Modified Files (Review follow-up Round 3):**
- `renovate.json5` - Fixed HelmRelease customManager regex, added OCIRepository resource-boundary anchoring
- `Taskfile.yaml` - Added kustomize error output on validation failure
- `.yamllint.yaml` - Removed yes/no from truthy allowed-values
- `README.md` - Fixed bootstrap story reference from 1.1 to 1.3
- `.gitattributes` - Removed dead Taskfile.yml line

**New Files (Review follow-up Round 4):**
- `.github/workflows/ci.yaml` - CI workflow for yamllint and kustomize validation
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

**Modified Files (Review follow-up Round 4):**
- `README.md` - Added git init prerequisite note
- `renovate.json5` - Fixed docker image regex to handle quoted repository values
- `.yamllint.yaml` - Removed .yml pattern (project uses .yaml only)
- `.sops.yaml` - Removed .yml pattern from regex (project uses .yaml only)
- `.gitignore` - Made log file patterns more specific
- `.gitattributes` - Added .pre-commit-config.yaml

**Note:** All files above are new (untracked in git). `.gitignore` was created new, not modified from existing.

