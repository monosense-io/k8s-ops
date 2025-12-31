# Story 5.2: Implement Branch-Based Staged Rollout

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want automated staged rollout with 24h soak time,
so that changes are validated on infra before affecting apps cluster.

## Acceptance Criteria

1. **AC1**: Infra cluster Flux references `main` branch:
   - `clusters/infra/flux/config/cluster-*.yaml` Kustomizations source from GitRepository with `ref.branch: main`
   - Verify with `flux get sources git k8s-ops -n flux-system -o yaml | grep branch`
   - Changes merged to main are reconciled immediately on infra cluster

2. **AC2**: Apps cluster Flux references `release` branch:
   - `clusters/apps/flux/config/cluster-*.yaml` Kustomizations source from GitRepository with `ref.branch: release`
   - GitRepository resource in apps cluster configured for `release` branch
   - Verify with `kubectl --context apps get gitrepository k8s-ops -n flux-system -o jsonpath='{.spec.ref.branch}'`
   - Expected output: `release`

3. **AC3**: `.github/workflows/release-promote.yaml` exists with:
   - Trigger on merge to main (push event)
   - 24-hour delay mechanism (environment wait timer or scheduled workflow)
   - Fast-forward `release` branch to `main`
   - Manual override via `workflow_dispatch`
   - Proper git configuration for github-actions bot

4. **AC4**: Merging to main updates infra cluster immediately:
   - Push to main triggers Flux reconciliation on infra cluster
   - `flux get kustomization -n flux-system` shows reconciled state within 5 minutes
   - Infra cluster reflects changes from main branch

5. **AC5**: Apps cluster updates 24 hours later automatically:
   - After 24-hour soak period, release branch is fast-forwarded to main
   - Apps cluster Flux detects branch update
   - Apps cluster reconciles changes from release branch
   - Verify with `flux get sources git k8s-ops -n flux-system --context apps`

6. **AC6**: `task flux:override-staged-rollout` forces immediate apps update:
   - Taskfile task exists in `.taskfiles/flux/Taskfile.yaml`
   - Task triggers `workflow_dispatch` event OR performs manual fast-forward
   - Apps cluster receives updates without waiting for soak period
   - Verification command succeeds: `task flux:override-staged-rollout`

7. **AC7**: Release branch exists and is properly initialized:
   - `release` branch exists in GitHub repository
   - Initial state matches `main` branch
   - Branch protection rules configured (optional but recommended)

8. **AC8**: GitHub Actions workflow has proper permissions:
   - Workflow has `contents: write` permission
   - GitHub token has push access to release branch
   - Bot commits use standard github-actions identity

## Tasks / Subtasks

