# Changelog

All notable changes to this reproducible research template will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

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
