# Platform Compatibility and System Configuration

This document covers platform-specific configuration, GPU support, and cross-platform considerations.

## Supported Platforms

### Linux

**Status**: ✅ Fully supported (primary development platform)

**Requirements**:

- GNU Make 4.3+ (for grouped targets)
- Python 3.12 (via uv)
- Git 2.0+
- GLIBC 2.17+ (for prebuilt Python wheels)

**Installation**:
```bash
# Check GNU Make version
make --version
# Should be 4.3 or higher

# If too old:
# Ubuntu/Debian:
sudo apt update && sudo apt install make

# CentOS/RHEL 8+:
sudo dnf install make
```

**Platform detection**: Automatically detected via `uname -s` in Makefile

### macOS

**Status**: ✅ Supported (tested on macOS 11+)

**Requirements**:

- macOS 11 (Big Sur) or later
- Xcode Command Line Tools (for git, make)
- Homebrew (optional, for GNU Make 4.3+)

**Installation**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Check Make version
make --version

# If < 4.3, install GNU Make via Homebrew:
brew install make
# Then use 'gmake' instead of 'make'
```

**Caveats**:

- Apple Silicon (M1/M2/M3): All Python/Julia packages work via Rosetta or native ARM builds
- GNU Make: macOS ships with Make 3.81; install via Homebrew for 4.3+
- Stata: macOS uses `stata-mp` or `stata-se` (not `stata` command)

**Platform detection**: Automatically detected via `uname -s` in Makefile

### Windows

**Status**: ⚠️ Limited support (requires WSL)

**Recommended approach**: Windows Subsystem for Linux (WSL 2)

```bash
# In PowerShell (as Administrator):
wsl --install -d Ubuntu-22.04

# Then follow Linux instructions above
```

**Native Windows**: Not officially supported due to:

- GNU Make 4.3+ availability
- Path handling differences
- Virtualenv activation
- Git line ending issues

## GPU Configuration

### CPU-Only (Default)

The template defaults to CPU-only operation for maximum compatibility:

```bash
make environment
# → No CUDA dependencies installed
# → Julia and Python run on CPU
```

This is the right setup on any machine without an NVIDIA GPU, including Apple
Silicon Macs.

### Enabling GPU Support (Julia / CUDA)

GPU acceleration is available for the Julia regression backend
(`FixedEffectModels.jl` via CUDA.jl), used by `run_did.py`. Install it with a
single environment variable:

```bash
JULIA_ENABLE_CUDA=1 make environment
```

**What this does:**

- Installs CUDA.jl into a separate, **gitignored, machine-local** Julia
  environment at `.julia/gpu-env/`. The committed `env/Project.toml` is *not*
  modified, so the project stays portable (a non-GPU machine such as a Mac never
  installs CUDA) and the working tree stays clean for `make publish`.
- `run_did.py` automatically layers `.julia/gpu-env` onto `JULIA_LOAD_PATH` when
  that directory exists, so `using CUDA` resolves only where it was installed.

There is no Python GPU stack (PyTorch/JAX/CuPy) in the template — GPU support is
Julia-only. CUDA.jl ships its own CUDA runtime via artifacts, so a system CUDA
toolkit / `LD_LIBRARY_PATH` is not required (only a working NVIDIA driver).

### Selecting the device at runtime

`run_did.py` chooses the device with `--use-gpu`:

| Value | Behaviour |
|-------|-----------|
| `auto` (default) | Use the GPU when CUDA.jl is functional, else fall back to CPU |
| `1` | Prefer the GPU; warn if unavailable, then use CPU |
| `0` | Force CPU; never import CUDA |

Because the default is `auto`, the same command runs on the GPU on a CUDA machine
and on the CPU everywhere else — no flags or manual edits needed. The GPU path
keeps `double_precision=true` (Float64), so results match the CPU path.

### Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `JULIA_ENABLE_CUDA` | `0` | Install CUDA.jl into `.julia/gpu-env` during `make environment` |
| `JULIA_CONDAPKG_BACKEND` | `Null` | Disable CondaPkg duplicate Python |
| `JULIA_PYTHONCALL_EXE` | `.venv/bin/python` | Python executable for PythonCall |
| `JULIA_PROJECT` | `env/` | Julia environment location |
| `JULIA_DEPOT_PATH` | `.julia/` | Local package depot (not `~/.julia/`) |

### GPU Verification

After `JULIA_ENABLE_CUDA=1 make environment`:

```bash
env/scripts/runpython run_did.py --use-gpu=1
# Expect: ✓ GPU acceleration enabled (method=:CUDA, Float64) on <your GPU>
```

Check the driver directly with `nvidia-smi` (CUDA.jl needs a working NVIDIA
driver; a system `nvcc` is optional).

### GPU Troubleshooting

**CUDA reports not functional, or precompilation fails:** confirm the driver
works (`nvidia-smi`), then rebuild the GPU environment from scratch:

```bash
rm -rf .julia/gpu-env .julia/compiled
JULIA_ENABLE_CUDA=1 make environment
```

## Cross-Platform File Sharing

### Git Line Endings

**Problem**: Windows uses CRLF (`\r\n`), Linux/macOS use LF (`\n`)

**Solution**: Configure Git to handle line endings:

```bash
# Linux/macOS - always use LF:
git config core.autocrlf input

