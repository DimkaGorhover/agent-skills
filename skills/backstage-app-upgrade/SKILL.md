---
name: backstage-app-upgrade
description: Use when upgrading a Backstage developer portal to a newer version. Triggers on version bumps, breaking change migration, Yarn patch management for community plugins, and post-upgrade verification. Covers the full upgrade lifecycle from planning through manual QA.
---

# Backstage App Upgrade Skill

Comprehensive, battle-tested procedure for upgrading a Backstage monorepo to a newer release. Distilled from real upgrades (1.47→1.48, 1.48→1.49) with Yarn 4 workspaces, community plugins, and Yarn patches.

## When to Use

- User says "upgrade backstage" / "bump backstage version"
- A new Backstage release is available and needs adoption
- Breaking changes need migration after a version bump
- Yarn patches need regeneration after dependency version changes
- Community plugins need compatibility checks after a core bump

______________________________________________________________________

## Pre-Upgrade Checklist

Before touching any dependency:

```bash
# 1. Find the target version
# Check https://backstage.io/docs/releases or GitHub releases
cat backstage.json  # current version

# 2. Create an upgrade branch
git checkout -b upgrade/backstage-<target-version>
git tag snapshot/pre-backstage-<target-version>  # rollback point

# 3. Capture baseline — ALL must pass before you change anything
yarn install --immutable
yarn tsc
yarn lint:all
yarn test
yarn build:all
```

Document any pre-existing failures BEFORE the upgrade starts. This prevents confusing pre-existing issues with upgrade regressions.

______________________________________________________________________

## Phase 1: Core Backstage Bump

### The Official Command

```bash
yarn backstage-cli versions:bump --release <target-version>
```

### What It Does

- Updates ALL `@backstage/*` package versions across every `package.json`
- Updates `backstage.json` to the new version
- Runs `yarn install` automatically

### What It Does NOT Do

- Does NOT bump community plugins (`@backstage-community/*`, `@immobiliarelabs/*`, `@dweber019/*`)
- Does NOT fix source-level breaking changes (removed props, renamed APIs)
- Does NOT update `resolutions` entries or Yarn patch references
- Does NOT add newly required dependencies (like `@backstage/cli-defaults`)

### Post-Bump Immediate Actions

```bash
# Verify the bump worked
cat backstage.json  # should show target version

# Check for newly required root devDependencies
# Example: @backstage/cli-defaults was required starting in 1.49.x
yarn add -D @backstage/cli-defaults  # if not already present

# Resolve the lockfile
yarn install
```

### Commit Strategy

```
chore(backstage): bump core packages to <target-version>
```

______________________________________________________________________

## Phase 2: Breaking Change Migration

### How to Find Breaking Changes

1. **Upgrade Helper**: https://backstage.github.io/upgrade-helper/?yarnPlugin=0 (set `yarnPlugin=0` if not using the Backstage Yarn plugin)
1. **Release notes**: https://backstage.io/docs/releases/v<major>.<minor>.0
1. **create-app CHANGELOG**: https://github.com/backstage/backstage/blob/master/packages/create-app/CHANGELOG.md
1. Check every package that jumped a **major** version in the diff

### Common Breaking Change Patterns

| Pattern                 | Example                                        | Migration                          |
| ----------------------- | ---------------------------------------------- | ---------------------------------- |
| Removed prop            | `variant="gridItem"` removed from entity cards | Delete the prop from all callsites |
| Renamed export          | `ScaffolderApi` → new API                      | Update imports                     |
| New required dependency | `@backstage/cli-defaults`                      | Add to devDependencies             |
| Changed type signature  | `AlertApi` → `ToastApi`                        | Update usage                       |
| Removed component       | Legacy layout wrappers                         | Use new equivalents                |

### TDD Approach for Breaking Changes

```bash
# Before fix: count occurrences of the removed pattern
grep -r 'variant="gridItem"' packages/app/src/ | wc -l  # e.g., 21

# Apply fix (remove the pattern)

# After fix: verify zero occurrences
grep -r 'variant="gridItem"' packages/app/src/ | wc -l  # must be 0

# Verify compilation
yarn tsc
yarn workspace app test
```

### Commit Strategy

```
fix(app): remove deprecated <pattern> for backstage <version>
```

______________________________________________________________________

## Phase 3: Community Plugin Compatibility

### Key Principle

`backstage-cli versions:bump` does NOT touch community plugins. You must check and update them manually.

### Workflow Per Plugin Family

For each community plugin family:

1. **Check latest version on npm**:

   ```bash
   npm view @backstage-community/plugin-<name> version
   ```

1. **Check peer dependency compatibility**: Does the latest version require `@backstage/core-components@^X.Y.Z` that matches your upgraded Backstage?

1. **Upgrade if compatible**:

   ```bash
   yarn upgrade @backstage-community/plugin-<name>
   ```

