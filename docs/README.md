# Documentation Index

Complete guide to the reproducible research template.

---

## 🚀 Getting Started (Start Here!)

1. **[README.md](../README.md)** - Project overview and quick reference
2. **[QUICKSTART.md](../QUICKSTART.md)** - Get up and running in 5 minutes
3. **[TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md)** - How to customize this template for your project

---

## 📖 Core Documentation

### Running the Project
- **[running_locally_vs_docker.md](running_locally_vs_docker.md)** - Local (uv) vs. Docker
  - How to run each, step by step
  - How the two relate (shared specs, separate built envs)
  - Why pick one over the other, and caveats

### Environment Setup
- **[environment.md](environment.md)** - Complete environment installation and management guide
  - Python 3.12 uv virtualenv
  - Julia installation via juliacall
  - Stata package setup
  - Environment wrappers (`runpython`, `runjulia`, `runstata`)

- **[repro_tools_submodule.md](repro_tools_submodule.md)** - Git submodule setup for repro-tools
  - Why use a git submodule
  - Automatic initialization
  - Working with editable installs
  - Updating to latest version
  - Troubleshooting

- **[submodule_cheatsheet.md](submodule_cheatsheet.md)** - Quick reference for submodule workflows
  - Creating new projects from template
  - Editing repro-tools
  - Updating to latest
  - Common scenarios and troubleshooting

### Build System
- **[notebook_support.md](notebook_support.md)** - Jupyter notebook integration and workflow
- **[notebook_interactive_workflow.md](notebook_interactive_workflow.md)** - Interactive development with Jupyter (complete guide)
- **[provenance.md](provenance.md)** - Provenance tracking system explained
  - Build provenance (per-artifact records)
  - Publication provenance (aggregated tracking)
  - Git state capture
  - SHA256 checksums
  - Verification workflows

- **[publishing.md](publishing.md)** - Publishing workflow and safety checks
  - Git safety checks (clean tree, not behind upstream)
  - REQUIRE_CURRENT_HEAD strict mode
  - Publishing specific artifacts
  - Troubleshooting publish failures

- **[defaults_system.md](defaults_system.md)** - 3-level defaults system (NEW!)
  - Docopt defaults (lowest priority)
  - config.DEFAULTS (global defaults)
  - config.STUDIES[study] (study-specific)
  - Command-line EXTRA_ARGS (highest priority)
  - Examples and best practices

- **[vscode_integration.md](vscode_integration.md)** - VS Code integration guide
  - Complete VS Code workflow without command line
  - Tasks for all Make targets
  - Debug configurations for Python scripts
  - Testing integration
  - Keyboard shortcuts and tips

- **[flexible_analyses.md](flexible_analyses.md)** - Flexible analysis definitions
  - Macro-based system for defining analyses
  - No rigid naming conventions
  - Multiple outputs per analysis
  - Examples and migration guide

- **[makefile_improvements.md](makefile_improvements.md)** - Recent Makefile improvements
  - Comparison with housing-analysis/Makefile
  - What was incorporated and why
  - New utility targets
  - Environment variables (JULIA_NUM_THREADS)

### Project Organization
- **[directory_structure.md](directory_structure.md)** - Complete directory layout
  - Build outputs (`output/`)
  - Published artifacts (`paper/`)
  - Environment specs (`env/`)
  - Analysis scripts (root level)
  - Shared utilities (`shared/`)

### Configuration and Validation
- **[shared/README.md](../shared/README.md)** - Project configuration (`shared/config.py`)
  - Generic CLI/validation utilities live in `repro_tools`:
  - `friendly_docopt()` - Enhanced error messages with typo suggestions
  - `setup_environment()` - Auto-detect Jupyter, IPython, terminal
  - `validate_study_config()` - Pre-flight configuration validation
  - `print_config()` - Pretty-printed configuration display

### Testing & Quality Assurance
- **Automated Testing** - pytest-based test suite (70+ tests)
  - Unit tests for provenance tracking (`tests/test_provenance.py`)
  - Integration tests for build workflow (`tests/test_integration.py`)
  - Environment setup tests (`tests/test_environment.py`)
  - Publishing workflow tests (`tests/test_publishing.py`)
  - Run with `make test` or `make test-cov` for coverage
- **Code Quality Tools** - Integrated linting and formatting
  - `make lint`: Ruff linter for code quality
  - `make format`: Auto-format with black and ruff (imports, whitespace, etc.)
  - `make format-check`: Check formatting without changes
  - `make type-check`: Mypy type checking for build scripts
  - `make check`: All quality checks (lint + format + type + test)