# Windows (if not using WSL):
git config core.autocrlf true
```

The repository includes `.gitattributes`:
```gitattributes
* text=auto
*.sh text eol=lf
*.py text eol=lf
*.jl text eol=lf
*.do text eol=lf
```

Forces Unix line endings for shell scripts and code.

### Path Separators

**Problem**: Windows uses backslashes (`\`), Unix uses forward slashes (`/`)

**Mitigation**:

- Python: Use `pathlib.Path` (cross-platform)
- Julia: Use `joinpath()` (cross-platform)
- Shell: Always use forward slashes (work on all platforms via Git Bash/WSL)

Example:
```python
from pathlib import Path

# Good (cross-platform):
data_file = Path("data") / "housing_panel.csv"

# Bad (breaks on Windows):
data_file = "data/housing_panel.csv"
```

### Manifest.toml Handling

**Problem**: Julia's `Manifest.toml` is platform-specific (includes binary artifact hashes)

**Solution**: Gitignore `Manifest.toml`:

```gitignore
# .gitignore
env/Manifest.toml
```

Each platform regenerates its own Manifest:
```bash
make -C env julia-install-via-python
# → Generates platform-specific Manifest.toml
```

**Pros**:

- No merge conflicts between platforms
- Each platform uses optimal binaries

**Cons**:

- Slightly different dependency resolution
- Must regenerate on new platform

### Python Environment Portability

**Recommendation**: Declare dependencies in `pyproject.toml` and commit `uv.lock` for reproducible, cross-platform resolution.

```toml
# pyproject.toml (cross-platform)
[project]
name = "project_template"
requires-python = ">=3.12"
dependencies = [
    "pandas",
    "matplotlib",
]
```

`uv.lock` records exact versions and hashes; `uv sync` reproduces the same environment on any supported platform.

## Julia Precompilation Issues

### Error: "Cannot execute native code"

**Cause**: Julia precompiled on different platform or with different GPU config

**Solution**: Clear cache and recompile:
```bash
rm -rf .julia/compiled
make -C env julia-install-via-python
```

### Error: "Package X not found in current path"

**Cause**: `Manifest.toml` from different platform

**Solution**: Regenerate Manifest:
```bash
rm -f env/Manifest.toml
make -C env julia-install-via-python
```

### Slow first run

Julia compiles code Just-In-Time (JIT). First run is slow, subsequent runs are fast.

**Mitigation**: Use `--compile=min` for scripting tasks where startup time matters:
```bash
env/scripts/runjulia --compile=min my_script.jl
```

Or precompile packages:
```bash
env/scripts/runjulia -e 'using Pkg; Pkg.precompile()'
```

## System Requirements Summary

### Minimum

- **CPU**: x86_64 (Intel/AMD) or ARM64 (Apple Silicon)
- **RAM**: 8GB
- **Disk**: 5GB free (2GB environment + 3GB cache)
- **OS**: Linux (GLIBC 2.17+), macOS 11+, or Windows 10+ with WSL 2

### Recommended

- **CPU**: 4+ cores
- **RAM**: 16GB (for large datasets)
- **Disk**: 10GB free (allows multiple environments)
- **OS**: Ubuntu 22.04 LTS or macOS 13+

### For GPU Support

- **GPU**: NVIDIA GPU with CUDA Compute Capability 5.0+
- **CUDA**: 12.x or 13.x
- **VRAM**: 4GB minimum (8GB+ recommended)
- **Driver**: NVIDIA driver 525+ (for CUDA 12) or 545+ (for CUDA 13)

## Environment Activation

### Via virtualenv

```bash
# Activate (works on all platforms):
source .venv/bin/activate

