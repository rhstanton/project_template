# Interactive Jupyter Notebook Workflow

Complete guide to developing, running, and integrating Jupyter notebooks in this reproducible research template.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Interactive Development Workflow](#interactive-development-workflow)
3. [Creating Notebooks](#creating-notebooks)
4. [Editing Notebooks](#editing-notebooks)
5. [Julia Integration](#julia-integration)
6. [Converting to Reproducible Build](#converting-to-reproducible-build)
7. [Best Practices](#best-practices)
8. [Complete Examples](#complete-examples)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Launch Jupyter Lab

```bash
# Activate environment
conda activate .env

# Launch Jupyter Lab
jupyter lab

# Opens browser at http://localhost:8888
```

### Create and Run Notebook

1. **New Launcher** → **Notebook** → **Python 3 (ipykernel)**
2. Write code in cells
3. **Shift+Enter** to run cells
4. **Ctrl+S** to save

### Test Reproducible Build

```bash
# Exit Jupyter (Ctrl+C in terminal)

# Add to Makefile and config.py

# Test build
make my_analysis

# Check outputs
ls output/figures/my_analysis.pdf
ls output/tables/my_analysis.tex
ls output/provenance/my_analysis.yml
```

---

## Interactive Development Workflow

### The Two-Phase Approach

**Phase 1: Interactive Development** (Jupyter Lab)
- Fast iteration
- See outputs inline
- Debug interactively
- Experiment freely
- **NO provenance tracking**

**Phase 2: Reproducible Build** (`make`)
- Full provenance tracking
- Parameters from Makefile
- Git state recorded
- Executed notebook saved
- Reproducible across machines

### Typical Workflow

```bash
# 1. Start Jupyter Lab
conda activate .env
jupyter lab

# 2. Develop interactively
#    - Create notebook
#    - Add cells
#    - Run and test
#    - Iterate until satisfied

# 3. Save and exit
#    Ctrl+S, then Ctrl+C

# 4. Make reproducible
#    - Tag parameters cell
#    - Add provenance cell
#    - Add to Makefile

# 5. Test reproducibility
make my_analysis

# 6. View executed notebook
jupyter lab output/executed_notebooks/my_analysis_executed.ipynb

# 7. Iterate as needed
jupyter lab notebooks/my_analysis.ipynb
# Make changes, save
make my_analysis  # Test again
```

---

## Creating Notebooks

### Method 1: Via Jupyter Lab (Recommended for Interactive)

```bash
conda activate .env
jupyter lab

# File → New → Notebook → Python 3 (ipykernel)
```

**Pros:**
- ✅ Visual interface
- ✅ Immediate feedback
- ✅ Easy cell manipulation
- ✅ Inline outputs

**Cons:**
- ⚠️ May create notebooks without proper metadata for papermill
- ⚠️ Requires manual kernel metadata addition

### Method 2: Programmatically with nbformat (Recommended for Make Integration)

```python
conda activate .env
python << 'EOF'
import nbformat as nbf

# Create notebook with proper metadata
nb = nbf.v4.new_notebook()

# CRITICAL: Set kernel metadata for papermill
nb.metadata = {
    'kernelspec': {
        'display_name': 'Python 3 (ipykernel)',
        'language': 'python',
        'name': 'python3'
    },
    'language_info': {
        'codemirror_mode': {'name': 'ipython', 'version': 3},
        'file_extension': '.py',
        'mimetype': 'text/x-python',
        'name': 'python',
        'nbconvert_exporter': 'python',
        'pygments_lexer': 'ipython3',
        'version': '3.11'
    }
}

# Add markdown cell
nb.cells.append(nbf.v4.new_markdown_cell('# My Analysis'))

# Add parameters cell (tagged for papermill)
params_cell = nbf.v4.new_code_cell(
    'study = "my_analysis"\n'
    'data_file = "data/panel_data.csv"\n'
    'out_fig = "output/figures/my_analysis.pdf"\n'
    'out_table = "output/tables/my_analysis.tex"\n'
    'out_meta = "output/provenance/my_analysis.yml"'
)
params_cell.metadata['tags'] = ['parameters']
nb.cells.append(params_cell)

# Add code cells
nb.cells.append(nbf.v4.new_code_cell('import pandas as pd'))
# ... more cells

# Write to file
with open('notebooks/my_analysis.ipynb', 'w') as f:
    nbf.write(nb, f)
EOF

# Then edit interactively
jupyter lab notebooks/my_analysis.ipynb
```

**Pros:**
- ✅ Proper kernel metadata guaranteed
- ✅ Parameters cell pre-tagged
- ✅ Works with papermill immediately
- ✅ Scriptable/automatable

**Cons:**
- ⚠️ More verbose
- ⚠️ Less visual

### Method 3: Copy Template

```bash
cp notebooks/correlation_analysis.ipynb notebooks/my_analysis.ipynb
jupyter lab notebooks/my_analysis.ipynb
# Edit as needed
```

**Pros:**
- ✅ Fastest way to start
- ✅ Inherits working structure
- ✅ Kernel metadata already correct

---

## Editing Notebooks

### Interactive Editing (Jupyter Lab)

```bash
conda activate .env
jupyter lab notebooks/my_analysis.ipynb
```

**Keyboard shortcuts:**
- `Shift+Enter` - Run cell and move to next
- `Ctrl+Enter` - Run cell and stay
- `A` - Insert cell above
- `B` - Insert cell below
- `M` - Convert to markdown
- `Y` - Convert to code
- `DD` - Delete cell
- `Z` - Undo cell deletion

**Cell toolbar for tags:**
1. View → Cell Toolbar → Tags
2. Click cell
3. Add tag (e.g., "parameters")
4. Save

### Interactive Editing (VS Code)

```bash
code notebooks/my_analysis.ipynb
```

**Requires:** Jupyter extension for VS Code

**Features:**
- ✅ Native notebook interface
- ✅ Variable inspector
- ✅ Debugger support
- ✅ Git integration

**Note:** VS Code's native format may not include kernel metadata. Use `nbformat` to ensure compatibility.

### Programmatic Editing

```python
conda activate .env
python << 'EOF'
import nbformat as nbf

# Read notebook
with open('notebooks/my_analysis.ipynb', 'r') as f:
    nb = nbf.read(f, as_version=4)

# Edit cells
nb.cells.append(nbf.v4.new_code_cell('print("New cell")'))

# Or modify existing
nb.cells[2] = nbf.v4.new_code_cell('# Updated cell')

# Write back
with open('notebooks/my_analysis.ipynb', 'w') as f:
    nbf.write(nb, f)
EOF
```

**Use cases:**
- Bulk edits
- Automation
- Metadata fixes
- CI/CD pipelines

---

## Julia Integration

### Option 1: Julia via juliacall (Recommended)

**Uses Python notebook with Julia backend for computations.**

**Example notebook:** `notebooks/julia_demo.ipynb`

**Setup (already done):**
```bash
# juliacall is already installed via env/python.yml
# Julia is auto-installed to .julia/pyjuliapkg/
```

**Usage in notebook cells:**

```python
# Cell 1: Import Julia
from juliacall import Main as jl
print(f"Julia version: {jl.VERSION}")

# Cell 2: Load Julia packages
jl.seval("using Statistics")

# Cell 3: Use Julia functions
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
julia_mean = jl.mean(arr)
julia_std = jl.std(arr)
print(f"Mean: {julia_mean}, Std: {julia_std}")

# Cell 4: Mix Python and Julia
import pandas as pd
df = pd.read_csv("data/panel_data.csv")
for col in df.select_dtypes(include=['number']).columns:
    arr = np.array(df[col])
    stats = {
        'mean': float(jl.mean(arr)),
        'std': float(jl.std(arr)),
        'median': float(jl.median(arr))
    }
    print(f"{col}: {stats}")
```

**Benefits:**
- ✅ Already configured (no extra setup)
- ✅ Use Julia for performance-critical code
- ✅ Use Python for data I/O and plotting
- ✅ Best of both worlds
- ✅ Works with papermill
- ✅ Full provenance tracking

**When to use:**
- Large numerical computations (Julia is 10-100x faster than Python)
- Matrix operations
- Statistical modeling
- Optimization problems
- Want to leverage Julia packages

**Example build:**
```bash
make julia_demo
ls output/figures/julia_demo.pdf
```

### Option 2: Pure Julia Notebook (Native Kernel)

**Uses IJulia kernel for pure Julia experience.**

**Setup (one-time):**
```bash
# Install IJulia package
env/scripts/runjulia -e 'using Pkg; Pkg.add("IJulia")'

# Install kernel for Jupyter
conda activate .env
env/scripts/runjulia -e 'using IJulia; installkernel("Julia")'

# Verify kernel installed
jupyter kernelspec list
# Should show: julia-1.xx
```

**Create pure Julia notebook:**
```bash
conda activate .env
jupyter lab

# File → New → Notebook → Select "Julia 1.xx" kernel
```

**Example Julia cells:**
```julia
# Cell 1: Load packages
using DataFrames, Statistics, CSV

# Cell 2: Load data
df = CSV.read("data/panel_data.csv", DataFrame)

# Cell 3: Compute statistics
describe(df)

# Cell 4: Advanced analysis
using GLM
model = lm(@formula(y ~ x1 + x2), df)
```

**Limitations:**
- ⚠️ Papermill doesn't support Julia kernels well
- ⚠️ Need custom Makefile integration
- ⚠️ Provenance tracking more complex
- ⚠️ Can't mix Python for plotting easily

**When to use:**
- Pure Julia workflow
- Don't need Python at all
- Want native Julia REPL experience
- Exploratory analysis only (not for reproducible builds)

**Recommendation:** Use Option 1 (Python + juliacall) for reproducible builds. Use Option 2 for exploration only.

---

## Converting to Reproducible Build

### Step 1: Ensure Proper Structure

Your notebook needs:

1. **Kernel metadata** (required by papermill)
2. **Parameters cell** (tagged with "parameters")
3. **Provenance cell** (at the end)
4. **Setup cell** (creates output directories)

### Step 2: Add Parameters Cell

```python
# Tag this cell with "parameters" in Jupyter
study = "my_analysis"
data_file = "data/panel_data.csv"
out_fig = "output/figures/my_analysis.pdf"
out_table = "output/tables/my_analysis.tex"
out_meta = "output/provenance/my_analysis.yml"
```

**In Jupyter Lab:**
1. Select the cell
2. View → Cell Toolbar → Tags
3. Add tag: "parameters"
4. Save notebook

### Step 3: Add Setup Cell (After Parameters)

```python
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from repro_tools import write_build_record

# Create output directories
for p in [Path(out_fig), Path(out_table), Path(out_meta)]:
    p.parent.mkdir(parents=True, exist_ok=True)
```

### Step 4: Add Provenance Cell (Last Cell)

```python
# Generate provenance record
write_build_record(
    out_meta=Path(out_meta),
    artifact_name=study,
    command=["papermill", "notebooks/my_analysis.ipynb"],
    repo_root=Path(".").resolve(),
    inputs=[Path(data_file)],
    outputs=[Path(out_fig), Path(out_table)],
)
print(f"✓ Saved provenance to {out_meta}")
print("🎉 Complete!")
```

**Why `write_build_record()` not `auto_build_record()`?**
- `auto_build_record()` tries to access `__file__` which doesn't exist in notebooks
- `write_build_record()` requires explicit parameters

### Step 5: Add to Makefile

Add variables before the `$(foreach ...)` rule generator (around line 200):

```makefile
# my_analysis (description)
my_analysis.script  := notebooks/my_analysis.ipynb
my_analysis.runner  := $(NOTEBOOK)
my_analysis.inputs  := data/panel_data.csv
my_analysis.outputs := $(OUT_FIG_DIR)/my_analysis.pdf $(OUT_TBL_DIR)/my_analysis.tex $(OUT_PROV_DIR)/my_analysis.yml
my_analysis.args    := my_analysis
```

Add to `ANALYSES` variable (around line 79):

```makefile
ANALYSES := price_base remodel_base correlation julia_demo my_analysis
```

### Step 6: Test Reproducible Build

```bash
make my_analysis

# Check outputs created
ls output/figures/my_analysis.pdf
ls output/tables/my_analysis.tex
ls output/provenance/my_analysis.yml

# View executed notebook
jupyter lab output/executed_notebooks/my_analysis_executed.ipynb
```

---

## Best Practices

### Development Workflow

1. **Start interactive** - Use Jupyter Lab for initial development
2. **Test frequently** - Run cells as you develop
3. **Use markdown** - Document your analysis with markdown cells
4. **Validate early** - Check data loads and basic operations work
5. **Add provenance** - Add provenance cell before first `make` test
6. **Test reproducibility** - Run `make <analysis>` to ensure it works
7. **Iterate** - Continue developing in Jupyter, test with `make` periodically

### Notebook Organization

```
notebooks/
├── correlation_analysis.ipynb    # Production: reproducible builds
├── julia_demo.ipynb              # Production: Julia integration example
├── exploratory/                  # Exploratory: not in Makefile
│   ├── data_exploration.ipynb
│   └── prototyping.ipynb
└── archived/                     # Old versions
    └── old_analysis_v1.ipynb
```

**Production notebooks:**
- Added to Makefile
- Parameters cell tagged
- Provenance cell included
- Tested with `make`

**Exploratory notebooks:**
- NOT in Makefile
- Ad-hoc analysis
- Quick prototyping
- Data exploration

### Code Quality

**DO:**
- ✅ Use `matplotlib.use('Agg')` for non-interactive backend
- ✅ Create output directories before saving files
- ✅ Validate inputs (check files exist, data loads correctly)
- ✅ Print progress indicators
- ✅ Handle errors gracefully
- ✅ Use descriptive variable names
- ✅ Add markdown cells explaining analysis

**DON'T:**
- ❌ Hardcode paths (use parameters)
- ❌ Use interactive plotting backends
- ❌ Skip parameter validation
- ❌ Mix exploration and production in same notebook
- ❌ Commit executed notebooks to git (output/ is gitignored)
- ❌ Forget to tag parameters cell

### Performance Tips

**For large computations:**
- Use Julia via juliacall for numerical work
- Use pandas for data manipulation
- Use numpy arrays for array operations
- Profile code to find bottlenecks

**For long-running notebooks:**
- Add progress indicators (`print()` statements)
- Save intermediate results
- Use checkpoints for expensive computations

---

## Complete Examples

### Example 1: Basic Analysis (Python Only)

See `notebooks/correlation_analysis.ipynb`

**Structure:**
1. Markdown: Introduction
2. Code (tagged "parameters"): Parameters
3. Code: Setup and imports
4. Code: Load data
5. Code: Analysis
6. Code: Generate figure
7. Code: Generate table
8. Code: Provenance

**Build:**
```bash
make correlation
```

**Outputs:**
- `output/figures/correlation.pdf` - Heatmap
- `output/tables/correlation.tex` - Summary table
- `output/provenance/correlation.yml` - Build record
- `output/executed_notebooks/correlation_analysis_executed.ipynb` - Executed version

### Example 2: Julia Integration (Python + juliacall)

See `notebooks/julia_demo.ipynb`

**Structure:**
1. Markdown: Introduction
2. Code (tagged "parameters"): Parameters
3. Code: Setup and imports (Python)
4. Code: Import Julia and load Statistics
5. Code: Load data (pandas)
6. Code: Compute statistics in Julia
7. Code: Plot with matplotlib
8. Code: Save table
9. Code: Provenance

**Build:**
```bash
make julia_demo
```

**Demonstrates:**
- Calling Julia from Python
- Using Julia's Statistics package
- Converting between Python and Julia data structures
- Mixing Python I/O with Julia computation

### Example 3: Creating from Scratch

**Complete workflow:**

```bash
# 1. Create notebook with proper metadata
conda activate .env
python << 'EOF'
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    'kernelspec': {
        'display_name': 'Python 3 (ipykernel)',
        'language': 'python',
        'name': 'python3'
    }
}

nb.cells.append(nbf.v4.new_markdown_cell('# My Custom Analysis'))

params_cell = nbf.v4.new_code_cell(
    'study = "custom"\n'
    'data_file = "data/panel_data.csv"\n'
    'out_fig = "output/figures/custom.pdf"\n'
    'out_table = "output/tables/custom.tex"\n'
    'out_meta = "output/provenance/custom.yml"'
)
params_cell.metadata['tags'] = ['parameters']
nb.cells.append(params_cell)

with open('notebooks/custom.ipynb', 'w') as f:
    nbf.write(nb, f)
EOF

# 2. Develop interactively
jupyter lab notebooks/custom.ipynb
# Add analysis cells, test, save

# 3. Add to Makefile (around line 210)
# custom.script  := notebooks/custom.ipynb
# custom.runner  := $(NOTEBOOK)
# custom.inputs  := data/panel_data.csv
# custom.outputs := $(OUT_FIG_DIR)/custom.pdf $(OUT_TBL_DIR)/custom.tex $(OUT_PROV_DIR)/custom.yml
# custom.args    := custom

# 4. Add to ANALYSES (around line 79)
# ANALYSES := price_base remodel_base correlation julia_demo custom

# 5. Test build
make custom

# 6. Verify outputs
ls output/figures/custom.pdf
ls output/tables/custom.tex
ls output/provenance/custom.yml
```

---

## Troubleshooting

### Issue: "No kernel name found in notebook"

**Cause:** Notebook missing kernel metadata

**Solution:** Create notebook with `nbformat` or copy from template:
```bash
cp notebooks/correlation_analysis.ipynb notebooks/my_analysis.ipynb
```

Or add metadata:
```python
import nbformat as nbf
with open('notebooks/my_analysis.ipynb', 'r') as f:
    nb = nbf.read(f, as_version=4)
    
nb.metadata = {
    'kernelspec': {
        'display_name': 'Python 3 (ipykernel)',
        'language': 'python',
        'name': 'python3'
    }
}

with open('notebooks/my_analysis.ipynb', 'w') as f:
    nbf.write(nb, f)
```

### Issue: "Passed unknown parameter: study"

**Cause:** Parameters cell not tagged

**Solution:** In Jupyter Lab:
1. Select parameters cell
2. View → Cell Toolbar → Tags
3. Add "parameters" tag
4. Save notebook

### Issue: Jupyter won't start

**Cause:** Environment not activated or jupyter not installed

**Solution:**
```bash
conda activate .env
which jupyter  # Should show .env/bin/jupyter
jupyter --version  # Should show version

# If not found:
make environment  # Reinstall environment
```

### Issue: Can't import repro_tools in notebook

**Cause:** PYTHONPATH not set or wrong environment

**Solution:** When using `make`, this is handled automatically. When using Jupyter directly:
```bash
# Ensure you're in project root
cd /path/to/project_template

# Activate environment
conda activate .env

# Launch Jupyter
jupyter lab
```

Or add to notebook:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
```

### Issue: Julia functions not found (e.g., `mean` not defined)

**Cause:** Statistics package not loaded in Julia

**Solution:** Add to notebook:
```python
from juliacall import Main as jl
jl.seval("using Statistics")  # Load Statistics into Main
```

### Issue: Notebook runs in Jupyter but fails with `make`

**Cause:** Hardcoded paths or missing parameters

**Solution:** 
- Use parameters from parameters cell, not hardcoded values
- Ensure all paths are relative to project root
- Check log file: `cat output/logs/<analysis>.log`

### Issue: `make <analysis>` says "Nothing to be done"

**Cause:** Outputs already exist and are up-to-date

**Solution:** Force rebuild:
```bash
rm output/figures/<analysis>.pdf
make <analysis>

# Or force rebuild of everything
make clean
make <analysis>
```

---

## Advanced Topics

### Parameterizing Multiple Outputs

For analyses generating multiple figures:

```python
# Parameters cell
study = "multi_fig"
out_fig_prefix = "output/figures/multi_fig"
out_table = "output/tables/multi_fig.tex"
out_meta = "output/provenance/multi_fig.yml"

# Analysis cell
figures = []
for i, var in enumerate(['var1', 'var2', 'var3']):
    fig_path = Path(f"{out_fig_prefix}_{i+1}.pdf")
    # ... create figure
    fig.savefig(fig_path)
    figures.append(fig_path)

# Provenance cell
write_build_record(
    out_meta=Path(out_meta),
    artifact_name=study,
    command=["papermill", "notebooks/multi_fig.ipynb"],
    repo_root=Path(".").resolve(),
    inputs=[Path(data_file)],
    outputs=figures + [Path(out_table)],
)
```

### Using Different Python Packages

Add to notebook:
```python
# Check if package available
try:
    import some_package
except ImportError:
    print("Installing some_package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "some_package"])
    import some_package
```

Better: Add to `env/python.yml` and run `make environment`

### Mixing Julia and Python Visualizations

```python
# Use Julia for computation
from juliacall import Main as jl
jl.seval("using Statistics")
stats = jl.mean(data)

# Use Python for plotting (better plotting libraries)
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(data)
ax.axhline(float(stats), color='red', label=f'Julia mean: {stats:.2f}')
fig.savefig(out_fig)
```

---

## See Also

- [notebook_support.md](notebook_support.md) - Notebook integration overview
- [provenance.md](provenance.md) - Provenance tracking details
- [julia_python_integration.md](julia_python_integration.md) - Julia/Python bridge
- [vscode_integration.md](vscode_integration.md) - VS Code notebook support
- [Jupyter documentation](https://jupyter.org/documentation)
- [Papermill documentation](https://papermill.readthedocs.io/)
- [nbformat documentation](https://nbformat.readthedocs.io/)
- [juliacall documentation](https://juliapy.github.io/PythonCall.jl/)

---

**Last updated:** February 1, 2026
