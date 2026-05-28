# Template Usage Guide

How to customize this template for your own research project.

---

## Starting a New Project

### Option 1: Clone as Template (Recommended)

```bash
# Create new repo from template on GitHub
# (Use "Use this template" button)

# Or clone with submodules:
git clone --recursive <this-repo-url> my-project
cd my-project
make environment  # Installs everything
```

### Option 2: Clone and Reset History

```bash
# Clone with submodules
git clone --recursive <this-repo-url> my-project
cd my-project

# Reset git history (optional)
rm -rf .git
git init
git add .
git commit -m "Initial commit from template"

# Reinitialize submodule
git submodule add https://github.com/rhstanton/repro-tools.git lib/repro-tools
make environment
```

### Option 3: Copy Files (NOT Recommended)

If you must copy files manually:

```bash
# Copy template to new location
cp -r project_template my-project
cd my-project

# DON'T copy lib/repro-tools contents!
rm -rf .git .venv .julia output lib/repro-tools/*

# Initialize as new git repo
git init
git add .
git commit -m "Initial commit from template"

# Let git clone the submodule
git submodule add https://github.com/rhstanton/repro-tools.git lib/repro-tools
make environment
```

**IMPORTANT:** Never manually copy the `lib/repro-tools/` directory contents. Always let git handle submodules.

### Then customize with `bootstrap.py`

After cloning, run the bootstrap script **once** inside your new project (before `make environment`) to automate the common customizations — selecting languages and renaming:

```bash
python bootstrap.py --interactive
# or non-interactively, e.g.:
python bootstrap.py --python-only                  # Python only
python bootstrap.py --remove-stata --rename "My Project"   # Python + Julia
python bootstrap.py --remove-julia                 # Python + Stata
```

**Python is always kept** — the whole harness (`repro_tools`, `run_analysis.py`, the test suite, the Make plumbing) runs on it — so "one language" means Python-only. Julia and Stata are the two you can drop.

Dropping a language removes its environment plumbing **and** the example analyses that depend on it (e.g. `--remove-julia` also removes `julia_demo` and `did_example`), so `make all` still builds cleanly afterwards — it delegates to `make remove-analysis` for each. This is the only safe way to drop a language; deleting files by hand leaves the build referencing a backend that's gone.

The manual checklist below covers anything `bootstrap.py` doesn't.

---

## Customization Checklist

### 1. Update Project Metadata

**README.md**:
- [ ] Change project title
- [ ] Update description
- [ ] Add your institution/affiliation
- [ ] Update contact information
- [ ] Add project-specific details

**CHANGELOG.md**:
- [ ] Reset to version 0.1.0
- [ ] Add initial commit entry

### 2. Configure Environments

**pyproject.toml** (exact versions pinned in `uv.lock`):
```toml
[project]
name = "my-project"  # Change project name
requires-python = ">=3.12"
dependencies = [
    # Add your packages:
    "scikit-learn",
    "statsmodels",
    "seaborn",
    # Keep required packages:
    "pandas",
    "matplotlib",
    "pyyaml",
    "jinja2",
    "juliacall>=0.9.14",
]
```

**env/Project.toml** (Julia):
```toml
[deps]
PythonCall = "6099a3de-0909-46bc-b1f4-468b9a2dfc0d"
DataFrames = "a93c6f00-e57d-5684-b7b6-d8193f3e46c0"
# Add your Julia packages:
# CSV = "336ed68f-0bac-5ca0-87d4-7b16caf5d00b"
# FixedEffectModels = "9d5cd8c9-2029-5cab-9928-427838db53e3"

[compat]
julia = "1.10, 1.11, 1.12"
PythonCall = "0.9"
DataFrames = "1"
# Add version constraints for new packages
```

**env/stata-packages.txt** (if using Stata):
```text
estout
# Add your Stata packages:
# reghdfe
# ftools
# gtools
```

### 3. Add Your Data

**data/ directory**:
```bash
# Add your CSV files:
cp /path/to/your/data.csv data/

# Or create symlink to external data:
ln -s /external/data/location data/external_data
```

**Update .gitignore** if needed:
```gitignore
# Add patterns for large data files
data/*.dta
data/*.parquet
data/raw/

# Or exclude all data except samples:
data/*
!data/sample_*.csv
```

