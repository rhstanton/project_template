# Publishing Workflow

This document explains how to publish build artifacts from `output/` to `paper/` with full provenance tracking.

## Overview

The publishing workflow:

1. **Builds** artifacts in `output/` (ephemeral, can be deleted)
2. **Publishes** vetted outputs to `paper/` (permanent, tracked separately)
3. **Updates** `paper/provenance.yml` with full build+publish metadata

This separation allows:

- Experimentation in `output/` without affecting paper
- Explicit, traceable publication events
- Different git histories for analysis vs. paper repos

**Publishing is idempotent**: Running `make publish` multiple times only re-publishes artifacts whose source files have changed. If everything is up-to-date, it reports "Nothing to publish - all up-to-date".

## Basic Usage

The publishing system supports two modes:

1. **Analysis-level selection**: Publish all outputs from specific analyses
2. **File-level selection**: Publish only specific output files

### Publish All Analyses

```bash
make publish
```

This publishes all outputs from all analyses defined in `ANALYSES` variable.

### Publish Specific Analyses

```bash
make publish PUBLISH_ANALYSES="price_base remodel_base"
```

This publishes ALL outputs (figures, tables, etc.) from the specified analyses.

**Use case**: You've updated `price_base` analysis but `remodel_base` outputs are already in the paper.

### Publish Specific Files (Fine-Grained Control)

```bash
make publish PUBLISH_FILES="output/figures/price_base.pdf output/tables/custom_table.tex"
```

This publishes only the specified files, regardless of which analysis they came from.

**Use cases**:

- Analysis generates 5 figures but you only want 2 in the paper
- You have supplementary materials in separate subdirectories
- Custom aggregated tables that combine data from multiple analyses

**Note**: File paths should be relative to project root or absolute.

**Provenance tracking**: File-level publishing uses a separate `files:` section in `paper/provenance.yml` and removes any previous `artifacts:` section (from analysis-level publishes) since the two publishing modes are mutually exclusive. Each file entry includes its source path, analysis name, and full build record.

### Examples of Mixed Publishing

```bash
# ERROR: Cannot use both modes simultaneously
make publish PUBLISH_ANALYSES="price_base" PUBLISH_FILES="output/figures/remodel_base.pdf"
# This will fail - must choose one mode

# CORRECT: Use file-level for everything
make publish PUBLISH_FILES="output/figures/price_base.pdf output/tables/price_base.tex output/figures/remodel_base.pdf"
```

**Important**: `PUBLISH_ANALYSES` and `PUBLISH_FILES` are mutually exclusive. Choose one mode per invocation.

**Publishing mode switching**: If you switch from analysis-level to file-level publishing (or vice versa), the provenance file structure changes:
- Analysis-level uses `artifacts:` section
- File-level uses `files:` section  
- Switching modes clears the previous section to avoid stale data

**Important**: Publishing never deletes files from `paper/`, it only adds or updates them. If you switch publishing modes or stop publishing certain outputs, you may have orphaned files in `paper/` that are no longer tracked in provenance.

**To clean up orphaned files**:
```bash
# Check for orphaned files
ls -1 paper/figures/ paper/tables/
grep "^  " paper/provenance.yml  # See what's tracked

# Clean republish (be careful!)
rm -rf paper/figures/* paper/tables/*
make publish PUBLISH_ANALYSES="price_base remodel_base"  # Whichever you want
```

### Strict Publishing (Require Current HEAD)

```bash
make publish REQUIRE_CURRENT_HEAD=1
```

This ensures all artifacts were built from the current git commit, preventing accidental publication of stale outputs. Works with both modes.

### Force Re-publish (Override Up-to-date Check)

```bash
make publish-force
```

This clears the publish tracking and forces all artifacts to be re-published, even if they haven't changed. Useful if you manually modified files in `paper/` and want to restore from `output/`.


## Git Safety Checks

Publishing enforces several git safety checks to ensure reproducibility.

### 1. Artifacts Built from Clean Tree

**Default**: Refuses to publish if artifacts were built from a dirty working tree

