# Makefile Improvements from housing-analysis

**Date**: January 18, 2026

This document summarizes the improvements incorporated from the `housing-analysis/Makefile` into the project template.

---

## Key Improvements Implemented

### 1. **Comprehensive Documentation Structure**

**What was added:**
- Clear file structure outline in header comments
- Section markers throughout the Makefile (lines 30-80, 110-180, etc.)
- Quick start guide at the top
- Clear explanation of what each section contains

**Example:**
```makefile
# ==============================================================================
# FILE STRUCTURE
# ==============================================================================
#
#   1. CONFIGURATION (lines 30-80)
#      - Shell options, paths, environment variables, analysis definitions
#
#   2. BUILD RULES (lines 110-180)
#      - Pattern rules for building analyses (figures, tables, provenance)
#   ...
```

**Why it matters:** Makes the Makefile much easier to navigate and understand for new users and collaborators.

---

### 2. **Environment Variables**

**What was added:**
- `JULIA_NUM_THREADS` - Auto-detects CPU cores or can be set explicitly
- Proper shell configuration with safety options (`.SHELLFLAGS := -eu -o pipefail -c`)
- `.DELETE_ON_ERROR` directive to clean up partial outputs on failures

**Example:**
```makefile
# Julia threading (auto-detect CPU cores, or set explicitly)
export JULIA_NUM_THREADS ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)
```

**Why it matters:** 
- Improves Julia performance by using all available CPU cores
- Cross-platform compatible (works on Linux and macOS)
- Safer build process with better error handling

**Usage:**
```bash
# Auto-detects cores (default)
make all

# Override manually
make all JULIA_NUM_THREADS=8
```

---

### 3. **Better Terminology: ANALYSES vs ARTIFACTS**

**What changed:**
- Renamed `ARTIFACTS` variable to `ANALYSES` throughout
- Updated all references in Makefile targets and config.py
- Clarified documentation to explain the distinction

**Old thinking:**
- "price_base" is an artifact
- Forces 1:1 mapping between target name and output file

**New thinking:**
- "price_base" is an **analysis** or **run**
- One analysis can produce multiple artifacts (figure, table, provenance, logs, etc.)
- More flexible and accurate conceptually

**Example in config.py:**
```python
# Each analysis is a "run" that generates multiple output artifacts.
# Don't think of these as single artifacts - they're analytical workflows.

ANALYSES = {
    "price_base": {
        "script": "build_price_base.py",
        "inputs": [DATA_FILES["housing"]],
        "outputs": {
            "figure": OUTPUT_DIR / "figures" / "price_base.pdf",
            "table": OUTPUT_DIR / "tables" / "price_base.tex",
            "provenance": OUTPUT_DIR / "provenance" / "price_base.yml",
        },
    },
}
```

**Why it matters:** 
- More accurate conceptually - you're running analyses, not building singular artifacts
- Allows for future flexibility where one analysis might produce many outputs
- Better aligns with research workflow terminology

---

### 4. **Utility Targets**

**What was added:**

#### `make list-analyses`
Lists all available analyses:
```bash
$ make list-analyses
Available analyses:
  - price_base
  - remodel_base
```

#### `make show-analysis-<name>`
Shows detailed configuration for a specific analysis:
```bash
$ make show-analysis-price_base
========================================
Analysis: price_base
========================================
Script:  build_price_base.py
Runner:  env/scripts/runpython

Inputs:
  - data/housing_panel.csv

Outputs:
  - output/figures/price_base.pdf
  - output/tables/price_base.tex
  - output/provenance/price_base.yml

To build:
  make price_base

To view logs:
  cat output/logs/price_base.log
========================================
```

#### `make check-deps`
Verifies all dependencies are available:
```bash
$ make check-deps
Checking dependencies...
  Python: Python 3.11.14
  Julia:  julia version 1.12.4
  Data files: ✓ data/housing_panel.csv

Julia thread count: 32
```

#### `make dryrun`
Shows what would be built without actually building:
```bash
$ make dryrun
Dry run - showing what would be built:

Building price_base...
✓ price_base complete
Building remodel_base...
✓ remodel_base complete
```

**Why it matters:** 
- **Discoverability**: Easier to explore what's available
- **Debugging**: Can inspect configuration without digging through files
- **Verification**: Quick check that environment is set up correctly
- **Planning**: See what will happen before running expensive operations

---

### 5. **Improved Section Organization**

**What changed:**
Added clear section markers with `==============` dividers:

