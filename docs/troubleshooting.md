# Troubleshooting Guide

Quick solutions to common issues. Use the diagnostic commands below to identify problems.

---

## Quick Diagnostics

### Check Environment Installation

```bash
# Full environment check
ls -d .venv
# Should show .venv in repo root

# Python check
.venv/bin/python --version
# Should be 3.12.x

# Package verification
.venv/bin/python -c "import pandas, matplotlib; print('OK')"
# Should print: OK
```
<!-- julia:start -->
```bash
# Julia check (if installed)
ls -la .julia/pyjuliapkg/install/bin/julia
# Should exist

# The Julia bridge
.venv/bin/python -c "import juliacall; print('OK')"
# Should print: OK
```
<!-- julia:end -->

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

#### "uv: command not found"

**Cause**: uv not installed

**Solution**: Auto-installs during `make environment`

```bash
make environment
# Checks for uv
# Auto-installs uv if not found
```

**Manual installation** (if auto-install fails):
```bash
# Install uv (official installer):
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Then retry:
make environment
```

#### "No virtualenv found" or "lockfile out of date"

**Cause**: `.venv/` not created yet, or `pyproject.toml` changed without re-syncing

**Solution**:
```bash
# Recreate/sync the environment from the lockfile:
uv sync

# Or pull latest fixes:
git pull
make environment
```

<!-- julia:start -->
#### "No module named 'juliacall'"

**Cause**: Python environment not installed

**Solution**:
```bash
uv sync   # or: make environment
```

**Or activate and install manually**:
```bash
source .venv/bin/activate
uv pip install juliacall
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
<!-- julia:end -->

### Build Errors

#### "ImportError: No module named 'scripts'"

**Cause**: `scripts/` not in Python path

**Solution**: Use environment wrappers (not bare Python):
```bash
# Good:
env/scripts/runpython run_analysis.py price_base

# Bad:
python run_analysis.py price_base
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
# Check if jinja2 in pyproject.toml
grep jinja2 pyproject.toml

# If missing, add and reinstall:
uv sync   # or: make environment
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

<!-- julia:start -->
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
source .venv/bin/activate
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
source .venv/bin/activate
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
<!-- julia:end -->

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

**Cause**: prebuilt Python wheels require GLIBC 2.17+

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

<!-- julia:start -->
### Julia compilation is slow on first run

**Expected**: Julia uses Just-In-Time compilation

**First run**: Slow (compiles code)  
**Subsequent runs**: Fast (uses cached compilation)

**Mitigation**: Precompile packages
```bash
env/scripts/runjulia -e 'using Pkg; Pkg.precompile()'
```
<!-- julia:end -->

### Disk space warnings

**Check usage**:
```bash
du -sh .venv .julia output
```

**Clean build outputs**:
```bash
make clean  # Remove output/
```

**Clean environments** (careful - will need reinstall):
```bash
make cleanall  # Remove .venv, .julia, output/
```

---

## Problems caused by how you obtained the project

These four have one thing in common: nothing is wrong with your code, and the
error message points somewhere other than the cause. They are grouped here
because the trigger is how the working tree came to exist, not anything you did
in it.

### "clone of 'git@github.com:...' failed" — which is usually not an auth problem

```
fatal: destination path '.../lib/repro-tools' already exists and is not an empty directory.
fatal: clone of 'git@github.com:owner/repro-tools.git' into submodule path '...' failed
Failed to clone 'lib/repro-tools' a second time, aborting
```

**Read the first line, not the second.** The second names a GitHub URL and reads
exactly like a credentials failure; the first says the real cause. This happens
whenever a *working tree* is copied over a clone — `rsync`, `cp -r`, restoring a
backup — so `lib/repro-tools/` contains plain files and git refuses to clone
into it.

**Fix**: remove the directory and let git populate it.

```bash
rm -rf lib/repro-tools
git submodule update --init --recursive
```

**Before assuming credentials are broken, test them:**

```bash
ssh -T git@github.com          # expect: "Hi <you>! You've successfully authenticated"
git ls-remote <submodule-url>  # expect: a list of refs
```

An error message that offers a single hypothesis invites you to accept it. Test
the hypothesis before acting on it.

### Tests fail on `AGENTS.md` / `CLAUDE.md` with a `pathlib` traceback

```
FAILED tests/test_documented_commands_exist.py::test_the_sweep_finds_commands
  .../pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
```

`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` and
`COAUTHOR_SETUP.md` are symlinks into the gitignored `private/` overlay created
by `make private-init`. A fresh clone has neither the links nor their target,
which is fine. A **copied** working tree keeps the links and loses the target,
leaving them dangling.

