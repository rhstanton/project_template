# 3-Level Defaults System

This document explains how defaults are resolved with multiple priority levels.

## Overview

The template implements a **3-level defaults system** inspired by the fire/housing-analysis project, allowing you to define defaults at multiple levels and override them flexibly.

**Priority order (lowest to highest)**:
1. **Docopt defaults** (in `run_analysis.py` docstring)
2. **`config.DEFAULTS`** (in `shared/config.py`)
3. **`config.STUDIES[study]`** (study-specific config)
4. **Command-line arguments** (via `EXTRA_ARGS` or direct flags)

Later levels override earlier ones.

---

## Level 1: Docopt Defaults

Defined in the docstring of `run_analysis.py`:

```python
Options:
  ...
  --table-agg=<fn>   Override table aggregation (mean|sum|median|count|std|min|max) [default: mean]
```

These are the **lowest priority** and apply when nothing else is specified.

**Usage**: Automatic, no action needed.

---

## Level 2: Global Defaults (`config.DEFAULTS`)

Defined in `shared/config.py`:

```python
DEFAULTS = {
    "data": DATA_FILES["housing"],  # Default data source
    "xlabel": "Year",  # Default x-axis label
    "ylabel": "Value",  # Default y-axis label
    "title": "Analysis",  # Default plot title
    "groupby": "region",  # Default grouping variable
    "xvar": "year",  # Default x-axis variable
    "table_agg": "mean",  # Default table aggregation function
}
```

These apply to **all studies** unless overridden by study-specific config or command-line args.

**Usage**: Edit `shared/config.py` to change global defaults.

**When to use**: 
- Common settings shared across most/all studies
- Project-wide conventions (e.g., all analyses use the same data file)

---

## Level 3: Study-Specific Config (`config.STUDIES`)

Defined in `shared/config.py`:

```python
STUDIES = {
    "price_base": {
        # Only specify what differs from DEFAULTS
        "ylabel": "Price index",  # Override default ylabel
        "title": "Price index over time",  # Override default title
        "yvar": "price_index",  # Study-specific outcome variable
        "figure": OUTPUT_DIR / "figures" / "price_base.pdf",
        "table": OUTPUT_DIR / "tables" / "price_base.tex",
        # Inherits: data, xlabel, groupby, xvar, table_agg from DEFAULTS
    },
}
```

These override `DEFAULTS` for a specific study.

**Usage**: Edit `shared/config.py` to add/modify studies.

**When to use**:
- Study-specific parameters (e.g., different outcome variable)
- Required unique values (output paths must differ per study)

