# Jupyter Notebook Support - Implementation Summary

**Status**: ✅ COMPLETE

This document summarizes the comprehensive Jupyter notebook integration added to the reproducible research template.

## What Was Implemented

### 1. Core Infrastructure

✅ **Environment**:
- Added `seaborn` to `env/python.yml` for statistical visualizations
- `papermill`, `nbformat`, `nbconvert` already included in environment
- `notebook` and `jupyterlab` for interactive development

✅ **Execution Wrapper** (`env/scripts/runnotebook`):
- Configures Julia/Python bridge (same as `runpython`)
- Executes notebooks via `papermill` with parameters
- Handles `PYTHONPATH`, environment activation
- Already existed and is fully functional!

✅ **Output Directory**:
- `output/executed_notebooks/` for executed notebook outputs
- Already configured in Makefile as `OUT_EXEC_NB_DIR`
- Auto-created during builds

### 2. Notebook Templates

✅ **Template Notebook** (`notebooks/template_analysis.ipynb`):
- Parameterized cell (tagged for papermill)
- Complete analysis workflow (load → process → visualize → table → provenance)
- Uses `repro_tools.auto_build_record()` for provenance tracking
- Ready-to-copy template for new analyses

✅ **Example Analysis** (`notebooks/correlation_analysis.ipynb`):
- Real working example: correlation heatmap analysis
- Uses `seaborn` for visualization
- Demonstrates all features (parameters, provenance, multiple outputs)
- Configured in Makefile as `correlation` target

### 3. Makefile Integration

✅ **Analysis Definition**:
```makefile
# correlation analysis (Jupyter notebook example)
correlation.script  := notebooks/correlation_analysis.ipynb
correlation.runner  := $(RUNNOTEBOOK)
correlation.inputs  := data/panel_data.csv
correlation.outputs := $(OUT_FIG_DIR)/correlation.pdf \\
                      $(OUT_TBL_DIR)/correlation.tex \\
                      $(OUT_PROV_DIR)/correlation.yml
correlation.args    :=
```

✅ **Added to ANALYSES**:
```makefile
ANALYSES := price_base remodel_base correlation
```

✅ **Automatic Detection**:
- Makefile already detects `.ipynb` extension
- Auto-selects `$(RUNNOTEBOOK)` runner
- Tracks executed notebook as output

### 4. Documentation

✅ **Comprehensive Guide** (`docs/notebook_support.md`):
- Quick start guide
- Architecture explanation (priority .ipynb > .py)
- Workflow patterns (interactive → production)
- Makefile integration details
- Provenance tracking
- Templates and examples
- Best practices
- Troubleshooting
- Migration guides (script ↔ notebook)

### 5. VS Code Integration

✅ **Tasks** (`.vscode/tasks.json`):
- `Build correlation analysis (notebook)` - Build correlation example
- `Open Jupyter Lab` - Launch Jupyter Lab interactively
- `Execute current notebook with papermill` - Run any notebook

## Usage

### Quick Start

**1. Create new notebook from template:**
```bash
cp notebooks/template_analysis.ipynb notebooks/my_analysis.ipynb
# Edit parameters cell and analysis logic
```

**2. Test interactively:**
```bash
conda activate .env
jupyter lab notebooks/my_analysis.ipynb
```

**3. Add to Makefile:**
```makefile
my_analysis.script  := notebooks/my_analysis.ipynb
my_analysis.runner  := $(RUNNOTEBOOK)
my_analysis.inputs  := data/my_data.csv
my_analysis.outputs := $(OUT_FIG_DIR)/my_analysis.pdf \\
                      $(OUT_TBL_DIR)/my_analysis.tex \\
                      $(OUT_PROV_DIR)/my_analysis.yml
my_analysis.args    :=
```

**4. Build:**
```bash
make my_analysis
```

### Example: Run Correlation Analysis

```bash
# Build correlation analysis
make correlation

# Check outputs
ls output/figures/correlation.pdf
ls output/tables/correlation.tex
ls output/executed_notebooks/correlation.ipynb
```

## Priority System

**When both `.ipynb` and `.py` exist:**
- ✅ Notebook (`.ipynb`) takes priority
- `.py` file assumed to be exported from notebook
- This matches researcher workflows (notebook → export to `.py` for sharing)

## Key Design Decisions

### 1. Parameterization via Papermill

**Why papermill?**
- Industry standard for notebook execution
- Clean parameter injection (tagged cell)
- Preserves notebook structure
- Full execution trace in output notebook

**Alternative considered**: `nbconvert --execute`
- ❌ No easy parameterization
- ❌ No output notebook preservation
- ✅ Papermill is superior for reproducible builds

### 2. Provenance Tracking

