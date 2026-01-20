# Changelog

All notable changes to this reproducible research template will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Development tools and environment enhancements**:
  - **Python packages**:
    - `ipython` - Better REPL experience with Emacs integration (`.dir-locals.el` configured)
    - `black` - Opinionated code formatter (in addition to ruff)
    - `notebook`, `jupyterlab`, `ipywidgets` - Jupyter notebook support
    - `ibis-framework`, `python-duckdb`, `pyarrow` - Advanced data analysis tools
    - `types-docopt`, `pandas-stubs`, `scipy-stubs` - Type stubs for better type checking
  - **Julia packages**:
    - `Distributions`, `StatsModels`, `FixedEffectModels` - Statistical modeling
    - `Arrow` - Fast columnar data format
    - `RDatasets` - Example datasets for testing
    - `Adapt`, `OpenSSL_jll` - GPU support and secure connections
    - GPU configuration with `[extras]` and `[targets]` for CUDA
    - Pinned `PythonCall` to `0.9.31` with detailed version constraints
    - Added Julia 1.9 to compatibility range
  - **Stata packages**:
    - Added version constraints: `estout 3.1.2`, `coefplot 2.0.0`
  - **Makefile code quality targets**:
    - Enhanced `make format` to run both black and ruff formatters
    - Improved `make format-check` to validate both formatters
    - Updated `make type-check` to check `run_analysis.py` and `shared/` modules
    - Added detailed progress output for all formatting steps
    - `make check` now validates: lint (ruff) + format (black + ruff) + type-check (mypy) + tests (pytest)
  - **Emacs integration**:
    - `.dir-locals.el` configured for Python, Julia, and LSP
    - IPython REPL integration for better interactive development
    - Auto-detection of project-local environments

- **3-level defaults system** for flexible configuration:
  - **Level 1 (Docopt)**: Default values in docstring `[default: mean]` syntax
  - **Level 2 (DEFAULTS)**: Global defaults in `shared/config.py` DEFAULTS dictionary
  - **Level 3 (STUDIES)**: Study-specific overrides in `shared/config.py` STUDIES dictionary
  - **Level 4 (Command-line)**: Highest priority via EXTRA_ARGS or direct flags
  - Created `build_config()` function in `run_analysis.py` to merge priorities
  - DRY configuration pattern: studies only specify differences from DEFAULTS
  - Added EXTRA_ARGS support to Makefile (global and per-analysis)
  - Extended `run_analysis.py` with 10 override flags (--data, --yvar, --xlabel, --ylabel, --title, --groupby, --xvar, --table-agg, --figure, --table)
  - Pattern inspired by fire/housing-analysis EXTRA_ARGS workflow
  - Documentation: `docs/defaults_system.md` (400+ line comprehensive guide)
  - Tests: 11 new tests in `tests/test_defaults.py` validating all priority levels

- **Unified analysis script pattern** (following fire/housing-analysis):
  - `run_analysis.py`: Single executable that handles multiple studies via configuration
  - `config.STUDIES`: Study configurations define all parameters (data, variables, outputs)
  - `--list` option to display available studies
  - `--version` option for version tracking
  - Simplified Makefile pattern definitions (just study name as argument)
- **docopt CLI parsing** for self-documenting command-line interfaces:
  - Added docopt to `env/python.yml` dependencies
  - Clean help text with Usage, Options, and Arguments sections
- **Enhanced CLI utilities** (ported from fire/housing-analysis):
  - `shared/cli.py`: CLI utilities module
    - `friendly_docopt()`: Enhanced error messages with suggestions for typos (e.g., "--lists" suggests "--list")
    - `print_config()`: Pretty-printed configuration display with formatted headers
    - `print_header()`: Extract and display script name/description from docstring
    - `ConfigBuilder`: Structured configuration builder with validation
    - `setup_environment()`: Auto-detect execution environment (Jupyter, IPython, Emacs, terminal)
    - `filter_ipython_args()`: Clean up IPython-specific arguments
    - Parse utilities: `parse_csv_list()`, `parse_int_or_auto()`, `parse_float_or_auto()`, `parse_string_or_auto()`
  - `shared/config_validator.py`: Configuration validation module
    - `validate_config()`: Validate study configuration before execution
      - Check required keys (data, xlabel, ylabel, yvar, xvar, figure, table)
      - Verify input data files exist
      - Validate output directories can be created
      - Check variable names are strings
      - Validate aggregation functions
    - `print_validation_errors()`: User-friendly error display with formatted output
  - `shared/__init__.py`: Package initialization with exports

