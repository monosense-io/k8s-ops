# Story 0.5: Create GitHub Workflows for Validation

Status: ready-for-dev

## Story

As a **platform operator**,
I want **GitHub Actions workflows to validate changes before merge**,
So that **I can catch manifest errors and security issues in PRs**.

## Acceptance Criteria

1. **Given** the configured repository structure
   **When** GitHub workflows are created
   **Then** `.github/workflows/` contains:
   - `validate-kustomize.yaml` that runs `kustomize build` for affected paths
   - `kubeconform.yaml` for schema validation against CRDs
   - `gitleaks.yaml` for secret detection in code
   - `flux-diff.yaml` to show Flux resource changes in PRs

2. **And** workflows trigger on pull requests to main branch

3. **And** `CODEOWNERS` file exists requiring review for changes

4. **And** `dependabot.yaml` is configured for GitHub Actions updates

## Tasks / Subtasks

- [ ] Task 1: Create validate-kustomize workflow (AC: #1, #2)
  - [ ] Create `.github/workflows/validate-kustomize.yaml`
  - [ ] Configure trigger on `pull_request` to `main` branch
  - [ ] Add path filtering for `clusters/**`, `kubernetes/**`, `infrastructure/**`
  - [ ] Set up kustomize using `yokawasa/action-setup-kube-tools` action
  - [ ] Run `kustomize build` for `clusters/infra/flux` and `clusters/apps/flux`
  - [ ] Use `--enable-helm` flag for HelmRelease rendering
  - [ ] Fail on any build errors

- [ ] Task 2: Create kubeconform validation workflow (AC: #1, #2)
  - [ ] Create `.github/workflows/kubeconform.yaml`
  - [ ] Configure trigger on `pull_request` to `main` branch
  - [ ] Add path filtering for Kubernetes manifests
  - [ ] Download Flux CRD schemas from FluxCD releases
  - [ ] Download Kubernetes CRD schemas from Datree catalog
  - [ ] Configure kubeconform with `-strict`, `-ignore-missing-schemas`, `-verbose`, `-summary`
  - [ ] Set schema locations for Flux CRDs and default Kubernetes schemas
  - [ ] Pipe `kustomize build` output to kubeconform for both clusters
  - [ ] Report validation results in PR comments (optional)

- [ ] Task 3: Create gitleaks secret detection workflow (AC: #1, #2)
  - [ ] Create `.github/workflows/gitleaks.yaml`
  - [ ] Configure trigger on `pull_request`, `push`, and `workflow_dispatch`
  - [ ] Use `gitleaks/gitleaks-action@v2` action
  - [ ] Configure `fetch-depth: 0` for full git history
  - [ ] Pass `GITHUB_TOKEN` for PR commenting
  - [ ] Create `.gitleaks.toml` configuration at repository root if custom rules needed
  - [ ] Consider allowlist for known non-secrets (public keys, test data)

- [ ] Task 4: Create flux-diff workflow (AC: #1, #2)
  - [ ] Create `.github/workflows/flux-diff.yaml`
  - [ ] Configure trigger on `pull_request` to `main` branch
  - [ ] Add path filtering for Flux-managed paths
  - [ ] Set up Flux CLI using `fluxcd/flux2/action`
  - [ ] Run `flux diff kustomization` for changed paths (with local manifests)
  - [ ] Post diff results as PR comment using `peter-evans/create-or-update-comment`
  - [ ] Highlight HelmRelease value changes affecting rendered manifests
  - [ ] Use matrix strategy for both `infra` and `apps` clusters

- [ ] Task 5: Create CODEOWNERS file (AC: #3)
  - [ ] Create `.github/CODEOWNERS`
  - [ ] Assign `@monosense` as owner for all files (`*`)
  - [ ] Add specific ownership rules for critical paths:
    - `clusters/**` - cluster configurations
    - `infrastructure/**` - shared infrastructure
    - `bootstrap/**` - bootstrap configurations
    - `.sops.yaml` - encryption configuration
    - `.github/**` - workflow files

- [ ] Task 6: Create dependabot configuration (AC: #4)
  - [ ] Create `.github/dependabot.yaml`
  - [ ] Configure `github-actions` package ecosystem
  - [ ] Set update schedule (weekly recommended)
  - [ ] Target `/.github/workflows/` directory
  - [ ] Add labels for automated PR categorization
  - [ ] Configure commit message prefix

- [ ] Task 7: Create reusable validation script (optional enhancement)
  - [ ] Create `scripts/validate.sh` for local validation
  - [ ] Include kustomize build, kubeconform, and gitleaks checks
  - [ ] Make script runnable in CI and locally
  - [ ] Document usage in comments

- [ ] Task 8: Validate all workflows (AC: #1-4)
  - [ ] Verify YAML syntax for all workflow files
  - [ ] Test workflow triggers locally if possible (act)
  - [ ] Ensure all required secrets/permissions are documented
  - [ ] Verify path filters match repository structure

## Dev Notes

### Architecture Patterns & Constraints

**From Story 0.5 Requirements (epics.md):**
- Workflows must validate Flux manifests via GitHub Actions before merge
- Must trigger on pull requests to main branch
- CODEOWNERS file required for review enforcement
- dependabot.yaml for GitHub Actions updates

**Critical Implementation Rules:**

1. **File naming:** Use `.yaml` extension for all workflow files (consistent with repository standard)
2. **Workflow triggers:** Use `pull_request` for validation, not `pull_request_target` (security)
3. **Path filters:** Only run on relevant changes to minimize CI cost
4. **Schema validation:** Download Flux CRD schemas to validate custom resources
5. **Secret handling:** Never echo secrets; use masked environment variables

### Kubeconform Configuration (Best Practices)

**From FluxCD Example Repository:**
```bash
# Download Flux CRD schemas
mkdir -p /tmp/flux-crd-schemas
curl -sL https://github.com/fluxcd/flux2/releases/latest/download/crd-schemas.tar.gz | \
  tar zxf - -C /tmp/flux-crd-schemas

# Run kubeconform with recommended flags
kustomize build clusters/infra/flux --enable-helm | \
  kubeconform -strict -ignore-missing-schemas -verbose -summary \
  -schema-location default \
  -schema-location '/tmp/flux-crd-schemas/{{ .ResourceKind }}_{{ .ResourceAPIVersion }}.json'
```

**Kubeconform Flags:**
| Flag | Purpose |
|------|---------|
| `-strict` | Disallow additional properties not in schema (catches typos) |
| `-ignore-missing-schemas` | Don't fail on CRDs without schemas |
| `-verbose` | Show detailed validation results |
| `-summary` | Show summary statistics |
| `-schema-location default` | Use default Kubernetes schemas |

### Gitleaks Configuration

**Gitleaks-Action v2 (Official):**
```yaml
- uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Note on Licensing:**
- Personal repos: No license required
- Organization repos: Requires `GITLEAKS_LICENSE` secret from gitleaks.io
- Alternative: Use `DariuszPorowski/github-action-gitleaks@v2` (community, no license)

**Custom Configuration (.gitleaks.toml):**
```toml
# .gitleaks.toml - Optional custom rules
title = "k8s-ops gitleaks config"

# Allowlist for known non-secrets
[allowlist]
  description = "Allowlisted items"
  paths = [
    # Public AGE key in .sops.yaml (not a secret)
    '''\.sops\.yaml$''',
    # Test fixtures
    '''tests/.*''',
  ]
  regexes = [
    # AGE public keys start with age1 (not secret)
    '''age1[a-z0-9]{58}''',
  ]
```

### Flux Diff Workflow Pattern

**From FluxCD Documentation:**
```yaml
- name: Setup Flux CLI
  uses: fluxcd/flux2/action@main

- name: Diff Kustomization
  run: |
    flux diff kustomization cluster-apps \
      --path ./clusters/infra/flux \
      --local-sources HelmRepository/flux-system \
      || true  # Don't fail on diff (informational)
```

**PR Comment Integration:**
```yaml
- name: Post Diff Comment
  uses: peter-evans/create-or-update-comment@v4
  with:
    issue-number: ${{ github.event.pull_request.number }}
    body: |
      ## Flux Diff Results
      ```diff
      ${{ steps.diff.outputs.diff }}
      ```
```

### CODEOWNERS Pattern

**From GitHub Documentation:**
```
# .github/CODEOWNERS
# Default owner for everything
*                           @monosense

# Cluster-specific configurations
clusters/infra/**           @monosense
clusters/apps/**            @monosense

# Shared infrastructure
infrastructure/**           @monosense

# Bootstrap and sensitive configs
bootstrap/**                @monosense
.sops.yaml                  @monosense

# Workflow files (require review for CI changes)
.github/**                  @monosense
```

### Dependabot Configuration

**From GitHub Documentation:**
```yaml
# .github/dependabot.yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: monday
    commit-message:
      prefix: "ci(deps)"
    labels:
      - dependencies
      - github-actions
    open-pull-requests-limit: 10
```

### Workflow Trigger Patterns

**Path Filters for Efficiency:**
```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - 'clusters/**'
      - 'kubernetes/**'
      - 'infrastructure/**'
      - '.github/workflows/**'
```

**Excluding Documentation Changes:**
```yaml
paths-ignore:
  - 'docs/**'
  - '*.md'
  - 'LICENSE'
```

### Technology Stack Versions

| Tool | Recommended Version | Notes |
|------|---------------------|-------|
| kustomize | v5.x | Use action for consistent version |
| kubeconform | v0.6.x | Latest stable |
| gitleaks | v8.x | Via gitleaks-action@v2 |
| flux CLI | v2.7.5+ | Match cluster version |

### Project Structure Notes

**Files to Create:**
```
k8s-ops/
├── .github/
│   ├── CODEOWNERS
│   ├── dependabot.yaml
│   └── workflows/
│       ├── validate-kustomize.yaml
│       ├── kubeconform.yaml
│       ├── gitleaks.yaml
│       └── flux-diff.yaml
├── .gitleaks.toml                    # Optional custom rules
└── scripts/
    └── validate.sh                   # Optional local validation
```

### Sample Workflow: validate-kustomize.yaml

```yaml
name: Validate Kustomize

on:
  pull_request:
    branches: [main]
    paths:
      - 'clusters/**'
      - 'kubernetes/**'
      - 'infrastructure/**'

jobs:
  validate:
    name: Validate Kustomize Build
    runs-on: ubuntu-latest
    strategy:
      matrix:
        cluster: [infra, apps]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Kustomize
        uses: yokawasa/action-setup-kube-tools@v0.11.1
        with:
          kustomize: '5.4.3'

      - name: Validate ${{ matrix.cluster }} cluster
        run: |
          kustomize build clusters/${{ matrix.cluster }}/flux --enable-helm
```

### Sample Workflow: kubeconform.yaml

```yaml
name: Kubeconform

on:
  pull_request:
    branches: [main]
    paths:
      - 'clusters/**'
      - 'kubernetes/**'
      - 'infrastructure/**'

jobs:
  validate:
    name: Validate with Kubeconform
    runs-on: ubuntu-latest
    strategy:
      matrix:
        cluster: [infra, apps]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Tools
        uses: yokawasa/action-setup-kube-tools@v0.11.1
        with:
          kustomize: '5.4.3'
          kubeconform: '0.6.7'

      - name: Download Flux CRD Schemas
        run: |
          mkdir -p /tmp/flux-crd-schemas
          curl -sL https://github.com/fluxcd/flux2/releases/latest/download/crd-schemas.tar.gz | \
            tar zxf - -C /tmp/flux-crd-schemas

      - name: Validate ${{ matrix.cluster }} cluster
        run: |
          kustomize build clusters/${{ matrix.cluster }}/flux --enable-helm | \
            kubeconform -strict -ignore-missing-schemas -verbose -summary \
            -schema-location default \
            -schema-location '/tmp/flux-crd-schemas/{{ .ResourceKind }}_{{ .ResourceAPIVersion }}.json'
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 0.5: Create GitHub Workflows for Validation]
- [Source: docs/project-context.md#Development Workflow Rules]
- [Source: docs/project-context.md#PR Review Checklist]
- [FluxCD Validation Example](https://github.com/fluxcd/flux2-kustomize-helm-example)
- [Kubeconform Documentation](https://github.com/yannh/kubeconform)
- [Gitleaks Action](https://github.com/gitleaks/gitleaks-action)
- [Flux GitHub Action](https://fluxcd.io/flux/flux-gh-action/)
- [GitHub CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)

### Previous Story Intelligence

**From Story 0.1 - Initialize Repository Structure:**
- Repository structure established with `.github/` directory
- `CODEOWNERS` placeholder may already exist
- `dependabot.yaml` mentioned as deliverable

**From Story 0.2 - Create Shared Infrastructure Base:**
- Repository definitions in `infrastructure/base/repositories/`
- These will be validated by the workflows

**From Story 0.3 - Configure Cluster-Specific Flux Entry Points:**
- Cluster Flux directories at `clusters/infra/flux/` and `clusters/apps/flux/`
- These are the primary targets for kustomize validation

**From Story 0.4 - Configure SOPS/AGE Encryption:**
- SOPS configuration at `.sops.yaml`
- Encrypted files use `*.sops.yaml` pattern
- Gitleaks should allowlist AGE public key (not a secret)

**Key Learnings from Previous Stories:**
- All YAML files use `.yaml` extension
- Use relative paths from repository root
- Matrix strategy for multi-cluster validation
- Validate configurations before considering complete
- Reference exact tool versions for reproducibility

### Security Considerations

1. **Workflow Permissions:**
   - Use minimal permissions (`contents: read`)
   - Add `pull-requests: write` only for PR comments
   - Never use `permissions: write-all`

2. **Secrets in Workflows:**
   - Use `${{ secrets.GITHUB_TOKEN }}` (auto-provided)
   - Never expose secrets in logs
   - Gitleaks license only required for org repos

3. **Pull Request Security:**
   - Use `pull_request` not `pull_request_target` for untrusted code
   - Be cautious with `workflow_dispatch` permissions
   - Validate inputs in reusable workflows

### Git Commit Message Format

```
ci(workflows): add GitHub Actions for Flux manifest validation

- Add validate-kustomize workflow for kustomize build validation
- Add kubeconform workflow for schema validation with Flux CRDs
- Add gitleaks workflow for secret detection
- Add flux-diff workflow for PR change preview
- Create CODEOWNERS for review requirements
- Configure dependabot for GitHub Actions updates
```

### Common Gotchas

1. **Matrix strategy limitations** - GitHub Actions matrix has 256 job limit
2. **Path filters precision** - Use exact paths, not wildcards that match too much
3. **CRD schema availability** - Not all CRDs have public schemas; use `-ignore-missing-schemas`
4. **Flux diff requires cluster** - `flux diff kustomization` may need cluster context; use `--local-sources`
5. **Gitleaks false positives** - AGE public keys, test fixtures may trigger; use allowlist
6. **CODEOWNERS syntax** - Paths are relative to repo root; use leading `/` for root-relative
7. **dependabot schedule** - Too frequent updates create PR noise; weekly is recommended

### Workflow Dependencies

This story depends on:
- Story 0.1: Repository structure with `.github/` directory
- Story 0.3: Cluster Flux directories for validation targets

This story enables:
- Story 3.4: Implement PR Review and Branch Protection (uses these workflows as status checks)

### Estimated Validation Time

| Workflow | Estimated Duration |
|----------|-------------------|
| validate-kustomize | ~1-2 minutes per cluster |
| kubeconform | ~2-3 minutes per cluster |
| gitleaks | ~1-2 minutes |
| flux-diff | ~2-3 minutes per cluster |

**Total PR validation time: ~10-15 minutes** (parallel execution)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