**Fix**: recreate the overlay with `make private-init`, or delete the dangling
links. Current versions skip unreadable documents rather than crashing, so this
appears only on older checkouts.

```bash
find . -maxdepth 2 -type l ! -exec test -e {} \; -print   # list dangling symlinks
```

### A wrapper looks correctly configured because your shell already was

If you use `direnv`, `env/env.sh` is loaded into **every shell inside the
repository**. A wrapper that fails to set up the environment therefore *inherits
a correct one*, and any measurement taken from an interactive shell agrees with
a wrapper that is actually broken. The failure appears only for callers that
were not already handed the environment — cron, CI, an editor, another
project's shell.

**Test wrappers with the environment stripped**, never from a shell inside the
project:

```bash
env -u JULIA_PROJECT -u JULIA_LOAD_PATH -u JULIA_DEPOT_PATH -u PYTHONPATH \
    -u VIRTUAL_ENV env/scripts/runpython -c "import sys; print(sys.prefix)"
```

`tests/test_entry_points_agree.py` does this, and compares the entry points
against each other rather than against the shell that launched them.

### Paths mysteriously become two paths (`CDPATH`)

If `CDPATH` is set in your shell, `cd` **prints the directory it resolved** when
it resolves through `CDPATH`. Every script here finds itself with

```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
```

so that printed line is captured too, and `ROOT` silently becomes two
newline-separated paths. Nothing errors. It surfaces much later as a module that
will not import, or a second package depot appearing out of nowhere.

**Fix, and the two cases differ:**

- A script that is **executed**: `unset CDPATH` near the top.
- A file that is **sourced** (`env/env.sh`, anything `.envrc` pulls in): clear it
  inside the subshell instead — `ROOT="$(CDPATH= cd -- ... && pwd)"`. Using
  `unset` in a sourced file mutates the interactive shell of whoever sourced it.

Check this first after touching any wrapper.

---

## How to investigate something not listed here

**Ask make what it will do, rather than reading the Makefile.** The build is
heavily pattern-generated, so make is the only thing that knows the expanded
rules:

```bash
make dryrun                  # or: make -n all
make list-analyses           # what analyses exist
make list-analyses-names     # the same, machine-readable
make show-analysis-<name>    # one analysis: script, runner, inputs, outputs
make info                    # version and layout
make system-info             # OS, Make, Python, and language versions
```

**Narrow before you dig.**

```bash
make test-fast               # ~1 minute; skips the integration tests
make test                    # everything
python3 -m pytest tests/test_foo.py::TestClass::test_case -v
```

**Never invoke the interpreters directly.** Use `env/scripts/runpython` and its
siblings. They source `env/env.sh`, which is the single source of truth for the
environment — `PYTHONPATH`, the language bridges, and the thread-count pin that
keeps floating-point reduction order identical across machines. A bare `python`
gets whichever interpreter your shell happens to offer, and the results may
differ in the last digits.

**When a check passes, ask what it would look like if it were broken.** If the
answer is "the same", it is not a check. Several bugs in this project's own
machinery were exactly that: output redirected to `/dev/null` with `|| true`
appended and a stamp file touched afterwards; a command with no entry point that
ignored its arguments and exited 0; a test whose skip condition matched a
comment saying the feature was absent. All reported success indefinitely.

---

## Debugging Tips

### Enable verbose output

```bash
# Make verbose mode:
make -d all  # Show all decisions

# Python verbose mode:
env/scripts/runpython -v run_analysis.py price_base
```

### Check environment variables

```bash
env/scripts/runpython -c 'import os; print("\\n".join(f"{k}={v}" for k,v in sorted(os.environ.items()) if "PYTHON" in k))'
```
<!-- julia:start -->
```bash
# Julia bridge variables:
env/scripts/runpython -c 'import os; print("\\n".join(f"{k}={v}" for k,v in sorted(os.environ.items()) if "JULIA" in k))'
```
<!-- julia:end -->

### Test Python imports

```bash
.venv/bin/python -c "
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

<!-- julia:start -->
### Test Julia environment

```bash
env/scripts/runjulia -e '
using Pkg
println("Julia: ", VERSION)
println("Project: ", Base.active_project())
Pkg.status()
'
```
<!-- julia:end -->

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
<!-- julia:start -->
4. [docs/julia_python_integration.md](julia_python_integration.md) - Julia/Python bridge
<!-- julia:end -->
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

This troubleshooting guide is for **template v2.0.2**.

See [CHANGELOG.md](../CHANGELOG.md) for version history.