### 4. Add Study Configurations

The template uses a **unified analysis script** (`run_analysis.py`) that reads study parameters from `shared/config.py`.

**Add a new study to `shared/config.py`**:

```python
STUDIES = {
    "price_base": { ... },
    "remodel_base": { ... },
    "your_analysis": {
        "data": DATA_FILES["your_data"],
        "xlabel": "Year",
        "ylabel": "Your metric",
        "title": "Your analysis title",
        "groupby": "category",
        "yvar": "your_variable",
        "xvar": "year",
        "table_agg": "mean",  # or "sum", "median", etc.
        "figure": OUTPUT_DIR / "figures" / "your_analysis.pdf",
        "table": OUTPUT_DIR / "tables" / "your_analysis.tex",
    },
}
```

**That's it!** No need to create a separate Python script. The `run_analysis.py` script handles all studies using the configuration from `config.py`.

**For custom analysis logic**: If you need analysis that doesn't fit the standard pattern (different plot types, multiple figures, etc.), you can still create a custom `build_your_custom_analysis.py` script following this pattern:

```python
#!/usr/bin/env python
"""Custom analysis with non-standard outputs."""
from pathlib import Path
import pandas as pd
from docopt import docopt
from repro_tools import auto_build_record

def main():
    args = docopt(__doc__)

    # Your custom analysis logic here
    # ...

    # Generate provenance
    auto_build_record(
        artifact_name="your_custom_analysis",
        out_meta=prov_file,
        inputs=[input_files],
        outputs=[output_files],
    )

if __name__ == "__main__":
    main()
```

### 5. Update Makefile

**Add to ARTIFACTS variable**:
```makefile
# Line 6 in Makefile:
ARTIFACTS := price_base remodel_base your_analysis another_analysis
```

**Add custom data files** (if needed):
### 5. Update Makefile

**Add to ANALYSES variable**:
```makefile
# Line 6 in Makefile:
ANALYSES := price_base remodel_base your_analysis
```

**Add pattern definition**:
```makefile
# Add after other analysis definitions:
your_analysis.script  := run_analysis.py
your_analysis.runner  := $(PYTHON)
your_analysis.inputs  := $(DATA)  # or $(YOUR_DATA) if different
your_analysis.outputs := $(OUT_FIG_DIR)/your_analysis.pdf $(OUT_TBL_DIR)/your_analysis.tex $(OUT_PROV_DIR)/your_analysis.yml
your_analysis.args    := your_analysis
```

**Add custom data files** (if needed):
```makefile
# After DATA definition (~line 13):
DATA := data/housing_panel.csv
YOUR_DATA := data/your_data.csv
```

**Custom targets for non-standard analyses** (if needed):
If you created a custom `build_*.py` script that doesn't follow the standard pattern:
```makefile
custom_analysis.script  := build_custom_analysis.py
custom_analysis.runner  := $(PYTHON)
custom_analysis.inputs  := $(YOUR_DATA)
custom_analysis.outputs := $(OUT_FIG_DIR)/custom.pdf $(OUT_TBL_DIR)/custom.tex $(OUT_PROV_DIR)/custom.yml
custom_analysis.args    := --data $(YOUR_DATA) --custom-arg value
```

### 6. Configure Publishing

**paper/ directory setup**:

If using Overleaf:
```bash
cd paper
git init
git remote add overleaf https://git.overleaf.com/your-project-id
git add README.md
git commit -m "Initial paper structure"
git pull overleaf main --allow-unrelated-histories
git push overleaf main
```

**Update Makefile publish settings**:
```makefile
# Adjust safety checks (lines ~15-17):
ALLOW_DIRTY := 0              # Require clean tree
REQUIRE_NOT_BEHIND := 1       # Require up-to-date branch
REQUIRE_CURRENT_HEAD := 1     # Require artifacts from HEAD
```

### 7. Add Project-Specific Documentation

**Create docs/ files for your domain**:

- `docs/data_sources.md` - Where data comes from
- `docs/methodology.md` - Statistical methods used
- `docs/results_interpretation.md` - How to read outputs
- `docs/replication_instructions.md` - For journal submission

