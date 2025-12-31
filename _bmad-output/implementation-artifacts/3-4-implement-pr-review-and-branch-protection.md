# Story 3.4: Implement PR Review and Branch Protection

Status: ready-for-dev

## Story

As a **platform operator**,
I want **branch protection requiring PR reviews and passing CI**,
So that **changes are validated before affecting clusters, ensuring stability and preventing misconfigurations from reaching production**.

## Acceptance Criteria

1. **Given** GitHub workflows from Story 0.5
   **When** branch protection is configured
   **Then** `main` branch has protection rules:
   - Require PR reviews (minimum 1 approval)
   - Require status checks to pass (validate-kustomize, kubeconform, gitleaks)
   - Require branches to be up to date
   - Dismiss stale reviews when new commits pushed

2. **And** `CODEOWNERS` assigns reviewers for critical paths

3. **And** direct pushes to main are blocked

4. **And** PRs cannot merge until all checks pass

5. **And** `.github/workflows/flux-hr-sync.yaml` reports HelmRelease sync status

## Tasks / Subtasks

- [ ] Task 1: Create CODEOWNERS File (AC: #2)
  - [ ] Create `.github/CODEOWNERS` file
  - [ ] Define owners for critical paths (`/clusters/`, `/infrastructure/`, `/kubernetes/`)
  - [ ] Define owners for bootstrap configurations (`/bootstrap/`)
  - [ ] Define owners for GitHub workflows (`.github/`)
  - [ ] Assign monosense as default owner for all paths

- [ ] Task 2: Create Flux Diff Workflow (AC: #4, #5)
  - [ ] Create `.github/workflows/flux-diff.yaml`
  - [ ] Configure trigger on pull_request to main branch
  - [ ] Install Flux CLI using `fluxcd/flux2/action`
  - [ ] Run `flux diff kustomization` for affected paths
  - [ ] Post diff output as PR comment for reviewability
  - [ ] Use permissions: pull-requests: write for commenting

- [ ] Task 3: Create HelmRelease Sync Status Workflow (AC: #5)
  - [ ] Create `.github/workflows/flux-hr-sync.yaml`
  - [ ] Configure trigger on push to main branch
  - [ ] Connect to cluster securely (via kubeconfig secret or Tailscale)
  - [ ] Run `flux get hr -A` to check HelmRelease status
  - [ ] Report sync failures via GitHub commit status or issue
  - [ ] Add workflow_dispatch for manual triggering

- [ ] Task 4: Configure Branch Protection via GitHub UI or API (AC: #1, #3, #4)
  - [ ] Document branch protection configuration steps
  - [ ] Require pull request before merging
  - [ ] Require 1 approval (from CODEOWNERS if available)
  - [ ] Dismiss stale pull request approvals when new commits are pushed
  - [ ] Require status checks to pass before merging:
    - `validate-kustomize`
    - `kubeconform` (if exists from Story 0.5)
    - `gitleaks` (if exists from Story 0.5)
  - [ ] Require branches to be up to date before merging
  - [ ] Block direct pushes (include administrators)
  - [ ] Optionally: Consider GitHub Rulesets as modern alternative

- [ ] Task 5: Update Existing Validation Workflows (AC: #4)
  - [ ] Review `.github/workflows/validate-kustomize.yaml` (from Story 0.5)
  - [ ] Ensure workflow name matches branch protection status check
  - [ ] Add concurrency group to cancel outdated runs
  - [ ] Ensure paths trigger covers all Kubernetes manifests

- [ ] Task 6: Create PR Template with Checklist (AC: #1)
  - [ ] Create `.github/pull_request_template.md`
  - [ ] Include checklist items from project-context.md PR Review Checklist
  - [ ] Add sections for Description, Type of Change, Testing
  - [ ] Include reminder about branch protection requirements

- [ ] Task 7: Verify Branch Protection Configuration (AC: #1, #3, #4)
  - [ ] Test that direct push to main is blocked
  - [ ] Test that PR without approval cannot merge
  - [ ] Test that PR with failing status checks cannot merge
  - [ ] Test that stale reviews are dismissed on new commits
  - [ ] Verify CODEOWNERS auto-requests reviews

- [ ] Task 8: Document Branch Protection in Runbook
  - [ ] Add branch protection section to `docs/runbooks/` or `README.md`
  - [ ] Document how to request bypass (emergency procedures)
  - [ ] Document required status checks and their purpose
  - [ ] Update project-context.md if needed

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **FRs Covered (Epic 3: GitOps Operations):**
   - FR8: Operator can validate Flux manifests via GitHub Actions before merge
   - FR11: Operator can enforce PR reviews before changes apply to clusters

2. **Staged Rollout Integration:**
   - Changes merged to `main` → infra cluster (immediate reconciliation)
   - GitHub Action fast-forwards `release` branch after 24h → apps cluster
   - Branch protection ensures quality before changes reach infra cluster

3. **Git Commit Message Format:**
   ```
   <type>(<scope>): <description>

   Types: feat, fix, refactor, chore, docs, ci
   Scopes: infra, apps, flux, talos, bootstrap, renovate
   ```

4. **CI Workflow Requirements (from architecture.md):**
   ```yaml
   # .github/workflows/validate.yaml
   - name: Validate Kustomize
     run: |
       for cluster in infra apps; do
         kustomize build clusters/${cluster}/flux --enable-helm
       done

   - name: Lint HelmReleases
     run: |
       # Check all HelmReleases have remediation configured
       grep -r "strategy: rollback" kubernetes/apps/
   ```

### Project Context Rules (Critical)

**From project-context.md:**

1. **PR Review Checklist (to be enforced):**
   - [ ] `kustomize build --enable-helm` passes for affected paths
   - [ ] HelmRelease has install + upgrade remediation configured
   - [ ] Secrets use ExternalSecret (no hardcoded values)
   - [ ] Network policies present for Tier 2 apps
   - [ ] Dependencies declared in ks.yaml
   - [ ] HTTPRoute uses correct Gateway reference
   - [ ] Variable substitution uses `${VAR}` syntax
   - [ ] CNPG apps include healthCheckExprs
   - [ ] Image tags pinned with `@sha256:` digest

2. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`)
   - Workflows in `.github/workflows/`

3. **Staged Rollout Pattern:**
   | Cluster | Branch | Reconciliation |
   |---------|--------|----------------|
   | infra | `main` | Immediate |
   | apps | `release` | 24h delayed (auto fast-forward) |

### GitHub Branch Protection Best Practices (Web Research)

**From GitHub Documentation:**

1. **Rulesets vs Branch Protection Rules:**
   - GitHub Rulesets are the modern, recommended approach
   - Multiple rulesets can apply simultaneously (most restrictive wins)
   - Better for organization-wide standards
   - Consider using Rulesets for future-proofing

2. **Rollout Strategy for Rulesets:**
   - Test phase: Start in "evaluate" mode to confirm functionality
   - Pilot phase: Roll out to specific repos
   - Expand phase: Expand to all repos, review rule insights
   - Enforce phase: Move to active mode

3. **Bypass Management:**
   - Grant bypass only to roles/teams with clear break-glass procedures
   - Monitor bypass exceptions via audit log
   - Avoid "impossible merge" situations (e.g., when required workflow unavailable)

4. **Key Protection Settings:**
   - Require pull request reviews before merging
   - Dismiss stale pull request approvals when new commits are pushed
   - Require review from Code Owners
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Require signed commits (optional, consider for high-security)

### FluxCD GitHub Actions Patterns (Web Research)

**From FluxCD Documentation:**

1. **Flux GitHub Action:**
   - Use `fluxcd/flux2/action` for installing Flux CLI in CI
   - Compatible with Linux, macOS, and Windows runners
   - Can automate Flux upgrades via Pull Requests

2. **Flux Diff for PR Validation:**
   - `flux diff kustomization --path X` shows what would change
   - Post diff as PR comment for reviewability
   - Useful for catching errors early and communicating PR impact
   - Consider read-only service account for cluster access

3. **Static Validation:**
   - Use flux2-kustomize-helm-example scripts for static validation
   - Some validation requires cluster access (CRDs, admission controllers)

### CODEOWNERS Configuration

**Recommended CODEOWNERS:**

```
# Default owner for all files
* @monosense

# Critical infrastructure paths
/clusters/                @monosense
/infrastructure/          @monosense
/kubernetes/              @monosense
/bootstrap/               @monosense

# GitHub configuration
/.github/                 @monosense

# Sensitive files
*.sops.yaml               @monosense
*.sops.yml                @monosense
talconfig.yaml            @monosense
```

### Workflow Templates

**flux-diff.yaml:**

```yaml
---
name: Flux Diff

on:
  pull_request:
    branches: [main]
    paths:
      - 'clusters/**'
      - 'kubernetes/**'
      - 'infrastructure/**'

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  flux-diff:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main

      - name: Diff Kustomizations
        id: diff
        run: |
          mkdir -p /tmp/diff
          for cluster in infra apps; do
            echo "## Cluster: ${cluster}" >> /tmp/diff/output.md
            echo '```diff' >> /tmp/diff/output.md
            flux diff kustomization cluster-apps \
              --path ./clusters/${cluster}/flux \
              --local-only 2>&1 >> /tmp/diff/output.md || true
            echo '```' >> /tmp/diff/output.md
          done

      - name: Post Diff as PR Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const diff = fs.readFileSync('/tmp/diff/output.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Flux Diff Preview\n\n' + diff
            });
```

**flux-hr-sync.yaml:**

```yaml
---
name: Flux HelmRelease Sync Status

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  statuses: write

jobs:
  check-sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main

      - name: Check HelmRelease Status
        id: status
        env:
          KUBECONFIG_DATA: ${{ secrets.KUBECONFIG_INFRA }}
        run: |
          echo "$KUBECONFIG_DATA" > /tmp/kubeconfig
          export KUBECONFIG=/tmp/kubeconfig

          echo "## HelmRelease Status - Infra Cluster" >> status.md
          flux get hr -A --context=infra >> status.md 2>&1 || echo "Could not connect to infra cluster" >> status.md

          # Check for failures
          if flux get hr -A --context=infra | grep -q "False"; then
            echo "hr_status=failed" >> $GITHUB_OUTPUT
          else
            echo "hr_status=success" >> $GITHUB_OUTPUT
          fi

      - name: Create Commit Status
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: '${{ steps.status.outputs.hr_status }}' === 'success' ? 'success' : 'failure',
              context: 'flux-hr-sync',
              description: 'HelmRelease sync status'
            });
```

**pull_request_template.md:**

```markdown
## Description

<!-- Describe your changes -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Infrastructure change
- [ ] Helm chart update
- [ ] Renovate dependency update

## Clusters Affected

- [ ] Infra cluster
- [ ] Apps cluster
- [ ] Both clusters

## PR Review Checklist

- [ ] `kustomize build --enable-helm` passes for affected paths
- [ ] HelmRelease has install + upgrade remediation configured
- [ ] Secrets use ExternalSecret (no hardcoded values)
- [ ] Network policies present for Tier 2 apps
- [ ] Dependencies declared in ks.yaml
- [ ] HTTPRoute uses correct Gateway reference
- [ ] Variable substitution uses `${VAR}` syntax
- [ ] CNPG apps include healthCheckExprs
- [ ] Image tags pinned with `@sha256:` digest

## Testing

<!-- How did you test this change? -->

## Additional Notes

<!-- Any additional information -->
```

### Previous Story Intelligence

**From Story 3.1 (Flux Operational Taskfiles):**
- Flux CLI usage patterns established (`flux reconcile`, `flux suspend`, etc.)
- Multi-cluster context handling with CLUSTER variable
- Preconditions for validation
- Detailed summaries with examples

**From Story 3.2 (Renovate Configuration):**
- `renovate.json5` configuration at repository root
- File matching patterns for Kubernetes manifests
- Automerge strategy (patch updates only, not for apps cluster)
- Semantic commit messages (`chore(renovate): <description>`)

**From Story 3.3 (Reusable Kustomize Components):**
- Component structure in `kubernetes/components/`
- Kustomize Component API (`v1alpha1`)
- Validation with `kustomize build`
- ExternalSecret uses `external-secrets.io/v1` API version

**Key Learnings Applied:**
- Use `.yaml` extension consistently
- Follow kebab-case naming conventions
- Include comprehensive examples in documentation
- Validate with `kustomize build` before committing
- Workflows should use concurrency groups to cancel outdated runs
- Permissions should be minimally scoped

### Directory Structure Impact

```
k8s-ops/
├── .github/
│   ├── CODEOWNERS                          # NEW: Code ownership
│   ├── pull_request_template.md            # NEW: PR template
│   ├── dependabot.yaml                     # Existing from Story 0.5
│   └── workflows/
│       ├── validate-kustomize.yaml         # Existing from Story 0.5
│       ├── kubeconform.yaml                # Existing from Story 0.5
│       ├── gitleaks.yaml                   # Existing from Story 0.5
│       ├── flux-diff.yaml                  # NEW: Flux diff for PRs
│       ├── flux-hr-sync.yaml               # NEW: HelmRelease sync status
│       └── release-promote.yaml            # Existing/planned for staged rollout
```

### Branch Protection Configuration Steps

**Via GitHub UI:**

1. Go to Settings → Branches → Branch protection rules
2. Click "Add rule"
3. Branch name pattern: `main`
4. Enable:
   - ✅ Require a pull request before merging
     - ✅ Require approvals (1)
     - ✅ Dismiss stale pull request approvals when new commits are pushed
     - ✅ Require review from Code Owners
   - ✅ Require status checks to pass before merging
     - ✅ Require branches to be up to date before merging
     - Add status checks: `validate-kustomize`, `kubeconform`, `gitleaks`
   - ✅ Do not allow bypassing the above settings
5. Save changes

**Via GitHub CLI (gh):**

```bash
gh api -X PUT /repos/monosense/k8s-ops/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["validate-kustomize","kubeconform","gitleaks"]}' \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  -f enforce_admins=true \
  -f restrictions=null
```

### Verification Commands

```bash
# Verify CODEOWNERS syntax
cat .github/CODEOWNERS

# Test workflow locally with act (optional)
act -j validate-kustomize pull_request

# Check branch protection via API
gh api /repos/monosense/k8s-ops/branches/main/protection

# Test that direct push is blocked (should fail)
git push origin main

# Create test PR and verify checks run
gh pr create --title "test: verify branch protection" --body "Test PR"
```

### Critical Implementation Rules

1. **CODEOWNERS Syntax:**
   - Lines starting with `#` are comments
   - Patterns follow `.gitignore` syntax
   - Last matching pattern takes precedence
   - Use `@username` or `@org/team-name` format

2. **Workflow Permissions:**
   - Use minimal permissions
   - `contents: read` for checkout
   - `pull-requests: write` for commenting on PRs
   - `statuses: write` for creating commit statuses

3. **Status Check Names:**
   - Must match exactly what appears in GitHub Checks
   - Usually the job name or workflow name
   - Case-sensitive

4. **Concurrency Groups:**
   - Use to cancel outdated workflow runs
   - Include PR number for PR-triggered workflows
   - Prevents resource waste on rapid pushes

5. **Secrets for Cluster Access:**
   - Store kubeconfig as GitHub secret
   - Consider using Tailscale for secure cluster access
   - Limit cluster access scope (read-only for status checks)

### Project Structure Notes

- **CODEOWNERS:** `.github/CODEOWNERS`
- **PR Template:** `.github/pull_request_template.md`
- **Workflows:** `.github/workflows/`
- **Documentation:** `docs/runbooks/` or project README

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4: Implement PR Review and Branch Protection]
- [Source: _bmad-output/planning-artifacts/architecture.md#CI/CD Workflows]
- [Source: docs/project-context.md#PR Review Checklist]
- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [GitHub Rulesets Best Practices](https://wellarchitected.github.com/library/governance/recommendations/managing-repositories-at-scale/rulesets-best-practices/)
- [About Rulesets - GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [FluxCD GitHub Action](https://fluxcd.io/flux/flux-gh-action/)
- [FluxCD Flux Diff Discussion](https://github.com/fluxcd/flux2/discussions/820)
- [GitHub CODEOWNERS Syntax](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

### Validation Checklist

Before marking complete, verify:
- [ ] `.github/CODEOWNERS` file created with appropriate owners
- [ ] `.github/pull_request_template.md` created with PR checklist
- [ ] `.github/workflows/flux-diff.yaml` created and functional
- [ ] `.github/workflows/flux-hr-sync.yaml` created and functional
- [ ] Branch protection enabled on `main` branch
- [ ] Require 1 approval before merging
- [ ] Require status checks to pass (validate-kustomize, kubeconform, gitleaks)
- [ ] Dismiss stale reviews when new commits pushed
- [ ] Direct push to main is blocked
- [ ] CODEOWNERS auto-requests review from monosense
- [ ] Flux diff posts comment on PRs
- [ ] Branch protection documented in runbook

### Git Commit Message Format

```
feat(ci): implement PR review and branch protection

- Add .github/CODEOWNERS for code ownership
- Add pull_request_template.md with review checklist
- Add flux-diff.yaml workflow for PR diff preview
- Add flux-hr-sync.yaml for HelmRelease sync status
- Configure main branch protection rules
- FR8: Validate Flux manifests via GitHub Actions
- FR11: Enforce PR reviews before changes apply
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