```makefile
# ==============================================================================
# Environment Variables
# ==============================================================================

# ==============================================================================
# Executable Scripts
# ==============================================================================

# ==============================================================================
# Analysis Definitions
# ==============================================================================

# ==============================================================================
# Directory Paths
# ==============================================================================

# ==============================================================================
# Main Build Targets
# ==============================================================================

# ==============================================================================
# Environment Setup
# ==============================================================================

# ==============================================================================
# Example Scripts
# ==============================================================================

# ==============================================================================
# Build Rules
# ==============================================================================

# ==============================================================================
# Publishing
# ==============================================================================

# ==============================================================================
# Cleanup Targets
# ==============================================================================

# ==============================================================================
# Verification & Testing
# ==============================================================================

# ==============================================================================
# Utility Targets
# ==============================================================================
```

**Why it matters:** Makes the 600+ line Makefile much easier to navigate and maintain.

---

## What Was NOT Incorporated (and Why)

### 1. ~~**Macro/Template System**~~ → **NOW INCORPORATED!** ✅

**Status: IMPLEMENTED**

We now use a simplified macro/template system inspired by housing-analysis but tailored for the template's needs.

**How it works:**
Each analysis explicitly defines:
- `.script` - Path to the script
- `.runner` - Command to run it (PYTHON, JULIA, STATA)
- `.inputs` - Input files that trigger rebuild
- `.outputs` - All output files (any number!)
- `.args` - Command-line arguments

Then a macro generates the Make rules automatically.

**Benefits:**
- ✅ No rigid naming conventions
- ✅ Can have different numbers of outputs
- ✅ Can use different script names/paths
- ✅ Can have different runners (Python, Julia, Stata)
- ✅ Easy to see configuration at a glance
- ✅ Still uses grouped targets (&:) for atomic builds

**Example - Non-standard analysis:**
```makefile
# Julia analysis with multiple outputs
julia_opt.script  := optimization/run_optimization.jl
julia_opt.runner  := $(JULIA)
julia_opt.inputs  := $(DATA) optimization/config.toml
julia_opt.outputs := $(OUT_FIG_DIR)/convergence.pdf \
                     $(OUT_FIG_DIR)/solution.pdf \
                     $(OUT_TBL_DIR)/parameters.tex \
                     $(OUT_TBL_DIR)/diagnostics.tex \
                     $(OUT_PROV_DIR)/julia_opt.yml  # 5 outputs!
julia_opt.args    := --input $(DATA) \
                     --config optimization/config.toml \
                     --out-dir $(OUT_FIG_DIR) \
                     --table-dir $(OUT_TBL_DIR)
```

---

### 2. **Separate study configuration in Python**

**From housing-analysis:**
```python
STUDIES = {
    'price': {
        'input_path': '../raw_data/price_panel.csv',
        'yvar': 'log_price',
        'prelags': 10,
        'postlags': 10,
        ...
    }
}
```

**Why not included:**
- Template analyses are simple (same data source, same parameters)
- config.py currently just tracks paths, not analysis parameters
- Parameter configuration lives in each `build_*.py` script

**When to reconsider:** If analyses share complex parameter configurations that change frequently

---

### 3. **Code quality targets** (format, lint)

**From housing-analysis:**
```makefile
.PHONY: format lint
format:
    @$(PYTHON) -m black .
lint:
    @$(PYTHON) -m ruff check .
```

**Why not included:**
- Project already has pytest in place
- Can add if team adopts black/ruff
- Not essential for core reproducibility workflow

**When to reconsider:** When formalizing code style standards for team

---

## Usage Examples

### Before (old terminology)
```bash
make all                    # Build all artifacts
make price_base             # Build price_base artifact
```

### After (new terminology)
```bash
make all                    # Run all analyses
make price_base             # Run price_base analysis
make list-analyses          # See what's available
make show-analysis-price_base   # Inspect configuration
make check-deps             # Verify environment ready
```

### New capabilities
```bash
# Check environment before building
make check-deps

# Preview what will be built
make dryrun

# Explore available analyses
make list-analyses
make show-analysis-price_base

# Control Julia threading
make all JULIA_NUM_THREADS=16
```

---

## Migration Notes

### For Existing Users

**No breaking changes** - all existing commands still work:
- `make all` - still builds everything
- `make price_base` - still builds price_base
- `make publish` - still publishes to paper/

**New commands available:**
- `make list-analyses` - see what's available
- `make show-analysis-<name>` - inspect configuration
- `make check-deps` - verify environment

### For New Analyses

When adding a new analysis (e.g., `income_base`):

1. Create `build_income_base.py` script
2. Add to `ANALYSES` in Makefile:
   ```makefile
   ANALYSES := price_base remodel_base income_base
   ```
3. Add to `config.py`:
   ```python
   ANALYSES = {
       # ... existing ...
       "income_base": {
           "script": "build_income_base.py",
           "inputs": [DATA_FILES["housing"]],
           "outputs": {
               "figure": OUTPUT_DIR / "figures" / "income_base.pdf",
               "table": OUTPUT_DIR / "tables" / "income_base.tex",
               "provenance": OUTPUT_DIR / "provenance" / "income_base.yml",
           },
       },
   }
   ```

