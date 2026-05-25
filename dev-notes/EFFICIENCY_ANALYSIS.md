# Template Efficiency Analysis

**Goal**: Identify opportunities to make the template more efficient and reduce duplication across projects.

## Executive Summary

The template is already quite well-organized with good use of the repro-tools submodule. However, there are several opportunities to make it even more efficient:

### High Impact Improvements

1. **Create a Makefile library in repro-tools** (~50% reduction in Makefile size)
2. **Move more boilerplate to repro-tools** (eliminate shared/ directory duplication)
3. **Create template scaffolding tool** (automate new project setup)
4. **Standardize configuration pattern** (single source of truth)

### Estimated Reductions

- **Makefile**: From 1022 lines → ~400 lines (60% reduction)
- **Boilerplate code**: Eliminate ~200 lines of duplicated Python
- **Setup time**: From manual copying → single command
- **Maintenance**: Update once in repro-tools vs. every project

---

## Detailed Analysis

### 1. Makefile Duplication (HIGH PRIORITY)

**Current State**: 1022-line Makefile with much generic content

**Problem Areas**:

#### Generic Targets (Lines 137-400+)
These targets are identical across projects:
- `environment` setup
- `examples` runners (sample-python, sample-julia, etc.)
- `verify` checks
- `test` infrastructure
- `lint`, `format`, `type-check`, `check`
- `system-info`, `diff-outputs`, `pre-submit`
- `journal-package` creation
- `clean`, `cleanall`
- `help`, `info`, `default` displays

**These represent ~400-500 lines of boilerplate.**

#### Project-Specific Content (Lines 60-280)
Only these parts are truly project-specific:
- Analysis definitions (ANALYSES variable + configurations)
- Input data files (DATA variable)
- Build rule macro (make-analysis-rule)
- Publishing configuration

**Proposed Solution**: Create `repro-tools/lib/common.mk`

```makefile
# In project Makefile (reduced to ~400 lines):
include lib/repro-tools/lib/common.mk

# Only define project-specific parts:
ANALYSES := price_base remodel_base
DATA := data/housing_panel.csv

price_base.script := run_analysis.py
price_base.args := price_base
# ... etc

# All generic targets come from common.mk
```

**Benefits**:
- ✅ Projects only maintain ~400 lines vs 1022
- ✅ Updates to generic targets happen once in repro-tools
- ✅ Easier to maintain consistency across projects
- ✅ Less cognitive load for researchers

**Implementation Complexity**: Medium (requires careful design of include file)

---

### 2. Shared Python Utilities Duplication (MEDIUM PRIORITY)

**Current State**: `shared/` directory with project-specific wrappers

