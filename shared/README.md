# Shared Utilities

This directory contains **project-specific** configuration for the analysis pipeline.

**Note:** Generic utilities (`friendly_docopt`, `print_config`, config validation, provenance,
publishing, etc.) live in the `repro-tools` package to avoid duplication across projects. Import
those from `repro_tools`; import only project configuration from `shared`.

## Modules

### `config.py` - Study Configurations

Central configuration defining study parameters in the `STUDIES` dictionary (with shared `DEFAULTS`):

```python
from shared.config import STUDIES, DATA_FILES, OUTPUT_DIR

study = STUDIES["price_base"]
data_file = study["data"]
```

Each study may define (anything omitted falls back to `DEFAULTS`):
- `data` - Input data file path
- `xlabel`, `ylabel`, `title` - Plot parameters
- `xvar`, `yvar`, `groupby` - Variable names
- `table_agg` - Aggregation function (mean, sum, etc.)
- `figure`, `table` - Output paths

Resolution priority is `DEFAULTS` < `STUDIES[study]` < command-line overrides.

## Usage in `run_analysis.py`

Configuration validation lives in `repro_tools` (`validate_study_config`), not in this directory:

```python
from repro_tools import (
    friendly_docopt,
    print_config,
    print_validation_errors,
    setup_environment,
    validate_study_config,
)

from shared import config


def main() -> None:
    setup_environment()
    args = friendly_docopt(__doc__, version="run_analysis 1.0")

    study = config.STUDIES[study_name]

    errors = validate_study_config(study, study_name)
    if errors:
        print_validation_errors(errors)
        sys.exit(1)

    print_config(
        {"Study": study_name, "Data": study["data"]},
        title=f"RUNNING STUDY: {study_name.upper()}",
    )
```

## What's in `repro_tools` vs `shared`

**`repro_tools`** (generic, reusable across projects):
- CLI parsing with typo suggestions (`friendly_docopt`)
- Environment detection (`setup_environment`)
- Configuration display (`print_config`)
- Study-config validation (`validate_study_config`, `print_validation_errors`)
- Provenance tracking (`auto_build_record`, `write_build_record`)
- Publishing infrastructure

**`shared/`** (project-specific):
- Study configurations (`STUDIES`, `DEFAULTS`)
- Data file paths (`DATA_FILES`)
- Project directory paths (`REPO_ROOT`, `OUTPUT_DIR`, `PAPER_DIR`)

## See Also

- [lib/repro-tools](../lib/repro-tools/) - Generic reproducibility tools (git submodule)
- [run_analysis.py](../run_analysis.py) - Example usage pattern
- [docopt documentation](http://docopt.org/) - CLI parsing library
