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

- `env/python.yml`: conda environment spec (Python, pandas, matplotlib, PyYAML, juliacall)
- `env/Project.toml`: Julia dependencies (PythonCall, DataFrames)
- `env/Manifest.toml`: Julia lockfile (auto-generated during `make environment`)
- `env/stata-packages.txt`: Stata packages to install (reghdfe, ftools, estout)
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

## Examples

Test the environment with sample scripts:

```bash
make examples              # Run Python + Julia examples
make sample-python         # Python only
make sample-julia          # Julia only
make sample-stata          # Stata only (if installed)
```
