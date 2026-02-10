# Troubleshooting Guide

Quick solutions to common issues. Use the diagnostic commands below to identify problems.

---

## Quick Diagnostics

### Check Environment Installation

```bash
# Full environment check
conda env list
# Should show .env in repo root

# Python check
.env/bin/python --version
# Should be 3.11.x

# Julia check (if installed)
ls -la .julia/pyjuliapkg/install/bin/julia
# Should exist

# Package verification
.env/bin/python -c "import pandas, matplotlib, juliacall; print('OK')"
# Should print: OK
```

### Check Build Outputs

```bash
# List figures
ls -lh output/figures/
# Should show .pdf files

# List tables  
ls -lh output/tables/
# Should show .tex files

# List provenance
ls -lh output/provenance/
# Should show .yml files
```

### Check Git State

```bash
# Working tree status
git status
# Should be clean for publishing

# Branch status
git status -sb
# Check if behind origin
```

---

## Common Issues

### Make Errors

#### "make: command not found"

**Solution (Linux)**:
```bash
sudo apt update && sudo apt install make
```

**Solution (macOS)**:
```bash
brew install make
# Then use 'gmake' instead of 'make'
```

#### "make: *** No rule to make target 'all'"

**Cause**: GNU Make version too old (< 4.3)

**Check version**:
```bash
make --version
```

**Solution (macOS)**:
```bash
brew install make
alias make=gmake  # Add to ~/.bashrc or ~/.zshrc
```

**Solution (Linux)**:
```bash
# Ubuntu 22.04+:
sudo apt install make

# Older systems - build from source:
wget http://ftp.gnu.org/gnu/make/make-4.3.tar.gz
tar -xzvf make-4.3.tar.gz
cd make-4.3
./configure && make && sudo make install
```

#### Makefile syntax errors

**Check indentation**: Make requires **TAB** characters, not spaces

**Fix**:
```bash
# In vim:
:set noexpandtab
# Re-indent with TABs

# In VS Code:
# Set "editor.insertSpaces": false for Makefiles
```

---

### Environment Setup Errors

#### "warning: overriding commands for target `&`"

**Cause**: Using GNU Make < 4.3 (macOS ships with Make 3.81 from 2006)

**Error messages**:
```
Makefile:277: warning: overriding commands for target `&'
Makefile:277: warning: ignoring old commands for target `&'
```

**Impact**: The warnings are harmless but indicate Make doesn't understand grouped targets (`&:` syntax). This could cause builds to behave incorrectly (re-running scripts multiple times).

**Solution** (macOS):
```bash
# Install modern Make via Homebrew
brew install make

# Use gmake instead of make
gmake environment
gmake all
```

**Solution** (Linux - if needed):
```bash
# Most Linux distros have Make 4.3+, check version:
make --version

# If < 4.3, update:
sudo apt-get update && sudo apt-get install make  # Debian/Ubuntu
# or equivalent for your distro
```

**Verification**:
```bash
# Should show 4.3 or higher
gmake --version  # macOS
make --version   # Linux
```

#### "conda: command not found"

**Cause**: conda/mamba/micromamba not installed

**Solution**: Auto-installs during `make environment`

```bash
make -C env python-env
# Checks for conda/mamba/micromamba
# Auto-installs micromamba if none found
```

**Manual installation** (if auto-install fails):
```bash
# Micromamba (lightweight, recommended):
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
./bin/micromamba shell init -s bash -p ~/.local/share/mamba
source ~/.bashrc

# Then retry:
make environment
```

#### "No prefix found" or "Environment must first be created"

**Cause**: Using mamba/conda for first-time environment setup (fixed in latest version)

**Error message**:
```
error    libmamba No prefix found at: /path/to/project/.env
error    libmamba Environment must first be created with "mamba create -n {env_name} ..."
```

**Solution** (if using older version of this template):
```bash
# Manual workaround:
mamba env create --prefix ./.env --file env/python.yml

# Or pull latest fixes:
git pull
make environment
```

**Fixed in**: Latest version now correctly uses `env create` for initial setup and `env update` for updates, regardless of which conda-like tool is being used.

#### "No module named 'juliacall'"

**Cause**: Python environment not installed

**Solution**:
```bash
make -C env python-env
```

**Or activate and install manually**:
```bash
conda activate .env
pip install juliacall
```

#### "Julia not found"

**Cause**: Julia not installed yet (installed via juliacall)

**Solution**:
```bash
make -C env python-env                  # Install juliacall
make -C env julia-install-via-python    # Install Julia packages
```

#### "Package PythonCall does not seem to be installed"

**Cause**: `PythonCall` is listed in `env/Project.toml` (THIS IS WRONG!)

**Solution**: Remove PythonCall from `env/Project.toml`

```bash
# Check if PythonCall is in env/Project.toml
grep -i pythoncall env/Project.toml

# If found, edit env/Project.toml and remove the PythonCall line
# Then retry:
rm -rf .julia/compiled env/Manifest.toml
make -C env julia-install-via-python
```

