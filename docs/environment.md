# Environment notes

## Setup

### Standard Setup (Recommended)

Run once to install Python, Julia, and Stata packages:

```bash
make environment
```

This creates:
- `.env/`: Python 3.11 environment with conda/micromamba
- `.julia/`: Julia depot with packages via juliacall
- `.stata/`: Stata packages (reghdfe, ftools, estout) if Stata is installed
- `lib/repro-tools/`: Git submodule with reproducibility tools (auto-initialized)

**Note:** Git submodules are automatically initialized. The first run downloads repro-tools from GitHub.

### Alternative: Nix Development Shell (Optional)

If you have Nix installed, you can use the provided flake for a reproducible environment:

```bash
nix develop              # Enter default shell (CPU)
nix develop .#gpu        # GPU-enabled shell (Linux only)
```

The Nix shell provides:
- Julia + micromamba + GNU tools
- Isolated environment (doesn't affect system)
- Automatic `JULIA_PROJECT` and `JULIA_DEPOT_PATH` configuration
- Optional CUDA toolkit (`.#gpu` shell)

**Note**: Nix shell provides system tools, but you still need to run `make environment` inside the shell to install Python/Julia packages.

## Components

- `env/python.yml`: conda environment spec
  - Core: Python 3.11, pandas, numpy, matplotlib, scipy
  - Data tools: ibis-framework, python-duckdb, pyarrow
  - Interactive: ipython, notebook, jupyterlab, ipywidgets
  - Quality: ruff, black, mypy, pytest
  - Type stubs: types-docopt, pandas-stubs, scipy-stubs
  - Bridge: juliacall (Python/Julia interop)
- `env/Project.toml`: Julia dependencies
  - Core: PythonCall, DataFrames
  - Stats: Distributions, StatsModels, FixedEffectModels
  - Data: Arrow, RDatasets
  - Utils: Adapt (GPU), OpenSSL_jll
- `env/Manifest.toml`: Julia lockfile (auto-generated during `make environment`)
- `env/stata-packages.txt`: Stata packages (reghdfe, ftools, estout 3.1.2, coefplot 2.0.0)
- `env/scripts/runpython`: Wrapper that activates conda env and configures Julia/Python bridge
- `env/scripts/runstata`: Wrapper that runs Stata with local package path
- `env/scripts/execute.ado`: Stata helper for running .do files with logging
- `env/scripts/install_micromamba.sh`: Auto-installs micromamba if conda not found
- `env/scripts/install_julia.py`: Triggers Julia installation via juliacall
- `lib/repro-tools/`: Git submodule with reproducibility tools (installed in editable mode)

**See also:** [docs/repro_tools_submodule.md](repro_tools_submodule.md) for details on the repro-tools git submodule.

## Python/Julia Integration

The `runpython` wrapper:
- Activates the `.env` Python environment
- Configures `JULIA_PROJECT` to point to `env/`
- Sets `PYTHON_JULIAPKG_EXE` to use the bundled Julia in `.julia/pyjuliapkg/`
- Prevents juliacall from downloading a duplicate Julia

## Reproducibility

For exact reproducibility:
- Python: `env/python.yml` pins major versions; consider `conda-lock` for full lockfile
- Julia: `env/Manifest.toml` provides exact version locking
- Stata: `env/stata-packages.txt` specifies package names and optional versions
- All are captured in per-artifact provenance via `repro_tools`

## Alternative Environment Managers

### Why Conda/Micromamba (Current Default)?

**Target audience**: Academic researchers

**Advantages**:
- ✅ **Multi-language**: Handles Python, Julia packages, R, system libraries
- ✅ **Widely adopted**: Standard in scientific computing
- ✅ **Large ecosystem**: conda-forge has 20,000+ packages
- ✅ **Binary packages**: No compilation needed
- ✅ **Familiar**: Most researchers already know conda

**Limitations**:
- ⚠️ Slower than modern alternatives
- ⚠️ Lockfiles less robust than newer tools
- ⚠️ Environment resolution can be slow

### Considered Alternatives

#### uv (Not Implemented)

**What it is**: Fast Python package installer (Rust-based, ~10-100x faster than pip)

**Why not used**:
- ❌ **Python-only** - Cannot handle Julia, Stata, or binary dependencies
- ❌ Missing conda-forge packages
- ❌ juliacall setup requires conda Python
- ❌ Breaking change for multi-language workflow

**Use case**: Pure Python projects without Julia/Stata

#### pixi (Future Consideration)

**What it is**: Modern conda-compatible package manager (Rust-based, from Prefix.dev)

**Potential advantages**:
- ✅ **Multi-language** like conda (Python + Julia + R + system libs)
- ✅ Much faster than conda/mamba
- ✅ Better lockfiles (`pixi.lock` with exact hashes)
- ✅ Drop-in replacement for conda (uses conda-forge)
- ✅ Built-in task runner (could simplify Makefile)

**Why not yet implemented**:
- ⚠️ Newer tool (less mature ecosystem)
- ⚠️ Smaller community than conda
- ⚠️ Would require converting `env/python.yml` → `pixi.toml`
- ⚠️ Additional learning curve for users

**Future**: Could add `pixi.toml` as an **optional alternative** to `env/python.yml` while keeping conda as default.

#### Nix (Already Supported as Optional)

**What it is**: Declarative package manager with true reproducibility

**Current support**: `flake.nix` provides optional dev shell

**Use case**:
- Dev shell with system tools (julia, micromamba, GNU make)
- True bit-for-bit reproducibility across platforms
- Optional, not required

**Why optional not required**:
- ❌ Steep learning curve
- ❌ Not familiar to most academic researchers
- ❌ Many HPC clusters don't allow Nix
- ❌ Harder to debug when things break

**Recommendation**: Use Nix if you're already familiar with it; stick with conda otherwise.

### Summary

| Tool | Multi-Language | Speed | Academic Adoption | Status |
|------|---------------|-------|------------------|--------|
| **conda/micromamba** | ✅ | ⚠️ Slow | ✅ Very High | **Default** |
| **uv** | ❌ Python-only | ✅ Fast | ⚠️ Growing | Not used |
| **pixi** | ✅ | ✅ Fast | ⚠️ Low | Future option |
| **Nix** | ✅ | ⚠️ Moderate | ❌ Very Low | Optional |

**Philosophy**: Prioritize **usability for researchers** over **cutting-edge tooling**. Conda is the lingua franca of scientific computing.

## Examples

Test the environment with sample scripts:

```bash
make examples              # Run Python + Julia examples
make sample-python         # Python only
make sample-julia          # Julia only
make sample-stata          # Stata only (if installed)
```