### Changed
- **Refactored from multiple scripts to unified approach**:
  - Removed `build_price_base.py` and `build_remodel_base.py`
  - All analyses now use single `run_analysis.py` script
  - Study parameters stored in `config.STUDIES` dictionary
  - Makefile simplified: `price_base.args := price_base` instead of full command-line args
- **config.py structure**:
  - Moved `config.py` → `shared/config.py` to match fire/housing-analysis organization
  - Fixed `REPO_ROOT` path calculation (now uses `.parent.parent` since config is in subdirectory)
  - Renamed `ANALYSES` → `STUDIES` to match fire/housing-analysis naming
  - Studies now define analysis parameters instead of file paths
  - Includes xlabel, ylabel, title, groupby, yvar, xvar, table_agg parameters
- **VS Code integration**:
  - Updated debug configurations to use `run_analysis.py` with study name argument
  - Changed from script-specific configs to study-specific configs
- **Enhanced run_analysis.py**:
  - Uses `friendly_docopt()` instead of plain `docopt` for better error messages
  - Calls `setup_environment()` to detect and adapt to execution context
  - Validates configuration with `validate_config()` before running analysis
  - Displays configuration with `print_config()` for transparency
  - Improved error messages for unknown studies and invalid options
- **Documentation updates**:
  - README.md: Updated to reflect unified script pattern
  - TEMPLATE_USAGE.md: Shows how to add studies to config.py instead of creating new scripts
  - `.github/copilot-instructions.md`: Updated with unified script pattern
  - VS Code launch configs: Updated to use run_analysis.py

### Fixed
- **Test suite fixes**:
  - Fixed PyYAML import test: changed "pyyaml" to "yaml" (package imports as 'yaml')
  - Fixed git dirty state test: added initial commit to temp repo and modified tracked file
  - All 69 tests passing, 1 skipped

### Removed
- Individual build scripts (`build_price_base.py`, `build_remodel_base.py`)
  - Replaced by unified `run_analysis.py` with config.py-based study definitions

---

## [1.0.0] - 2026-01-16

### Added
- **repro-tools git submodule** for portable dependency management:
  - Added `lib/repro-tools/` as git submodule tracking https://github.com/rhstanton/repro-tools.git
  - Configured to track `main` branch for automatic updates
  - Automatic submodule initialization in Makefile (runs on every make invocation)
  - Editable install (`-e ../lib/repro-tools`) for immediate availability of changes
  - Comprehensive documentation in `docs/repro_tools_submodule.md`
- Journal submission documentation package:
  - `CITATION.cff`: Structured citation metadata in Citation File Format
  - `JOURNAL_EXCLUDE`: List of directories to exclude from journal submission
  - `DATA_AVAILABILITY.md`: Comprehensive data availability statement template
  - `data/CHECKSUMS.txt`: SHA256 checksums for data verification
  - `data/DATA_README.md`: Detailed data dictionary with variable descriptions
  - `docs/journal_editor_readme.md`: One-page quick guide for journal editors with "What Success Looks Like" sections
  - `docs/paper_output_mapping.md`: Maps paper figures/tables to output files and make targets
  - `docs/expected_outputs.md`: Verification checklist with file descriptions