**Update docs/README.md**:
```markdown
# Documentation Index

## Project-Specific
- [Data Sources](data_sources.md)
- [Methodology](methodology.md)
- [Results Interpretation](results_interpretation.md)

## Template Documentation
- [Environment Setup](environment.md)
- [Provenance Tracking](provenance.md)
- [Publishing Workflow](publishing.md)
```

---

## Keeping private maintainer files (the `private/` overlay)

Some files are *just for you* — working notes, AI agent instructions and settings, coauthor onboarding — and must **never** ship in the public repo. But you still want them **version-controlled** (not just loose, un-backed-up files) and **usable** at their normal paths. This template provides a small pattern that gets all three:

- **usable** — files live at their expected paths via symlinks, so every tool finds them;
- **tracked** — their real homes live inside `private/`, a *separate git repo* you can push to a private backup remote;
- **private** — `private/` and every symlink name are gitignored by this repo, so none of it is ever committed or shipped.

### Set it up

```bash
make private-init      # or: ./scripts/init-private.sh
```

This is **idempotent** — run it any time to create or repair the overlay. It never overwrites a real file. It:

1. initializes `private/` as a nested git repo (with an initial commit) and seeds template files;
2. migrates any leftover public `.claude/` files into the overlay (older layouts);
3. creates the gitignored symlinks below.

### Layout

```
private/                              ← nested git repo, gitignored by this repo
├── README.md                         (explains the overlay + backup-remote one-liner)
├── .gitignore
├── dev-notes/                        ← maintainer working/milestone notes
├── docs/  tests/                     ← homes for maintainer-only docs (see below)
├── COAUTHOR_SETUP.md                 ← private coauthor onboarding notes
├── ai/AGENTS.md                      ← canonical AI agent instructions (every tool)
└── ai/.claude/settings.local.json    ← per-user Claude Code config

dev-notes                       → private/dev-notes                (gitignored symlink)
COAUTHOR_SETUP.md               → private/COAUTHOR_SETUP.md         (gitignored symlink)
AGENTS.md                       → private/ai/AGENTS.md              (gitignored symlink)
CLAUDE.md                       → private/ai/AGENTS.md              (gitignored symlink)
.claude                         → private/ai/.claude                (gitignored symlink)
.github/copilot-instructions.md → ../private/ai/AGENTS.md           (gitignored symlink)
```

### AI agent files are entirely private

The public repo ships **no** AI-tool files at all — no `AGENTS.md`, no `CLAUDE.md`, no `.claude/`, no Copilot instructions. Every AI tool that looks for guidance lands on the same `private/ai/AGENTS.md` via a gitignored symlink, so Claude Code, Codex, and Copilot all read identical instructions while the content stays out of the public repo. Claude Code's per-user permissions (`settings.local.json`) live alongside it under `private/ai/.claude/`. Adopters of the template get a clean codebase with no inherited AI guidance — they consult the regular `docs/` like any other contributor, and write their own private overlay if they want one.

### Adding a maintainer-only doc that lives in a public directory

To keep a doc like `docs/IMPLEMENTATION_NOTES.md` private even though `docs/` is public, create it under `private/docs/` (or `private/tests/`) and re-run `make private-init` — the script symlinks it into place only when the private source exists, so links never dangle. (`docs/NOTEBOOK_SUPPORT_IMPLEMENTATION.md`, `tests/NOTEBOOK_TESTS_SUMMARY.md`, and `tests/TEST_IMPROVEMENTS.md` are pre-wired this way.)

### Backing up the overlay (optional)

`private/` has no remote by default. To back it up, create a **private** repo and:

```bash
git -C private remote add origin git@github.com:<you>/<project>-private.git
git -C private add -A && git -C private commit -m "Update private overlay"
git -C private push -u origin main
```

### For adopters of this template

If you cloned this template, the overlay starts empty — run `make private-init` to scaffold your own. Nothing the original maintainer kept private was ever in the repo you cloned; the pattern ships, the content does not.

---

## Domain-Specific Adaptations

### Economics/Econometrics

**Additional packages**:
```toml
# pyproject.toml
dependencies = [
    "statsmodels",
    "linearmodels",
    "scikit-learn",
    "pyfixest",  # Fast fixed effects
    "doubleml",  # Causal ML
]
```

