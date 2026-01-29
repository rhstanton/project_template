# Julia/Python Integration

This document explains how Julia and Python environments are integrated in this template.

## Overview

The template supports three modes of Python/Julia interaction:

1. **Pure Python**: Use Python libraries directly
2. **Pure Julia**: Run Julia scripts via `runjulia` wrapper
3. **Python ↔ Julia interop**: Call Julia from Python (or vice versa) via juliacall/PythonCall

## Architecture

> **⚠️ CRITICAL: PythonCall Must NOT Be In env/Project.toml**
> 
> This is the #1 most common mistake that causes installation failures!
> 
> **DO NOT** add `PythonCall` to your `env/Project.toml` dependencies. PythonCall is
> managed by juliacall in `.julia/pyjuliapkg/` and should ONLY exist there.
> 
> **Symptom if you do this wrong:**
> ```
> ERROR: ArgumentError: Package PythonCall [6099a3de-...] is required but
> does not seem to be installed
> ```
> 
> **Why this happens:** When PythonCall is in `env/Project.toml`, Julia looks for it
> in the `env/` project but it's actually installed in `.julia/pyjuliapkg/`. This
> creates a mismatch that breaks the installation.
> 
> **The two projects:**
> - `.julia/pyjuliapkg/` - juliacall's managed environment (contains PythonCall)
> - `env/` - Your analysis packages (DataFrames, FixedEffectModels, etc.)

### Julia Installation

Julia is **automatically installed** via the `juliacall` Python package:

```bash
make environment
# → Installs conda environment with juliacall
# → juliacall downloads Julia to .julia/pyjuliapkg/install/
# → No manual Julia installation needed
```

**Location**: `.julia/pyjuliapkg/install/bin/julia`

**Version**: Julia 1.10-1.12 (determined by juliacall)

### Environment Variables

Critical variables for Julia/Python bridge:

```bash
# Disable CondaPkg (use main Python environment)
export JULIA_CONDAPKG_BACKEND=Null

# Point PythonCall to conda Python
export JULIA_PYTHONCALL_EXE="$REPO_ROOT/.env/bin/python"

# Julia project location
export JULIA_PROJECT="$REPO_ROOT/env"

# Julia package depot (local to repo)
export JULIA_DEPOT_PATH="$REPO_ROOT/.julia"

# Add shared juliapkg project to load path
export JULIA_LOAD_PATH="$JULIA_PROJECT:$PYTHON_JULIAPKG_PROJECT:@stdlib"

# Point juliacall to bundled Julia
export PYTHON_JULIAPKG_EXE="$REPO_ROOT/.julia/pyjuliapkg/install/bin/julia"

# Julia packages location for juliacall
export PYTHON_JULIAPKG_PROJECT="$REPO_ROOT/.julia"
```

These are set automatically by:
- `env/scripts/runpython` (for Python scripts)
- `env/scripts/runjulia` (for Julia scripts)

## The CondaPkg Problem

**Problem**: By default, PythonCall.jl uses CondaPkg to create its own isolated conda environment at `env/.CondaPkg/.pixi/`.

This creates redundancy:
- Main Python: `.env/` (~2GB)
- CondaPkg Python: `env/.CondaPkg/.pixi/` (~500MB)
- Two separate Python installations with duplicate packages

**Solution**: Set `JULIA_CONDAPKG_BACKEND=Null` to disable CondaPkg and use the main Python environment.

**Benefits**:
- ✅ Single Python environment
- ✅ Saves ~500MB disk space
- ✅ Faster installation
- ✅ Consistent packages everywhere
- ✅ Simpler debugging

## Usage Patterns

### 1. Pure Python

Standard Python scripts:

```bash
env/scripts/runpython my_script.py
```

Or activate conda environment:
```bash
conda activate .env
python my_script.py
```

### 2. Pure Julia

Julia scripts using the bundled Julia:

```bash
env/scripts/runjulia my_script.jl
```

Example (`env/examples/sample_julia.jl`):
```julia
using DataFrames

# Create sample data
df = DataFrame(
    x = 1:10,
    y = rand(10)
)

println(df)
println("Mean of y: ", mean(df.y))
```

### 3. Python → Julia (via juliacall)

Call Julia code from Python:

```python
from juliacall import Main as jl

# Load Julia packages
jl.seval("using DataFrames")

# Create Julia DataFrame
df = jl.DataFrame(x=[1,2,3], y=[4,5,6])

# Call Julia functions
mean_y = jl.mean(df.y)
```

Example script: `env/examples/sample_juliacall.py`

### 4. Julia → Python (via PythonCall)

Call Python code from Julia:

```julia
using PythonCall

# Import Python modules
pd = pyimport("pandas")
np = pyimport("numpy")

# Use Python libraries
arr = np.array([1, 2, 3])
df = pd.DataFrame(Dict("x" => [1,2,3], "y" => [4,5,6]))
```

## Package Management

### Python Packages

Managed via `env/python.yml`:

```yaml
dependencies:
  - python=3.11
  - pandas
  - matplotlib
  - pyyaml
  - jinja2
  - pip:
    - juliacall>=0.9.14
```

Install/update:
```bash
make -C env python-env
```

### Julia Packages

Managed via `env/Project.toml`:

```toml
[deps]
PythonCall = "6099a3de-0909-46bc-b1f4-468b9a2dfc0d"
DataFrames = "a93c6f00-e57d-5684-b7b6-d8193f3e46c0"

[compat]
julia = "1.10, 1.11, 1.12"
PythonCall = "0.9"
DataFrames = "1"
```

**Important**: Do NOT include `name`, `uuid`, `version` fields - this is an environment, not a package.

Install/update:
```bash
make -C env julia-install-via-python
```

## Directory Structure

