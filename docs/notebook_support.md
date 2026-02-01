# Jupyter Notebook Support

This template provides **full integration with Jupyter Notebooks** as an alternative to Python scripts for reproducible research analyses.

## Overview

Notebooks are treated as **first-class citizens** alongside `.py` scripts:
- ✅ Same provenance tracking
- ✅ Same Makefile integration
- ✅ Same parameterization system
- ✅ Executed via Papermill (parameterized execution)
- ✅ Output saved to `output/executed_notebooks/`

## Quick Start

### 1. Create Analysis Notebook

Use the provided template:
```bash
cp notebooks/template_analysis.ipynb notebooks/my_analysis.ipynb
```

Or create from scratch with these requirements:
- **Parameters cell** (tagged for papermill)
- Uses `repro_tools.auto_build_record()` for provenance
- Saves outputs to `output/figures/` and `output/tables/`

### 2. Run Interactively (Development)

```bash
jupyter notebook notebooks/my_analysis.ipynb
# Or:
jupyter lab notebooks/my_analysis.ipynb
```

**Important**: Activate environment first:
```bash
conda activate .env
jupyter lab
```

### 3. Run via Makefile (Production)

Add to `shared/config.py`:
```python
ANALYSES["my_analysis"] = {
    "script": "notebooks/my_analysis.ipynb",
    "runner": "$(RUNNOTEBOOK)",
    # ... rest of configuration
}
```

Then build:
```bash
make my_analysis
```

## Architecture

### Priority: .ipynb > .py

When both `analysis.ipynb` and `analysis.py` exist in the same directory:
- **Notebook takes priority** (assumed to be the source)
- `.py` file is likely exported from notebook (e.g., via `jupyter nbconvert`)

### Parameterization with Papermill

Notebooks use **papermill** for parameterized execution:

**Parameters cell** (must be tagged with `parameters`):
```python
# Parameters (tagged for papermill)
study = "example"
data_file = "data/housing.csv"
out_fig = "output/figures/example.pdf"
out_table = "output/tables/example.tex"
out_meta = "output/provenance/example.yml"
```

When executed via papermill, these values are **replaced** with actual parameters from Makefile.

### Directory Structure

```
notebooks/
├── template_analysis.ipynb       # Template for new analyses
├── correlation_analysis.ipynb    # Example: Correlation heatmap
├── my_analysis.ipynb             # Your analyses
└── exploratory/                  # Optional: exploratory notebooks
    └── data_exploration.ipynb

output/
├── executed_notebooks/           # Executed notebook outputs
│   ├── my_analysis.ipynb        # Complete record of execution
│   └── correlation.ipynb
├── figures/                      # Same as Python scripts
├── tables/                       # Same as Python scripts
└── provenance/                   # Same as Python scripts
```

## Workflow Patterns

### Pattern 1: Notebook-Only Analysis

Use notebook for entire workflow:

1. Create `notebooks/my_analysis.ipynb`
2. Tag parameters cell with "parameters"
3. Use `auto_build_record()` at end
4. Add to `shared/config.py`
5. Run: `make my_analysis`

**Outputs**:
- Figure: `output/figures/my_analysis.pdf`
- Table: `output/tables/my_analysis.tex`
- Provenance: `output/provenance/my_analysis.yml`
- Executed notebook: `output/executed_notebooks/my_analysis.ipynb`

### Pattern 2: Interactive Development → Production Build

Development workflow:
```bash
# 1. Interactive development
jupyter lab notebooks/my_analysis.ipynb
# Iterate, test, validate

# 2. Production build
make my_analysis
# Executes with papermill, generates provenance
```

### Pattern 3: Exploratory Notebooks (No Build)

For ad-hoc analysis not in paper:
```bash
# Just run interactively (no Makefile integration)
jupyter lab notebooks/exploratory/data_exploration.ipynb
```

**Not recommended**: Don't add to Makefile unless producing paper outputs.

## Makefile Integration

### Auto-Detection (.ipynb vs .py)

The Makefile automatically detects whether a notebook or Python script should be used:

```makefile
# Makefile automatically selects runner based on file extension
my_analysis.script  := notebooks/my_analysis.ipynb
my_analysis.runner  := $(RUNNOTEBOOK)  # Auto-selected for .ipynb
```