This check reads the provenance files and verifies that `git.dirty` was `false` when each artifact was built.

```bash
# If you built with uncommitted changes:
make all  # While tree was dirty
git commit -am "Commit changes"
make publish
# Error: Refusing to publish: some artifacts were built from a dirty working tree:
#   price_base
#   remodel_base
# 
# Rebuild from a clean tree: git commit/stash, then make clean && make all
# Or set --allow-dirty 1 to allow.
```

**Solution**: Commit changes first, then rebuild:
```bash
git commit -am "Commit changes"
make clean && make all
make publish
```

**Override** (not recommended):
```bash
make publish ALLOW_DIRTY=1  # Via Makefile variable
```

### 2. Current Working Tree Clean

**Default**: Refuses to publish if current working tree is dirty

```bash
# If you have uncommitted changes:
make publish
# Error: Refusing to publish from a dirty working tree
```

**Override** (not recommended):
```bash
make publish --allow-dirty 1
```

Or set in Makefile:
```makefile
publish-figures: ...
    $(REPRO_PUBLISH) \
      --allow-dirty 1 \
      ...
```

### 3. Not Behind Upstream

**Default**: Refuses if branch is behind remote

```bash
# If you haven't pulled latest changes:
make publish
# Error: Refusing to publish: your branch is behind upstream by 2 commit(s)
```

**Override**:
```bash
make publish --require-not-behind 0
```

Or edit Makefile to change default.

### 4. Current HEAD (Optional)

**Default**: Allows artifacts from any commit (flexible for incremental work)

**Strict mode** ensures all artifacts match current HEAD:
```bash
make publish REQUIRE_CURRENT_HEAD=1
```

If artifacts are stale:
```
Refusing to publish: some artifacts were not built from current HEAD:
  price_base: built from abc123f, but HEAD is def456a
  remodel_base: built from abc123f, but HEAD is def456a

Run: make clean && make all
Or set --require-current-head 0 to allow.
```

## Publishing Targets

### Figures Only

```bash
make publish-figures
```

Copies `output/figures/*.pdf` → `paper/figures/*.pdf`

### Tables Only

```bash
make publish-tables
```

Copies `output/tables/*.tex` → `paper/tables/*.tex`

### Both (Default)

```bash
make publish
```

Runs both `publish-figures` and `publish-tables`.

## What Gets Updated

### Files Copied

For each artifact in `PUBLISH_ARTIFACTS`:
- `output/figures/<name>.pdf` → `paper/figures/<name>.pdf`
- `output/tables/<name>.tex` → `paper/tables/<name>.tex`

Files are only copied if content differs (checked via SHA256). If already up-to-date, `copied: false` is recorded in provenance.

### Provenance Updated

`paper/provenance.yml` is updated with:

```yaml
paper_provenance_version: 1
last_updated_utc: '2026-01-17T04:12:30+00:00'
analysis_git:
  commit: cbb163e  # Current commit at publish time
  branch: main
  dirty: false
artifacts:
  price_base:
    figures:
      published_at_utc: '2026-01-17T04:12:30+00:00'
      copied: true  # or false if unchanged
      src: /path/to/output/figures/price_base.pdf
      dst: /path/to/paper/figures/price_base.pdf
      dst_sha256: 3855687d...  # Hash of published file
      build_record:
        # Full build provenance from output/provenance/price_base.yml
        artifact: price_base
        built_at_utc: '2026-01-17T04:04:49+00:00'
        git:
          commit: cbb163e  # Commit that built this artifact
        ...
```

## Recommended Workflow

### During Development

```bash
# Build and test iteratively
make price_base
# Review output/figures/price_base.pdf

# Rebuild after edits
make price_base
```

Don't publish during active development.

### Before Publication

```bash
# 1. Commit all changes
git add -A
git commit -m "Final analysis for paper"

# 2. Rebuild everything from clean state
make clean
make all

# 3. Publish with strict checks
make publish REQUIRE_CURRENT_HEAD=1

# 4. Verify provenance
cat paper/provenance.yml
```

