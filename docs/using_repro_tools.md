# Using repro-tools in Your Project

This document shows how to use the `repro-tools` package conveniently in your research project, based on lessons learned from `project_template`.

## Installation

### In Your Environment Specification

Add to `env/python.yml`:

```yaml
name: your_project
channels:
  - conda-forge
dependencies:
  - python=3.11
  - pandas
  - matplotlib
  - pyyaml
  - pip:
    # Install repro-tools in editable mode (for development)
    - -e ../../../infrastructure/40_lib/python/repro-tools
    # OR install from PyPI (when published):
    # - repro-tools>=0.2.0
```

### In Your Python Scripts

**Minimal setup - just 2 lines:**

```python
from repro_tools import enable_auto_provenance

# Enable automatic provenance recording at script exit
enable_auto_provenance(__file__)

def main():
    # Your analysis code here
    pass

if __name__ == "__main__":
    main()
```

That's it! Provenance is automatically recorded when the script exits.

## Makefile Integration

### Define CLI Command Variables

At the top of your Makefile, after defining `PYTHON`:

```makefile
# Environment script paths
PYTHON := env/scripts/runpython
JULIA  := env/scripts/runjulia
STATA  := env/scripts/runstata

# repro-tools CLI commands (via Python module for portability)
REPRO_CHECK   := $(PYTHON) -m repro_tools.cli check
REPRO_PUBLISH := $(PYTHON) -m repro_tools.cli publish
REPRO_COMPARE := $(PYTHON) -m repro_tools.cli compare
REPRO_SYSINFO := $(PYTHON) -m repro_tools.cli sysinfo
REPRO_REPORT  := $(PYTHON) -m repro_tools.cli report
```

**Why `$(PYTHON) -m repro_tools.cli` instead of `repro-check` directly?**

- ✅ Works regardless of whether repro-tools is in PATH
- ✅ Uses the same Python environment as $(PYTHON)
- ✅ No need to activate virtual environment before running make
- ✅ More portable across different setups
- ✅ Consistent with how other Python tools are called

### Publishing Target

```makefile
# Publishing configuration
PUBLISH_ANALYSES ?= $(ANALYSES)
REQUIRE_CURRENT_HEAD ?= 0  # Set to 1 for strict mode
ALLOW_DIRTY ?= 0
REQUIRE_NOT_BEHIND ?= 1

.PHONY: publish
publish:
	@$(REPRO_CHECK) --allow-dirty $(ALLOW_DIRTY) \
	                --require-not-behind $(REQUIRE_NOT_BEHIND) \
	                --require-current-head $(REQUIRE_CURRENT_HEAD) \
	                --artifacts "$(PUBLISH_ANALYSES)"
	@$(REPRO_PUBLISH) --paper-root paper \
	                  --analyses "$(PUBLISH_ANALYSES)"
```

### Other Useful Targets

```makefile
# System information logging
.PHONY: system-info
system-info:
	@$(REPRO_SYSINFO) --output output/system_info.yml --repo-root .

# Compare current vs. published outputs
.PHONY: diff-outputs
diff-outputs:
	@$(REPRO_COMPARE) --reference paper --current-dir output

# Pre-submission checklist
.PHONY: pre-submit
pre-submit:
	@$(REPRO_CHECK) --pre-submit

.PHONY: pre-submit-strict
pre-submit-strict:
	@$(REPRO_CHECK) --pre-submit --strict

# Generate replication report
.PHONY: replication-report
replication-report:
	@$(REPRO_REPORT) --format html --output output/replication_report.html
```

## Quick Reference

### Python API (in your scripts)

```python
from repro_tools import enable_auto_provenance

# Basic usage - automatic provenance at exit
enable_auto_provenance(__file__)

# Manual provenance recording (if needed)
from repro_tools import write_build_record
write_build_record(
    metadata_path="output/provenance/my_analysis.yml",
    inputs=["data/input.csv"],
    outputs=["output/figures/my_fig.pdf", "output/tables/my_table.tex"],
    script=__file__,
    cmd=sys.argv
)
```

### CLI Commands (in Makefile or terminal)

```bash
# Check git state (pre-publishing)
$(PYTHON) -m repro_tools.cli check --allow-dirty 0 --artifacts "price_base"

# Publish analyses
$(PYTHON) -m repro_tools.cli publish --paper-root paper --analyses "price_base remodel_base"

# Publish specific files
$(PYTHON) -m repro_tools.cli publish --paper-root paper --files "output/figures/fig1.pdf"

# Compare outputs
$(PYTHON) -m repro_tools.cli compare --reference paper --current-dir output

# Log system info
$(PYTHON) -m repro_tools.cli sysinfo --output output/system_info.yml

# Pre-submission checks
$(PYTHON) -m repro_tools.cli check --pre-submit
$(PYTHON) -m repro_tools.cli check --pre-submit --strict

# Generate replication report
$(PYTHON) -m repro_tools.cli report --format html --output output/report.html
```

## Benefits for New Projects

When starting a new project:

1. **Copy the Makefile snippet** above (lines defining REPRO_* variables)
2. **Add repro-tools to env/python.yml**
3. **Add 2 lines to each Python script** (import + enable_auto_provenance)
4. **You're done!**

No need to copy utility scripts, no need to maintain provenance code, just use the package.

## Why This Approach?

### Separation of Concerns

- **Your project**: Contains only project-specific code (analysis scripts, data, docs)
- **repro-tools**: Contains reusable infrastructure (provenance, publishing, QA)

### Easy to Update

```bash
# Update repro-tools across all projects
cd /path/to/repro-tools
git pull
# All projects using it get updates automatically (if editable install)
```

### Consistent Across Projects

- Same provenance format
- Same publishing workflow
- Same pre-submission checks
- Easier to maintain multiple projects

### Teaching-Friendly

Students can:
- Install repro-tools once
- Use it in all their projects
- Learn a standard workflow
- Focus on analysis, not infrastructure

## Example: Full Analysis Script

```python
#!/usr/bin/env python
"""
build_my_analysis.py

Analyzes XYZ and generates figure + table.
"""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from repro_tools import enable_auto_provenance

# Enable automatic provenance - that's it!
enable_auto_provenance(__file__)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out-fig", type=Path, required=True)
    parser.add_argument("--out-table", type=Path, required=True)
    args = parser.parse_args()
    
    # Create output directories
    args.out_fig.parent.mkdir(parents=True, exist_ok=True)
    args.out_table.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(args.data)
    
    # Generate figure
    fig, ax = plt.subplots()
    # ... your plotting code ...
    fig.savefig(args.out_fig)
    plt.close(fig)
    
    # Generate table
    # ... your table generation code ...
    table.to_latex(args.out_table, index=False)
    
    # That's it! Provenance recorded automatically at exit

if __name__ == "__main__":
    main()
```

## Next Steps

See `project_template/` for a complete working example with:
- Multi-language support (Python, Julia, Stata)
- Flexible analysis definitions
- Publishing workflow
- Testing and QA
- Journal submission helpers