### Multiple Outputs

Notebooks can generate multiple outputs:

```makefile
my_analysis.outputs := $(OUT_FIG_DIR)/fig1.pdf $(OUT_FIG_DIR)/fig2.pdf \\
                      $(OUT_TBL_DIR)/table1.tex $(OUT_TBL_DIR)/table2.tex \\
                      $(OUT_PROV_DIR)/my_analysis.yml \\
                      $(EXEC_NB_DIR)/my_analysis.ipynb
```

### Executed Notebook as Output

The executed notebook is tracked as an output:

```makefile
EXEC_NB_DIR := output/executed_notebooks

my_analysis.outputs := ... $(EXEC_NB_DIR)/my_analysis.ipynb
```

This ensures:
- Executed notebook is part of build artifacts
- Can be inspected for debugging
- Contains full execution history (inputs, outputs, intermediate results)

## Provenance Tracking

Same as Python scripts - use `repro_tools.auto_build_record()`:

```python
from repro_tools import auto_build_record

# At end of notebook
auto_build_record(
    artifact_name=study,
    out_meta=out_meta,
    inputs=[data_file],
    outputs=[out_fig, out_table]
)
```

Generates `output/provenance/<name>.yml` with:
- Git commit hash
- Input/output SHA256 checksums
- Execution timestamp
- Command that was run

## Templates

### Template: Basic Analysis

See `notebooks/template_analysis.ipynb` for complete example:

**Structure**:
1. Parameters cell (tagged)
2. Import libraries
3. Validate parameters
4. Load data
5. Analysis/processing
6. Generate figure
7. Generate table
8. Generate provenance

**Usage**:
```bash
cp notebooks/template_analysis.ipynb notebooks/my_new_analysis.ipynb
# Edit as needed
make my_new_analysis
```

### Template: Correlation Analysis

See `notebooks/correlation_analysis.ipynb` for real example:

**Features**:
- Correlation matrix calculation
- Heatmap visualization (seaborn)
- Summary table of significant correlations
- Full provenance tracking

**Usage**:
```bash
make correlation
```

## VS Code Integration

Notebooks work seamlessly in VS Code:

**Tasks** (`.vscode/tasks.json`):
```json
{
  "label": "Run notebook: correlation",
  "type": "shell",
  "command": "make",
  "args": ["correlation"]
}
```

**Keyboard shortcuts**:
- `Ctrl+Shift+B`: Build current notebook (if configured)
- `F5`: Debug Python cells (experimental)

See [docs/vscode_integration.md](vscode_integration.md) for details.

## Best Practices

### ✅ Do

1. **Tag parameters cell**: Must be tagged with "parameters" for papermill
2. **Use auto_build_record()**: Ensures provenance tracking
3. **Create output directories**: `path.parent.mkdir(parents=True, exist_ok=True)`
4. **Use non-interactive backend**: `matplotlib.use('Agg')` before importing pyplot
5. **Test interactively first**: Run `jupyter lab` before `make` integration
6. **Keep notebooks focused**: One notebook = one analysis (figure + table)

### ❌ Don't

1. **Don't commit executed notebooks**: `output/executed_notebooks/` is gitignored
2. **Don't hardcode paths**: Use parameters passed from Makefile
3. **Don't mix exploration + production**: Keep exploratory notebooks separate
4. **Don't forget provenance**: Always call `auto_build_record()` at end
5. **Don't skip parameter validation**: Check paths exist, types are correct

## Common Issues

### "Kernel died" or "Connection failed"

**Cause**: Environment not activated or Julia bridge misconfigured

**Solution**:
```bash
conda activate .env
jupyter lab
```

Or use `runnotebook` wrapper which handles this.

### Parameters not replaced by papermill

**Cause**: Parameters cell not tagged

**Solution**:
1. Open notebook in Jupyter
2. View → Cell Toolbar → Tags
3. Add "parameters" tag to parameters cell
4. Save notebook

### Import errors in notebook

**Cause**: `PYTHONPATH` not set or wrong environment

**Solution**:
- Use `runnotebook` wrapper (handles `PYTHONPATH`)
- Or activate environment: `conda activate .env`

### Provenance file not generated

**Cause**: `auto_build_record()` not called or failed

