# Improving repro-tools Convenience in project_template

## Current State Analysis

After migrating all utility code to `repro-tools`, we have opportunities to make using the package more convenient.

## Issues Identified

### 1. **Makefile Still References Deleted scripts/ Files**

Lines that need updating:
- Line 288: `scripts/check_git_state.py` → Use `repro-check` CLI
- Line 355: `scripts/publish_specific_files.py` → Use `repro-publish` CLI  
- Line 364, 376: `scripts/publish_artifacts.py` → Use `repro-publish` CLI
- Line 452: `scripts/log_system_info.py` → Use `repro-sysinfo` CLI
- Line 479: `scripts/compare_outputs.py` → Use `repro-compare` CLI
- Line 487, 493: `scripts/pre_submit_check.py` → Use `repro-check` CLI
- Line 499: `scripts/generate_replication_report.py` → Use `repro-report` CLI

### 2. **Python Script Imports Could Be Simplified**

Current:
```python
from repro_tools import enable_auto_provenance
enable_auto_provenance(__file__)
```

Could be even simpler with a decorator or context manager.

### 3. **Config File Not Fully Leveraged**

We have `config.py` with paths and analysis definitions, but repro-tools doesn't read it directly.

### 4. **Documentation Needs Updating**

Many docs still reference the old scripts/ structure.

## Proposed Improvements

### Priority 1: Replace scripts/ Calls with CLI Commands

**Benefits:**
- Uses official CLI interface
- No dependency on deleted files
- Easier to understand for new users
- Consistent with how other projects will use repro-tools

**Changes:**

```makefile
# OLD:
@$(PYTHON) scripts/check_git_state.py --allow-dirty $(ALLOW_DIRTY) ...

# NEW:
@$(PYTHON) -m repro_tools.cli check --allow-dirty $(ALLOW_DIRTY) ...
# OR:
@repro-check --allow-dirty $(ALLOW_DIRTY) ...
```

### Priority 2: Create Makefile Helper Variables

Make it easy to call repro-tools commands:

```makefile
# At top of Makefile with other executables
REPRO_CHECK   := $(PYTHON) -m repro_tools.cli check
REPRO_PUBLISH := $(PYTHON) -m repro_tools.cli publish  
REPRO_COMPARE := $(PYTHON) -m repro_tools.cli compare
REPRO_SYSINFO := $(PYTHON) -m repro_tools.cli sysinfo
REPRO_REPORT  := $(PYTHON) -m repro_tools.cli report

# Then use them:
publish:
	@$(REPRO_CHECK) --allow-dirty $(ALLOW_DIRTY) --artifacts "$(PUBLISH_ANALYSES)"
	@$(REPRO_PUBLISH) --paper-root $(PAPER_DIR) --analyses "$(PUBLISH_ANALYSES)"
```

### Priority 3: Simplify Python Scripts Even More

**Option A: Use decorator (requires code in repro-tools)**
```python
from repro_tools import auto_provenance

@auto_provenance
def main():
    # ... your code ...

if __name__ == "__main__":
    main()
```

**Option B: Current approach is already pretty simple**
```python
from repro_tools import enable_auto_provenance
enable_auto_provenance(__file__)
# Just 2 lines!
```

Verdict: Current approach is already excellent. Don't over-engineer it.

### Priority 4: Create Template Makefile Snippet

Provide a reusable Makefile snippet that projects can copy:

```makefile
# ==============================================================================
# repro-tools Integration
# ==============================================================================
# Add this to your Makefile for easy access to repro-tools commands

PYTHON := env/scripts/runpython

# repro-tools CLI commands (use Python module for portability)
REPRO_RECORD  := $(PYTHON) -m repro_tools.cli record
REPRO_PUBLISH := $(PYTHON) -m repro_tools.cli publish
REPRO_COMPARE := $(PYTHON) -m repro_tools.cli compare
REPRO_SYSINFO := $(PYTHON) -m repro_tools.cli sysinfo
REPRO_CHECK   := $(PYTHON) -m repro_tools.cli check
REPRO_REPORT  := $(PYTHON) -m repro_tools.cli report

# Publishing configuration
PUBLISH_ANALYSES ?= $(ANALYSES)
REQUIRE_CURRENT_HEAD ?= 0
ALLOW_DIRTY ?= 0
REQUIRE_NOT_BEHIND ?= 1

# Publish target
publish:
	@$(REPRO_CHECK) --allow-dirty $(ALLOW_DIRTY) \
	                --require-not-behind $(REQUIRE_NOT_BEHIND) \
	                --require-current-head $(REQUIRE_CURRENT_HEAD) \
	                --artifacts "$(PUBLISH_ANALYSES)"
	@$(REPRO_PUBLISH) --paper-root paper \
	                  --analyses "$(PUBLISH_ANALYSES)"
```

### Priority 5: Add HOWTO Guide

Create `docs/using_repro_tools.md` that shows best practices.

## Implementation Plan

1. **Immediate (Now)**: Update Makefile to use CLI commands via `$(PYTHON) -m repro_tools.cli`
2. **Short-term**: Create template Makefile snippet in repro-tools package
3. **Medium-term**: Add comprehensive HOWTO guide
4. **Long-term**: Consider if config.py could be leveraged by repro-tools

## Decision: Use `$(PYTHON) -m repro_tools.cli <command>` Pattern

**Why not direct CLI commands like `repro-check`?**
- Requires repro-tools to be in PATH (not always the case)
- Python virtual environment might not be activated when make runs
- `$(PYTHON)` already points to the right Python with repro-tools installed
- More portable across different setups

**Why `-m repro_tools.cli` instead of importing Python code?**
- Uses official CLI interface (same as command-line users)
- Arguments stay in Makefile (easier to see what's happening)
- Consistent with how other tools are called (make, git, etc.)
- Easier for users to understand and modify

## Benefits for Future Projects

Once this template is cleaned up:

1. **Copy-paste ready**: New projects can copy the updated Makefile patterns
2. **Clear separation**: Build logic in Makefile, utilities in repro-tools package
3. **Easy to customize**: Change CLI arguments in Makefile without touching Python
4. **Consistent interface**: All projects use same CLI commands
5. **Better docs**: Template shows best practices by example