**Best practice**: Only specify values that **differ from DEFAULTS**. This keeps the config DRY (Don't Repeat Yourself).

---

## Level 4: Command-Line Arguments (Highest Priority)

### Direct command-line flags

```bash
env/scripts/runpython run_analysis.py price_base --ylabel="Custom Label" --table-agg=sum
```

### Via Make with `EXTRA_ARGS` (global)

```bash
make price_base EXTRA_ARGS="--ylabel='Custom Label' --table-agg=sum"
```

Applies to **all analyses** in the make command.

### Via Make with `<analysis>_EXTRA_ARGS` (analysis-specific)

```bash
make price_base price_base_EXTRA_ARGS="--title='My Custom Title'"
```

Applies only to the specific analysis.

**When to use**:
- Quick one-off experiments without editing config files
- Testing different parameters
- Sensitivity analyses with varying parameters

---

## Example: How Defaults Are Resolved

Given:

**Docopt default**: `--table-agg=<fn> [default: mean]`

**config.DEFAULTS**:
```python
DEFAULTS = {
    "ylabel": "Value",
    "table_agg": "mean",
}
```

**config.STUDIES["price_base"]**:
```python
"price_base": {
    "ylabel": "Price index",
    # table_agg not specified, inherits from DEFAULTS
}
```

**Command**: `make price_base EXTRA_ARGS="--table-agg=sum"`

**Final configuration**:
- `ylabel`: `"Price index"` (from STUDIES, overrides DEFAULTS)
- `table_agg`: `"sum"` (from EXTRA_ARGS, overrides everything)

---

## Practical Examples

### Example 1: Test Different Aggregations

```bash
# Test with sum
make price_base EXTRA_ARGS="--table-agg=sum"

# Test with median
make price_base EXTRA_ARGS="--table-agg=median"

# Test with standard deviation
make price_base EXTRA_ARGS="--table-agg=std"
```

No need to edit config files!

### Example 2: Custom Labels for Presentation

```bash
make price_base EXTRA_ARGS="--xlabel='Year' --ylabel='Housing Price Index (2018=100)' --title='California Housing Prices'"
```

### Example 3: Different Data File

```bash
make price_base EXTRA_ARGS="--data=data/alternative_data.csv"
```

### Example 4: Analysis-Specific Override

```bash
# Different title for price_base only
make price_base price_base_EXTRA_ARGS="--title='Main Result'"

# Different title for remodel_base only  
make remodel_base remodel_base_EXTRA_ARGS="--title='Robustness Check'"
```

### Example 5: Global + Analysis-Specific

```bash
# Apply --ylabel to all, but custom title to price_base only
make all EXTRA_ARGS="--ylabel='Custom Y'" price_base_EXTRA_ARGS="--title='Special Title'"
```

---

## Implementation Details

### How `build_config()` Works

In `run_analysis.py`:

```python
def build_config(study_name: str, args: dict) -> dict:
    """
    Build configuration with 3-level priority:
      1. config.DEFAULTS (lowest)
      2. config.STUDIES[study_name] (medium)
      3. Command-line args (highest)
    """
    # Start with global defaults
    cfg = config.DEFAULTS.copy()
    
    # Override with study-specific config
    if study_name in config.STUDIES:
        cfg.update(config.STUDIES[study_name])
    
    # Override with command-line arguments (if provided)
    override_map = {
        "--data": "data",
        "--yvar": "yvar",
        "--xvar": "xvar",
        # ... etc
    }
    
    for arg_name, cfg_key in override_map.items():
        if args.get(arg_name):
            cfg[cfg_key] = args[arg_name]
    
    return cfg
```

### How Makefile Passes `EXTRA_ARGS`

In `Makefile`:

```makefile
# Global variable
EXTRA_ARGS ?=

# Analysis-specific variable (auto-defined per analysis)
# price_base_EXTRA_ARGS, remodel_base_EXTRA_ARGS, etc.

# Command construction
$($(1).runner) $($(1).script) $($(1).args) $(EXTRA_ARGS) $($(1)_EXTRA_ARGS)
```

---

## Available Override Flags

All these can be used with `EXTRA_ARGS` or `<analysis>_EXTRA_ARGS`:

- `--data=<path>` - Override input data file
- `--yvar=<name>` - Override outcome variable
- `--xvar=<name>` - Override x-axis variable
- `--groupby=<name>` - Override grouping variable
- `--xlabel=<text>` - Override x-axis label
- `--ylabel=<text>` - Override y-axis label
- `--title=<text>` - Override plot title
- `--table-agg=<fn>` - Override table aggregation (mean|sum|median|count|std|min|max)
- `--figure=<path>` - Override figure output path
- `--table=<path>` - Override table output path

---

## Best Practices

### 1. Use DEFAULTS for Common Values

```python
# ✅ GOOD: Define once in DEFAULTS
DEFAULTS = {
    "data": DATA_FILES["housing"],
    "xlabel": "Year",
    "groupby": "region",
}

STUDIES = {
    "price_base": {
        "yvar": "price_index",  # Only study-specific
        ...
    },
    "remodel_base": {
        "yvar": "remodel_rate",  # Only study-specific
        ...
    },
}
```

```python
# ❌ BAD: Repeat in every study
STUDIES = {
    "price_base": {
        "data": DATA_FILES["housing"],  # Repeated!
        "xlabel": "Year",               # Repeated!
        "groupby": "region",            # Repeated!
        "yvar": "price_index",
        ...
    },
}
```

### 2. Use EXTRA_ARGS for Experiments

Don't edit config files for one-off tests:

```bash
# ✅ GOOD: Quick test without editing files
make price_base EXTRA_ARGS="--table-agg=median"

# ❌ BAD: Edit config.py just to test median
# (then forget to change it back)
```

### 3. Document Non-Obvious Defaults

```python
DEFAULTS = {
    "table_agg": "mean",  # Use mean not median (matches paper convention)
    "groupby": "region",  # Region-level aggregation throughout
}
```

### 4. Keep Studies DRY

```python
# ✅ GOOD: Minimal, only what differs
"price_base": {
    "yvar": "price_index",
    "ylabel": "Price index",
    "title": "Price index over time",
    "figure": OUTPUT_DIR / "figures" / "price_base.pdf",
    "table": OUTPUT_DIR / "tables" / "price_base.tex",
}

# ❌ BAD: Repeating DEFAULTS values
"price_base": {
    "data": DATA_FILES["housing"],  # From DEFAULTS
    "xlabel": "Year",               # From DEFAULTS
    "xvar": "year",                 # From DEFAULTS
    "groupby": "region",            # From DEFAULTS
    "table_agg": "mean",            # From DEFAULTS
    "yvar": "price_index",          # Actually needed
    ...
}
```

---

## Troubleshooting

### "My override isn't working!"

**Check**:
1. Are you using the correct flag name? (e.g., `--ylabel` not `--y-label`)
2. Are you quoting correctly? Use `EXTRA_ARGS="--title='My Title'"` not `EXTRA_ARGS=--title='My Title'`
3. Is the analysis name correct? (`price_base_EXTRA_ARGS` not `pricebase_EXTRA_ARGS`)

### "I changed DEFAULTS but nothing changed"

**Remember**: STUDIES overrides DEFAULTS. If the study explicitly sets a value, DEFAULTS won't affect it.

**Fix**: Remove the explicit value from STUDIES to let it inherit from DEFAULTS.

### "Multiple studies ignoring EXTRA_ARGS"

**Cause**: You might be using `<analysis>_EXTRA_ARGS` which only applies to one analysis.

**Fix**: Use global `EXTRA_ARGS` instead:

```bash
# ✅ Applies to all
make all EXTRA_ARGS="--ylabel='Common Label'"

# ❌ Only applies to price_base
make all price_base_EXTRA_ARGS="--ylabel='Common Label'"
```

---

## Testing the System

Run the test suite:

```bash
make test
```

Tests for defaults system are in `tests/test_defaults.py`:
- `TestDefaultsPriority` - Tests the 3-level merge logic
- `TestCommandLineOverrides` - Tests command-line argument handling
- `TestMakefileExtraArgs` - Tests Makefile EXTRA_ARGS passing

Manual testing:

```bash
# 1. Check DEFAULTS are used
make price_base
grep "mean_price_index" output/tables/price_base.tex  # Should find (uses default agg)

# 2. Check EXTRA_ARGS override
make clean
make price_base EXTRA_ARGS="--table-agg=sum"
grep "sum_price_index" output/tables/price_base.tex  # Should find (overridden)

# 3. Check analysis-specific EXTRA_ARGS
make clean
make price_base price_base_EXTRA_ARGS="--table-agg=median"
grep "median_price_index" output/tables/price_base.tex  # Should find
```

---

## See Also

- [README.md](../README.md) - Project overview
- [shared/config.py](../shared/config.py) - DEFAULTS and STUDIES definitions
- [run_analysis.py](../run_analysis.py) - build_config() implementation
- [Makefile](../Makefile) - EXTRA_ARGS passing logic
- [tests/test_defaults.py](../tests/test_defaults.py) - Test suite for defaults system

---

**Last updated**: January 19, 2026