- **Output Comparison** - Track changes between builds
  - `make diff-outputs` compares current vs. published outputs
  - Shows differences in figures (checksums) and tables (line-by-line diff)
- **Pre-Submission Checks** - Comprehensive validation
  - `make pre-submit` runs all quality checks
  - Validates git state, data checksums, provenance, documentation
  - Strict mode available: `make pre-submit-strict`
- **Replication Reports** - Auto-generated documentation
  - `make replication-report` creates HTML report for reviewers
  - Includes system info, provenance, verification commands

### Journal Submission
- **[journal_editor_readme.md](journal_editor_readme.md)** - One-page quick guide for journal editors and reviewers
  - Step-by-step replication instructions
  - "What Success Looks Like" sections with expected output
  - Common troubleshooting
  - Contact information template

- **[paper_output_mapping.md](paper_output_mapping.md)** - Map paper figures/tables to output files
  - Quick reference table for targeted replication
  - LaTeX integration examples
  - Make target reference

- **[expected_outputs.md](expected_outputs.md)** - Verification checklist
  - Complete list of expected outputs
  - File descriptions and verification commands
  - Sample output content

- **[../DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md)** - Data availability statement for journal
  - Data access instructions
  - Restrictions and IRB information
  - Verification checksums

---

## 🔧 Technical Guides

### Multi-Language Integration
- **[julia_python_integration.md](julia_python_integration.md)** - Julia/Python bridge
  - Julia auto-installation via juliacall
  - CondaPkg configuration (why `JULIA_CONDAPKG_BACKEND=Null`)
  - Environment variables explained
  - Usage patterns (Python ↔ Julia interop)
  - Troubleshooting Julia issues

### Platform Support
- **[platform_compatibility.md](platform_compatibility.md)** - System requirements and configuration
  - Linux, macOS, Windows (WSL) support
  - GPU configuration (CUDA support)
  - Cross-platform file sharing
  - Environment variables reference
  - Julia precompilation issues

### Development Workflow
- **Code Quality** - Linting, formatting, and type checking
  - Integrated ruff linter for code quality enforcement
  - Auto-formatting with black and ruff (`make format`)
  - Type checking with mypy for build scripts
  - Comprehensive `make check` runs all quality tools
  - Configured via `pyproject.toml`

### Problem Solving
- **[troubleshooting.md](troubleshooting.md)** - Solutions to common issues
  - Quick diagnostics
  - Make errors
  - Environment setup errors
  - Build errors
  - Publishing errors
  - Julia/Python integration issues
  - Platform-specific issues

---

## 📋 Reference Documents

- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes
  - Track template evolution
  - Feature additions
  - Infrastructure changes
  - Breaking changes

- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - AI assistant guidance
  - Project architecture overview
  - Key workflows
  - Critical conventions
  - Integration points

---

## 📂 Examples

See **[env/examples/](../env/examples/)** directory for:
- `sample_python.py` - Pure Python example
- `sample_julia.jl` - Pure Julia example
- `sample_juliacall.py` - Python → Julia interop
- `sample_stata.do` - Stata example

Each example includes a Makefile target for testing.

---

## 🎯 Documentation by Use Case

### "I want to..."

#### Build and publish artifacts
1. [QUICKSTART.md](../QUICKSTART.md) - Copy-paste commands
2. [provenance.md](provenance.md) - Understand what's tracked
3. [publishing.md](publishing.md) - Learn safety checks

#### Set up environment on new machine
1. [QUICKSTART.md](../QUICKSTART.md) - Prerequisites section
2. [environment.md](environment.md) - Detailed installation
3. [platform_compatibility.md](platform_compatibility.md) - Platform-specific notes

