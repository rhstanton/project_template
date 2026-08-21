# Environment notes

## Setup

### Standard Setup (Recommended)

Run once to install Python, Julia, and Stata packages:

```bash
make environment
```

This creates:
- `.venv/`: Python 3.12 uv-managed virtualenv
<!-- julia:start -->
- `.julia/`: Julia depot with packages via juliacall
<!-- julia:end -->
<!-- stata:start -->
- `.stata/`: Stata packages (reghdfe, ftools, estout) if Stata is installed
<!-- stata:end -->
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
<!-- julia:start -->
- Automatic `JULIA_PROJECT` and `JULIA_DEPOT_PATH` configuration
<!-- julia:end -->
- Optional CUDA toolkit (`.#gpu` shell)

**Note**: Nix shell provides system tools, but you still need to run `make environment` inside the shell to install Python/Julia packages.

## Components

- `pyproject.toml`: Python dependencies (exact versions pinned in `uv.lock`)
  - Core: Python 3.12, pandas, numpy, matplotlib, scipy
  - Data tools: ibis-framework, python-duckdb, pyarrow
  - Interactive: ipython, notebook, jupyterlab, ipywidgets
  - Quality: ruff, black, mypy, pytest
  - Type stubs: types-docopt, pandas-stubs, scipy-stubs
<!-- julia:start -->
  - Bridge: juliacall (Python/Julia interop)
<!-- julia:end -->
<!-- julia:start -->
- `env/Project.toml`: Julia dependencies
  - Core: PythonCall, DataFrames
  - Stats: Distributions, StatsModels, FixedEffectModels
  - Data: Arrow, RDatasets
  - Utils: Adapt (GPU), OpenSSL_jll
- `env/Manifest.toml`: Julia lockfile — **committed**, not regenerated per build.
  `Project.toml` alone admits any `FixedEffectModels` 1.x, so the Manifest is
  what actually pins.
- `env/juliapkg.json`: pins the Julia **binary** version, which `Project.toml`
  cannot. Copied into the juliapkg project before install.
