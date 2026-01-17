# Reproducible Research Template

**A minimal template for reproducible research with provenance tracking and automated builds**

This template provides a complete workflow for building research artifacts (figures and tables) with full provenance tracking, separating build outputs from published results.

---

## 🚀 Quick Start

**First time setup (required once, ~10-15 minutes):**
```bash
make environment    # Install Python, Julia, Stata packages
```

**To build all artifacts:**
```bash
make all           # Build figures + tables + provenance
```

**To publish to paper directory:**
```bash
make publish       # Copy outputs to paper/ with provenance
```

**To test setup:**
```bash
make examples      # Run example scripts
```

---

## 📊 What This Template Provides

### Core Features

- **Reproducible builds**: GNU Make orchestration with grouped targets
- **Provenance tracking**: Full git state + input/output SHA256 hashes
- **Build/publish separation**: Build in `output/`, publish to `paper/`
- **Multi-language support**: Python, Julia, Stata
- **Example workflows**: Sample scripts for all three languages

### Directory Structure

```
project_template/
├── build_price_base.py    # Analysis scripts
├── build_remodel_base.py
├── data/              # Input datasets
├── env/               # Environment setup (Python/Julia/Stata)
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

- **OS**: Linux or macOS (Windows requires WSL)
- **RAM**: 8GB minimum
- **Disk**: 5GB (2GB environment + 3GB cache)
- **Software**: GNU Make 4.3+, conda/mamba/micromamba
- **Optional**: Nix (for reproducible dev shell via `flake.nix`)

---

## 🔍 Makefile Targets

```bash
make                  # Show help (default)
make help             # Show detailed commands
make info             # Show quick start guide

make environment      # Setup Python/Julia/Stata (one-time)
make all              # Build all artifacts
make <artifact>       # Build specific artifact

make publish          # Publish all to paper/
make publish PUBLISH_ARTIFACTS="x y"  # Publish specific
make publish REQUIRE_CURRENT_HEAD=1   # Strict: require current HEAD

make examples         # Run example scripts
make clean            # Remove all outputs
```

---

## 📖 Documentation

- `README.md` (this file) - Overview and quick start
- `docs/environment.md` - Detailed environment setup guide
- `docs/provenance.md` - Provenance tracking explained
- `docs/publishing.md` - Publishing workflow guide
- `docs/directory_structure.md` - Project organization
- `examples/README.md` - Example scripts documentation
- `.github/copilot-instructions.md` - AI agent guidance

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

**Last updated**: January 16, 2026