```
.julia/
├── pyjuliapkg/           # Julia installed by juliacall
│   └── install/
│       └── bin/julia     # Julia binary
├── packages/             # Installed packages
├── compiled/             # Precompiled cache
└── environments/         # Environment-specific data
```

**Git status**: Entire `.julia/` is in `.gitignore`

## Troubleshooting

### "No module named 'juliacall'"

Julia not installed yet:
```bash
make -C env python-env    # Install juliacall
```

### "CondaPkg is trying to install packages"

CondaPkg not disabled:
```bash
# Check environment variables
env | grep JULIA_CONDAPKG_BACKEND
# Should be: JULIA_CONDAPKG_BACKEND=Null

# If using scripts directly (not via make):
export JULIA_CONDAPKG_BACKEND=Null
```

### "LoadError: ArgumentError: Package PythonCall not found"

Julia packages not installed:
```bash
make -C env julia-install-via-python
```

### Julia precompilation fails

Clear cache and retry:
```bash
rm -rf .julia/compiled
rm -rf env/Manifest.toml
make -C env julia-install-via-python
```

### "Project.toml is for a package, not an environment"

The `env/Project.toml` should NOT have these fields:
```toml
# BAD - remove these:
name = "..."
uuid = "..."
version = "..."
```

Only keep `[deps]` and `[compat]` sections.

## Environment Wrappers

### runpython

Sets up Julia bridge before running Python:

```bash
#!/usr/bin/env bash
# Find repo root
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="$REPO_ROOT/.env/bin/python"

# Julia/Python bridge configuration
export PYTHON_JULIACALL_HANDLE_SIGNALS=yes
export PYTHON_JULIAPKG_PROJECT="$REPO_ROOT/.julia"
export JULIA_PROJECT="$REPO_ROOT/env"
export JULIA_DEPOT_PATH="$REPO_ROOT/.julia"
export JULIA_CONDAPKG_BACKEND=Null
export JULIA_PYTHONCALL_EXE="$PYTHON_BIN"

# Add repo root to PYTHONPATH
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec "$PYTHON_BIN" -u "$@"
```

**Key configuration details**:

- `PYTHON_JULIACALL_HANDLE_SIGNALS=yes`: **Prevents segfaults** by letting Python handle system signals instead of Julia. Without this, Julia and Python can conflict over signal handling (SIGINT, SIGTERM, etc.), causing crashes.
- `PYTHON_JULIAPKG_PROJECT`: Points to `.julia/` where juliacall creates the `pyjuliapkg/` subdirectory
- `JULIA_PROJECT`: Points to `env/` for user packages (DataFrames, etc.)
- `JULIA_DEPOT_PATH`: Local package depot (not `~/.julia/`)
- `JULIA_CONDAPKG_BACKEND=Null`: Disables CondaPkg to avoid duplicate Python environments
- `JULIA_PYTHONCALL_EXE`: Points to conda Python so PythonCall uses correct interpreter

### runjulia

Points to bundled Julia and sets project:

```bash
#!/usr/bin/env bash
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUNDLED_JULIA="$REPO_ROOT/.julia/pyjuliapkg/install/bin/julia"

if [[ ! -x "$BUNDLED_JULIA" ]]; then
  echo "❌ Julia not found. Run: make environment"
  exit 1
fi

export JULIA_PROJECT="$REPO_ROOT/env"
export JULIA_DEPOT_PATH="$REPO_ROOT/.julia"

exec "$BUNDLED_JULIA" --project="$JULIA_PROJECT" "$@"
```

## Best Practices

1. **Always use wrappers**: `env/scripts/runpython` or `env/scripts/runjulia`, not bare `python` or `julia`
2. **Keep environments separate**: Don't install Julia packages via juliacall in scripts (use `env/Project.toml`)
3. **Disable CondaPkg**: Always set `JULIA_CONDAPKG_BACKEND=Null`
4. **Local depot**: Keep `.julia/` in repo root, not global `~/.julia/`
5. **Version control**: Commit `env/Project.toml` but NOT `env/Manifest.toml` (platform-specific)

## Performance Considerations

### First Call Overhead

The first juliacall import in a Python session takes ~5-10 seconds:
- Loading Julia runtime
- Precompiling packages
- Initializing bridge

Subsequent calls are fast (~milliseconds).

**Mitigation**: Use juliacall for computationally intensive tasks where startup overhead is amortized.

### Data Transfer

Converting between Python and Julia objects has overhead:
- Small arrays (<1000 elements): negligible
- Large arrays (>1M elements): can be significant
- DataFrames: moderate overhead

**Mitigation**: 
- Do bulk operations in one language
- Minimize back-and-forth conversions
- Consider pure Julia for large-scale numerical work

## Advanced: GPU Support

The template is configured for CPU-only operation. To add GPU support:

1. **Set environment variables** before `make environment`:
   ```bash
   export JULIA_ENABLE_CUDA=1
   export GPU_CUDA_MAJOR=12  # or 13
   make environment
   ```

2. **Add CUDA.jl** to `env/Project.toml`:
   ```toml
   [deps]
   CUDA = "052768ef-5323-5732-b1bb-66c8b64840ba"
   ```

3. **Install CUDA-enabled Python packages** (optional):
   ```yaml
   # env/python.yml
   pip:
     - torch  # with CUDA support
     - jax[cuda12]
   ```

**Note**: GPU support not included by default to keep template simple and portable.

## References

- [juliacall documentation](https://juliapy.github.io/PythonCall.jl/stable/)
- [PythonCall.jl documentation](https://juliapy.github.io/PythonCall.jl/stable/)
- [CondaPkg.jl](https://github.com/JuliaPy/CondaPkg.jl)
- [Julia environment variables](https://docs.julialang.org/en/v1/manual/environment-variables/)