# Deactivate:
deactivate
```

### Via Makefile

```bash
# Uses environment wrappers automatically:
make all
make price_base
```

### Direct script execution

```bash
# Python:
env/scripts/runpython my_script.py

# Julia:
env/scripts/runjulia my_script.jl

# Stata (if installed):
env/scripts/runstata my_script.do
```

## Clock Skew Warnings

You may see warnings like:
```
make: Warning: File 'foo.py' has modification time in the future
```

**Cause**: Files extracted from zip archives may have future timestamps (common with ChatGPT attachments)

**Impact**: Harmless - Make still works correctly

**Fix** (optional):
```bash
# Reset all timestamps to current time:
find . -type f -exec touch {} +
```

## Debugging Environment Issues

### Check platform detection

```bash
uname -s
# Linux → Linux
# Darwin → macOS
```

### Check Python environment

```bash
ls -d .venv
# Should show .venv in repo root
.venv/bin/python --version
```

### Check Julia installation

```bash
ls -la .julia/pyjuliapkg/install/bin/julia
# Should exist if environment installed
```

### Check environment variables

```bash
env/scripts/runpython -c 'import os; print(os.environ["JULIA_CONDAPKG_BACKEND"])'
# Should print: Null
```

### Verify package installation

```bash
# Python packages:
uv pip list

# Julia packages:
env/scripts/runjulia -e 'using Pkg; Pkg.status()'
```

## CI/CD Considerations

### GitHub Actions

Example workflow for Linux:

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup environment
        run: make environment
      
      - name: Run all builds
        run: make all
      
      - name: Check provenance
        run: ls -la output/provenance/
```

**Note**: Use `runs-on: macos-latest` for macOS testing

### Docker

The template ships a **digest-pinned, uv-based `Dockerfile`** at the repo root:

```bash
docker build -t project-template-repro .
docker run --rm -v "$PWD/output:/project/output" project-template-repro
```

It builds the environment with uv (`pyproject.toml` + `uv.lock`) and juliacall, then
reproduces all artifacts. On Debian (Python links OpenSSL 3.5) juliapkg installs Julia
1.12 automatically. Stata is omitted (commercial license). For a reviewer-standard
`linux/amd64` image on Apple Silicon, add `--platform linux/amd64` to the build.

## Security Considerations

### Local-Only Environments

The template installs packages to `.venv/` and `.julia/` **within the repo**, not globally.

**Benefits**:

- No pollution of global environment
- Full control over versions
- Easy cleanup (`rm -rf .venv .julia`)
- Reproducible across machines

**Caveat**: Each project needs its own environment (~2GB disk space per project)

### Git Secrets

Never commit to `.venv/` or `.julia/` directories (they're in `.gitignore`).

Also check that `paper/` (if separate repo) doesn't leak credentials.

## Performance Tuning

### Parallelism

Enable parallel builds:
```bash
make -j4 all  # Use 4 cores
```

**Note**: Only works for independent targets (e.g., `price_base` and `remodel_base`)

### Compilation Caching

Julia caches compiled code in `.julia/compiled/`. Do NOT delete unless troubleshooting.

Python uses `__pycache__/`. Safe to delete but will slow down subsequent runs.

### Disk Space Optimization

The environment requires ~2GB. To reduce:

1. **Remove unused packages** from `pyproject.toml` (then `uv sync`)
2. **Clean uv cache**: `uv cache clean`
3. **Remove old Julia depot**: `rm -rf ~/.julia` (if you use local depot)

---

**See also**:

- [docs/environment.md](environment.md) for installation details
- [docs/julia_python_integration.md](julia_python_integration.md) for Julia/Python bridge
- [README.md](../README.md) for quick start
