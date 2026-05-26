# Environment notes

## Setup

### Standard Setup (Recommended)

Run once to install Python, Julia, and Stata packages:

```bash
make environment
```

This creates:
- `.venv/`: Python 3.11 uv-managed virtualenv
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
- Julia + uv + GNU tools
- Isolated environment (doesn't affect system)
- Automatic `JULIA_PROJECT` and `JULIA_DEPOT_PATH` configuration
- Optional CUDA toolkit (`.#gpu` shell)

**Note**: Nix shell provides system tools, but you still need to run `make environment` inside the shell to install Python/Julia packages.

## Components

- `pyproject.toml`: Python dependencies (exact versions pinned in `uv.lock`)
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
- `env/scripts/runpython`: Wrapper that activates the uv virtualenv and configures Julia/Python bridge
- `env/scripts/runstata`: Wrapper that runs Stata with local package path
- `env/scripts/execute.ado`: Stata helper for running .do files with logging
- `env/scripts/install_uv.sh`: Auto-installs uv if not found
- `env/scripts/install_julia.py`: Triggers Julia installation via juliacall
- `lib/repro-tools/`: Git submodule with reproducibility tools (installed in editable mode)

**See also:** [docs/repro_tools_submodule.md](repro_tools_submodule.md) for details on the repro-tools git submodule.

## Python/Julia Integration

The `runpython` wrapper:
- Activates the `.venv` Python environment
- Configures `JULIA_PROJECT` to point to `env/`
- Sets `PYTHON_JULIAPKG_EXE` to use the bundled Julia in `.julia/pyjuliapkg/`
- Prevents juliacall from downloading a duplicate Julia

## Reproducibility

For exact reproducibility:
- Python: `pyproject.toml` declares dependencies; `uv.lock` pins exact versions for full reproducibility
- Julia: `env/Manifest.toml` provides exact version locking
- Stata: `env/stata-packages.txt` specifies package names and optional versions
- All are captured in per-artifact provenance via `repro_tools`

## Alternative Environment Managers

### Why uv (Current Default)?

**Target audience**: Academic researchers

**Advantages**:
- ✅ **Fast**: Rust-based resolver/installer, ~10-100x faster than pip/conda
- ✅ **Reproducible**: `uv.lock` pins exact versions with hashes
- ✅ **Standard tooling**: Plain `pyproject.toml`, no custom YAML format
- ✅ **Lightweight**: Single static binary, easy to auto-install
- ✅ **Manages Python itself**: Can fetch the required Python interpreter

**Limitations**:
- ⚠️ Python-only (Julia handled separately via juliacall, Stata via local packages)
- ⚠️ Newer than conda, smaller (but fast-growing) community

### Considered Alternatives

#### conda/micromamba (Previous Default)

**What it is**: Multi-language package manager using conda-forge

**Why not used now**:
- ❌ Slower environment resolution than uv
- ❌ Heavier install and larger footprint
- ❌ Custom `environment.yml`/`python.yml` format rather than standard `pyproject.toml`

**Use case**: Projects that need conda-forge binary packages or non-Python (R, system libs) dependencies beyond Julia/Stata.

#### pixi (the conda-world analogue to uv — the main "what if" alternative)

**What it is**: A Rust-based environment manager from Prefix.dev — effectively "uv for the conda ecosystem." It installs **conda-forge** packages (so it *can* manage system libraries, R, and even Julia itself, which uv cannot) **and** PyPI packages — and it **uses uv internally** for the PyPI side. It produces a cross-platform `pixi.lock` and has a built-in task runner. In short, it's the *modern* conda option; if we ever needed conda-forge, pixi (not classic conda) is what we'd reach for.

**Why uv instead, today**: every dependency here is on PyPI, Julia comes via juliacall, and Stata is external — so conda-forge's breadth isn't needed and uv is simpler.

**Would migrating be cheap since pixi uses uv internally? No.** "Uses uv internally" makes the *dependency resolution* cheap, but that was never the cost. Switching means redoing the same plumbing the conda→uv migration touched: `env/Makefile`, the `run*` wrappers (interpreter path → `.pixi/envs/…`), the installer script, `check_prerequisites.sh`, `flake.nix`, CI, tests, `.gitignore`, the `Dockerfile`, the repro-tools submodule's `common.mk`, and a full doc sweep. The `pyproject.toml` dependency list carries over (pixi reads it), but `uv.lock` → a regenerated `pixi.lock`. That's roughly the effort of the conda→uv migration — for **~no gain if pixi only replaces the Python layer**.

**When pixi would actually be worth it** (the real win a Python-only swap does *not* deliver): managing **Python and Julia together from conda-forge** — one lockfile across both languages, and likely **eliminating the `juliacall`/OpenSSL→Julia-version coupling** documented in [julia_python_integration.md](julia_python_integration.md) (conda-forge would manage OpenSSL coherently for both, so no `<=python` mismatch / macOS-1.11-vs-Linux-1.12 split). That is a **Julia-bridge rearchitecture** (move off juliacall's `juliapkg` to conda-forge Julia + PythonCall) and would still keep Make for grouped-target builds — a multi-day, higher-risk change. **Reconsider pixi if** you hit that Julia/OpenSSL coupling again, or need a conda-forge-only system package.

Because pixi speaks `pyproject.toml` and uses uv, a *future* uv→pixi move is cheaper than the old conda→pixi would have been — so staying on uv now loses nothing.

#### Nix (Already Supported as Optional)

**What it is**: Declarative package manager with true reproducibility

**Current support**: `flake.nix` provides optional dev shell

**Use case**:
- Dev shell with system tools (julia, uv, GNU make)
- True bit-for-bit reproducibility across platforms
- Optional, not required

**Why optional not required**:
- ❌ Steep learning curve
- ❌ Not familiar to most academic researchers
- ❌ Many HPC clusters don't allow Nix
- ❌ Harder to debug when things break

**Recommendation**: Use Nix if you're already familiar with it; stick with uv otherwise.

### Summary

| Tool | Multi-Language | Speed | Academic Adoption | Status |
|------|---------------|-------|------------------|--------|
| **uv** | ❌ Python-only | ✅ Fast | ⚠️ Growing | **Default** |
| **conda/micromamba** | ✅ | ⚠️ Slow | ✅ Very High | Previous default |
| **pixi** | ✅ | ✅ Fast | ⚠️ Low | Future option |
| **Nix** | ✅ | ⚠️ Moderate | ❌ Very Low | Optional |

**Philosophy**: Prioritize **fast, reproducible Python environments** built on standard `pyproject.toml`/`uv.lock`, while keeping Julia and Stata handled by their own tooling.

## Examples

Test the environment with sample scripts:

```bash
make examples              # Run Python + Julia examples
make sample-python         # Python only
make sample-julia          # Julia only
make sample-stata          # Stata only (if installed)
```
