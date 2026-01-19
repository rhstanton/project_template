# Copilot Instructions: Research Build → Publish Workflow

## Project Architecture

This is a **reproducible research workflow** template with strict separation of build outputs and published artifacts, supporting **multi-language analysis** (Python, Julia, Stata):

- **Build outputs** live in `output/` (figures, tables, logs, per-artifact provenance)
- **Published artifacts** live in `paper/` (a separate git repo intended for Overleaf)
- Publishing is **explicit and traceable**: artifacts are copied from `output/` to `paper/` only via `make publish`, with full provenance tracking
- **Multi-language support**: Unified environment with Python 3.11, Julia 1.10-1.12 (via juliacall), and optional Stata

### Key directories

- **Root directory**: Analysis scripts that generate one figure + one table each (e.g., `build_price_base.py`, `build_remodel_base.py`)
  - Scripts are in the root for simplicity (not in `analysis/` subdirectory)
- `data/`: Input data (CSV files)
- `output/`: All build outputs including `output/provenance/*.yml` (per-artifact build records)
- `paper/`: Destination for published artifacts; separate git repo with `paper/provenance.yml` tracking what was published
- `scripts/`: Shared utilities (`provenance.py` for build records, `publish_artifacts.py` for publishing)
- `env/`: Environment specs and wrappers
  - `python.yml` - Conda environment specification
  - `Project.toml` - Julia package environment
  - `stata-packages.txt` - Stata package list
  - `scripts/runpython` - Python wrapper with PYTHONPATH and Julia bridge config
  - `scripts/runjulia` - Julia wrapper pointing to bundled Julia
  - `scripts/runstata` - Stata wrapper for local package installation
- `examples/`: Sample scripts demonstrating Python, Julia, juliacall, and Stata usage
- `docs/`: Comprehensive documentation (environment, provenance, publishing, troubleshooting, etc.)

## Critical Workflows

### Building artifacts

```bash
make all              # Build everything
make price_base       # Build one artifact (figure + table + provenance)
```