- New Makefile targets for verification and journal submission:
  - `make verify`: Quick environment smoke test (~1 min)
  - `make test-outputs`: Verify all expected output files exist
  - `make system-info`: Log computational environment to output/system_info.yml
  - `make journal-package`: Create clean replication package (excludes development files)
  - `make journal-package-tarball`: Create .tar.gz archive for submission
  - `make journal-package-zip`: Create .zip archive for submission
  - `make clean-journal`: Remove journal package artifacts
  - `make test`: Run pytest test suite
  - `make test-cov`: Run tests with coverage report
  - `make diff-outputs`: Compare current vs. published outputs
  - `make pre-submit`: Run pre-submission checklist
  - `make pre-submit-strict`: Strict mode pre-submission checks
  - `make replication-report`: Generate HTML replication report
- `scripts/log_system_info.py`: Utility to capture computational environment (OS, Python, Julia versions, packages)
- `scripts/compare_outputs.py`: Compare outputs between builds (figures and tables)
- `scripts/pre_submit_check.py`: Comprehensive pre-publication validation
- `scripts/generate_replication_report.py`: Auto-generate replication reports for reviewers
- `tests/` directory with pytest-based test suite:
  - `tests/test_provenance.py`: Unit tests for provenance tracking
  - `tests/test_integration.py`: Integration tests for build workflow
  - `tests/test_environment.py`: Environment setup and update tests (28 tests)
  - `tests/test_publishing.py`: Publishing workflow and safety check tests (25 tests)
- Code quality infrastructure:
  - `make lint`: Run ruff linter on all Python files
  - `make format`: Auto-format code with ruff (imports, trailing whitespace, etc.)
  - `make format-check`: Check formatting without modifying files
  - `make type-check`: Run mypy type checker on build scripts
  - `make check`: Comprehensive quality check (lint + format-check + type-check + test)
  - Added ruff and mypy to `env/python.yml` dependencies
  - Configured in `pyproject.toml` with project-specific rules
- Runtime estimates throughout documentation

### Changed
- **repro-tools installation method**:
  - Changed from absolute path (`-e /home/user/...`) to git submodule (`-e ../lib/repro-tools`)
  - Makes template portable across machines and users
  - Maintains editable install for development workflow
  - Updated `env/python.yml` with portable relative path
- **Makefile enhancements**:
  - Added automatic git submodule initialization at top of Makefile
  - Enhanced `environment` target with submodule initialization messaging
  - Added repro-tools location to environment setup output
- **Documentation updates** for git submodule approach:
  - Updated `README.md` with lib/ directory in structure
  - Updated `QUICKSTART.md` with submodule initialization step
  - Updated `docs/directory_structure.md` with lib/ section
  - Updated `docs/environment.md` with submodule details
  - Updated `docs/README.md` with link to repro_tools_submodule.md
- **Three-tier help system** (matches fire project UX):
  - `make` (default): Brief guidance showing essential commands (~20 lines)
  - `make help`: Detailed command reference organized by category (~80 lines)
  - `make info`: Comprehensive project information (pipeline, structure, requirements)
  - Updated `.DEFAULT_GOAL` from `help` to `default` for brief output

### Fixed
- **Publishing safety**: Publishing now checks if artifacts were built from a dirty working tree (not just if current tree is dirty). Prevents scenario where you build with dirty tree, commit, then publish stale outputs. Controlled by `--allow-dirty` flag.
- **Git provenance tracking**: Fixed `repo_root` calculation in build scripts - was using `.parents[1]` (parent of project dir) instead of `.parent` (project root), causing git state to not be recorded in provenance files
- **Idempotent publishing**: `make publish` now uses stamp files to track published artifacts. Only re-publishes when source files change. Shows "Nothing to publish - all up-to-date" when everything current. Added `make publish-force` to override.
- Updated README.md:
  - Added runtime estimates in Quick Start section
  - Enhanced system requirements with time estimates
  - Improved Makefile targets section with all new verification and journal targets
  - Added references to journal submission documentation
  - Added testing and quality assurance features to core features list
  - Updated help system documentation (make/help/info)
- Updated env/python.yml:
  - Added pytest and pytest-cov for testing
- Updated QUICKSTART.md:
  - Added "What Success Looks Like" sections showing expected console output for each step
  - Added `make verify` and `make test-outputs` to workflow
  - Added note about three-tier help system at top
