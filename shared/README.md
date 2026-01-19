# Shared Utilities

This directory contains shared utilities for configuration, CLI parsing, and validation, ported from the fire/housing-analysis production project.

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

### `cli.py` - Command-Line Interface Utilities

Enhanced CLI tools for better user experience:

- **`friendly_docopt(doc, version=None)`** - Enhanced docopt with typo suggestions
  ```python
  args = friendly_docopt(__doc__, version="my_script 1.0")
  # Unknown option --lis? Suggests: Did you mean --list?
  ```

- **`setup_environment()`** - Auto-detect execution context
  ```python
  env = setup_environment()
  # Returns: 'terminal', 'jupyter', 'ipython', 'emacs-python', etc.
  # Automatically filters IPython-specific arguments
  ```

- **`print_config(config, title="CONFIGURATION")`** - Pretty-print configuration
  ```python
  print_config({
      "Study": "price_base",
      "Data": "data/housing.csv",
      "Y Variable": "price_index"
  }, title="RUNNING STUDY: PRICE_BASE")
  # Outputs formatted table with aligned columns
  ```

- **`ConfigBuilder`** - Structured configuration building
  ```python
  builder = ConfigBuilder(args)
  builder.add("input_path", lambda: args["--input"])
  builder.add("limit", lambda: int(args["--limit"]) if args["--limit"] else None)
  config = builder.build()  # Prints and returns config dict
  ```

- **Parse utilities** - Type conversion with "auto" support
  - `parse_csv_list(value)` - Parse comma-separated strings
  - `parse_int_or_auto(value, default=None)` - Integer or "auto"
  - `parse_float_or_auto(value, default=None)` - Float or "auto"
  - `parse_string_or_auto(value, default=None)` - String or "auto"

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

- **`print_validation_errors(errors)`** - User-friendly error display
  ```python
  print_validation_errors([
      "Missing required config: yvar",
      "Input file not found: data.csv"
  ])
  # Outputs formatted error list with numbered items
  ```

## Usage in `run_analysis.py`

```python
from shared import (
    friendly_docopt,
    print_config,
    print_validation_errors,
    setup_environment,
    validate_config,
)

def main():
    # Detect environment and filter IPython args
    setup_environment()
    
    # Parse with enhanced error messages
    args = friendly_docopt(__doc__, version="run_analysis 1.0")
    
    # Validate configuration
    errors = validate_config(study_config, study_name)
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

## Benefits

1. **Better Error Messages** - Suggests corrections for typos
2. **Environment Awareness** - Adapts to Jupyter, IPython, Emacs, terminal
3. **Pre-flight Validation** - Catches configuration errors before execution
4. **Clear Output** - Pretty-printed configuration for transparency
5. **Production-Tested** - Patterns from real research project

## Excluded from Fire Project

The following patterns were **not** ported to keep the template simple:

- **Caching system** - Data/computation caching (too complex for template)
- **Backend selection** - Julia/Python/GPU backend switching (handled via environment)
- **Advanced parsing** - 90+ command-line options (template has ~5)

These can be added to your project if needed by referring to the fire/housing-analysis implementation.

## See Also

- [fire/housing-analysis](https://github.com/yourusername/fire) - Original implementation
- [docopt documentation](http://docopt.org/) - CLI parsing library
- [run_analysis.py](../run_analysis.py) - Example usage
