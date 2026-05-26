# Quick Start Guide

**Get the reproducible research template up and running in 5 minutes.**

**Need help?** Run `make` for brief guidance, `make help` for all commands, or `make info` for comprehensive project information.

**Local or Docker?** The steps below build **locally** (uv — fastest). To build in an isolated, OS‑pinned container instead (only Docker required), see **[Build with Docker instead](#build-with-docker-instead)** below, or the full **[local‑vs‑Docker guide](docs/running_locally_vs_docker.md)**.

---

## TL;DR - Copy-Paste Commands

```bash
# 1. Start YOUR project: click "Use this template" on GitHub for your OWN repo
#    (details in "Starting your own project" below). Then clone it and customize:
git clone --recursive <your-repo-url>   # YOUR repo, cloned WITH --recursive
cd <your-project>
python bootstrap.py --interactive        # choose languages, rename

# 2. Install environment (~5 minutes)
make environment
# Installs:
#   - Git submodules (repro-tools automatically)
#   - Python 3.12 uv virtualenv (.venv/)
#   - Julia via juliacall (.julia/)
#   - Stata packages if Stata installed (.stata/)

# 3. Verify setup
make verify
# Checks environment, packages, data availability

# 4. Build all artifacts
make all
# Creates:
#   - output/figures/price_base.pdf
#   - output/figures/remodel_base.pdf
#   - output/tables/price_base.tex
#   - output/tables/remodel_base.tex
#   - output/provenance/*.yml (build records)

# 5. Verify outputs
make test-outputs
# Confirms all expected files exist

# 6. Publish to paper repo
make publish
# Copies artifacts to paper/ with provenance tracking
```

**Total time**: ~5-10 minutes
**Total disk**: ~2.5 GB installed (2 GB env + ~0.5 GB Julia); keep ~5 GB free

### Build with Docker instead

Prefer an isolated, OS‑pinned container? Then you need **only Docker** on your machine (no Make/uv/Julia). Do step 1 above, then replace steps 2–5 with:

```bash
docker build -t my-project .                                  # build the full environment into the image
docker run --rm -v "$PWD/output:/project/output" my-project   # reproduce all artifacts -> ./output
```

See the full comparison — and how to *develop* inside a container — in **[docs/running_locally_vs_docker.md](docs/running_locally_vs_docker.md)**.

---

## Starting your own project

This repo is a **template**. Your project should be **its own git repository** — don't just keep working inside a clone of the template, or you'd be committing to the template's history and remote. Pick one:

**A. GitHub "Use this template" (recommended).** On the template's GitHub page, click **Use this template → Create a new repository**. You get a fresh repo — your own history and remote — containing every file *except* the template's commit history. Then clone **your** repo with submodules:

```bash
git clone --recursive https://github.com/<you>/my-project.git
cd my-project
```

**B. Clone, then detach (no GitHub, or local-only).**

```bash
git clone --recursive https://github.com/rhstanton/project_template.git my-project
cd my-project
rm -rf .git && git init                       # drop the template's history
git submodule add https://github.com/rhstanton/repro-tools.git lib/repro-tools
git add . && git commit -m "Initial commit from template"
git remote add origin <your-new-repo-url>     # point at YOUR remote
```

**Then customize** — run the bootstrap script once, inside your new project:

```bash
python bootstrap.py --interactive
#   • keep or drop Julia / Stata
#   • rename the project
```

Non-interactive equivalent, for example:

```bash
python bootstrap.py --remove-stata --rename "Housing Market Analysis"
```

> **Always clone with `--recursive`** (or run `git submodule update --init --recursive`) so `lib/repro-tools/` is populated — the build depends on it, and `make environment` stops with a clear error if it's missing. Full customization checklist: **[TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)**.

---

## What Success Looks Like

### After `make environment`

You should see:
```
📦 Initializing git submodules...
📦 Installing Python environment...
✅ Python environment created at .venv/

📦 Installing Julia via juliacall...
✅ Julia installed at .julia/pyjuliapkg/install/

📦 Installing Julia packages...
✅ Julia packages installed

🎉 Environment setup complete!
```

### After `make verify`

You should see:
```
✅ Python environment: OK (3.12.x)
✅ Python packages: pandas, matplotlib, juliacall, pyyaml, papermill, seaborn, pytest, ruff, mypy
✅ Julia: OK (1.10+)
✅ Julia packages: PythonCall, DataFrames
✅ Data files: housing_panel.csv (SHA256 matches)
✅ Environment verified!
```

### After `make all`

You should see:
```
Building price_base...
✅ output/figures/price_base.pdf
✅ output/tables/price_base.tex
✅ output/provenance/price_base.yml

Building remodel_base...
✅ output/figures/remodel_base.pdf
✅ output/tables/remodel_base.tex
✅ output/provenance/remodel_base.yml

All artifacts built successfully!
```

### After `make test-outputs`

You should see:
```
Checking expected outputs...
✅ output/figures/price_base.pdf (12.5 KB)
✅ output/figures/remodel_base.pdf (13.1 KB)
✅ output/tables/price_base.tex (193 bytes)
✅ output/tables/remodel_base.tex (201 bytes)
✅ output/provenance/price_base.yml
✅ output/provenance/remodel_base.yml

All expected outputs present!
```

---

## What Just Happened?

### `make environment`

Installed complete multi-language environment:

- **Python 3.12** via uv (~2GB in `.venv/`)
- **Julia 1.10-1.12** via juliacall (~500MB in `.julia/pyjuliapkg/`)
- **Python packages**: pandas, matplotlib, juliacall, pyyaml, jinja2, pytest, ruff, mypy
- **Julia packages**: PythonCall, DataFrames
- **Stata packages** (if Stata installed): estout, etc.

**Key features**:
- ✅ Auto-installs uv if not found
- ✅ Julia auto-downloaded (no manual installation)
- ✅ Single unified Python environment (no CondaPkg duplication)
- ✅ Project-local packages (no global pollution)

### `make all`

Ran all analysis scripts:

1. **`run_analysis.py price_base`**: Housing price analysis
   - Input: `data/housing_panel.csv`
   - Outputs:
     - `output/figures/price_base.pdf` (matplotlib figure)
     - `output/tables/price_base.tex` (LaTeX table)
     - `output/provenance/price_base.yml` (build record)

2. **`run_analysis.py remodel_base`**: Remodeling rate analysis
   - Same structure as above

**Provenance**: Each build records git state + SHA256 hashes of inputs/outputs

### `make publish`

Published artifacts to `paper/` directory:

- Copied figures and tables from `output/` to `paper/`
- Updated `paper/provenance.yml` with publication record
- Ran git safety checks (clean tree, not behind upstream)

**Safety**: Refuses to publish from dirty tree or outdated branch

---

## Prerequisites

### Zero Prerequisites!

**Auto-installed by `make environment`:**

- ✅ **uv** - Auto-installs uv if not found
- ✅ **Python 3.12** - Installed via uv
- ✅ **Julia** - Auto-downloaded by juliacall
- ✅ **Python/Julia packages** - From `pyproject.toml` (pinned in `uv.lock`) and `env/Project.toml`

**Only required pre-installed tool:**

- **GNU Make 4.3+**
  - Linux: Usually pre-installed (`apt install make`)
  - macOS: `brew install make` (use `gmake` instead of `make`)
  - Windows: Use WSL 2 with Ubuntu

**Optional:**

- **Stata** (commercial software, for Stata examples only)
- **Git** (for version control and provenance tracking)
- **Nix** (for reproducible dev shell via `nix develop`, see `flake.nix`)

### System Requirements

**Minimum**:
- CPU: x86_64 or ARM64 (Apple Silicon)
- RAM: 8GB
- Disk: 5GB free (~2.5GB installed + headroom)
- OS: Linux, macOS 11+, or Windows 10+ with WSL 2

**Recommended**:
- RAM: 16GB (for large datasets)
- Disk: 10GB free
- OS: Ubuntu 22.04 LTS or macOS 13+

**For GPU support** (optional, Julia/CUDA only):
- NVIDIA GPU with a working driver (CUDA.jl bundles its own runtime)
- Run `JULIA_ENABLE_CUDA=1 make environment` (installs CUDA.jl into the gitignored
  `.julia/gpu-env`); `run_did.py` then uses the GPU automatically via `--use-gpu=auto`

---

## Directory Structure After Setup

```
project_template/
├── .venv/                     # Python uv virtualenv (2GB)
├── .julia/                    # Julia packages (500MB)
├── .stata/                    # Stata packages if installed
│
├── data/                      # Input data (CSV files)
│   └── housing_panel.csv
│
├── run_analysis.py            # Unified analysis script (study configs in shared/config.py)
│
├── output/                    # Build outputs (ephemeral)
│   ├── figures/
│   │   ├── price_base.pdf
│   │   └── remodel_base.pdf
│   ├── tables/
│   │   ├── price_base.tex
│   │   └── remodel_base.tex
│   ├── provenance/            # Build records
│   │   ├── price_base.yml
│   │   └── remodel_base.yml
│   └── logs/
│
├── paper/                     # Published artifacts (permanent)
│   ├── figures/
│   ├── tables/
│   ├── provenance.yml         # Publication record
│   └── README.md
│
├── scripts/
│   ├── provenance.py          # Provenance utilities
│   └── publish_artifacts.py   # Publishing with safety checks
│
├── pyproject.toml             # Python dependencies (uv)
├── uv.lock                    # Pinned Python versions (uv)
│
├── env/                       # Environment specifications
│   ├── Project.toml           # Julia environment
│   ├── examples/              # Example scripts
│   │   ├── sample_python.py
│   │   ├── sample_julia.jl
│   │   ├── sample_juliacall.py
│   │   └── sample_stata.do
│   └── scripts/
│       ├── runpython          # Python wrapper
│       ├── runjulia           # Julia wrapper
│       └── runstata           # Stata wrapper
│
├── docs/                      # Documentation
│   ├── environment.md
│   ├── provenance.md
│   ├── publishing.md
│   ├── julia_python_integration.md
│   ├── platform_compatibility.md
│   └── directory_structure.md
│
├── Makefile                   # Build orchestration
├── README.md                  # Project overview
├── CHANGELOG.md               # Version history
└── .gitignore                 # Git exclusions
```

---

## Common Workflows

### Build Single Artifact

```bash
make price_base
# → output/figures/price_base.pdf
# → output/tables/price_base.tex
# → output/provenance/price_base.yml
```

### Build All Artifacts

```bash
make all
# Builds all artifacts in parallel
```

### Publish Artifacts

```bash
# Publish all:
make publish

# Publish specific artifact:
make publish PUBLISH_ARTIFACTS="price_base"

# Publish multiple:
make publish PUBLISH_ARTIFACTS="price_base remodel_base"
```

### Clean and Rebuild

```bash
# Remove all build outputs:
make clean

# Remove everything including environments:
make cleanall

# Rebuild from scratch:
make cleanall
make environment
make all
```

### Run Examples

```bash
# Python example:
make -C examples python

# Julia example:
make -C examples julia

# Python → Julia interop:
make -C examples juliacall

# Stata example (if installed):
make -C examples stata
```

---

## Adding Your Own Analysis

### 1. Add Study Configuration

Add to `shared/config.py`:

```python
STUDIES = {
    "price_base": { ... },
    "remodel_base": { ... },
    "your_analysis": {
        "data": DATA_FILES["your_data"],
        "xlabel": "Year",
        "ylabel": "Your metric",
        "title": "Your analysis",
        "groupby": "category",
        "yvar": "your_variable",
        "xvar": "year",
        "table_agg": "mean",
        "figure": OUTPUT_DIR / "figures" / "your_analysis.pdf",
        "table": OUTPUT_DIR / "tables" / "your_analysis.tex",
    },
}
```

### 2. Add to Makefile

Add pattern definition:
```makefile
your_analysis.script  := run_analysis.py
your_analysis.runner  := $(PYTHON)
your_analysis.inputs  := $(DATA)
your_analysis.outputs := $(OUT_FIG_DIR)/your_analysis.pdf $(OUT_TBL_DIR)/your_analysis.tex $(OUT_PROV_DIR)/your_analysis.yml
your_analysis.args    := your_analysis
```

### 3. Build and Publish

```bash
make your_analysis
make publish PUBLISH_ANALYSES="your_analysis"
```

---

## Alternative: Custom Analysis Script

If you need custom logic not covered by the standard pattern, create `build_your_analysis.py`:

```python
#!/usr/bin/env python
import argparse
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

    # Load data
    df = pd.read_csv(args.data)

    # Analysis...
    # (your code here)

    # Save figure
    fig, ax = plt.subplots()
    # (your plot code)
    fig.savefig(args.out_fig, bbox_inches="tight")
    plt.close(fig)

    # Save table
    # (your table code)
    result_table.to_latex(args.out_table, index=False)

    # Save provenance
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

### 2. Add to Makefile

Add artifact name to `ARTIFACTS` variable:

```makefile
ARTIFACTS := price_base remodel_base your_analysis
```

That's it! The Makefile's pattern rules handle the rest.

### 3. Build and Publish

```bash
make your_analysis              # Build
make publish PUBLISH_ARTIFACTS="your_analysis"  # Publish
```

---

## Troubleshooting

### "make: *** No rule to make target 'all'"

**Cause**: GNU Make version too old (< 4.3)

**Fix**:
```bash
make --version
# If < 4.3:
# macOS: brew install make; use gmake
# Linux: sudo apt install make
```

### "uv not found"

**Cause**: uv not installed

**Fix**: `make environment` auto-installs uv

### "ImportError: No module named 'juliacall'"

**Cause**: Python environment not activated

**Fix**:
```bash
make environment  # Install
source .venv/bin/activate  # Activate
```

### "Julia not found"

**Cause**: Julia not installed yet

**Fix**: Julia is auto-installed by juliacall during `make environment`

### "Package X not found in current path"

**Cause**: Julia packages not installed

**Fix**:
```bash
make -C env julia-install-via-python
```

### Git safety check failures

**Dirty tree**:
```bash
git status
git add .
git commit -m "Commit changes"
make publish
```

**Behind upstream**:
```bash
git pull
make publish
```

**Artifacts not from current HEAD**:
```bash
make all  # Rebuild from current commit
make publish
```

---

## Next Steps

### Learn More

- [README.md](README.md) - Full project overview
- [docs/environment.md](docs/environment.md) - Environment details
- [docs/provenance.md](docs/provenance.md) - Provenance system
- [docs/publishing.md](docs/publishing.md) - Publishing workflow
- [docs/julia_python_integration.md](docs/julia_python_integration.md) - Julia/Python bridge
- [docs/platform_compatibility.md](docs/platform_compatibility.md) - System configuration

### Customize Template

1. **Update `data/`**: Replace with your data files
2. **Add a study**: Add an entry to the `STUDIES` dict in `shared/config.py`
3. **Update `pyproject.toml`**: Add your Python dependencies (then run `uv sync` or `make environment`)
4. **Update `env/Project.toml`**: Add your Julia dependencies
5. **Update Makefile**: Add the study name to the `ANALYSES` variable (and a pattern block)

### Set Up Paper Repository

The `paper/` directory is intended to be a **separate git repository** with an Overleaf remote:

```bash
cd paper
git init
git add .
git commit -m "Initial paper structure"

# Add Overleaf remote:
git remote add overleaf https://git.overleaf.com/your-project-id
git pull overleaf main --allow-unrelated-histories
git push overleaf main
```

Then `make publish` copies artifacts to this separate repo.

### Enable GPU Support (Optional)

For CUDA GPU support:

```bash
# Before make environment:
export JULIA_ENABLE_CUDA=1
export GPU_CUDA_MAJOR=12  # or 13
make environment
```

See [docs/platform_compatibility.md](docs/platform_compatibility.md) for details.

---

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `env/examples/` directory
- **Issues**: Check git history and commit messages
- **Questions**: Refer to inline comments in Makefile and scripts

## Version

This quickstart is for **template v2.0.2**.

See [CHANGELOG.md](CHANGELOG.md) for version history.
