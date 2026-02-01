# Flexible Analysis Definitions

**Updated:** January 18, 2026

The Makefile now uses a flexible macro-based system for defining analyses, removing the rigid naming conventions of the old pattern rules.

---

## The Old Way (Rigid Pattern Rule)

```makefile
# Old system - INFLEXIBLE
$(OUT_FIG_DIR)/%.pdf $(OUT_TBL_DIR)/%.tex $(OUT_PROV_DIR)/%.yml &: \
  build_%.py $(DATA)
    $(PYTHON) build_$*.py --data $(DATA) \
      --out-fig $(OUT_FIG_DIR)/$*.pdf \
      --out-table $(OUT_TBL_DIR)/$*.tex
```

**Limitations:**
- ❌ Script MUST be `build_<name>.py`
- ❌ MUST produce exactly 3 files: `<name>.pdf`, `<name>.tex`, `<name>.yml`
- ❌ Same naming relationship for ALL analyses
- ❌ Hard to add analyses with different structures
- ❌ Can't easily see what an analysis does

---

## The New Way (Flexible Macro System)

```makefile
# New system - FLEXIBLE
# Define analysis configuration explicitly
price_base.script  := build_price_base.py
price_base.runner  := $(PYTHON)
price_base.inputs  := $(DATA)
price_base.outputs := $(OUT_FIG_DIR)/price_base.pdf \
                      $(OUT_TBL_DIR)/price_base.tex \
                      $(OUT_PROV_DIR)/price_base.yml
price_base.args    := --data $(DATA) \
                      --out-fig $(OUT_FIG_DIR)/price_base.pdf \
                      --out-table $(OUT_TBL_DIR)/price_base.tex

# Macro automatically generates build rules
$(foreach analysis,$(ANALYSES),$(eval $(call make-analysis-rule,$(analysis))))
```

**Advantages:**
- ✅ Any script name or path
- ✅ Any number of outputs
- ✅ Different configurations per analysis
- ✅ Easy to see what each analysis does
- ✅ Can use different runners (Python, Julia, Stata)
- ✅ Custom arguments per analysis

---

## Examples

### Example 1: Multiple Outputs

```makefile
# Income analysis produces 2 figures + 2 tables
income_effects.script  := analysis/income_analysis.py
income_effects.runner  := $(PYTHON)
income_effects.inputs  := $(DATA) data/income_supplement.csv
income_effects.outputs := $(OUT_FIG_DIR)/income_main.pdf \
                          $(OUT_FIG_DIR)/income_robustness.pdf \
                          $(OUT_TBL_DIR)/income_regression.tex \
                          $(OUT_TBL_DIR)/income_summary.tex \
                          $(OUT_PROV_DIR)/income_effects.yml
income_effects.args    := --data $(DATA) \
                          --supplement data/income_supplement.csv \
                          --output-dir $(OUT_FIG_DIR) \
                          --table-dir $(OUT_TBL_DIR)
```

### Example 2: Julia Runner

```makefile
# High-performance Julia optimization
optimization.script  := optimization/solve.jl
optimization.runner  := $(JULIA)
optimization.inputs  := $(DATA) optimization/config.toml
optimization.outputs := $(OUT_FIG_DIR)/convergence.pdf \
                        $(OUT_TBL_DIR)/solution.tex \
                        $(OUT_PROV_DIR)/optimization.yml
optimization.args    := --data $(DATA) \
                        --config optimization/config.toml \
                        --threads $(JULIA_NUM_THREADS)
```

### Example 3: Different Script Path

```makefile
# Script in subdirectory with non-standard name
mortgage.script  := models/mortgage_did.py  # Not build_*.py!
mortgage.runner  := $(PYTHON)
mortgage.inputs  := data/mortgage_panel.csv
mortgage.outputs := $(OUT_FIG_DIR)/mortgage_default.pdf \
                    $(OUT_FIG_DIR)/mortgage_prepay.pdf \
                    $(OUT_TBL_DIR)/mortgage_regs.tex \
                    $(OUT_PROV_DIR)/mortgage.yml
mortgage.args    := --input data/mortgage_panel.csv \
                    --output-prefix mortgage
```

### Example 4: Stata Analysis