**Why this happens**: PythonCall is managed by juliacall in `.julia/pyjuliapkg/` and
should ONLY exist there. When it's in `env/Project.toml`, Julia looks for it in the
wrong project, causing installation to fail.

**This is the #1 most common Julia installation error!**

#### "Package X not found in current path" (Julia)

**Cause**: Julia packages not installed

**Solution**:
```bash
make -C env julia-install-via-python
```

**Or clean and reinstall**:
```bash
rm -rf .julia/compiled
rm -f env/Manifest.toml
make -C env julia-install-via-python
```

---

### Build Errors

#### "ImportError: No module named 'scripts'"

**Cause**: `scripts/` not in Python path

**Solution**: Use environment wrappers (not bare Python):
```bash
# Good:
env/scripts/runpython build_price_base.py --data ...

# Bad:
python build_price_base.py --data ...
```

The `runpython` wrapper sets `PYTHONPATH` correctly.

#### "FileNotFoundError: data/housing_panel.csv"

**Cause**: Input data file missing

**Solution**: Add your data to `data/` directory
```bash
ls -lh data/
# Should show your CSV files
```

#### Matplotlib backend errors

**Error**: "Failed to allocate bitmap" or "no display name"

**Cause**: No X11 display (headless environment)

**Solution**: Use non-interactive backend

Add to analysis script:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
```

Or set environment variable:
```bash
export MPLBACKEND=Agg
make all
```

#### LaTeX table export errors

**Error**: "No module named 'jinja2'"

**Cause**: jinja2 not installed (required by pandas LaTeX export)

**Solution**:
```bash
# Check if jinja2 in env/python.yml
grep jinja2 env/python.yml