1. **Verify after each family**:

   ```bash
   yarn tsc
   yarn workspace app test
   yarn workspace backend build
   ```

1. If a plugin has NO compatible release yet: keep it pinned and verify it still works against the upgraded core at runtime.

### Common Community Plugin Families

| Family        | Packages                                                                                | Notes                                  |
| ------------- | --------------------------------------------------------------------------------------- | -------------------------------------- |
| ADR           | plugin-adr, plugin-adr-common, plugin-adr-backend, search-backend-module-adr            | Often has Yarn patches — see Phase 4   |
| Announcements | plugin-announcements, plugin-announcements-backend, search-backend-module-announcements | Usually straightforward                |
| GitLab        | @immobiliarelabs/backstage-plugin-gitlab, gitlab-backend                                | Infrequent releases, may have patches  |
| End-of-Life   | @dweber019/backstage-plugin-endoflife, endoflife-backend                                | Small plugin, watch for peer dep drift |

### Commit Strategy

```
chore(plugins): update <family> packages
```

______________________________________________________________________

## Phase 4: Yarn Patch Management

This is the HIGHEST RISK area of any Backstage upgrade. Yarn patches are version-pinned and WILL break when the patched package version changes.

### How Yarn Patches Work

Patches are stored in `.yarn/patches/` with version-specific filenames:

```
.yarn/patches/@backstage-community-plugin-adr-backend-npm-0.19.1-f7474efaad.patch
```

They're referenced in `package.json` via `resolutions`:

```json
"resolutions": {
  "@backstage-community/plugin-adr-backend@npm:0.19.1": "patch:@backstage-community/plugin-adr-backend@npm%3A0.19.1#~/.yarn/patches/@backstage-community-plugin-adr-backend-npm-0.19.1-f7474efaad.patch"
}
```

### Decision Gate for Each Patch

When a patched package has a new version available:

```
┌─ Did the package version change?
│
├─ NO → Keep patch as-is. Done.
│
└─ YES → Check upstream:
    │
    ├─ Fix merged upstream? → Remove patch file + resolution entry
    │
    └─ Fix NOT merged? → Regenerate patch for new version
```

### Regenerating a Patch

```bash
# 1. Create a temporary patching workspace
cd /tmp && mkdir patch-work && cd patch-work

# 2. Initialize a temporary yarn project
yarn init -2
yarn add <package>@<new-version>

# 3. Make a copy of the original dist file
cp node_modules/<package>/dist/<file>.cjs.js original.cjs.js

# 4. Edit the dist file with your fix
# Apply the same logical fix to the new version's code

# 5. Generate the patch
diff -u original.cjs.js node_modules/<package>/dist/<file>.cjs.js > fix.patch

# 6. Or use yarn patch workflow
yarn patch <package>@<new-version>
# Make changes in the temp directory yarn provides
yarn patch-commit -s <temp-directory>
```

### Updating References After Regeneration

1. Delete the old patch file from `.yarn/patches/`
1. Place the new patch file in `.yarn/patches/` with the new version in the filename
1. Update the `resolutions` entry in `package.json` to reference the new filename and version
1. Run `yarn install` to verify the patch applies cleanly

### Common Backstage Patches and Their Status

These are patches we've maintained across upgrades. Always check if they're still needed:

| Patch                          | Bug                                               | Typical upstream status                                      |
| ------------------------------ | ------------------------------------------------- | ------------------------------------------------------------ |
| ADR backend NotModifiedError   | Cache empty + etag present → 500 error            | NOT fixed upstream as of plugin-adr-backend 0.20.0           |
| ADR search adrFiles null guard | Missing adrFiles in cache → crash during indexing | NOT fixed upstream as of search-backend-module-adr 0.17.0    |
| GitLab contributor avatars     | Email-only matching instead of email+name         | NOT fixed in @immobiliarelabs/backstage-plugin-gitlab 6.13.0 |

### Commit Strategy

```
fix(<scope>): regenerate <patch-name> patch for <new-version>
# or
chore(<scope>): drop obsolete <patch-name> patch (merged upstream)
```

______________________________________________________________________

## Phase 5: Full Verification

Run ALL of these in order. Every command must pass.

```bash
yarn install          # Clean dependency resolution
yarn tsc              # TypeScript compilation — zero errors
yarn lint:all         # ESLint — clean
yarn test             # Jest tests — all pass (or document pre-existing failures)
yarn build:all        # Full build — frontend + backend
```

### Backend Startup Test

Even if you can't run the full app (e.g., no local database), verify the backend initializes:

```bash
# Attempt backend startup — look for plugin discovery, not DB connection
yarn start backend 2>&1 | head -50
# Success indicators:
#   - All plugins discovered and registered
#   - No "Cannot find module" errors
#   - No import failures
# Expected failure (acceptable):
#   - Database connection refused (no local PG)
```

______________________________________________________________________

## Phase 6: Manual QA

