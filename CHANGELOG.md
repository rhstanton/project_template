# Changelog

All notable changes to this reproducible research template will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
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
- Runtime estimates throughout documentation

### Changed
- **Three-tier help system** (matches fire project UX):
  - `make` (default): Brief guidance showing essential commands (~20 lines)
  - `make help`: Detailed command reference organized by category (~80 lines)
  - `make info`: Comprehensive project information (pipeline, structure, requirements)
  - Updated `.DEFAULT_GOAL` from `help` to `default` for brief output
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