**Julia packages**:
```toml
[deps]
FixedEffectModels = "9d5cd8c9-2029-5cab-9928-427838db53e3"
GLM = "38e38edf-8417-5370-95a0-9cbb8c7f171a"
```

### Machine Learning

**Additional packages**:
```yaml
dependencies:
  - scikit-learn
  - xgboost
  - lightgbm
  - pytorch
  - tensorflow
```

**GPU support**:
```bash
export JULIA_ENABLE_CUDA=1
export GPU_CUDA_MAJOR=12
make environment
```

### Computational Biology

**Additional packages**:
```yaml
dependencies:
  - biopython
  - scikit-bio
  - numpy
  - scipy
```

### Spatial Analysis

**Additional packages**:
```yaml
dependencies:
  - geopandas
  - shapely
  - rasterio
  - pyproj
```

---

## Advanced Customizations

### Add R Environment

**Create env/r-packages.txt**:
```text
tidyverse
ggplot2
data.table
lfe
fixest
```

**Create env/scripts/runr**:
```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
R_LIBS="$REPO_ROOT/.r/library"

export R_LIBS_USER="$R_LIBS"
mkdir -p "$R_LIBS"

exec Rscript "$@"
```

**Add to env/Makefile**:
```makefile
.PHONY: r-env
r-env:
	@echo "📦 Installing R packages..."
	@while read -r pkg; do \
		./scripts/runr -e "install.packages('$$pkg', repos='https://cran.rstudio.com/')"; \
	done < r-packages.txt
```

### Add Docker Support

**The template ships a digest-pinned, uv-based `Dockerfile` at the repo root.** Its essence:
```dockerfile
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        make git curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.0 /uv /uvx /usr/local/bin/

WORKDIR /project
COPY . .
RUN make environment        # uv sync (pyproject.toml + uv.lock) + Julia via juliacall
CMD ["make", "all"]
```

**Create .dockerignore**:
```
.venv/
.julia/
.stata/
output/
paper/
.git/
```

**Build and run**:
```bash
docker build -t my-project .
docker run -v $(pwd)/output:/project/output my-project
```

### Add Continuous Integration

**Create .github/workflows/build.yml**:
```yaml
name: Build All Artifacts

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup environment
        run: make environment

      - name: Build artifacts
        run: make all

      - name: Upload outputs
        uses: actions/upload-artifact@v3
        with:
          name: outputs
          path: output/
```

---

## Workflow Variations

### Option A: Separate Build/Analysis Repos

```bash
# Repository structure:
my-project/          # Git repo 1: analysis code
├── build_*.py
├── scripts/
├── env/
└── Makefile

my-project-paper/    # Git repo 2: paper + published artifacts
├── paper.tex
├── figures/
├── tables/
└── provenance.yml
```

**Publishing**: `make publish` pushes to separate repo

### Option B: Monorepo with Submodules

```bash
my-project/
├── analysis/        # Git submodule
│   ├── build_*.py
│   └── Makefile
├── paper/           # Git submodule (Overleaf)
│   ├── paper.tex
│   └── figures/
└── README.md
```

### Option C: Notebook-Based Workflow

Convert build scripts to Jupyter notebooks:

**Create build_your_analysis.ipynb**:
```python
# Cell 1: Imports
import pandas as pd
import matplotlib.pyplot as plt
from scripts.provenance import write_build_record

# Cell 2: Load data
df = pd.read_csv("data/your_data.csv")

# Cell 3: Analysis
# ...

# Cell 4: Save outputs
fig.savefig("output/figures/your_analysis.pdf")
# ...
```

**Add to Makefile**:
```makefile
JUPYTER := .venv/bin/jupyter

output/figures/your_analysis.pdf: build_your_analysis.ipynb
	$(JUPYTER) nbconvert --execute --to notebook $<
```

---

## Migration from Existing Project

### From Manual Workflow

1. **Inventory current scripts**: List all analysis scripts
2. **Standardize script pattern**: Add argparse for inputs/outputs
3. **Add provenance calls**: Insert `write_build_record()` at end
4. **Create Makefile targets**: Map scripts to artifacts
5. **Test builds**: `make all` and verify outputs