**Files in shared/**:
- `config.py` - Project-specific (good, keep)
- `config_validator.py` - Generic wrapper around repro_tools.validation (duplicative)
- `__init__.py` - Boilerplate

**Problem**: `config_validator.py` reimplements validation logic that's already in repro_tools

**Proposed Solution**: Move to repro-tools

```python
# Option A: Use repro_tools.validation directly in run_analysis.py
from repro_tools.validation import validate_study_config

errors = validate_study_config(config, study_name)

# Option B: Keep thin wrapper but make it truly minimal
# shared/config_validator.py (5 lines instead of 89)
from repro_tools.validation import validate_study_config as validate_config
```

**Benefits**:
- ✅ Eliminate ~70 lines of duplicated validation logic
- ✅ Validation improvements benefit all projects automatically
- ✅ Less to maintain per project

**Implementation Complexity**: Low

---

### 3. CLI Utilities Already in repro-tools (LOW PRIORITY)

**Current State**: Template uses repro-tools CLI utilities

**Good News**: No duplication here! The template correctly uses:
- `repro_tools.cli_utils.friendly_docopt()` ✅
- `repro_tools.validation` functions ✅
- `$(PYTHON) -m repro_tools.cli publish` ✅

**Recommendation**: Keep as-is. This is the right pattern.

---

### 4. Environment Setup Duplication (MEDIUM PRIORITY)

**Current State**: Each project has `env/` directory with:
- `Makefile` (200 lines)
- `python.yml` (mostly standard packages)
- `Project.toml` (mostly standard packages)
- `scripts/runpython`, `runjulia`, `runstata` (boilerplate)

**Problem**: Environment specs are 80% identical across projects

**Proposed Solution**: Template inheritance pattern

```yaml
# env/python.yml (project-specific, ~20 lines)
name: my_project
channels:
  - conda-forge

# Inherit base environment
dependencies:
  - repro-tools-base-env  # Meta-package with common deps

  # Project-specific additions
  - scikit-learn
  - some-specialized-package
```

**Alternative**: Environment generator in repro-tools

```bash
# From template
repro-tools init-project my_project --languages python,julia,stata

# Creates minimal env/ with inheritance from repro-tools
```

**Benefits**:
- ✅ Less boilerplate per project
- ✅ Easier to update base environment across projects
- ✅ Clear separation of standard vs project-specific deps

**Implementation Complexity**: High (requires conda meta-package or custom tooling)

---

### 5. Configuration Pattern Duplication (HIGH PRIORITY)

**Current State**: Configuration spread across multiple files
- `shared/config.py` - Study definitions
- `Makefile` - Duplicate analysis definitions
- `run_analysis.py` - Parsing logic

**Problem**: Triple maintenance burden when adding new analysis

**Example - Current process to add analysis**:
1. Add to `config.STUDIES` dictionary (config.py)
2. Add to `ANALYSES` variable (Makefile)
3. Add pattern definition (Makefile, 5 lines)

**Proposed Solution**: Single source of truth

```python
# shared/config.py
from repro_tools import Analysis

ANALYSES = {
    "price_base": Analysis(
        script="run_analysis.py",
        args=["price_base"],
        data=DATA_FILES["housing"],
        # Study-specific parameters
        xlabel="Year",
        ylabel="Price index",
        # ... auto-generates Makefile rules
    )
}

# Export for Makefile
if __name__ == "__main__":
    from repro_tools.makefile import export_analyses
    export_analyses(ANALYSES)
```

```makefile
# Makefile - auto-generated rules
# Generated by: python shared/config.py > .makefile-analyses
include .makefile-analyses

# Or use Make's $(shell ...) to generate inline
$(eval $(shell $(PYTHON) -m repro_tools.makefile shared/config.py))
```

**Benefits**:
- ✅ Define analysis once (not three times)
- ✅ Type-safe configuration
- ✅ Auto-generate Makefile rules
- ✅ Easier to maintain

**Implementation Complexity**: Medium-High

---

### 6. Template Scaffolding (HIGH PRIORITY)

**Current State**: Manual template copying via GitHub template or git clone

**Problem**: Researchers must:
1. Clone template
2. Delete example files
3. Update multiple configuration files
4. Search-and-replace project name
5. Risk leaving template artifacts

**Proposed Solution**: Scaffolding CLI tool

```bash
# Install
pip install repro-tools[template]

# Create new project
repro-tools new-project \
  --name "Housing Price Analysis" \
  --slug housing-price \
  --languages python,julia \
  --template minimal

# Interactive mode
repro-tools new-project --interactive

# Questions:
# > Project name? Housing Price Analysis
# > Project slug? housing-price
# > Languages? (python/julia/stata) python,julia
# > Template? (minimal/full/teaching) minimal
# > Initialize git? yes
# > Create paper/ as submodule? no

# Creates:
housing-price/
  ├── Makefile (includes repro-tools/lib/common.mk)
  ├── shared/config.py (stub)
  ├── data/ (empty)
  ├── lib/repro-tools/ (git submodule)
  └── env/ (minimal, inherits from repro-tools)
```

**Benefits**:
- ✅ Zero manual editing required
- ✅ Consistent project structure
- ✅ No leftover template artifacts
- ✅ Choice of templates (minimal/full/teaching)

**Implementation Complexity**: Medium

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (Week 1)

1. **Move validation to repro-tools** (2 hours)
   - Enhance `repro_tools.validation.validate_study_config()`
   - Update template to use it directly
   - Remove `shared/config_validator.py`

2. **Document current best practices** (2 hours)
   - Add "Creating New Projects" guide
   - Explain minimal vs full setup
   - Template customization patterns

### Phase 2: Makefile Library (Week 2-3)

3. **Create repro-tools/lib/common.mk** (1 week)
   - Extract generic targets from template Makefile
   - Test with 2-3 real projects
   - Document override patterns

4. **Update template to use common.mk** (2 days)
   - Reduce template Makefile to ~400 lines
   - Update documentation
   - Test all workflows

**Deliverable**: Template Makefile reduced by 60%

### Phase 3: Enhanced Automation (Month 2)

5. **Single-source configuration** (1 week)
   - Design `Analysis` class in repro-tools
   - Implement Makefile rule generation
   - Migrate template

6. **Scaffolding tool** (2 weeks)
   - Create `repro-tools new-project` CLI
   - Support minimal/full templates
   - Interactive mode

**Deliverable**: 10-second project creation vs 30 minutes

### Phase 4: Environment Optimization (Month 3, Optional)

7. **Base environment meta-package** (2 weeks)
   - Create conda meta-package: repro-tools-base-env
   - Publish to conda-forge
   - Update template to inherit

**Deliverable**: Smaller, more maintainable env/ directories

---

## Metrics for Success

### Before (Current)

- **New project setup**: 30 minutes manual work
- **Makefile maintenance**: 1022 lines per project
- **Shared code**: ~200 lines duplicated Python
- **Adding analysis**: Edit 3 files (config.py, Makefile x2)
- **Template updates**: Manual propagation to each project

### After (Target)

- **New project setup**: 10 seconds (`repro-tools new-project`)
- **Makefile maintenance**: ~400 lines per project (-60%)
- **Shared code**: ~50 lines (just project config)
- **Adding analysis**: Edit 1 file (config.py) + auto-generate
- **Template updates**: Update repro-tools once, projects get it automatically

### Return on Investment

**One-time cost**: ~6 weeks engineering
**Ongoing savings**: 
- 20 minutes per new project (setup)
- 5 minutes per analysis addition
- 30 minutes per template update (propagated to all projects)

**Break-even**: After ~10 projects or ~20 template updates

---

## Alternative: Keep Current Approach

**Arguments for status quo**:
- ✅ Current template is already quite good
- ✅ Researchers can see all code (no magic)
- ✅ Easy to customize (no abstraction layers)
- ✅ Works well for small number of projects

**Arguments for optimization**:
- ✅ Scales to many projects (lab with 10+ active projects)
- ✅ Easier onboarding (less overwhelming)
- ✅ Consistent best practices automatically
- ✅ Less maintenance burden over time

**Recommendation**: Implement Phase 1-2 (quick wins + Makefile library) regardless. These are low-risk, high-reward improvements that don't increase complexity for users.

Phase 3-4 (automation + environment) can wait until you have 3+ active projects to validate the patterns.

---

## Appendix: File-by-File Duplication Analysis

### High Duplication (Remove from template)

| File | Lines | Duplication | Action |
|------|-------|-------------|--------|
| Makefile (generic targets) | ~600 | 90% | → Move to common.mk |
| shared/config_validator.py | 89 | 80% | → Use repro_tools.validation |
| env/scripts/runpython | 50 | 95% | → Move to repro-tools/bin/ |
| env/scripts/runjulia | 40 | 95% | → Move to repro-tools/bin/ |

### Medium Duplication (Simplify)

| File | Lines | Duplication | Action |
|------|-------|-------------|--------|
| env/Makefile | 200 | 70% | → Template inheritance |
| env/python.yml | 60 | 50% | → Meta-package + additions |
| env/Project.toml | 40 | 60% | → Base + project deps |

### Project-Specific (Keep as-is)

| File | Lines | Duplication | Action |
|------|-------|-------------|--------|
| shared/config.py | varies | 0% | ✅ Keep (project-specific) |
| Makefile (analysis defs) | ~200 | 0% | ✅ Keep (but auto-generate) |
| run_analysis.py | varies | 0% | ✅ Keep (project logic) |
| data/ | varies | 0% | ✅ Keep |
| docs/ | varies | 20% | Partial template |

---

## Questions for Discussion

1. **Priority**: Which phase would provide most value for your workflow?
2. **Risk tolerance**: How much abstraction is acceptable? (Full control vs automation)
3. **User base**: How many projects will use this template? (1-2 vs 10+)
4. **Customization**: How much do projects typically deviate from template?
5. **Timeline**: Immediate need or can iterate over months?

---

**Next Steps**:

1. Review this analysis
2. Decide on implementation phases
3. Create issues/tasks for chosen improvements
4. Start with Phase 1 (quick wins) if uncertain