This ensures:

- All outputs from same commit
- No uncommitted changes
- Full provenance chain documented

### After Publication

The `paper/` directory can be:
- A separate git repository (recommended)
- Synced to Overleaf via git
- Archived with the manuscript

Initialize `paper/` as its own repo:
```bash
cd paper
git init
git add figures/ tables/ provenance.yml
git commit -m "Published outputs from analysis commit cbb163e"
git remote add origin <overleaf-git-url>
git push -u origin main
```

## Makefile Variables

Control publishing behavior via make variables:

```makefile
# Which artifacts to publish (default: all)
PUBLISH_ARTIFACTS ?= $(ARTIFACTS)

# Require artifacts from current HEAD (default: no)
REQUIRE_CURRENT_HEAD ?= 0
```

Override from command line:
```bash
make publish PUBLISH_ARTIFACTS="price_base" REQUIRE_CURRENT_HEAD=1
```

## Common Scenarios

### Scenario 1: Publish Subset of Outputs

Analysis generates many files but paper only uses some:

```bash
# Build analysis that creates 5 figures
make detailed_analysis
ls output/figures/
# → detailed_analysis_fig1.pdf
# → detailed_analysis_fig2.pdf
# → detailed_analysis_fig3.pdf
# → detailed_analysis_fig4.pdf
# → detailed_analysis_fig5.pdf

# Publish only figures 1 and 3 to paper
make publish PUBLISH_FILES="output/figures/detailed_analysis_fig1.pdf output/figures/detailed_analysis_fig3.pdf"
```

The file-level selection allows you to be selective about what goes into the final paper.

### Scenario 2: Incremental Updates

Build `price_base`, then later build `remodel_base`:

```bash
make price_base
# Time passes, commits happen
make remodel_base

# Publish both (from different commits)
make publish
```

`paper/provenance.yml` will show different `git.commit` for each artifact. This is allowed by default but not recommended for final publication.

### Scenario 3: Atomic Publication

Build everything together:

```bash
make clean
make all
make publish REQUIRE_CURRENT_HEAD=1
```

All artifacts from same commit, enforced by `REQUIRE_CURRENT_HEAD=1`.

### Scenario 4: Updating One Analysis

```bash
# Edit analysis/build_price_base.py
git commit -am "Fix price_base calculation"

make price_base
make publish PUBLISH_ANALYSES="price_base"
```

Only `price_base` is republished. Other artifacts remain from their original commits.

### Scenario 4: Emergency Fix (Dirty Tree)

```bash
# Quick fix without committing
make price_base
make publish PUBLISH_ARTIFACTS="price_base" --allow-dirty 1
```

**Not recommended**: Provenance will show `git.dirty: true`, making exact reproduction difficult.

## Troubleshooting

### "Refusing to publish from a dirty working tree"

**Cause**: Uncommitted changes in analysis repo

**Fix**:
```bash
git status
git add <files>
git commit -m "Description"
make publish
```

Or override (not recommended):
```bash
make publish --allow-dirty 1
```

### "Branch is behind upstream"

**Cause**: Haven't pulled latest changes

**Fix**:
```bash
git pull --rebase
make publish
```

### "Artifacts not built from current HEAD"

**Cause**: Using `REQUIRE_CURRENT_HEAD=1` but artifacts are stale

**Fix**:
```bash
make clean
make all
make publish REQUIRE_CURRENT_HEAD=1
```

### Missing Build Records

**Error**: `Missing build record output/provenance/price_base.yml`

**Cause**: Haven't built the artifact yet

**Fix**:
```bash
make price_base  # or make all
make publish
```

## Advanced: Custom Publishing

To publish to a different location:

```bash
make publish-figures PAPER_DIR=/path/to/alternative/paper
```

Or edit Makefile:
```makefile
PAPER_DIR ?= paper  # Change default
```

## See Also

- [docs/provenance.md](provenance.md) - Understanding provenance tracking
- [docs/directory_structure.md](directory_structure.md) - Project organization
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Workflow patterns
