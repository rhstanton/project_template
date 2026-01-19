# Shared Utilities

This directory contains **project-specific** configuration and validation utilities.

**Note:** Generic CLI utilities (friendly_docopt, print_config, ConfigBuilder, etc.) have been extracted to the `repro-tools` package to avoid code duplication. Import those from `repro_tools` instead of `shared`.

## Modules

### `config.py` - Study Configurations

Central configuration file defining all study parameters in the `STUDIES` dictionary:

```python
from shared.config import STUDIES, DATA_FILES, OUTPUT_DIR

# Access study configuration
study = STUDIES["price_base"]
data_file = study["data"]
```

Each study defines:
- `data` - Input data file path
- `xlabel`, `ylabel`, `title` - Plot parameters
- `xvar`, `yvar`, `groupby` - Variable names
- `table_agg` - Aggregation function (mean, sum, etc.)
- `figure`, `table` - Output paths

### `config_validator.py` - Configuration Validation

Validates study configurations before execution:

- **`validate_config(config, study_name)`** - Validate configuration
  ```python
  errors = validate_config(study_config, "price_base")
  if errors:
      print_validation_errors(errors)
      sys.exit(1)
  ```

  Checks:
  - Required keys present (data, xlabel, ylabel, yvar, xvar, figure, table)
  - Input data files exist
  - Output directories can be created
  - Variable names are strings
  - Aggregation functions are valid

## Usage in `run_analysis.py`

```python
# Import CLI utilities from repro_tools (not shared)
from repro_tools import (
    friendly_docopt,
    print_config,
    print_validation_errors,
    setup_environment,
)

# Import project-specific utilities from shared
from shared import config
from shared.config_validator import validate_config

def main():
    # Detect environment and filter IPython args
    setup_environment()
    
    # Parse with enhanced error messages
    args = friendly_docopt(__doc__, version="run_analysis 1.0")
    
    # Get study configuration
    study = config.STUDIES[study_name]
    
    # Validate configuration
    errors = validate_config(study, study_name)
    if errors:
        print_validation_errors(errors)
        sys.exit(1)
    
    # Display configuration
    print_config({
        "Study": study_name,
        "Data": study["data"],
        # ...
    }, title=f"RUNNING STUDY: {study_name.upper()}")
```

## Import Pattern

**For generic CLI utilities** (shared across projects):
```python
from repro_tools import (
    friendly_docopt,       # Enhanced docopt with typo suggestions
    print_config,          # Pretty-print configuration
    print_header,          # Extract script description from docstring
    setup_environment,     # Auto-detect execution environment
    ConfigBuilder,         # Fluent config builder
    parse_csv_list,        # Parse comma-separated lists
    parse_int_or_auto,     # Integer or "auto"
    print_validation_errors,  # User-friendly error display
)
```

**For project-specific utilities**:
```python
from shared import config              # Study configurations (STUDIES, DEFAULTS)
from shared.config_validator import validate_config  # Project-specific validation
```

## Benefits

1. **Separation of Concerns** - Generic utilities in repro_tools, project-specific in shared
2. **Code Reusability** - repro_tools can be shared across all research projects
3. **Pre-flight Validation** - Catches configuration errors before execution
4. **Production-Tested** - Patterns from fire/housing-analysis production project

## What's in repro_tools vs shared

**repro_tools** (generic, reusable):
- CLI parsing with typo suggestions (friendly_docopt)
- Environment detection (Jupyter, IPython, terminal)
- Configuration display (print_config, print_header)
- Type conversion utilities (parse_csv_list, parse_int_or_auto, etc.)
- Generic validation error display (print_validation_errors)
- Provenance tracking (git_state, write_build_record, etc.)
- Publishing infrastructure (publish_analyses, publish_files)

**shared/** (project-specific):
- Study configurations (STUDIES, DEFAULTS dictionaries)
- Data file paths (DATA_FILES)
- Project directory structure (REPO_ROOT, OUTPUT_DIR)
- Project-specific validation logic (validate_config)

## See Also

- [lib/repro-tools](../lib/repro-tools/) - Generic reproducibility tools (git submodule)
- [run_analysis.py](../run_analysis.py) - Example usage pattern
- [fire/housing-analysis](https://github.com/yourusername/fire) - Original patterns source
- [docopt documentation](http://docopt.org/) - CLI parsing library
