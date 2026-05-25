# Directory Structure

This document explains the organization of the reproducible research template.

## Overview

```
project_template/
├── .github/               # GitHub metadata
│   └── copilot-instructions.md
├── .gitignore             # Git exclusions
├── .gitmodules            # Git submodule configuration
├── run_analysis.py        # Unified analysis script (study configs in shared/config.py)
├── run_did.py             # Standalone DiD analysis (Julia/pyfixest backends)
├── data/                  # Input datasets
├── docs/                  # Documentation
├── env/                   # Environment setup
│   └── examples/          # Example scripts
├── lib/                   # Git submodules
│   └── repro-tools/       # Reproducibility tools (editable install)
├── notebooks/             # Notebook-based analyses (papermill)
├── output/                # Build outputs (ephemeral)
├── paper/                 # Published outputs (permanent)
├── scripts/               # Project helper scripts (check_prerequisites.sh)
├── shared/                # Project configuration
│   └── config.py          # Study configurations (STUDIES + DEFAULTS)
├── Makefile               # Build orchestration
└── README.md              # This overview
```

## Core Directories

### Analysis Scripts (Root)

Analysis scripts that generate figures and tables, located in the project root.

The primary script is the unified **`run_analysis.py`**, which takes a study name and reads its
parameters from the `STUDIES` dict in `shared/config.py`:

- `env/scripts/runpython run_analysis.py price_base`
- Produces one figure + one table + one provenance record per study
- Uses `repro_tools.auto_build_record()` for metadata

`run_did.py` is a standalone difference-in-differences example (Julia `FixedEffectModels` backend,
with a pyfixest fallback).

**Contents**:
```
project_template/
├── run_analysis.py        # Unified, config-driven analysis (price_base, remodel_base, ...)
└── run_did.py             # Standalone DiD analysis (did_example)
```

### `data/`

Input datasets (CSV, Parquet, etc.).

**Contents**:
```
data/
└── housing_panel.csv          # Sample housing data
```

**Not tracked in git** (for large datasets):
```
data/
├── raw/                       # Symlinks to external data
└── processed/                 # Generated datasets
```

Use `.gitignore` to exclude large files:
```gitignore
data/raw/
data/processed/
*.csv
!data/housing_panel.csv  # Except small samples
```

### `output/`

Build outputs - **ephemeral, can be deleted and rebuilt**.

```
output/
├── figures/
│   ├── price_base.pdf
│   └── remodel_base.pdf
├── tables/
│   ├── price_base.tex
│   └── remodel_base.tex
├── provenance/
│   ├── price_base.yml
│   └── remodel_base.yml
└── logs/
    ├── price_base.log
    ├── remodel_base.log
    ├── sample_python.log
    ├── sample_julia.log
    └── sample_stata.log
```

**Purpose**:
- `figures/`: Generated PDFs
- `tables/`: Generated LaTeX tables
- `provenance/`: Per-artifact build records
- `logs/`: Build and example execution logs

**Git exclusion**: Entire `output/` is in `.gitignore`.

### `paper/`

Published outputs - **permanent, tracked separately**.

```
paper/
├── figures/
│   ├── price_base.pdf
│   └── remodel_base.pdf
├── tables/
│   ├── price_base.tex
│   └── remodel_base.tex
├── provenance.yml             # Aggregated provenance
└── README.md                  # Paper repo documentation
```

**Intended use**: Separate git repository for Overleaf integration.

**Workflow**:
1. Build in `output/`
2. Publish to `paper/` with `make publish`
3. Commit `paper/` to its own git repo
4. Push to Overleaf git remote

**Git setup** (recommended):
```bash
cd paper
git init
git remote add overleaf <overleaf-git-url>
git add -A
git commit -m "Published outputs"
git push -u overleaf main
```

### `lib/`

Git submodules for external dependencies.

```
lib/
└── repro-tools/               # Reproducibility tools (git submodule)
    ├── src/
    │   └── repro_tools/       # Python package source
    ├── pyproject.toml
    └── README.md
```

**repro-tools**:
- Installed in editable mode (`pip install -e lib/repro-tools`)
- Changes immediately available (no reinstall needed)
- Automatically initialized by `make environment`
- See [docs/repro_tools_submodule.md](repro_tools_submodule.md) for details

**Git submodule**:
- Tracked in `.gitmodules`
- Auto-initialized by Makefile
- Update with: `git submodule update --remote lib/repro-tools`

### `scripts/`

Shared Python utilities used by analysis and publishing.

**NOTE:** Most scripts have been moved to the `repro-tools` package in `lib/repro-tools/`.
This directory may be deprecated in future versions.

```
scripts/
├── provenance.py              # Build provenance tracking (DEPRECATED - use repro_tools)
└── publish_artifacts.py       # Publishing with safety checks (DEPRECATED - use repro-tools CLI)
```

## Environment Directories

### `env/`

Environment configuration for Python, Julia, and Stata.

```
env/
├── Makefile                   # Environment build targets
├── Project.toml               # Julia dependencies
├── stata-packages.txt         # Stata package list
└── scripts/
    ├── install_uv.sh          # Auto-installer (uv)
    ├── install_julia.py       # Julia setup via juliacall
    ├── runpython              # Python wrapper
    ├── runjulia               # Julia wrapper
    ├── runstata               # Stata wrapper
    └── execute.ado            # Stata helper
```