- Updated docs/README.md:
  - Added new "Journal Submission" section
  - Added references to all 4 new journal-related documentation files
- Updated Makefile help:
  - Added "JOURNAL SUBMISSION (AUTHOR-ONLY)" section
  - Added `system-info` to verification section
  - Added references to new documentation files
- Updated .gitignore:
  - Explicitly includes JOURNAL_EXCLUDE and DATA_AVAILABILITY.md
  - Ignores journal-package/ directory and archives
- Enhanced paper/README.md with references to journal documentation
- Enhanced data/README.md with references to CHECKSUMS.txt and DATA_README.md

### Fixed
- Nothing yet

---

## [1.0.0] - 2026-01-16

### Initial Release

**Minimal template for reproducible research with provenance tracking and automated builds.**

#### Core Features

- **Build/Publish Separation**: Build artifacts in `output/` (ephemeral), publish to `paper/` (permanent)
- **Provenance Tracking**: Full git state + SHA256 hashes for all inputs/outputs
- **Multi-Language Support**: Python 3.11, Julia 1.10-1.12, Stata (optional)
- **GNU Make Orchestration**: Grouped targets for atomic multi-output builds

#### Infrastructure

**Environment System** (`env/` directory):
- Python 3.11 conda environment (`.env/`)
- Julia auto-installed via juliacall (`.julia/pyjuliapkg/`)
- Stata packages (`.stata/ado/plus/`)
- Environment wrappers: `runpython`, `runjulia`, `runstata`
- Optional Nix flake for reproducible dev shell (`flake.nix`)

**Provenance System**:
- Build records: `output/provenance/<name>.yml` per artifact
- Publication records: `paper/provenance.yml` aggregated
- Git safety checks on publishing (clean tree, not behind upstream)
- Optional strict mode: require artifacts from current HEAD

**Example Scripts**:
- Python example
- Pure Julia example
- Python/Julia interop (juliacall)
- Stata example (if installed)

#### Sample Artifacts

- `price_base`: Housing price analysis (figure + table)
- `remodel_base`: Remodeling rate analysis (figure + table)

#### Documentation

- `README.md`: Quick start and overview
- `docs/environment.md`: Environment setup details
- `docs/provenance.md`: Provenance tracking explained
- `docs/publishing.md`: Publishing workflow guide
- `docs/directory_structure.md`: Project organization
- `.github/copilot-instructions.md`: AI agent guidance

#### Developer Tools

- `.gitignore`: Excludes environments, build outputs
- `scripts/provenance.py`: Build provenance utilities
- `scripts/publish_artifacts.py`: Publishing with safety checks

### Architecture Highlights

**Atomic Builds**:
- GNU Make grouped targets (`&:` syntax, requires Make 4.3+)
- One script invocation produces figure + table + provenance
- Prevents partial/inconsistent outputs

**Provenance Chain**:
- Build time: Record git state, command, input/output hashes
- Publish time: Aggregate build records, track publication event
- Verification: SHA256 checksums detect any modifications

**Git Integration**:
- Tracks commit, branch, dirty status, ahead/behind counts
- Safety checks prevent publishing from dirty tree or outdated branch
- Optional strict mode ensures artifacts match current HEAD

**Environment Management**:
- Auto-installs micromamba if conda/mamba not found
- Julia installed via juliacall (no manual Julia installation needed)
- CondaPkg disabled (uses main Python environment)
- Stata packages installed locally to project

### System Requirements

- **OS**: Linux or macOS (Windows requires WSL)
- **RAM**: 8GB minimum
- **Disk**: 5GB (2GB environment + 3GB cache)
- **Software**: GNU Make 4.3+, conda/mamba/micromamba (auto-installed)

### Known Limitations

- Requires GNU Make 4.3+ for grouped targets
- Julia GPU support not configured (CPU only)
- Stata support requires system installation
- No automated testing framework included

---

## Version History Summary

- **1.0.0** (2026-01-16): Initial release with provenance tracking and multi-language support
