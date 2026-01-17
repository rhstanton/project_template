# Provenance Tracking

This project implements comprehensive provenance tracking to ensure reproducibility and traceability of all research outputs.

## Overview

Provenance tracking answers these critical questions:
- **What code** generated each figure/table?
- **What data** was used as input?
- **When** was it built?
- **What git commit** contains the exact code?
- **Has the output** been modified since build?

## Two Levels of Provenance

### 1. Build Provenance (`output/provenance/<name>.yml`)

Created when each artifact is built. Contains:

```yaml
artifact: price_base
built_at_utc: '2026-01-17T04:04:49+00:00'
command:
  - python
  - build_price_base.py
  - --data
  - data/housing_panel.csv
git:
  is_git_repo: true
  commit: cbb163e7a1b2c3d4e5f6...
  branch: main
  dirty: false
  ahead: 0
  behind: 0
inputs:
  - path: /path/to/data/housing_panel.csv
    sha256: 48917387ef250e81b4ec8a43e25a01f512a5c00c857614f82fee0729e48f91ce
    bytes: 325
    mtime: 1768622679.5022135
outputs:
  - path: /path/to/output/figures/price_base.pdf
    sha256: 3855687dcbeff3673679f5bb05a2019f94987f19e1c6d8fc5c2284fec73f9025
    bytes: 12482
    mtime: 1768622689.4427366
  - path: /path/to/output/tables/price_base.tex
    sha256: 958062fbe20ff4dee6ad0ae6af81fc45c8c4c2408418fabee0810fb4bc5a19bc
    bytes: 193
    mtime: 1768622689.2007284
```

### 2. Publication Provenance (`paper/provenance.yml`)

Created/updated when publishing. Aggregates build records and adds publication metadata:

```yaml
paper_provenance_version: 1
last_updated_utc: '2026-01-17T04:12:30+00:00'
analysis_git:
  is_git_repo: true
  commit: cbb163e7a1b2c3d4e5f6...
  branch: main
  dirty: false
  ahead: 0
  behind: 0
artifacts:
  price_base:
    figures:
      published_at_utc: '2026-01-17T04:12:30+00:00'
      copied: true
      src: /path/to/output/figures/price_base.pdf
      dst: /path/to/paper/figures/price_base.pdf
      dst_sha256: 3855687dcbeff3673679f5bb05a2019f94987f19e1c6d8fc5c2284fec73f9025
      build_record:
        # Full build provenance embedded here
        artifact: price_base
        built_at_utc: '2026-01-17T04:04:49+00:00'
        ...
    tables:
      published_at_utc: '2026-01-17T04:12:30+00:00'
      copied: true
      src: /path/to/output/tables/price_base.tex
      dst: /path/to/paper/tables/price_base.tex
      dst_sha256: 958062fbe20ff4dee6ad0ae6af81fc45c8c4c2408418fabee0810fb4bc5a19bc
      build_record:
        # Full build provenance embedded here
        ...
```

## Git State Tracking

The `git` section records:
- `commit`: Full SHA of current commit
- `branch`: Current branch name
- `dirty`: Whether working tree has uncommitted changes
- `ahead`: Commits ahead of upstream
- `behind`: Commits behind upstream

This allows precise reproduction: checkout the commit, verify inputs match their hashes, and re-run the build.

## SHA256 Checksums

Every input and output file is checksummed:
- **Inputs**: Proves exactly which data was used
- **Outputs**: Detects any manual modifications

To verify an output hasn't been modified:
```bash
sha256sum paper/figures/price_base.pdf
# Compare with dst_sha256 in paper/provenance.yml
```

## Timestamps

All timestamps are in UTC ISO format for unambiguous comparison across timezones:
```yaml
built_at_utc: '2026-01-17T04:04:49+00:00'
published_at_utc: '2026-01-17T04:12:30+00:00'
```

## Implementation

### In Analysis Scripts

Use `scripts/provenance.py`:

```python
from scripts.provenance import write_build_record

write_build_record(
    artifact="my_artifact",
    command=sys.argv,  # Exact command that was run
    inputs=[args.data],  # List of Path objects
    outputs=[args.out_fig, args.out_table],  # List of Path objects
    output_path=args.out_meta  # Where to write provenance YAML
)
```

This function:
1. Calls `git_state()` to get current git info
2. Calls `sha256_file()` on each input/output
3. Writes YAML with all metadata

### In Publishing

The `scripts/publish_artifacts.py` script:
1. Reads build provenance from `output/provenance/<name>.yml`
2. Copies artifacts to `paper/`
3. Embeds build records in `paper/provenance.yml`
4. Records current git state at publication time
5. Tracks whether files were actually copied (or already up-to-date)

## Verification Workflows

### Verify Output Hasn't Changed

```bash
# Get expected hash from provenance
grep "dst_sha256" paper/provenance.yml

# Compute actual hash
sha256sum paper/figures/price_base.pdf

# Compare
```

### Reproduce from Provenance

```bash
# 1. Checkout exact commit
git checkout $(grep "commit:" paper/provenance.yml | head -1 | awk '{print $2}')

# 2. Verify input data matches
sha256sum data/housing_panel.csv
# Compare with inputs[0].sha256 in provenance

# 3. Rebuild
make price_base

# 4. Verify output matches
sha256sum output/figures/price_base.pdf
# Should match original dst_sha256
```

## Git Safety Checks

Publishing enforces git hygiene:

**Default checks** (can be overridden):
- `--allow-dirty 0`: Refuses if working tree is dirty
- `--require-not-behind 1`: Refuses if branch is behind upstream
- `--require-current-head 0`: Allows artifacts from older commits (default)

**Strict mode** (recommended for final publication):
```bash
make publish REQUIRE_CURRENT_HEAD=1
```

This ensures all artifacts were built from the current HEAD commit, preventing accidental publication of stale outputs.

## Best Practices

1. **Commit before building**: Ensures `git.commit` is meaningful
2. **Clean working tree**: No uncommitted changes (`git.dirty: false`)
3. **Use strict publishing**: `REQUIRE_CURRENT_HEAD=1` for final publication
4. **Verify hashes**: Spot-check a few `dst_sha256` values match actual files
5. **Archive provenance**: The `paper/provenance.yml` is the permanent record

## Limitations

- File modification times (`mtime`) may vary across systems (timezones, filesystems)
- Only tracks files explicitly listed as inputs/outputs
- Doesn't capture environment variables or system state
- Assumes git repo exists (gracefully degrades if not)

## Future Enhancements

Potential improvements:
- Track Python/Julia package versions
- Record system info (OS, CPU, memory)
- Capture environment variable dumps
- Link to remote git repository URLs
- Generate provenance reports (HTML/PDF summary)