Each build produces **grouped outputs** in a single invocation:
- `output/figures/<name>.pdf`
- `output/tables/<name>.tex`
- `output/provenance/<name>.yml` (buiALLOW_DIRTY=0` default)
- Refuses if branch is behind upstream (`REQUIRE_NOT_BEHIND=1` default)
- **Strict mode**: Refuses if artifacts not built from current HEAD (`REQUIRE_CURRENT_HEAD=1` default)
  - Compares git commit in `output/provenance/<name>.yml` with current `HEAD`
  - Ensures published artifacts exactly match current code state
  - Disable with `make publish REQUIRE_CURRENT_HEAD=0`
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

Every `build_*.py` script follows this structure:
- Takes args: `--data`, `--out-fig`, `--out-table`, `--out-meta`
- Produces figure (PDF) + table (LaTeX) from input data
- Calls `write_build_record()` from `scripts/provenance.py` to generate `output/provenance/*.yml`

Example: [build_price_base.py](build_price_base.py)~67-76.

Pattern rule for all artifacts:
```makefile
output/figures/%.pdf output/tables/%.tex output/provenance/%.yml &: \
    build_%.py $(DATA)
	$(PYTHON) $< \
		--data $(DATA) \
		--out-fig output/figures/$*.pdf \
		--out-table output/tables/$*.tex \
		--out-meta output/provenance/$*.yml
```
Environment wrappers

Scripts are invoked via environment wrappers (not bare `python`/`julia`/`stata`) for proper configuration:

**`Multi-Language Environment

### Python 3.11 (conda)
- **Location**: `.env/` (local to repo, not global)
- **Packages**: pandas, matplotlib, juliacall, pyyaml, jinja2, pytest, ruff, mypy (see `env/python.yml`)
- **Auto-install**: `make environment` installs micromamba if conda/mamba not found
- **Usage**: `env/scripts/runpython script.py`

### Julia 1.10-1.12 (via juliacall)
- **Location**: `.julia/pyjuliapkg/install/` (auto-downloaded by juliacall)
- **Packages**: PythonCall, DataFrames (see `env/Project.toml`)
- **Important**: `env/Project.toml` is an **environment** not a package (no `name`, `uuid`, `version` fields)
- **Usage**: Pure Julia via in the **root directory** (not subdirectory) following the pattern in [build_price_base.py](build_price_base.py)
   - Must accept args: `--data`, `--out-fig`, `--out-table`, `--out-meta`
   - Must call `write_build_record()` to generate provenance
   - Can be Python, Julia, or Stata script
2. Add `<name>` to the `ARTIFACTS` variable in [Makefile](Makefile) (line ~6)
3. Build with `make <name>`
4. Publish with `make publish PUBLISH_ARTIFACTS="<name>"`

### Example Analysis Script Structure (Python)

```python
#!/usr/bin/env python
import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt
from scripts.provenance import write_build_record

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out-fig", required=True)
    parser.add_argument("--out-table", required=True)
    parser.add_argument("--out-meta", required=True)
    args = parser.parse_args()
    
    # Analysis code here
    df = pd.read_csv(args.data)
    # ...
    
    # Save outputs
    fig.savefig(args.out_fig, bbox_inches="tight")
    result_table.to_latex(args.out_table, index=False)
    
    # Write provenance
    write_build_record(
        metadata_path=args.out_meta,
        inputs=[args.data],
        outputs=[args.out_fig, args.out_table],
        script=__file__,
        cmd=" ".join(sys.argv)
    )

if __name__ == "__main__":
    main()
```

## Documentation

Comprehensive documentation in `docs/` directory:

- [README.md](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - 5-minute getting started guide
- [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Customization guide
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [docs/environment.md](../docs/environment.md) - Environment setup details
- [docs/provenance.md](../docs/provenance.md) - Provenance system explained
- [docs/publishing.md](../docs/publishing.md) - Publishing workflow
- [docs/directory_structure.md](../docs/directory_structure.md) - Project organization
- [docs/julia_python_integration.md](../docs/julia_python_integration.md) - Julia/Python bridge
- [docs/platform_compatibility.md](../docs/platform_compatibility.md) - System requirements, GPU support
- [docs/troubleshooting.md](../docs/troubleshooting.md) - Common issues and solutions
- [docs/README.md](../docs/README.md) - Documentation index

## Examples

Sample scripts in `examples/` directory demonstrating each language:

- `examples/sample_python.py` - Pure Python example
- `examples/sample_julia.jl` - Pure Julia example
- `examples/sample_juliacall.py` - Python → Julia interop via juliacall
- `examples/sample_stata.do` - Stata example (if Stata installed)

Each example has a Makefile target for testing: `make -C examples python`, `make -C examples julia`, etc.

## System Requirements

- **GNU Make 4.3+** (for grouped targets) - Critical!
  - macOS ships with Make 3.81, install via `brew install make` and use `gmake`
- **Python 3.11** via conda (auto-installed)
- **Julia 1.10-1.12** via juliacall (auto-installed)
- **Stata** (optional, commercial software, not auto-installed)
- **Git** for version control and provenance tracking
- **Disk**: ~5GB (2GB Python env + 500MB Julia + 2.5GB cache/data)
- **RAM**: 8GB minimum, 16GB recommended

## Critical Conventions

1. **Analysis scripts in root** (not `analysis/` subdirectory) for simplicity
2. **Always use environment wrappers** (`env/scripts/runpython` not bare `python`)
3. **CondaPkg must be disabled** (`JULIA_CONDAPKG_BACKEND=Null`) to avoid duplicate Python
4. **env/Project.toml is an environment** not a package (no `name` field)
5. **env/Manifest.toml is gitignored** (platform-specific, regenerated on each platform)
6. **Never edit paper/ directly** - always `make publish` to maintain provenance
7. **Grouped targets require Make 4.3+** - check version before expecting `make all` to work
8. **PYTHONPATH must include repo root** for `scripts` module imports (set by `runpython` wrapper)
9. **Code quality checks before commit** - run `make check` to ensure lint, format, type-check, and tests pass
10. **Auto-format with ruff** - run `make format` to fix most style issues automatically
- **Packages**: estout, etc. (see `env/stata-packages.txt`)
- **Location**: `.stata/ado/plus/` (local to repo)
- **Usage**: `env/scripts/runstata script.do`
- **Requirement**: System Stata installation (not auto-installed)

### Environment Installation
```bash
make environment              # Installs all languages
make -C env python-env        # Python only
make -C env julia-install-via-python  # Julia packages only
make -C env stata-packages    # Stata packages only (if Stata installed)
```

## Integration Points

- **paper/ as separate git repo**: In production, `paper/` should be its own git repo (ignored by the analysis repo) with an Overleaf remote. Publishing writes files there; you then commit/push manually.
- **No direct writes to paper/**: Never manually copy files to `paper/`. Always use `make publish` to maintain provenance chain.
- **Data inputs**: Scripts read from `data/`. Add more inputs to the `DATA` variable in Makefile and analysis script args.
- **Multi-language workflows**: Analysis scripts can be Python (`.py`), Julia (`.jl`), or Stata (`.do`). Python scripts can call Julia via juliacall for performance-critical code
  - `JULIA_PROJECT` - Sets Julia environment to `env/`
  - `JULIA_DEPOT_PATH` - Local package depot (`.julia/` not `~/.julia/`)
  - `PYTHON_JULIAPKG_EXE` - Points to bundled Julia binary
  - `PYTHON_JULIAPKG_PROJECT` - Julia packages location for juliacall

**`env/scripts/runjulia`**:
- Points to bundled Julia at `.julia/pyjuliapkg/install/bin/julia`
- Sets `JULIA_PROJECT=env/` for project environment
- Sets `JULIA_DEPOT_PATH=.julia/` for local packages

**`env/scripts/runstata`**:
- Sets `PLUS` adopath to `.stata/ado/plus/` for local package installation
- Runs Stata in batch mode for scripting
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

1. Create `build_<name>.py` following the pattern in [build_price_base.py](build_price_base.py)
2. Add `<name>` to the `ARTIFACTS` variable in [Makefile](Makefile) (line 6)
3. Build with `make <name>`
4. Publish with `make publish PUBLISH_ARTIFACTS="<name>"`