```makefile
# Stata analysis
regs_stata.script  := analysis/baseline_regressions.do
regs_stata.runner  := $(STATA)
regs_stata.inputs  := data/analysis_sample.dta
regs_stata.outputs := $(OUT_TBL_DIR)/baseline_regs.tex \
                      $(OUT_TBL_DIR)/robustness_regs.tex \
                      $(OUT_LOG_DIR)/stata_output.log \
                      $(OUT_PROV_DIR)/regs_stata.yml
regs_stata.args    := # Stata uses global macros, not args
```

---

## Adding a New Analysis

**Step 1:** Define the analysis configuration in Makefile:

```makefile
# Add after existing analyses (e.g., price_base, remodel_base)

# Your new analysis
my_analysis.script  := build_my_analysis.py
my_analysis.runner  := $(PYTHON)
my_analysis.inputs  := $(DATA)
my_analysis.outputs := $(OUT_FIG_DIR)/my_figure.pdf \
                       $(OUT_TBL_DIR)/my_table.tex \
                       $(OUT_PROV_DIR)/my_analysis.yml
my_analysis.args    := --data $(DATA) \
                       --output $(OUT_FIG_DIR)/my_figure.pdf \
                       --table $(OUT_TBL_DIR)/my_table.tex
```

**Step 2:** Add to ANALYSES list:

```makefile
ANALYSES := price_base remodel_base my_analysis
```

**Step 3:** Add to config.py (for provenance):

```python
ANALYSES = {
    # ... existing ...
    "my_analysis": {
        "script": "build_my_analysis.py",
        "inputs": [DATA_FILES["housing"]],
        "outputs": {
            "figure": OUTPUT_DIR / "figures" / "my_figure.pdf",
            "table": OUTPUT_DIR / "tables" / "my_table.tex",
            "provenance": OUTPUT_DIR / "provenance" / "my_analysis.yml",
        },
    },
}
```

**Step 4:** Build it:

```bash
make my_analysis
make show-analysis-my_analysis  # Inspect configuration
```

**That's it!** The macro system automatically generates all the Make rules.

---

## How It Works

### 1. Define Variables

Each analysis defines 5 variables:
- `<name>.script` - Path to executable script
- `<name>.runner` - Command to run it
- `<name>.inputs` - Files that trigger rebuild
- `<name>.outputs` - Files to create
- `<name>.args` - Command-line arguments

### 2. Macro Generates Rules

The `make-analysis-rule` macro converts these variables into Make rules:

```makefile
define make-analysis-rule
# Grouped target: all outputs built together
$($(1).outputs) &: $($(1).script) $($(1).inputs)
    $($(1).runner) $($(1).script) $($(1).args)

# Phony target (e.g., "make price_base")
.PHONY: $(1)
$(1): $($(1).outputs)
endef
```

### 3. Apply to All Analyses

One line applies the macro to every analysis:

```makefile
$(foreach analysis,$(ANALYSES),$(eval $(call make-analysis-rule,$(analysis))))
```

---

## Advantages Over Pattern Rules

### Pattern Rules (Old):
```makefile
%.pdf %.tex: build_%.py
    $(PYTHON) build_$*.py
```

**Pros:**
- Concise

**Cons:**
- Inflexible naming
- Can't vary number of outputs
- Hard to see what's configured
- Can't use different runners easily

### Macro System (New):
```makefile
price_base.script := build_price_base.py
price_base.outputs := fig.pdf table.tex
```

**Pros:**
- Explicit configuration
- Any number of outputs
- Easy to see what's happening
- Different configurations per analysis
- Self-documenting

**Cons:**
- Slightly more verbose

**Verdict:** The flexibility and clarity are worth the extra lines.

---

## Utility Commands

The macro system works seamlessly with utility targets:

```bash
# List all analyses
make list-analyses
make list-analyses-verbose  # With configuration details

# Inspect specific analysis
make show-analysis-price_base
# Shows:
#   - Script path
#   - Runner command
#   - Input files
#   - Output files
#   - Arguments

# Check dependencies
make check-deps

# Dry run (see what would be built)
make dryrun
```

---

## Grouped Targets Still Work

The macro system still uses grouped targets (`&:`):

```makefile
$($(1).outputs) &: $($(1).script) $($(1).inputs)
```

This means **all outputs are built by one command**, ensuring atomicity:
- Either all outputs are created, or none are
- No partial/inconsistent states
- Requires GNU Make 4.3+

