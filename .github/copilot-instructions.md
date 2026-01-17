# Copilot Instructions: Research Build → Publish Workflow

## Project Architecture

This is a **reproducible research workflow** template with strict separation of build outputs and published artifacts:

- **Build outputs** live in `output/` (figures, tables, logs, per-artifact provenance)
- **Published artifacts** live in `paper/` (a separate git repo intended for Overleaf)
- Publishing is **explicit and traceable**: artifacts are copied from `output/` to `paper/` only via `make publish`, with full provenance tracking

### Key directories

- `analysis/`: Python scripts that generate one figure + one table each (e.g., `build_price_base.py`)
- `data/`: Input data (CSV files)
- `output/`: All build outputs including `output/provenance/*.yml` (per-artifact build records)
- `paper/`: Destination for published artifacts; separate git repo with `paper/provenance.yml` tracking what was published
- `scripts/`: Shared utilities (`provenance.py` for build records, `publish_artifacts.py` for publishing)
- `env/`: Environment specs (`python.yml` for conda, `Project.toml` for Julia placeholder)

## Critical Workflows

### Building artifacts

```bash
make all              # Build everything
make price_base       # Build one artifact (figure + table + provenance)
```

Each build produces **grouped outputs** in a single invocation:
- `output/figures/<name>.pdf`
- `output/tables/<name>.tex`
- `output/provenance/<name>.yml` (build metadata)

### Publishing to paper repo

```bash
make publish                              # Publish all artifacts
make publish PUBLISH_ARTIFACTS="price_base"  # Publish specific artifact(s)
```

Publishing enforces **git safety checks** (configurable in Makefile):
- Refuses if working tree is dirty (`--allow-dirty 0`)
- Refuses if branch is behind upstream (`--require-not-behind 1`)

Updates `paper/provenance.yml` with per-artifact records including git commit, input/output SHA256, timestamps.

## Project Conventions

### Analysis script pattern

Every `analysis/build_*.py` script follows this structure:
- Takes args: `--data`, `--out-fig`, `--out-table`, `--out-meta`
- Produces figure (PDF) + table (LaTeX) from input data
- Calls `write_build_record()` from `scripts/provenance.py` to generate `output/provenance/*.yml`

Example: [analysis/build_price_base.py](analysis/build_price_base.py)

### Makefile grouped targets

Uses GNU Make **grouped targets** (`&:` syntax, requires Make >= 4.3) to ensure one script invocation produces all three outputs atomically. See [Makefile](Makefile) lines 27-35.

### Provenance records

- **Build provenance**: `output/provenance/<name>.yml` captures git state, input/output hashes, command, timestamp
- **Publish provenance**: `paper/provenance.yml` aggregates what was published and when, referencing build records

Key functions in [scripts/provenance.py](scripts/provenance.py):
- `git_state()`: captures commit, branch, dirty flag, ahead/behind counts
- `sha256_file()`: checksums inputs/outputs
- `write_build_record()`: writes per-artifact YAML

### Python environment wrapper

Scripts are invoked via `env/scripts/runpython` (not bare `python`) to allow environment activation. In this template it's a simple wrapper; in production it might activate conda/micromamba.

## Integration Points

- **paper/ as separate git repo**: In production, `paper/` should be its own git repo (ignored by the analysis repo) with an Overleaf remote. Publishing writes files there; you then commit/push manually.
- **No direct writes to paper/**: Never manually copy files to `paper/`. Always use `make publish` to maintain provenance chain.
- **Data inputs**: Scripts read from `data/`. Add more inputs to the `DATA` variable in Makefile and analysis script args.

## Adding New Artifacts

1. Create `analysis/build_<name>.py` following the pattern in [build_price_base.py](analysis/build_price_base.py)
2. Add `<name>` to the `ARTIFACTS` variable in [Makefile](Makefile) (line 6)
3. Build with `make <name>`
4. Publish with `make publish PUBLISH_ARTIFACTS="<name>"`