**Solution**:
- Check notebook has provenance cell
- Check for errors in executed notebook (`output/executed_notebooks/*.ipynb`)
- Verify output paths are correct

### "No kernel name found in notebook"

**Cause**: Notebook missing kernel metadata (common with VS Code's native notebook format)

**Solution**: Create notebooks with proper kernel metadata using `nbformat`:
```python
import nbformat as nbf

nb = nbf.v4.new_notebook()
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
```

### "KeyError: '__file__'" in provenance cell

**Cause**: Using `auto_build_record()` which tries to access `__file__` (doesn't exist in notebooks)

**Solution**: Use `write_build_record()` instead with explicit parameters:
```python
from repro_tools import write_build_record
from pathlib import Path

write_build_record(
    out_meta=out_meta,
    artifact_name=study,
    command=["papermill", "notebooks/my_analysis.ipynb"],
    repo_root=Path(".").resolve(),
    inputs=[data_file],
    outputs=[out_fig, out_table],
)
```

### CDPATH path pollution in runnotebook

**Cause**: Shell `CDPATH` variable polluting `cd` output in command substitutions

**Fix**: Already fixed in `env/scripts/runnotebook` with `unset CDPATH` at the top of the script. If you see path issues, verify the runnotebook wrapper includes:
```bash
#!/usr/bin/env bash
set -euo pipefail
unset CDPATH  # Prevents path pollution
```

### Make variable expansion issues

**Cause**: Variables like `$($(1).run_cmd)` expanding at wrong time

**Fix**: Already fixed in Makefile using delayed expansion (`$$`) for recipe-time evaluation. The notebook command is constructed correctly using:
```makefile
@set -o pipefail; $$($(1).run_cmd) 2>&1 | tee $(OUT_LOG_DIR)/$(1).log
```

## Migration Guide

### From Python Script to Notebook

1. **Create notebook**:
   ```bash
   cp notebooks/template_analysis.ipynb notebooks/my_analysis.ipynb
   ```

2. **Copy analysis logic** from `.py` script to notebook cells

3. **Add parameters cell** with tagged "parameters"

4. **Update Makefile**:
   ```makefile
   # Before:
   my_analysis.script  := build_my_analysis.py
   my_analysis.runner  := $(PYTHON)
   
   # After:
   my_analysis.script  := notebooks/my_analysis.ipynb
   my_analysis.runner  := $(RUNNOTEBOOK)
   ```

5. **Test**:
   ```bash
   make clean
   make my_analysis
   ```

### From Notebook to Python Script

Sometimes you want a standalone script (e.g., for HPC):

```bash
jupyter nbconvert --to python notebooks/my_analysis.ipynb
# → Creates my_analysis.py

# Edit to add argparse CLI (see existing Python scripts)
```

## Advanced Usage

### Custom Kernel

To use a different kernel (e.g., Julia):

```bash
# Install Julia kernel
julia -e 'using Pkg; Pkg.add("IJulia")'

# Create notebook with Julia kernel
jupyter notebook --kernel=julia-1.11
```

**Note**: Makefile assumes Python notebooks by default. Custom kernels require manual execution.

### Parallel Execution

Run multiple notebooks in parallel:

```bash
make -j4 correlation price_base remodel_base
```

Each notebook executes independently in papermill.

### Conditional Execution

Skip notebook if outputs up-to-date:

```bash
# Makefile automatically checks timestamps
make my_analysis
# → "Nothing to be done for 'my_analysis'"
```

Force rebuild:
```bash
make -B my_analysis
```

## Examples

See `notebooks/` directory:
- `template_analysis.ipynb` - Template for new analyses
- `correlation_analysis.ipynb` - Real analysis example

Run examples:
```bash
make correlation
ls output/figures/correlation.pdf
ls output/tables/correlation.tex
ls output/executed_notebooks/correlation.ipynb
```

## References

- [Papermill documentation](https://papermill.readthedocs.io/)
- [Jupyter documentation](https://jupyter.org/documentation)
- [docs/vscode_integration.md](vscode_integration.md) - VS Code notebook support
- [docs/provenance.md](provenance.md) - Provenance tracking

---

**See also**:
- [README.md](../README.md) - Quick start
- [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Customization
- [docs/directory_structure.md](directory_structure.md) - Project organization