- [ ] Task 1: Create and initialize release branch (AC: #7)
  - [ ] Subtask 1.1: Create `release` branch from current `main`
  - [ ] Subtask 1.2: Push release branch to origin
  - [ ] Subtask 1.3: Verify branch exists on GitHub

- [ ] Task 2: Update apps cluster Flux configuration (AC: #2)
  - [ ] Subtask 2.1: Modify `clusters/apps/flux/` GitRepository to reference `release` branch
  - [ ] Subtask 2.2: Verify all apps cluster Kustomizations reference the correct GitRepository
  - [ ] Subtask 2.3: Validate configuration with `kustomize build clusters/apps/flux --enable-helm`

- [ ] Task 3: Verify infra cluster uses main branch (AC: #1)
  - [ ] Subtask 3.1: Confirm `clusters/infra/flux/` GitRepository references `main` branch
  - [ ] Subtask 3.2: Document current configuration for reference

- [ ] Task 4: Create GitHub Actions release-promote workflow (AC: #3, #5, #8)
  - [ ] Subtask 4.1: Create `.github/workflows/release-promote.yaml` with push trigger
  - [ ] Subtask 4.2: Configure GitHub environment with 24-hour wait timer
  - [ ] Subtask 4.3: Implement fast-forward merge logic
  - [ ] Subtask 4.4: Add `workflow_dispatch` trigger for manual override
  - [ ] Subtask 4.5: Configure proper git identity for github-actions bot
  - [ ] Subtask 4.6: Add workflow permissions for contents:write

- [ ] Task 5: Create taskfile for manual override (AC: #6)
  - [ ] Subtask 5.1: Add `flux:override-staged-rollout` task to `.taskfiles/flux/Taskfile.yaml`
  - [ ] Subtask 5.2: Implement task to trigger workflow_dispatch OR manual fast-forward
  - [ ] Subtask 5.3: Add verification step after override

- [ ] Task 6: Test staged rollout end-to-end (AC: #4, #5)
  - [ ] Subtask 6.1: Make a test change on main branch
  - [ ] Subtask 6.2: Verify infra cluster receives change immediately
  - [ ] Subtask 6.3: Verify apps cluster does NOT receive change until release branch updates
  - [ ] Subtask 6.4: Test manual override workflow

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Implement the branch-based staged rollout pattern that ensures the infra cluster validates all changes for 24 hours before they are automatically promoted to the apps cluster. This provides a safety net for production workloads.

**Staged Rollout Pattern:**
```
Git Push → main branch → Infra Cluster (immediate)
                              ↓
                        24h soak period
                              ↓
           release branch → Apps Cluster (automatic)
```

**Why This Matters:**
- Infra cluster runs platform services that are more tolerant to issues
- Apps cluster runs business-critical production workloads (Odoo, n8n, ArsipQ)
- 24-hour delay gives operators time to detect and fix issues before affecting production
- Manual override provides escape hatch for urgent changes

### Previous Story Context (Story 5.1)

**Completed Infrastructure:**
- Apps cluster bootstrapped and operational
- Flux installed and connected to repository
- `clusters/apps/flux/` directory structure exists
- `cluster-vars.yaml` configured with `OBSERVABILITY_ROLE: spoke`

**Key Configuration from Story 5.1:**
- Apps cluster API endpoint: `https://10.25.13.10:6443`
- Cilium cluster.id=2, cluster.name=apps
- Apps cluster domain: `monosense.dev`

### Flux GitRepository Configuration

**Infra Cluster (main branch - immediate):**
```yaml
# clusters/infra/flux/config/flux-system.yaml or similar
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: k8s-ops
  namespace: flux-system
spec:
  interval: 1m
  ref:
    branch: main  # INFRA: Uses main for immediate updates
  url: ssh://git@github.com/monosense/k8s-ops.git
  secretRef:
    name: github-deploy-key
```

**Apps Cluster (release branch - 24h delayed):**
```yaml
# clusters/apps/flux/config/flux-system.yaml or similar
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: k8s-ops
  namespace: flux-system
spec:
  interval: 1m
  ref:
    branch: release  # APPS: Uses release for staged updates
  url: ssh://git@github.com/monosense/k8s-ops.git
  secretRef:
    name: github-deploy-key
```

### GitHub Actions Workflow Implementation

**Option 1: Environment Wait Timer (Recommended)**
Uses GitHub's built-in environment protection rules for the 24-hour delay:

```yaml
# .github/workflows/release-promote.yaml
name: Promote to Release Branch
on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      skip_wait:
        description: 'Skip 24-hour wait (emergency only)'
        required: false
        type: boolean
        default: false

permissions:
  contents: write

jobs:
  wait-for-soak:
    runs-on: ubuntu-latest
    environment:
      name: staged-rollout
      # Environment configured in GitHub with 1440 minute wait timer
    steps:
      - name: Soak period completed
        run: echo "24-hour soak period completed or skipped"

  promote-release:
    needs: wait-for-soak
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Fast-forward release to main
        run: |
          git fetch origin
          git checkout release || git checkout -b release origin/release

          # Check if fast-forward is possible
          if git merge-base --is-ancestor HEAD origin/main; then
            git merge --ff-only origin/main
            git push origin release
            echo "Successfully promoted main to release"
          else
            echo "::error::Cannot fast-forward release to main. Manual intervention required."
            exit 1
          fi
```

**Option 2: Scheduled Workflow**
Alternative using cron schedule for more predictable timing:

```yaml
name: Scheduled Release Promotion
on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  check-and-promote:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Check soak period
        id: check
        run: |
          # Get last main branch commit time
          LAST_COMMIT=$(git log -1 --format=%ct origin/main)
          CURRENT_TIME=$(date +%s)
          HOURS_SINCE=$((($CURRENT_TIME - $LAST_COMMIT) / 3600))

          if [ $HOURS_SINCE -ge 24 ]; then
            echo "ready=true" >> $GITHUB_OUTPUT
          else
            echo "ready=false" >> $GITHUB_OUTPUT
            echo "Only $HOURS_SINCE hours since last commit. Need 24 hours."
          fi

      - name: Promote if ready
        if: steps.check.outputs.ready == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git checkout release
          git merge --ff-only origin/main
          git push origin release
```

### GitHub Environment Setup

**Required Configuration:**
1. Go to Repository Settings → Environments
2. Create environment named `staged-rollout`
3. Add protection rule: **Wait timer** = `1440` minutes (24 hours)
4. Optionally add required reviewers for manual approval

### Taskfile Override Implementation

```yaml
# .taskfiles/flux/Taskfile.yaml (add to existing file)
version: '3'

tasks:
  override-staged-rollout:
    desc: Force immediate promotion of main to release branch (skip 24h soak)
    cmds:
      - |
        echo "Triggering immediate release promotion..."
        gh workflow run release-promote.yaml \
          --ref main \
          -f skip_wait=true
      - |
        echo "Waiting for workflow to start..."
        sleep 5
        gh run list --workflow=release-promote.yaml --limit 1
    preconditions:
      - sh: command -v gh
        msg: "GitHub CLI (gh) is required. Install with: brew install gh"
      - sh: gh auth status
        msg: "Please authenticate with GitHub CLI: gh auth login"
```

**Alternative: Direct Git Promotion Task:**
```yaml
  override-staged-rollout:
    desc: Force immediate promotion of main to release branch
    cmds:
      - git fetch origin
      - git checkout release
      - git merge --ff-only origin/main
      - git push origin release
      - echo "Release branch updated. Apps cluster will reconcile shortly."
      - flux reconcile source git k8s-ops -n flux-system --context apps
```

### Project Structure Notes

**Files to Create/Modify:**

| File | Action | Purpose |
|------|--------|---------|
| `.github/workflows/release-promote.yaml` | Create | Automated staged rollout workflow |
| `.github/environments/staged-rollout` | Configure | 24-hour wait timer (via GitHub UI) |
| `clusters/apps/flux/config/flux-system.yaml` | Modify | Change branch reference to `release` |
| `.taskfiles/flux/Taskfile.yaml` | Modify | Add override task |

**Directory Structure:**
```
.github/
├── workflows/
│   ├── release-promote.yaml    # NEW: Staged rollout workflow
│   ├── validate-kustomize.yaml # Existing
│   ├── kubeconform.yaml        # Existing
│   └── gitleaks.yaml           # Existing
clusters/
├── infra/
│   └── flux/
│       └── config/             # Uses main branch (no change)
└── apps/
    └── flux/
        └── config/             # Change to release branch
.taskfiles/
└── flux/
    └── Taskfile.yaml           # Add override task
```

### Critical Technical Details

**Git Fast-Forward Requirements:**
- Release branch MUST be behind or equal to main
- If release has diverged, manual resolution required
- Fast-forward prevents merge commits, keeping linear history

**Branch Protection Considerations:**
- Release branch should allow GitHub Actions to push
- Consider requiring status checks before promotion
- Protect main branch with PR reviews (existing)

**Flux Reconciliation Timing:**
- GitRepository interval: 1 minute (default)
- Infra: Changes visible within 1-5 minutes of push to main
- Apps: Changes visible within 1-5 minutes of release branch update

### Verification Commands

```bash
# Verify branch configuration on apps cluster
kubectl --context apps get gitrepository k8s-ops -n flux-system \
  -o jsonpath='{.spec.ref.branch}'
# Expected: release

# Verify branch configuration on infra cluster
kubectl --context infra get gitrepository k8s-ops -n flux-system \
  -o jsonpath='{.spec.ref.branch}'
# Expected: main

# Check current git revision on each cluster
flux get sources git k8s-ops -n flux-system --context infra
flux get sources git k8s-ops -n flux-system --context apps

# Verify workflow exists
gh workflow list | grep release-promote

# Test manual override
task flux:override-staged-rollout

# Force reconciliation after override
flux reconcile source git k8s-ops -n flux-system --context apps
```

### Anti-Patterns to Avoid

1. **DO NOT** configure apps cluster to use `main` branch - staged rollout is critical for production safety
2. **DO NOT** use merge commits for release promotion - fast-forward only maintains linear history
3. **DO NOT** manually push to release branch - all changes must flow through main first
4. **DO NOT** skip soak period routinely - only use override for genuine emergencies
5. **DO NOT** configure different content between branches - release must be fast-forward from main
6. **DO NOT** use rebase or force push on release branch - can break Flux tracking

### Edge Cases to Handle

**Scenario: Fast-forward not possible**
- Cause: Someone pushed directly to release branch
- Solution: Reset release to main, or create merge commit (not recommended)
- Prevention: Protect release branch from direct pushes

**Scenario: Urgent security fix needed**
- Use `task flux:override-staged-rollout` for immediate promotion
- Or use `workflow_dispatch` with `skip_wait=true`
- Document reason for audit trail

**Scenario: Apps cluster not updating after promotion**
- Check GitRepository source status: `flux get sources git -n flux-system --context apps`
- Force reconciliation: `flux reconcile source git k8s-ops -n flux-system --context apps`
- Verify release branch has expected commit

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 3: Staged Rollout Automation] - Branch-based staging pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Staged Rollout Pattern] - 24h soak requirement
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cluster Patterns] - Cluster branch mapping
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.2] - Original acceptance criteria
- [Source: docs/project-context.md#Staged Rollout Pattern] - Branch configuration
- [Source: 5-1-bootstrap-apps-cluster.md] - Previous story context

### External Documentation

- [Flux CD GitRepository](https://fluxcd.io/flux/components/source/gitrepositories/)
- [GitHub Actions Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Actions Wait Timer](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments)
- [GitHub CLI Workflow Commands](https://cli.github.com/manual/gh_workflow)
- [Git Fast-Forward Merge](https://git-scm.com/docs/git-merge#_fast_forward_merge)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