<!-- julia:end -->
<!-- stata:start -->
- `env/stata-packages.txt`: Stata package **names only**, no versions — see
  [Stata packages](#stata-packages).
- `env/stata-requirements.txt`: the version record, generated from what is
  installed and verified by `make stata-check`.
<!-- stata:end -->
- `env/env.sh`: **the single source of truth for the environment.** Every wrapper
  and `.envrc` sources it; none declares environment variables of its own.
- `env/scripts/runpython`, `runnotebook`: thin wrappers that source
  `env/env.sh` and exec.
<!-- julia:start -->
- `env/scripts/runjulia`: the same wrapper for Julia.
<!-- julia:end -->
<!-- stata:start -->
- `env/scripts/runstata`: the same wrapper for Stata.
<!-- stata:end -->
<!-- stata:start -->
- `env/scripts/execute.ado`: Stata helper for running .do files with logging
<!-- stata:end -->
- `env/scripts/install_uv.sh`: Auto-installs uv if not found
<!-- julia:start -->
- `env/scripts/install_julia.py`: Triggers Julia installation via juliacall
<!-- julia:end -->
- `lib/repro-tools/`: Git submodule with reproducibility tools (editable install).
  Also holds the **shared half** of the environment,
  `src/repro_tools/lib/env.sh`, so environment fixes reach projects generated
  before the fix existed.

**See also:** [docs/repro_tools_submodule.md](repro_tools_submodule.md) for details on the repro-tools git submodule.

## Where the environment is defined

Two files, and the split is deliberate:

| | |
|---|---|
| `lib/repro-tools/src/repro_tools/lib/env.sh` | Toolchain: which Python, which Julia, how they bridge. Identical in every project, so it lives in the submodule and **updates**. |
| `env/env.sh` | Project-specific: `DATA_DIR`, `PYTHONPATH`, `env/local.sh`. Yours to edit. |

Machinery copied into a project at creation is frozen there forever. Every
environment bug found in this template so far has been in the toolchain half, so
that half lives where a fix can propagate: update the submodule, get the fix.

Two rules that look like style but are not:

- **Sourced vs executed decides how you handle `CDPATH`.** A script that is
  *executed* uses `unset CDPATH`. A file that is *sourced* must instead use
  `CDPATH= cd -- ...` inside the command substitution, because `unset` in a
  sourced file mutates the caller's interactive shell. When `cd` resolves through
  `CDPATH` it echoes the directory, and inside `$( )` that lands in your variable
  — so the repo root silently becomes two newline-separated paths, and the damage
  surfaces much later as a missing module or a second Julia depot.
- **Project-scoped values are assigned unconditionally, never `${VAR:-default}`.**
  The `:-` form defers to whatever the calling shell holds, and the calling shell
  holds whatever project you were last in. Written that way, `DATA_DIR` once
  pointed a run in this template at *another repository's licensed data*. The
  sanctioned override is `env/local.sh`, sourced last so a deliberate choice
  still wins.

`PYTHON_JULIAPKG_EXE` follows the same logic and is the sharpest case: it is set
from this project's bundled Julia, or **unset**. Leaving an inherited value is
not neutral — building a fresh clone from a shell that still had another
checkout's environment loaded silently builds against that other project's Julia
and reports success, GPU check included.

<!-- julia:start -->
## Python/Julia Integration

`env/env.sh` (via the shared toolchain file):
- Selects `.venv/bin/python` — with no fallback, so a missing environment is an
  error rather than a quiet switch to some other interpreter
- Points `JULIA_PROJECT` at `env/` and the depot at `.julia/`
- Sets `JULIA_LOAD_PATH`, `JULIA_CONDAPKG_BACKEND=Null`, `JULIA_PYTHONCALL_EXE`
- Sets `PYTHON_JULIAPKG_EXE` to the bundled Julia, or unsets it
- Strips `juliaup` from `PATH` unconditionally, so nothing can resolve a
  different `julia` by lookup
- Pins `JULIA_NUM_THREADS=1`: thread count changes floating-point reduction
  order, so it is the only setting that gives the same answer on every machine.
  Override in `env/local.sh` when you want speed more than bit-identity.
<!-- julia:end -->

<!-- stata:start -->
<a name="stata-packages"></a>
## Stata packages

**SSC has no versioned install.** `ssc install estout 3.1.2` is not a version
request — it is a syntax error (`varlist not allowed`, r(101)) — and SSC serves
only whatever is current today. A version number in `stata-packages.txt`
therefore could not be enforced by anything, so there are none there.

The pin is the packages themselves: `.stata/ado/plus` is **committed**. This is
what the AEA Data Editor asks for — *"provide copies of such packages/modules
when the package repository does not allow you to specify a version."*

```bash
make stata-env           # installs nothing for already-vendored packages
make stata-check         # verifies the tree against env/stata-requirements.txt
make stata-requirements  # regenerate that record from what is installed
make stata-update        # deliberately refresh from SSC, then review the diff
```

`make stata-update` is the only path back to SSC, and it is never automatic: it
replaces reviewed, committed versions with whatever SSC serves today. Review
`git diff` on `.stata/ado/plus` and commit deliberately.

Stata returns exit status 0 even when a do-file aborts, so every rule here
judges success by the **log**, not by `$?`.
<!-- stata:end -->

## Reproducibility

For exact reproducibility:
- **Python**: `pyproject.toml` declares; `uv.lock` pins the full transitive closure
<!-- julia:start -->
- **Julia**: `env/Manifest.toml` pins packages, `env/juliapkg.json` pins the binary
<!-- julia:end -->
<!-- stata:start -->
- **Stata**: the ado files are committed; `env/stata-requirements.txt` records
  their versions and `make stata-check` verifies them
<!-- stata:end -->
- All are captured in per-artifact provenance via `repro_tools`

Every one of these is checkable, and there is a test for each:

```bash
pytest tests/test_environment_contract.py -v
```

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

#### pixi (the conda-world analog to uv — the main "what if" alternative)

**What it is**: A Rust-based environment manager from Prefix.dev — effectively "uv for the conda ecosystem." It installs **conda-forge** packages (so it *can* manage system libraries, R, and even Julia itself, which uv cannot) **and** PyPI packages — and it **uses uv internally** for the PyPI side. It produces a cross-platform `pixi.lock` and has a built-in task runner. In short, it's the *modern* conda option; if we ever needed conda-forge, pixi (not classic conda) is what we'd reach for.

**Why uv instead, today**: every dependency here is on PyPI, Julia comes via juliacall, and Stata is external — so conda-forge's breadth isn't needed and uv is simpler.

**Would migrating be cheap since pixi uses uv internally? No.** "Uses uv internally" makes the *dependency resolution* cheap, but that was never the cost. Switching means redoing the same plumbing the conda→uv migration touched: `env/Makefile`, the `run*` wrappers (interpreter path → `.pixi/envs/…`), the installer script, `check_prerequisites.sh`, `flake.nix`, CI, tests, `.gitignore`, the `Dockerfile`, the repro-tools submodule's `common.mk`, and a full doc sweep. The `pyproject.toml` dependency list carries over (pixi reads it), but `uv.lock` → a regenerated `pixi.lock`. That's roughly the effort of the conda→uv migration — for **~no gain if pixi only replaces the Python layer**.

<!-- julia:start -->
**When pixi would actually be worth it** (the real win a Python-only swap does *not* deliver): managing **Python and Julia together from conda-forge** — one lockfile across both languages, and likely **eliminating the `juliacall`/OpenSSL→Julia-version coupling** documented in [julia_python_integration.md](julia_python_integration.md) (conda-forge would manage OpenSSL coherently for both, so no `<=python` mismatch — the kind of coupling that forced this project onto Python 3.12 to keep Julia at 1.12 on every platform). That is a **Julia-bridge rearchitecture** (move off juliacall's `juliapkg` to conda-forge Julia + PythonCall) and would still keep Make for grouped-target builds — a multi-day, higher-risk change. **Reconsider pixi if** you hit that Julia/OpenSSL coupling again, or need a conda-forge-only system package.
<!-- julia:end -->

Because pixi speaks `pyproject.toml` and uses uv, a *future* uv→pixi move is cheaper than the old conda→pixi would have been — so staying on uv now loses nothing.

#### Nix (Already Supported as Optional)

**What it is**: Declarative package manager with true reproducibility

**Current support**: `flake.nix` provides optional dev shell

**Use case**:
- Dev shell with the system tools the project's languages need
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
make examples              # Run every example that applies
make sample-python         # Python only
```
<!-- julia:start -->
```bash
make sample-julia          # Julia only
```
<!-- julia:end -->
<!-- stata:start -->
```bash
make sample-stata          # Stata only (if installed)
```
<!-- stata:end -->