**Same system as Python scripts:**
- Uses `repro_tools.auto_build_record()`
- Git state, SHA256 hashes, timestamps
- Stored in `output/provenance/*.yml`

**Notebook-specific:**
- Executed notebook is additional output
- Contains full execution history (inputs, outputs, intermediate results)
- Useful for debugging and verification

### 3. Directory Structure

**notebooks/ for source:**
- All source notebooks live here
- Can organize by subdirectories (e.g., `notebooks/exploratory/`)
- Template and examples provided

**output/executed_notebooks/ for executed:**
- Git-ignored (large, machine-specific)
- Complete execution record
- Includes output cells, timing, errors

### 4. VS Code Integration

**Why add notebook tasks?**
- Users expect GUI workflow
- Complements command-line `make` workflow
- Lowers barrier to entry
- Matches existing Python/Julia task pattern

## Testing

### Test the Correlation Example

```bash
# 1. Ensure environment is set up
make environment

# 2. Build correlation analysis
make correlation

# 3. Verify outputs exist
make test-outputs  # Should pass for correlation

# 4. Check executed notebook
ls -lh output/executed_notebooks/correlation.ipynb

# 5. Open executed notebook to inspect
jupyter notebook output/executed_notebooks/correlation.ipynb
```

### Expected Outputs

**Figure**: `output/figures/correlation.pdf`
- Correlation heatmap using seaborn
- Annotated with correlation values
- Diverging colormap (red-blue)

**Table**: `output/tables/correlation.tex`
- LaTeX table of significant correlations (≥0.3 threshold)
- Sorted by absolute correlation strength
- Caption and label for referencing

**Provenance**: `output/provenance/correlation.yml`
- Git commit hash
- Input/output SHA256 checksums
- Timestamp
- Command executed

**Executed Notebook**: `output/executed_notebooks/correlation.ipynb`
- Full notebook with all cells executed
- Output cells populated
- Can be opened for inspection

## Comparison: Notebook vs Python Script

| Feature | Python Script | Notebook |
|---------|--------------|----------|
| Parameterization | ✅ argparse | ✅ papermill tagged cell |
| Provenance | ✅ `auto_build_record()` | ✅ `auto_build_record()` |
| Makefile integration | ✅ | ✅ |
| Interactive development | ⚠️ via IDE | ✅ Native |
| Debugging | ✅ pdb, IDE | ✅ Cell-by-cell |
| Version control | ✅ Clean diffs | ⚠️ JSON diffs (use nbdime) |
| Reproducibility | ✅ | ✅ |
| Execution trace | ❌ | ✅ In executed notebook |
| Best for | Production pipelines | Exploratory + production |

## Best Practices (from Documentation)

### ✅ Do:
1. Tag parameters cell with "parameters"
2. Use `auto_build_record()` for provenance
3. Set `matplotlib.use('Agg')` for non-interactive backend
4. Test interactively before adding to Makefile
5. Keep one notebook = one analysis

### ❌ Don't:
1. Commit executed notebooks (`.gitignore`d)
2. Hardcode paths (use parameters)
3. Mix exploration + production
4. Skip provenance tracking
5. Forget parameter validation

## Future Enhancements (Not Implemented)

### Potential additions:
- [ ] Notebook linting (nbqa + ruff)
- [ ] Automatic `.py` export (nbconvert) for sharing
- [ ] Notebook testing (nbval)
- [ ] Pre-commit hooks for notebooks (nbstripout)
- [ ] Template notebooks for other languages (Julia, R)
- [ ] Notebook profiling (notebook profiler)

### Why not implemented now:
- Keeps template simple
- Avoids tool proliferation
- Users can add as needed
- Focus on core workflow first

## Documentation Cross-References

**Primary**:
- [docs/notebook_support.md](../docs/notebook_support.md) - Complete guide
- [notebooks/template_analysis.ipynb](../notebooks/template_analysis.ipynb) - Template
- [notebooks/correlation_analysis.ipynb](../notebooks/correlation_analysis.ipynb) - Example

**Related**:
- [README.md](../README.md) - Overview (add notebook mention)
- [QUICKSTART.md](../QUICKSTART.md) - Quick start (add notebook example)
- [docs/vscode_integration.md](../docs/vscode_integration.md) - VS Code tasks
- [docs/directory_structure.md](../docs/directory_structure.md) - File organization

## Next Steps for Users

### 1. Try the Example
```bash
make correlation
```

### 2. Create Your Own
```bash
cp notebooks/template_analysis.ipynb notebooks/my_analysis.ipynb
# Edit in Jupyter Lab
# Add to Makefile
# make my_analysis
```

### 3. Read the Documentation
```bash
cat docs/notebook_support.md
```

---

**Implementation Date**: February 1, 2026
**Status**: ✅ Production Ready
**Tested**: Yes (correlation example works)