**Environment targets**:
- `make -C env all-env`: Setup everything
- `make -C env python-env`: Just Python
- `make -C env julia-install-via-python`: Just Julia
- `make -C env stata-env`: Just Stata

**Wrapper scripts** configure environment before execution:
- `runpython`: Sets PYTHONPATH, Julia bridge, uv virtualenv activation
- `runjulia`: Points to `.julia/pyjuliapkg/install/bin/julia`
- `runstata`: Sets STATA_PACKAGES, uses execute.ado

### `env/examples/`

Sample scripts demonstrating all three languages.

```
env/examples/
├── README.md
├── sample_python.py           # Python example
├── sample_julia.jl            # Pure Julia example
├── sample_juliacall.py        # Python/Julia interop
└── sample_stata.do            # Stata example
```

**Makefile targets**:
- `make examples`: Run all
- `make sample-python`: Python only
- `make sample-julia`: Julia only
- `make sample-juliacall`: Python/Julia interop
- `make sample-stata`: Stata only

## Documentation

### `docs/`

Project documentation.

```
docs/
├── environment.md             # Environment setup details
├── provenance.md              # Provenance tracking explained
├── publishing.md              # Publishing workflow
└── directory_structure.md     # This file
```

### `.github/`

GitHub-specific files.

```
.github/
└── copilot-instructions.md    # AI agent guidance
```

**Purpose**: Provides context for GitHub Copilot and other AI coding assistants working in this codebase.

## Hidden Directories (Git-Ignored)

### `.venv/`

uv-managed virtualenv (Python packages).

**Created by**: `make environment` → `uv sync`

**Size**: ~2GB

**Git status**: Ignored (in `.gitignore`)

### `.julia/`

Julia installation and packages.

```
.julia/
├── pyjuliapkg/                # Julia binary installed by juliacall
│   └── install/
│       └── bin/julia
├── packages/                  # Installed packages
└── compiled/                  # Precompiled cache
```

**Created by**: `make environment` → Julia auto-installs via juliacall

**Size**: ~1-2GB

**Git status**: Ignored

### `.stata/`

Stata packages (if Stata is installed).

```
.stata/
└── ado/
    └── plus/                  # User-installed packages
        ├── reghdfe.ado
        ├── ftools.ado
        └── estout.ado
```

**Created by**: `make environment` → `make -C env stata-env`

**Size**: ~100MB

**Git status**: Ignored

## Configuration Files

### Root Level

**Makefile**:
- Defines `ARTIFACTS` variable (list of artifacts)
- Grouped targets for atomic builds
- Publish targets with git safety
- Example targets
- Help/info targets

**README.md**:
- Quick start guide
- Overview of features and workflows

**.gitignore**:
```gitignore
# Build outputs
output/

# Environments
.venv/
.julia/
.stata/

# Python
__pycache__/
*.pyc

# OS
.DS_Store
```

## Typical File Paths

### During Analysis

**Input**: `data/housing_panel.csv`

**Build command**:
```bash
env/scripts/runpython run_analysis.py price_base
```

**Outputs**:
- `output/figures/price_base.pdf` (figure)
- `output/tables/price_base.tex` (table)
- `output/provenance/price_base.yml` (metadata)
- `output/logs/price_base.log` (build log)

### During Publishing

**Publish command**:
```bash
$(REPRO_PUBLISH) \
  --paper-root paper \
  --kind figures \
  --names "price_base remodel_base"
```

**Copies**:
- `output/figures/*.pdf` → `paper/figures/*.pdf`
- `output/tables/*.tex` → `paper/tables/*.tex`

**Updates**:
- `paper/provenance.yml` (aggregated provenance)

## Path References

### Absolute vs Relative

**Makefile**: Uses absolute paths via `$(abspath ...)`

**Scripts**: Receive absolute paths as arguments

**Provenance**: Records absolute paths for clarity

**Documentation**: Uses relative paths for portability

### Repo Root Detection

Scripts find repo root via:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
```

Python equivalent:
```python
from pathlib import Path
repo_root = Path(__file__).resolve().parents[2]
```

## Recommended Additions

### For Large Projects

Add these directories as needed:

**tests/**:
```
tests/
├── test_provenance.py
├── test_analysis.py
└── fixtures/
    └── sample_data.csv
```

**data-construction/**:
```
data-construction/
├── 01_import_raw.py
├── 02_clean.py
└── 03_merge.py
```

**notebooks/**:
```
notebooks/
├── exploration.ipynb
└── figures_draft.ipynb
```

### For Multi-Analysis Projects

Group studies by topic in `shared/config.py` (and add each name to `ANALYSES` in the Makefile):
```python
STUDIES = {
    # Housing
    "price_base":   {...},
    "remodel_base": {...},
    # Macro
    "gdp":          {...},
    "employment":   {...},
}
```

For an analysis that doesn't fit the unified `run_analysis.py` (e.g. a custom regression), add a
standalone root-level script like `run_did.py` and wire it into the Makefile `ANALYSES` with its own
pattern block.

## See Also

- [README.md](../README.md) - Quick start guide
- [docs/environment.md](environment.md) - Environment setup
- [docs/provenance.md](provenance.md) - Provenance tracking
- [docs/publishing.md](publishing.md) - Publishing workflow