### Entity Pages (most likely to regress)

- [ ] Component overview
- [ ] Service overview
- [ ] Website overview
- [ ] API overview + definition tab
- [ ] User profile
- [ ] Group profile
- [ ] System overview + diagram
- [ ] Domain overview

### Plugin Integrations

- [ ] GitLab cards: people, MRs, pipelines, releases, languages
- [ ] GitLab contributor avatars (especially for users with mismatched git/GitLab names)
- [ ] ADR tab: loads, files render, images display
- [ ] ADR search results
- [ ] Announcements page loads
- [ ] Announcements in search
- [ ] End-of-life cards where annotated
- [ ] TechDocs builds and renders

### Infrastructure

- [ ] Authentication flow (GitLab sign-in)
- [ ] Search page: all result types (catalog, techdocs, ADR, announcements)
- [ ] No console errors in browser DevTools
- [ ] No backend 500 errors in logs

______________________________________________________________________

## Atomic Commit Strategy (Recommended)

For a clean, bisectable history:

| Order | Commit                                                   | Content                             |
| ----- | -------------------------------------------------------- | ----------------------------------- |
| 1     | `chore(backstage): bump core packages to <version>`      | versions:bump output + cli-defaults |
| 2     | `fix(app): remove deprecated <pattern>`                  | Breaking change code fixes          |
| 3     | `chore(plugins): update <family> packages`               | One per plugin family               |
| 4     | `fix(<scope>): regenerate <patch> for <version>`         | One per patch                       |
| 5     | `chore: complete backstage <version> verification fixes` | Any remaining fixes                 |

For fewer commits, compress to:

1. Core bump + breaking change fixes
1. Community plugin updates + patch regeneration

______________________________________________________________________

## Upgrade Risk Matrix

| Risk                                                 | Severity | Mitigation                                                    |
| ---------------------------------------------------- | -------- | ------------------------------------------------------------- |
| TypeScript errors from removed props/APIs            | HIGH     | grep for patterns before/after, use Upgrade Helper            |
| Yarn patch application failure                       | HIGH     | Check version changes first, regenerate before `yarn install` |
| Community plugin peer dep mismatch                   | MEDIUM   | Check npm for compatible versions, keep pinned if no release  |
| Runtime regression (works in tsc, breaks in browser) | MEDIUM   | Manual QA is mandatory, not optional                          |
| TechDocs build failure                               | LOW      | Ensure mkdocs + mkdocs-techdocs-core installed locally        |

______________________________________________________________________

## Quick Reference: Key Files

| File                                                 | Purpose                                              |
| ---------------------------------------------------- | ---------------------------------------------------- |
| `backstage.json`                                     | Current Backstage version                            |
| `package.json` (root)                                | Root devDeps, resolutions, Yarn patch references     |
| `packages/app/package.json`                          | Frontend plugin versions                             |
| `packages/backend/package.json`                      | Backend plugin versions                              |
| `packages/app/src/components/catalog/EntityPage.tsx` | Entity page layout — most breaking changes land here |
| `.yarn/patches/`                                     | Yarn patch files (version-pinned)                    |
| `yarn.lock`                                          | Lockfile — always regenerated during upgrade         |
| `app-config.yaml`                                    | Config — rarely changes during upgrades              |

______________________________________________________________________

## Troubleshooting

### `yarn install` fails with patch error

The patch filename contains the package version. If the version changed, the patch can't find its target.

**Fix**: Regenerate the patch for the new version (see Phase 4).

### TypeScript errors after bump

1. Check the Upgrade Helper for template changes
1. Look at the CHANGELOG of the specific package that changed
1. Fix at the call site — NEVER use `as any` or `@ts-ignore`

### `spawn mkdocs ENOENT` in TechDocs

TechDocs with `builder: 'local'` requires mkdocs installed on the host:

```bash
uv tool install mkdocs --with mkdocs-techdocs-core
```

### Backend fails to start after upgrade

1. Check for missing `backend.add(import(...))` entries in `packages/backend/src/index.ts`
1. Check for renamed or moved backend plugin packages
1. Run `yarn workspace backend build` to get specific error messages

### Community plugin has no compatible release

Keep it pinned at the current version. Backstage's dependency resolution usually allows minor version mismatches in peer deps. Monitor for runtime errors and update when a compatible release ships.

______________________________________________________________________

## Historical Upgrade Log

| Upgrade         | Key Changes                                                                                                            | Patches Affected                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1.47.0 → 1.48.4 | No breaking code changes, 68 packages bumped                                                                           | None (patches were created during this cycle)                                                               |
| 1.48.4 → 1.49.3 | `variant="gridItem"` removed (21 occurrences), `@backstage/cli-defaults` required, plugin-catalog major bump to v2.0.1 | ADR backend: regenerated for 0.20.0; ADR search: regenerated for 0.17.0; GitLab: unchanged (no new release) |
