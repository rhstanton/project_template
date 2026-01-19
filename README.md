# Reproducible Research Template

**A minimal template for reproducible research with provenance tracking and automated builds**

This template provides a complete workflow for building research artifacts (figures and tables) with full provenance tracking, separating build outputs from published results.

---

## � Creating a New Project from This Template

**Option 1: Clone with submodules (recommended):**
```bash
git clone --recursive https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment
```

**Option 2: Clone normally (submodules auto-initialize):**
```bash
git clone https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment  # Automatically initializes git submodules
```

**⚠️ IMPORTANT:** When creating a new project, do **NOT** manually copy the `lib/repro-tools/` directory. Let git handle it as a submodule. The Makefile automatically initializes it when you run `make environment`.

**Updating repro-tools:** 
- Quick update: `make update-submodules` (updates submodule only)
- Full update: `make update-environment` (updates submodule + reinstalls environment)
- See [docs/submodule_cheatsheet.md](docs/submodule_cheatsheet.md) for details

---

## 🚀 Quick Start

**First time setup (required once, ~10-15 minutes):**
```bash
make environment    # Install Python, Julia, Stata packages + initialize submodules
```

**Verify setup:**
```bash
make verify         # Quick smoke test (~1 minute)
```

**To build all artifacts:**
```bash
make all           # Build figures + tables + provenance (~5 minutes)
```

**To publish to paper directory:**
```bash
make publish       # Copy outputs to paper/ with provenance
```

**To verify outputs:**
```bash
make test-outputs  # Check all expected files exist
```

**To test setup:**
```bash
make examples      # Run example scripts
```

**Need help?** See [`docs/journal_editor_readme.md`](docs/journal_editor_readme.md) for journal editors.

---

## � VS Code Users: No Command Line Required!

**Prefer working in VS Code?** Everything works through the UI:

1. **Install extensions** (VS Code will prompt you)
2. **Press `Ctrl+Shift+P`** → type "task" → browse available tasks
3. **Press `Ctrl+Shift+B`** to build everything
4. **Press `F5`** to debug Python scripts

**Full guide:** [GETTING_STARTED_VSCODE.md](GETTING_STARTED_VSCODE.md)  
**Cheat sheet:** [.vscode/QUICK_REFERENCE.md](.vscode/QUICK_REFERENCE.md)  
**Details:** [docs/vscode_integration.md](docs/vscode_integration.md)

All Make commands are available as VS Code tasks - you can work entirely in the GUI!

---

## �📊 What This Template Provides

### Core Features

- **Reproducible builds**: GNU Make orchestration with grouped targets
- **Provenance tracking**: Full git state + input/output SHA256 hashes
- **Build/publish separation**: Build in `output/`, publish to `paper/`
- **Multi-language support**: Python, Julia, Stata
- **VS Code integration**: Complete workflow via GUI (see [docs/vscode_integration.md](docs/vscode_integration.md))
- **Code quality tools**: Integrated linting (ruff), formatting, and type checking (mypy)
- **Automated testing**: pytest-based test suite for reliability
- **Output comparison**: Diff current vs. published outputs
- **Pre-submission checks**: Comprehensive validation before journal submission
- **Replication reports**: Auto-generated HTML reports for reviewers
- **Example workflows**: Sample scripts for all three languages

### Directory Structure

```
project_template/
├── build_price_base.py    # Analysis scripts
├── build_remodel_base.py
├── data/              # Input datasets
├── env/               # Environment setup (Python/Julia/Stata)
├── lib/               # Git submodules (repro-tools)
├── examples/          # Sample scripts for testing
├── output/            # Build outputs (can be deleted/rebuilt)
│   ├── figures/       # Generated PDFs
│   ├── tables/        # Generated LaTeX tables
│   ├── provenance/    # Per-artifact build records
│   └── logs/          # Build logs
├── paper/             # Published outputs (separate git repo)
│   ├── figures/       # Published figures
│   ├── tables/        # Published tables
│   └── provenance.yml # Aggregated publication provenance
└── scripts/           # Shared utilities (provenance.py, publish_artifacts.py)
```

See `docs/directory_structure.md` for complete details.

---

## 🎯 Workflows

### Building Artifacts

Each analysis script follows a standard pattern:

```bash
make price_base       # Builds one artifact
make all              # Builds all artifacts
```

This produces **three outputs per artifact** (atomically):
- `output/figures/<name>.pdf` - The figure
- `output/tables/<name>.tex` - The table  
- `output/provenance/<name>.yml` - Build metadata

### Publishing Results

```bash
make publish                              # Publish all artifacts
make publish PUBLISH_ARTIFACTS="price_base"  # Publish specific ones
make publish REQUIRE_CURRENT_HEAD=1         # Strict: require current HEAD
```

Publishing enforces **git safety checks**:
- Working tree must be clean
- Branch must not be behind upstream
- Optionally require artifacts from current HEAD

See `docs/publishing.md` for details.

### Provenance Chain

**Build provenance** (`output/provenance/<name>.yml`):
```yaml
artifact: price_base
built_at_utc: '2026-01-17T04:04:49+00:00'
command: [python, build_price_base.py, --data, data/housing_panel.csv]
git:
  commit: cbb163e
  branch: main
  dirty: false
inputs:
  - path: data/housing_panel.csv
    sha256: 48917387...
outputs:
  - path: output/figures/price_base.pdf
    sha256: 3855687d...
```

**Publication provenance** (`paper/provenance.yml`):
- Aggregates all build records
- Tracks when each artifact was published
- Records analysis repo git state at publication time

See `docs/provenance.md` for complete explanation.

---

## 🔧 Adding New Artifacts

1. **Create analysis script** following the pattern in [build_price_base.py](build_price_base.py):
   ```python
   from scripts.provenance import write_build_record
   
   def main():
       # ... build figure and table ...
       
       write_build_record(
           artifact="my_artifact",
           command=sys.argv,
           inputs=[args.data],
           outputs=[args.out_fig, args.out_table],
           output_path=args.out_meta
       )
   ```

2. **Add to Makefile**:
   ```makefile
   ARTIFACTS := price_base remodel_base my_artifact
   ```

3. **Build and publish**:
   ```bash
   make my_artifact
   make publish PUBLISH_ARTIFACTS="my_artifact"
   ```

---

## 🐍 Python Environment

Managed via conda with automatic Julia integration:

```bash
# Environment wrapper with Julia bridge
env/scripts/runpython script.py

# Direct conda activation (alternative)
conda activate .env
python script.py
```

**Packages** (see `env/python.yml`):
- pandas, matplotlib, numpy
- pyyaml (for provenance)
- juliacall (Python/Julia interop)
- jinja2 (for pandas LaTeX export)

---

## 📚 Julia Environment

**Pure Julia**:
```bash
env/scripts/runjulia script.jl
```

**Python/Julia interop** (via juliacall):
```python
from juliacall import Main as jl
jl.seval("using DataFrames")
df = jl.DataFrame(x=[1,2,3], y=[4,5,6])
```

**Packages** (see `env/Project.toml`):
- PythonCall (Julia/Python interop)
- DataFrames

Julia is auto-installed to `.julia/pyjuliapkg/` via juliacall.

---

## 📊 Stata Environment (Optional)

```bash
env/scripts/runstata script.do
```

**Packages** (see `env/stata-packages.txt`):
- reghdfe, ftools, estout

Installed to `.stata/ado/plus/` (local to project).

---

## 🧪 Examples

Test your setup:

```bash
make examples          # Run all examples
make sample-python     # Python example
make sample-julia      # Pure Julia example  
make sample-juliacall  # Python/Julia interop
make sample-stata      # Stata example (if installed)
```

See `examples/README.md` for details.

---

## ⚙️ System Requirements

- **OS:** Linux or macOS (Windows requires WSL)
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 5GB (2GB environment + 3GB cache)
- **Time:** ~15 minutes total (10 min setup + 5 min execution)
- **Software:** GNU Make 4.3+, conda/mamba (auto-installed if needed)
- **Optional:** Nix (for reproducible dev shell via `flake.nix`)

---

## 🔍 Makefile Targets