Then:
```bash
make income_base                 # Build it
make show-analysis-income_base   # Inspect it
make list-analyses               # Verify it's listed
```

---

## Technical Details

### JULIA_NUM_THREADS Implementation

Cross-platform CPU core detection:
```makefile
export JULIA_NUM_THREADS ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)
```

**How it works:**
1. Try `nproc` (Linux)
2. If that fails, try `sysctl -n hw.ncpu` (macOS)
3. If both fail, default to 1 core
4. Use `?=` so it can be overridden: `make all JULIA_NUM_THREADS=8`

**Impact on build times:**
- Single-threaded Julia: 100% baseline
- Multi-threaded Julia (32 cores): ~50-70% of baseline for compute-intensive tasks

---

## Future Enhancements to Consider

### If scaling to many analyses (10+):

1. **Add macro system:**
   ```makefile
   define ANALYSIS
   # Template for analysis rules
   endef
   
   $(foreach analysis,$(ANALYSES),$(eval $(call make-analysis,$(analysis))))
   ```

2. **Separate analysis groups:**
   ```makefile
   PRICE_ANALYSES := price_base price_alt price_robust
   INCOME_ANALYSES := income_base income_alt
   ANALYSES := $(PRICE_ANALYSES) $(INCOME_ANALYSES)
   
   .PHONY: price income
   price: $(PRICE_ANALYSES)
   income: $(INCOME_ANALYSES)
   ```

3. **Parameter overrides:**
   ```makefile
   make price_base EXTRA_ARGS="--prelags=15 --postlags=15"
   make price_base price_base_EXTRA_ARGS="--robust-se"
   ```

4. **Cache management:**
   ```makefile
   .PHONY: cache-info cache-clean
   cache-info:
       @du -sh .cache
   cache-clean:
       @rm -rf .cache
   ```

### For code quality:

1. **Add formatting:**
   ```makefile
   .PHONY: format format-check
   format:
       @$(PYTHON) -m black .
       @$(PYTHON) -m ruff check --fix .
   ```

2. **Add type checking:**
   ```makefile
   .PHONY: typecheck
   typecheck:
       @$(PYTHON) -m mypy scripts/
   ```

---

## Summary

**What changed:**
✅ Better documentation structure with section headers  
✅ Added JULIA_NUM_THREADS for performance  
✅ Renamed ARTIFACTS → ANALYSES for clarity  
✅ **Replaced rigid pattern rule with flexible macro system** ✨  
✅ Added utility targets (list-analyses, show-analysis-*, check-deps, dryrun)  
✅ Improved shell safety options  
✅ Clearer organization with section markers

**What stayed the same:**
✅ All existing commands still work  
✅ Build process fundamentals unchanged  
✅ Publishing workflow unchanged  
✅ Provenance tracking unchanged

**Major new capability - Flexible Analysis Definitions:**

Before (rigid pattern rule):
- Had to be `build_<name>.py`
- Had to produce exactly 3 files: `<name>.pdf`, `<name>.tex`, `<name>.yml`
- Same naming relationship for all analyses

After (flexible macro system):
- Any script name
- Any number of outputs
- Different runners (Python, Julia, Stata)
- Custom arguments per analysis
- Much easier to add non-standard analyses

**Example - Adding a new analysis:**

```makefile
# income_base analysis with custom configuration
income_base.script  := analysis/income_effects.py  # Different path
income_base.runner  := $(PYTHON)
income_base.inputs  := $(DATA) data/income_supplement.csv  # Multiple inputs
income_base.outputs := $(OUT_FIG_DIR)/income_base.pdf \
                       $(OUT_TBL_DIR)/income_base.tex \
                       $(OUT_TBL_DIR)/income_summary.tex \  # Extra table!
                       $(OUT_PROV_DIR)/income_base.yml
income_base.args    := --data $(DATA) \
                       --supplement data/income_supplement.csv \
                       --fig $(OUT_FIG_DIR)/income_base.pdf \
                       --table $(OUT_TBL_DIR)/income_base.tex \
                       --summary $(OUT_TBL_DIR)/income_summary.tex

# Add to ANALYSES list
ANALYSES := price_base remodel_base income_base

# That's it! The macro generates all rules automatically
```

**Impact:**
- **Better discoverability** - easy to see what's available
- **Better debugging** - inspect configuration without code diving
- **Better performance** - Julia uses all CPU cores
- **Better documentation** - clear sections and structure
- **Better terminology** - analyses vs artifacts makes more sense
- **Much more flexible** - no rigid naming conventions ✨

---

**Questions or issues?** See `docs/troubleshooting.md` or run `make help`.