# If missing, add and reinstall:
make -C env python-env
```

---

### Publishing Errors

#### "Refusing to publish: working tree is dirty"

**Cause**: Uncommitted changes

**Check**:
```bash
git status
```

**Solution**: Commit or stash changes
```bash
git add .
git commit -m "Commit changes"
make publish
```

**Or allow dirty tree** (not recommended):
```bash
make publish ALLOW_DIRTY=1
```

#### "Refusing to publish: behind upstream"

**Cause**: Local branch not up to date

**Check**:
```bash
git status -sb
```

**Solution**: Pull updates
```bash
git pull
make publish
```

**Or allow** (not recommended):
```bash
make publish REQUIRE_NOT_BEHIND=0
```

#### "Refusing to publish: artifacts not from current HEAD"

**Cause**: Build outputs created from different commit

**Check**: Look at `output/provenance/*.yml` files
```bash
grep commit: output/provenance/price_base.yml
git rev-parse HEAD
```

**Solution**: Rebuild from current commit
```bash
make all  # Rebuild everything
make publish
```

**Or disable check** (not recommended):
```bash
make publish REQUIRE_CURRENT_HEAD=0
```

---

### Julia/Python Integration Issues

#### "CondaPkg is trying to install packages"

**Cause**: `JULIA_CONDAPKG_BACKEND` not set to `Null`

**Check**:
```bash
env/scripts/runpython -c 'import os; print(os.environ.get("JULIA_CONDAPKG_BACKEND"))'
# Should print: Null
```

**Solution**: Already set by `runpython` wrapper - use that instead of bare `python`

**If using Python directly**:
```bash
export JULIA_CONDAPKG_BACKEND=Null
conda activate .env
python my_script.py
```

#### juliacall import is slow (5-10 seconds)

**Cause**: First import loads Julia runtime and precompiles packages

**Expected behavior**: First import is slow, subsequent imports fast

**Mitigation**: Precompile packages once:
```bash
env/scripts/runjulia -e 'using Pkg; Pkg.precompile()'
```

#### Python crashes/segfaults when using juliacall

**Error**: "Segmentation fault (core dumped)" or Python process crashes during Julia operations

**Cause**: Signal handling conflicts between Julia and Python

When both Julia and Python runtimes are running in the same process, they can conflict over who handles system signals (SIGINT for Ctrl+C, SIGTERM, etc.). By default, Julia tries to install its own signal handlers, which can interfere with Python's signal handling and cause crashes.

**Solution**: Use `runpython` wrapper (already configured)

The `env/scripts/runpython` wrapper sets:
```bash
export PYTHON_JULIACALL_HANDLE_SIGNALS=yes
```

This tells juliacall to let Python handle all signals instead of Julia, preventing crashes.

**If running Python directly** (not recommended):
```bash
export PYTHON_JULIACALL_HANDLE_SIGNALS=yes
conda activate .env
python my_script.py
```

**Verification**:
```bash
# Check if variable is set:
env/scripts/runpython -c 'import os; print(os.environ.get("PYTHON_JULIACALL_HANDLE_SIGNALS"))'
# Should print: yes
```

**Related**: The `install_julia.py` script uses subprocess for package installation to isolate Julia operations from the Python process, providing additional robustness.

#### "Project.toml is for a package, not an environment"

**Cause**: `env/Project.toml` has package metadata fields

**Check**:
```bash
grep -E '^(name|uuid|version)' env/Project.toml
```

**Solution**: Remove those fields, keep only `[deps]` and `[compat]`

```toml
# BAD - remove these:
name = "MyPackage"
uuid = "..."
version = "1.0.0"

# GOOD - keep these:
[deps]
PythonCall = "6099a3de-0909-46bc-b1f4-468b9a2dfc0d"
DataFrames = "a93c6f00-e57d-5684-b7b6-d8193f3e46c0"

[compat]
julia = "1.10, 1.11, 1.12"
```

#### Julia precompilation fails with GPU errors

**Cause**: CUDA configured but GPU not available

**Solution**: Disable CUDA
```bash
rm -rf .julia/compiled
unset JULIA_ENABLE_CUDA
make -C env julia-install-via-python
```

---

### Platform-Specific Issues

#### macOS: "make version 3.81 does not support grouped targets"

**Cause**: macOS ships with ancient Make

**Solution**:
```bash
brew install make
# Use gmake instead of make:
gmake all
gmake publish
```

**Or create alias**:
```bash
echo 'alias make=gmake' >> ~/.zshrc
source ~/.zshrc
```

#### Linux: "GLIBC version too old"

**Cause**: conda packages require GLIBC 2.17+

**Check**:
```bash
ldd --version
```

**Solution**: Upgrade to Ubuntu 18.04+ or CentOS 7+

#### Windows: "command not found" errors

**Cause**: Windows not officially supported

**Solution**: Use WSL 2
```powershell
# In PowerShell as Administrator:
wsl --install -d Ubuntu-22.04
```

Then follow Linux instructions.

---

### Git Issues

#### Clock skew warnings

**Warning**: "File has modification time in the future"

**Cause**: Files extracted from zip with future timestamps (common with ChatGPT attachments)

**Impact**: Harmless - Make still works

**Fix** (optional):
```bash
find . -type f -exec touch {} +
```

#### Line ending issues (Windows)

**Error**: "bad interpreter: /usr/bin/env^M: no such file or directory"

**Cause**: CRLF line endings in shell scripts

**Solution**:
```bash
# Fix specific file:
dos2unix env/scripts/runpython

# Fix all scripts:
find env/scripts -type f -exec dos2unix {} +

# Configure git:
git config core.autocrlf input
```

---

## Performance Issues

### Builds are slow

**Check parallelism**:
```bash
# Use multiple cores:
make -j4 all  # 4 parallel jobs
```

**Note**: Only helps for independent targets

### Julia compilation is slow on first run

**Expected**: Julia uses Just-In-Time compilation

**First run**: Slow (compiles code)  
**Subsequent runs**: Fast (uses cached compilation)

**Mitigation**: Precompile packages
```bash
env/scripts/runjulia -e 'using Pkg; Pkg.precompile()'
```

### Disk space warnings

**Check usage**:
```bash
du -sh .env .julia output
```

**Clean build outputs**:
```bash
make clean  # Remove output/
```

**Clean environments** (careful - will need reinstall):
```bash
make cleanall  # Remove .env, .julia, output/
```

---

## Debugging Tips

### Enable verbose output

```bash
# Make verbose mode:
make -d all  # Show all decisions

# Python verbose mode:
env/scripts/runpython -v build_price_base.py ...
```

### Check environment variables

```bash
env/scripts/runpython -c 'import os; print("\\n".join(f"{k}={v}" for k,v in sorted(os.environ.items()) if "JULIA" in k or "PYTHON" in k))'
```

### Test Python imports

```bash
.env/bin/python -c "
import sys
print('Python:', sys.executable)
print('Version:', sys.version)

import pandas as pd
print('pandas:', pd.__version__)

import matplotlib
print('matplotlib:', matplotlib.__version__)

from juliacall import Main as jl
print('juliacall: OK')
print('Julia version:', jl.VERSION)
"
```

### Test Julia environment

```bash
env/scripts/runjulia -e '
using Pkg
println("Julia: ", VERSION)
println("Project: ", Base.active_project())
Pkg.status()
'
```

### Verify provenance records

```bash
# Check build record
cat output/provenance/price_base.yml

# Verify SHA256 hashes
sha256sum output/figures/price_base.pdf
# Compare to hash in provenance file
```

---

## Getting Help

### Check documentation

1. [README.md](../README.md) - Project overview
2. [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
3. [docs/environment.md](environment.md) - Environment setup
4. [docs/julia_python_integration.md](julia_python_integration.md) - Julia/Python bridge
5. [docs/platform_compatibility.md](platform_compatibility.md) - System requirements

### Search logs

```bash
# Recent builds
ls -lt output/logs/

# Search for errors
grep -i error output/logs/*.log
grep -i fail output/logs/*.log
```

### Check git history

```bash
# Recent commits
git log --oneline -10

# Changes to specific file
git log -p Makefile
```

---

## Still Stuck?

1. **Check example scripts** in `env/examples/` directory
2. **Compare with fire project**: `../fire/` has similar structure
3. **Review inline comments** in Makefile and scripts
4. **Check git commit messages** for context

## Version

This troubleshooting guide is for **template v1.0.0**.

See [CHANGELOG.md](../CHANGELOG.md) for version history.