```bash
make                  # Brief guidance (essential commands)
make help             # Detailed command reference (all targets)
make info             # Comprehensive project information

make environment      # Setup Python/Julia/Stata (one-time)
make verify           # Verify environment and data (quick check)
make all              # Build all artifacts
make <artifact>       # Build specific artifact

make test-outputs     # Verify all expected outputs exist
make publish          # Publish all to paper/
make publish PUBLISH_ARTIFACTS="x y"  # Publish specific
make publish REQUIRE_CURRENT_HEAD=1   # Strict: require current HEAD

make test             # Run test suite
make lint             # Run code linter (ruff)
make format           # Auto-format code (ruff)
make type-check       # Run type checker (mypy)
make check            # Run all quality checks (lint + format + type + test)
make diff-outputs     # Compare current vs published outputs
make pre-submit       # Run pre-submission checklist
make replication-report  # Generate replication report
make journal-package  # Create journal submission package
make examples         # Run example scripts
make clean            # Remove all outputs
```

---

## 📖 Documentation

### Quick Start
- [QUICKSTART.md](QUICKSTART.md) - Get up and running in 5 minutes
- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes

### Detailed Guides
- [docs/environment.md](docs/environment.md) - Environment setup and management
- [docs/provenance.md](docs/provenance.md) - Provenance tracking system
- [docs/publishing.md](docs/publishing.md) - Publishing workflow and safety checks
- [docs/vscode_integration.md](docs/vscode_integration.md) - Working entirely in VS Code
- [docs/directory_structure.md](docs/directory_structure.md) - Project organization
- [docs/julia_python_integration.md](docs/julia_python_integration.md) - Julia/Python bridge configuration
- [docs/platform_compatibility.md](docs/platform_compatibility.md) - System requirements and GPU support
- [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues and solutions

### For Journal Submission
- [docs/journal_editor_readme.md](docs/journal_editor_readme.md) - One-page quick guide for reviewers
- [docs/paper_output_mapping.md](docs/paper_output_mapping.md) - Map paper figures/tables to outputs
- [docs/expected_outputs.md](docs/expected_outputs.md) - Verification checklist
- [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md) - Data access documentation

### Examples
See [examples/](examples/) directory for sample scripts in Python, Julia, and Stata.

---

## 🔒 Git Integration

Provenance tracking requires git:

```bash
git init
git add -A
git commit -m "Initial commit"
make all              # Builds include git commit hash
make publish          # Tracks publication from specific commit
```

The `paper/` directory is intended as a **separate git repository** for Overleaf integration.

---

## � Documentation

### Quick Start
- [QUICKSTART.md](QUICKSTART.md) - Get up and running in 5 minutes
- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes

### Detailed Guides
- [docs/environment.md](docs/environment.md) - Environment setup and management
- [docs/provenance.md](docs/provenance.md) - Provenance tracking system
- [docs/publishing.md](docs/publishing.md) - Publishing workflow and safety checks
- [docs/directory_structure.md](docs/directory_structure.md) - Project organization
- [docs/julia_python_integration.md](docs/julia_python_integration.md) - Julia/Python bridge configuration
- [docs/platform_compatibility.md](docs/platform_compatibility.md) - System requirements and GPU support
- [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues and solutions

### Examples
See [examples/](examples/) directory for sample scripts in Python, Julia, and Stata.

---

## 📞 Troubleshooting

**Quick fixes**:
- Import errors: Use `env/scripts/runpython` not bare `python`
- Build failures: `make clean && make all`
- Environment issues: `make cleanall && make environment`

**Detailed help**: See [docs/troubleshooting.md](docs/troubleshooting.md) for comprehensive solutions.

---

## 📄 License

MIT License - See `LICENSE` file.

---

## 📚 Citation

If you use this template, please cite:

```bibtex
@software{template2026,
  title = {Reproducible Research Template},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/project_template}
}
```

See `CITATION.cff` for structured metadata.

---

## 🎯 For Journal Submission

**Authors preparing replication packages:**

```bash
make journal-package    # Creates clean replication package
```

This creates a fresh git repository excluding:
- Development files (`.github/`, `.vscode/`, etc.)
- Author-only directories (`data-construction/`, `notes/`, `paper/`)
- Internal documentation (`TEMPLATE_USAGE.md`, etc.)

See `JOURNAL_EXCLUDE` for complete list and [`docs/journal_editor_readme.md`](docs/journal_editor_readme.md) for journal editor instructions.

---

**Last updated:** January 17, 2026
