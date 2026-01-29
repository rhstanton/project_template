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
rm -rf .git .env .julia output lib/repro-tools/*

# Initialize as new git repo
git init
git add .
git commit -m "Initial commit from template"

# Let git clone the submodule
git submodule add https://github.com/rhstanton/repro-tools.git lib/repro-tools
make environment
```

**IMPORTANT:** Never manually copy the `lib/repro-tools/` directory contents. Always let git handle submodules.

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

**.github/copilot-instructions.md**:

- [ ] Update project architecture section
- [ ] Add domain-specific conventions
- [ ] Update workflow descriptions

### 2. Configure Environments

**env/python.yml**:
```yaml
name: my_project  # Change project name
channels:
  - conda-forge
dependencies:
  - python=3.11
  # Add your packages:
  - scikit-learn
  - statsmodels
  - seaborn
  # Keep required packages:
  - pandas
  - matplotlib
  - pyyaml
  - jinja2
  - pip:
    - juliacall>=0.9.14
    # Add your pip packages
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

## Domain-Specific Adaptations

### Economics/Econometrics

**Additional packages**:
```yaml
# env/python.yml
dependencies:
  - statsmodels
  - linearmodels
  - scikit-learn
  - pip:
    - pyfixest  # Fast fixed effects
    - doubleml  # Causal ML
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

**Create Dockerfile**:
```dockerfile
FROM condaforge/mambaforge:latest

WORKDIR /project
COPY env/python.yml env/Project.toml ./env/
COPY env/Makefile ./env/

RUN make -C env python-env
RUN make -C env julia-install-via-python

COPY . .

CMD ["make", "all"]
```

**Create .dockerignore**:
```
.env/
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
JUPYTER := .env/bin/jupyter

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

**Q: Can I use environments other than conda?**

A: Yes (venv, poetry, etc.), but update `env/Makefile` accordingly.

**Q: Do I need both Python and Julia?**

A: No - remove Julia if not needed:

1. Remove `juliacall` from `env/python.yml`
2. Delete `env/Project.toml`
3. Remove Julia examples

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