---

## Comparison with housing-analysis

**housing-analysis approach:**
```makefile
# Very powerful but complex
define DID_ANALYSIS
$(call ANALYSIS,$(1),$(2),$(if $(3),--filter=shared.processing:$(3)) $(4))
endef

$(call DID_ANALYSIS,price_base,price,process_price,--prelags=10)
```

**Our approach:**
```makefile
# Simpler and more explicit
price_base.script  := build_price_base.py
price_base.args    := --data $(DATA) --prelags=10
```

**Why different:**
- housing-analysis has 43 analyses with shared configuration
- Template has 2-5 analyses with independent configuration
- Simpler = better for a template

**When to reconsider:** If you scale to 20+ analyses with shared patterns, adopt housing-analysis's approach.

---

## Migration from Old Pattern Rule

If you have existing analyses using the old pattern rule:

**Before:**
```makefile
# Pattern rule
$(OUT_FIG_DIR)/%.pdf $(OUT_TBL_DIR)/%.tex: build_%.py
    $(PYTHON) build_$*.py
```

**After:**
```makefile
# Explicit definition
my_analysis.script  := build_my_analysis.py
my_analysis.runner  := $(PYTHON)
my_analysis.inputs  := $(DATA)
my_analysis.outputs := $(OUT_FIG_DIR)/my_analysis.pdf \
                       $(OUT_TBL_DIR)/my_analysis.tex
my_analysis.args    := --data $(DATA)
```

**No code changes needed** - just convert pattern to explicit variables.

---

## Tips

### Tip 1: Use backslash for multi-line definitions

```makefile
analysis.outputs := $(OUT_FIG_DIR)/fig1.pdf \
                    $(OUT_FIG_DIR)/fig2.pdf \
                    $(OUT_TBL_DIR)/table.tex \
                    $(OUT_PROV_DIR)/analysis.yml
```

### Tip 2: Reference other variables

```makefile
SIZE_DATA := data/size_panel.csv

size_analysis.inputs := $(SIZE_DATA) scripts/helpers.py
```

### Tip 3: Check configuration before building

```bash
make show-analysis-my_analysis  # Inspect
make dryrun                      # Preview
make my_analysis                 # Build
```

### Tip 4: Keep related analyses together

```makefile
# ---- Price Analyses ----
price_base.script := ...
price_robust.script := ...

# ---- Size Analyses ----
size_base.script := ...
```

---

## Selective Publishing

With flexible analyses that can have many outputs, you often want to publish only a subset to the paper.

### Analysis-Level Selection (Default)

Publish all outputs from specific analyses:

```bash
# Publish everything from price_base and remodel_base
make publish PUBLISH_ARTIFACTS="price_base remodel_base"
```

### File-Level Selection (Fine-Grained)

Publish only specific files:

```bash
# Example: Analysis generates 5 figures but only want 2 in paper
make detailed_analysis  # Creates 5 figures

# Publish only specific figures
make publish PUBLISH_FILES="output/figures/detailed_analysis_fig1.pdf output/figures/detailed_analysis_fig3.pdf"
```

**Common scenarios:**
- Analysis generates multiple figures but paper only uses some
- Want appendix materials separate from main paper
- Different output subsets for paper vs. supplementary materials

**Provenance tracking**: File-level publications are tracked in `paper/provenance.yml` under `files:` section with links to source analysis.

---

## Summary

The new macro-based system gives you:

✅ **Flexibility** - No rigid naming conventions
✅ **Clarity** - See exactly what each analysis does
✅ **Extensibility** - Easy to add new analyses
✅ **Power** - Multiple outputs, different runners, custom args
✅ **Simplicity** - No complicated pattern matching

While keeping:

✅ **Atomicity** - Grouped targets still work
✅ **Dependencies** - Proper rebuilds on changes
✅ **Provenance** - Full tracking maintained
✅ **Simplicity** - Easy to understand and maintain

**Bottom line:** Much more flexible without sacrificing clarity or safety.

---

**See also:**
- [docs/makefile_improvements.md](makefile_improvements.md) - Full list of improvements
- [docs/publishing.md](publishing.md) - Complete publishing workflow guide
- [Makefile](../Makefile) - Lines 168-255 for macro definitions
- `make show-analysis-price_base` - Live example