### From Other Build Systems

**From R Makefile**:
- Convert R scripts to use `env/scripts/runr`
- Keep Makefile pattern rules
- Add provenance tracking to R scripts

**From Snakemake**:
- Convert Snakefile rules to Makefile targets
- Keep dependency graph structure
- Use grouped targets for multi-output rules

**From Jupyter notebooks**:
- Convert notebooks to `.py` scripts via `nbconvert`
- Or use `jupyter nbconvert --execute` in Makefile
- Add provenance cells at end

---

## Best Practices

### Naming Conventions

- **Scripts**: `build_<topic>_<variant>.py`
- **Artifacts**: Match script name (e.g., `price_base`)
- **Data files**: Descriptive names (`housing_panel.csv` not `data1.csv`)

### Code Organization

- **One script = one artifact** (figure + table + provenance)
- **Shared code** → `scripts/` directory
- **Constants/config** → `scripts/config.py`
- **Utilities** → `scripts/utils.py`

### Version Control

**Commit frequently**:
```bash
git add build_your_analysis.py
git commit -m "Add your_analysis: description"
```

**Bump the version** — one command sets it everywhere it appears (`pyproject.toml`, `uv.lock`, `_version.py`, `CITATION.cff` + release date, `README.md`, `QUICKSTART.md`) and rolls the CHANGELOG `[Unreleased]` section into the new release:
```bash
python scripts/bump_version.py 1.1.0   # dry run first — shows the plan, writes nothing
make bump-version VERSION=1.1.0        # then apply across all files
```
It reads the version **and package name** from `pyproject.toml`, so it works for your renamed/derived project too; files that don't apply (e.g. you removed QUICKSTART) are skipped, not errored. It deliberately does **not** commit or tag — review `git diff` first, then:

**Tag releases**:
```bash
git tag -a v1.0 -m "Initial submission"
git push origin v1.0
```

**Branch for revisions**:
```bash
git checkout -b revision-2024-02
# Make changes
git commit -am "Address reviewer comments"
```

### Provenance Discipline

- **Never bypass provenance**: Always use `write_build_record()`
- **Track all inputs**: Include data, config, code
- **Verify checksums**: Use `sha256sum` to confirm files unchanged
- **Publish from clean tree**: No uncommitted changes

---

## Common Customization Questions

**Q: Can I use a different build tool (e.g., Snakemake, SCons)?**

A: Yes, but you'll need to:
- Reimplement provenance tracking
- Ensure atomic multi-output builds
- Add git safety checks for publishing

**Q: Can I use environments other than uv?**

A: Yes (conda, venv, poetry, etc.), but update `env/Makefile` accordingly.

**Q: Do I need both Python and Julia?**

A: No — Python is required (the harness runs on it), but Julia is optional. Drop it with `python bootstrap.py --remove-julia`, which removes the `juliacall` dependency, `env/Project.toml`, the Julia wrappers/examples, **and** the Julia-backed example analyses (`julia_demo`, `did_example`) so `make all` still builds. (Likewise `--remove-stata`, or `--python-only` for both.) Don't remove these by hand — the pieces are spread across the Makefile, `shared/config.py`, and `pyproject.toml`, and a partial removal breaks the build.

**Q: Can I add more output types (not just PDF/TEX)?**

A: Yes - just update script to save other formats:
```python
# Save PNG, CSV, JSON, etc.
fig.savefig(args.out_fig_png, format='png')
results.to_csv(args.out_csv)
metadata = {"key": "value"}
with open(args.out_json, 'w') as f:
    json.dump(metadata, f)
```

Update Makefile pattern rules accordingly.

---

## Troubleshooting Customization

**Environment conflicts**:
```bash
make cleanall
rm env/Manifest.toml
make environment
```

**Makefile syntax errors**:
- Use TAB not spaces for indentation
- Check pattern rule syntax: `target &: prereqs`
- Test with `make -n <target>` (dry run)

**Git issues with provenance**:
```bash
# Reset if needed:
rm -rf output/ paper/provenance.yml
make all
```

---

**See also**:
- [docs/environment.md](docs/environment.md)
- [docs/provenance.md](docs/provenance.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)