#### Customize template for my project
1. [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Complete customization guide
2. [directory_structure.md](directory_structure.md) - Understand organization
3. [julia_python_integration.md](julia_python_integration.md) - Configure languages

#### Add Julia/Python analysis
1. [julia_python_integration.md](julia_python_integration.md) - Usage patterns
2. [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Script template
3. [env/examples/](../env/examples/) - Working examples

#### Enable GPU support
1. [platform_compatibility.md](platform_compatibility.md) - GPU configuration
2. [environment.md](environment.md) - Environment variables
3. [troubleshooting.md](troubleshooting.md) - GPU troubleshooting

#### Debug build failures
1. [troubleshooting.md](troubleshooting.md) - Common issues
2. [provenance.md](provenance.md) - Check build records
3. [environment.md](environment.md) - Verify environment

#### Publish to Overleaf
1. [publishing.md](publishing.md) - Publishing workflow
2. [QUICKSTART.md](../QUICKSTART.md) - Paper repo setup
3. [troubleshooting.md](troubleshooting.md) - Git safety check failures

#### Understand provenance system
1. [provenance.md](provenance.md) - Complete explanation
2. [publishing.md](publishing.md) - How publishing uses provenance
3. [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) - Add to custom scripts

---

## 📊 Documentation Structure

```
project_template/
├── README.md                           # Main entry point
├── QUICKSTART.md                       # Quick start (5 min)
├── CHANGELOG.md                        # Version history
├── TEMPLATE_USAGE.md                   # Customization guide
│
├── .github/
│   └── copilot-instructions.md         # AI assistant guidance
│
├── docs/
│   ├── README.md                       # This file
│   │
│   ├── environment.md                  # Environment setup
│   ├── provenance.md                   # Provenance tracking
│   ├── publishing.md                   # Publishing workflow
│   ├── directory_structure.md          # Project organization
│   │
│   ├── julia_python_integration.md     # Julia/Python bridge
│   ├── platform_compatibility.md       # System requirements
│   └── troubleshooting.md              # Problem solving
│
└── env/
    └── examples/
        ├── sample_python.py
        ├── sample_julia.jl
        ├── sample_juliacall.py
        └── sample_stata.do
```

---

## 📝 Documentation Conventions

### File Naming
- Root level: `UPPERCASE.md` (README, CHANGELOG, etc.)
- Docs directory: `lowercase_with_underscores.md`
- Cross-references: Relative paths with `.md` extension

### Structure
- **Quick reference** at top (TL;DR, quick commands)
- **Detailed explanation** in middle
- **Troubleshooting** at bottom
- **Cross-references** to related docs

### Code Examples
- Use `bash` language tags for shell commands
- Use `python`, `julia`, `makefile` for code
- Include comments explaining non-obvious parts
- Show expected output when helpful

### Emojis
- 🚀 Getting started / Quick actions
- 📖 Documentation / Reading
- 🔧 Technical / Configuration
- 📊 Data / Analysis
- 📂 Files / Directories
- ✅ Success / Correct
- ❌ Error / Incorrect
- ⚠️ Warning / Caution
- 💡 Tip / Best practice
- 📞 Help / Support

---

## 🔄 Keeping Documentation Updated

### When to Update

**Add to CHANGELOG.md**:
- New features
- Breaking changes
- Bug fixes
- Dependency updates

**Update technical docs**:
- New environment variables
- Changed directory structure
- New Makefile targets
- Modified workflows

**Update troubleshooting**:
- New common errors discovered
- Solutions to recurring issues
- Platform-specific problems

### Documentation Checklist for Changes

When making significant changes:

- [ ] Update CHANGELOG.md with version entry
- [ ] Update relevant technical doc (environment, provenance, etc.)
- [ ] Update QUICKSTART.md if quick start commands change
- [ ] Update README.md if core workflow changes
- [ ] Update troubleshooting.md with new issues found
- [ ] Update .github/copilot-instructions.md if architecture changes
- [ ] Update env/examples/ if usage patterns change
- [ ] Test all documented commands actually work

---

## 📧 Documentation Feedback

**Found an error?**
- Check git commit history for context
- Verify against current code
- Update or file issue

**Missing documentation?**
- Check if topic covered in related doc
- Add to troubleshooting.md if it's a common question
- Create new doc if substantial new topic

---

## 📈 Documentation Roadmap

### Completed (v1.0.0)
- ✅ Core workflow docs
- ✅ Environment setup
- ✅ Provenance system
- ✅ Multi-language integration
- ✅ Platform compatibility
- ✅ Troubleshooting guide
- ✅ Quick start guide
- ✅ Template customization guide

### Future Additions
- [ ] Video tutorials
- [ ] Architecture diagrams
- [ ] Performance optimization guide
- [ ] Advanced workflows (Docker, CI/CD)
- [ ] FAQ compilation
- [ ] Migration guides from other systems

---

## 🆘 Getting Help

### Documentation Not Clear?

1. **Check related docs**: Use "See also" links at bottom of pages
2. **Try examples**: Run code from `env/examples/` directory
3. **Check troubleshooting**: [troubleshooting.md](troubleshooting.md)
4. **Review git history**: See how features evolved
5. **Compare with fire project**: `../fire/` has similar structure

### Still Stuck?

- Check inline comments in code files
- Review Makefile for workflow logic
- Examine git commit messages for context
- Look at fire project documentation (this template is based on it)

---

**Template version**: 2.0.2

---

**[Back to README](../README.md)** | **[Quick Start](../QUICKSTART.md)** | **[Customization](../TEMPLATE_USAGE.md)**
