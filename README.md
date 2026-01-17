# Sample project: Build → Publish with per-artifact provenance

This sample demonstrates a workflow that satisfies all of your requirements:

- **Single authoritative build outputs** live under `output/` (not the paper repo)
- `make all` builds everything, but you can run subsets like `make price_base`
- Each artifact gets its own **sidecar provenance file**: `output/provenance/<name>.yml`
- Publishing copies artifacts into `paper/` **only on explicit command** and records exactly what was published in `paper/provenance.yml`
- The build recipe uses **GNU Make grouped targets** (`&:`) so one script invocation produces the figure + table + provenance exactly once

## Setup

First-time setup (installs Python + Julia + Stata environments):

```bash
make environment
```

This will:
- Install micromamba (if conda/mamba not found)
- Create a Python 3.11 environment in `.env/`
- Install Julia via juliacall in `.julia/`
- Install Stata packages to `.stata/` (if Stata is installed)
- Install all Python, Julia, and Stata packages

## Quick Start

After setup, test the environment with example scripts:

```bash
make examples
```

## Layout

```
project/
  analysis/
    build_price_base.py
    build_remodel_base.py
  data/
    housing_panel.csv
  env/
    python.yml       # Python dependencies
    Project.toml     # Julia dependencies
    Manifest.toml    # Julia lockfile (auto-generated)
    stata-packages.txt  # Stata packages
    scripts/
      runpython      # Python wrapper with Julia bridge
      runstata       # Stata wrapper
      execute.ado    # Stata helper
      install_micromamba.sh
      install_julia.py
  examples/          # Sample scripts for testing
    sample_python.py
    sample_julia.py
    sample_stata.do
  .env/              # Python environment (gitignored)
  .julia/            # Julia depot (gitignored)
  .stata/            # Stata packages (gitignored)
  output/
    figures/        # build outputs (PDF)
    tables/         # build outputs (TeX)
    provenance/     # per-artifact build records (YML)
    logs/
  paper/
    figures/        # published PDFs (tracked in paper repo / Overleaf)
    tables/         # published TeX tables
    provenance.yml  # what exactly is in paper/ and where it came from
  scripts/
    provenance.py
    publish_artifacts.py
  Makefile
```

## Build

Build everything:

```bash
make all
```

Build a subset (one figure + one table + provenance record):

```bash
make price_base
make remodel_base
```

Outputs:
- `output/figures/price_base.pdf`
- `output/tables/price_base.tex`
- `output/provenance/price_base.yml`

## Publish

Publish everything into `paper/`:

```bash
make publish
```

Publish only one artifact:

```bash
make publish PUBLISH_ARTIFACTS="price_base"
# or publish-figures / publish-tables separately
make publish-figures PUBLISH_ARTIFACTS="price_base"
make publish-tables  PUBLISH_ARTIFACTS="price_base"
```

Publishing updates:
- `paper/figures/<name>.pdf` and/or `paper/tables/<name>.tex`
- `paper/provenance.yml` with **per-figure and per-table provenance**, including:
  - analysis git commit + dirty flag
  - input data sha256 (here: `data/housing_panel.csv`)
  - output sha256

### Git safety checks

`publish_artifacts.py` defaults to:
- refuse if analysis working tree is dirty (`--allow-dirty 0`)
- refuse if your branch is behind upstream (`--require-not-behind 1`)

These are controlled by the Makefile flags in `publish-figures` and `publish-tables`.

## Notes about `paper/` being its own git repo

In your real setup:
- Your main analysis repo should ignore `paper/` (see `.gitignore` suggestion below)
- `paper/` should be its own git repo with an Overleaf remote
- Publishing just writes files into `paper/`; you then `cd paper && git add/commit/push`

## .gitignore suggestion (analysis repo)

Add this to the *analysis* repo:

```
paper/
output/
```

In practice you may prefer to keep `output/logs/` or `output/provenance/` for local debugging, but for journal replication packages you can archive snapshots.
