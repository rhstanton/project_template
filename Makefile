# ==============================================================================
# Reproducible Research Template - Makefile
# ==============================================================================
#
# This Makefile orchestrates all research analyses and artifact generation.
#
# QUICK START:
#   make all              # Run all analyses  
#   make price_base       # Run single analysis
#   make publish          # Publish results to paper/
#   make help             # Show all commands
#
# ==============================================================================
# Configuration: See config.py for centralized paths and analysis definitions
# ==============================================================================

# Delete partial outputs on error
.DELETE_ON_ERROR:

# Default shell with safer options
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Ensure git submodules are initialized (runs once per make invocation)
$(shell git submodule update --init --recursive 2>/dev/null || true)

# ==============================================================================
# Environment Variables
# ==============================================================================

# Julia threading (auto-detect CPU cores, or set explicitly)
export JULIA_NUM_THREADS ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)

# ==============================================================================
# Command-Line Overrides
# ==============================================================================
# EXTRA_ARGS: Global arguments appended to all analysis commands
# <analysis>_EXTRA_ARGS: Analysis-specific arguments
#
# Examples:
#   make price_base EXTRA_ARGS="--ylabel='Custom Label'"
#   make remodel_base EXTRA_ARGS="--table-agg=sum"
#   make price_base price_base_EXTRA_ARGS="--title='My Title'"
#
# Priority (lowest to highest):
#   1. Docopt defaults in run_analysis.py
#   2. config.DEFAULTS in shared/config.py
#   3. config.STUDIES[study] in shared/config.py
#   4. EXTRA_ARGS (global, affects all analyses)
#   5. <analysis>_EXTRA_ARGS (analysis-specific, highest priority)

EXTRA_ARGS ?=

# ==============================================================================
# Executable Scripts
# ==============================================================================

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

# ==============================================================================
# Analysis Definitions
# ==============================================================================
# Each analysis is a "run" that may generate multiple artifacts.
# Think of price_base as an analysis/run, not a single artifact.

# All analyses to run
ANALYSES := price_base remodel_base

# Input data files
DATA := data/housing_panel.csv

# ==============================================================================
# Directory Paths  
# ==============================================================================

# Repository root (for common.mk)
REPO_ROOT := $(shell pwd)

# Output directories
OUT_FIG_DIR := output/figures
OUT_TBL_DIR := output/tables
OUT_PROV_DIR := output/provenance
OUT_LOG_DIR := output/logs

# Paper directories
PAPER_DIR := paper
PAPER_FIG_DIR := $(PAPER_DIR)/figures
PAPER_TBL_DIR := $(PAPER_DIR)/tables

# Default target
.DEFAULT_GOAL := default

# ==============================================================================
# Include Generic Targets from repro-tools
# ==============================================================================
# This provides common targets used across all research projects:
#   - environment, examples, sample-*
#   - clean, cleanall, verify, test, test-cov
#   - lint, format, type-check, check
#   - update-submodules, update-environment
#   - diff-outputs, pre-submit, replication-report
#   - init-submodules (automatically run)

include lib/repro-tools/src/repro_tools/lib/common.mk

# ==============================================================================
# Main Build Targets
# ==============================================================================

# All targets
.PHONY: all
all:
	@rm -f .make_build_marker
	@$(MAKE) --no-print-directory $(ANALYSES)
	@if [ -f .make_build_marker ]; then \
		echo ""; \
		echo "=========================================="; \
		echo "✓ All analyses complete!"; \
		echo "=========================================="; \
		echo ""; \
		echo "Results:"; \
		echo "  - Figures: output/figures/"; \
		echo "  - Tables:  output/tables/"; \
		echo "  - Provenance: output/provenance/"; \
		echo ""; \
		rm -f .make_build_marker; \
	else \
		echo ""; \
		echo "=========================================="; \
		echo "✓ Nothing to do - all outputs up-to-date"; \
		echo "=========================================="; \
		echo ""; \
		echo "All artifacts are already built:"; \
		echo "  - Figures: output/figures/"; \
		echo "  - Tables:  output/tables/"; \
		echo "  - Provenance: output/provenance/"; \
		echo ""; \
		echo "To force rebuild: make clean && make all"; \
		echo ""; \
	fi

# ==============================================================================
# Analysis Build Rules (Macro-Based System)
# ==============================================================================
# Flexible analysis definitions - no rigid naming conventions required.
# Each analysis explicitly defines its script, inputs, and outputs.
# - Can have different numbers or types of outputs per analysis
# - Easier to add analyses with non-standard configurations
#
# Inspired by housing-analysis/Makefile but simplified for template use.
# ==============================================================================

# ------------------------------------------------------------------------------
# Analysis Definitions
# ------------------------------------------------------------------------------
# Define configuration for each analysis using simple Make variables.
# Format:
#   <analysis>.script  = path to script
#   <analysis>.runner  = command to run it (default: PYTHON)
#   <analysis>.inputs  = input files
#   <analysis>.outputs = output files (space-separated)
#   <analysis>.args    = command-line arguments

# price_base analysis
price_base.script  := run_analysis.py
price_base.runner  := $(PYTHON)
price_base.inputs  := $(DATA)
price_base.outputs := $(OUT_FIG_DIR)/price_base.pdf $(OUT_TBL_DIR)/price_base.tex $(OUT_PROV_DIR)/price_base.yml
price_base.args    := price_base

# remodel_base analysis
remodel_base.script  := run_analysis.py
remodel_base.runner  := $(PYTHON)
remodel_base.inputs  := $(DATA)
remodel_base.outputs := $(OUT_FIG_DIR)/remodel_base.pdf $(OUT_TBL_DIR)/remodel_base.tex $(OUT_PROV_DIR)/remodel_base.yml
remodel_base.args    := remodel_base

# ------------------------------------------------------------------------------
# Rule Generator Macro
# ------------------------------------------------------------------------------
# Takes an analysis name and generates Make rules for it.
# Uses grouped targets (&:) so all outputs are built by one command.
#
# Usage: $(call make-analysis-rule,<analysis_name>)

define make-analysis-rule

# Grouped target: all outputs built together
$($(1).outputs) &: $($(1).script) $($(1).inputs) | $(OUT_FIG_DIR) $(OUT_TBL_DIR) $(OUT_PROV_DIR) $(OUT_LOG_DIR)
	@echo "========================================"
	@echo "Running analysis: $(1)"
	@echo "========================================"
	@echo "Script:  $($(1).script)"
	@echo "Runner:  $($(1).runner)"
	@echo "Outputs: $($(1).outputs)"
	@echo ""
	$($(1).runner) $($(1).script) $($(1).args) $(EXTRA_ARGS) $($(1)_EXTRA_ARGS) 2>&1 | tee $(OUT_LOG_DIR)/$(1).log
	@echo ""
	@echo "✓ $(1) complete"
	@echo "  Outputs:"
	@$(foreach out,$($(1).outputs),echo "    - $(out)";)
	@echo "Built: $(1)" >> .make_build_marker

# Phony target for convenient invocation (e.g., "make price_base")
.PHONY: $(1)
$(1): $($(1).outputs)

endef

# ------------------------------------------------------------------------------
# Generate Rules for All Analyses
# ------------------------------------------------------------------------------
# Apply the template to each analysis defined in ANALYSES variable

$(foreach analysis,$(ANALYSES),$(eval $(call make-analysis-rule,$(analysis))))

# Ensure output directories exist
$(OUT_FIG_DIR) $(OUT_TBL_DIR) $(OUT_PROV_DIR) $(OUT_LOG_DIR):
	@mkdir -p $@

# ==============================================================================
# Publishing
# ==============================================================================
# Publishes build outputs from output/ to paper/ with provenance tracking.
# Git safety checks prevent publishing from dirty tree or outdated branch.
#
# Two modes of selective publishing:
#   1. Analysis-level: PUBLISH_ANALYSES="price_base remodel_base" 
#      Publishes ALL outputs from specified analyses
#   2. File-level: PUBLISH_FILES="output/figures/price_base.pdf output/tables/custom.tex"
#      Publishes only specified files (for fine-grained control)
#
# Examples:
#   make publish                                    # Publish all analyses
#   make publish PUBLISH_ANALYSES="price_base"     # Publish all outputs from price_base
#   make publish PUBLISH_FILES="output/figures/price_base.pdf"  # Publish only one figure

PUBLISH_ANALYSES ?= $(ANALYSES)
PUBLISH_FILES ?=  # Optional: space-separated paths like "output/figures/x.pdf output/tables/y.tex"
REQUIRE_CURRENT_HEAD ?= 0  # Set to 1 to ensure all artifacts from current HEAD
ALLOW_DIRTY ?= 0  # Set to 1 to allow publishing from dirty working tree (not recommended)
REQUIRE_NOT_BEHIND ?= 1  # Set to 0 to allow publishing when behind upstream
PUBLISH_STAMP_DIR := .publish_stamps

.PHONY: publish publish-force
publish:
	@$(REPRO_CHECK) --allow-dirty $(ALLOW_DIRTY) --require-not-behind $(REQUIRE_NOT_BEHIND) --require-current-head $(REQUIRE_CURRENT_HEAD) --artifacts "$(PUBLISH_ANALYSES)"
	@echo ""
	@echo "=========================================="
	@echo "Publishing outputs to paper/..."
	@echo "=========================================="
	@echo ""
ifdef PUBLISH_FILES
	@echo "Publishing mode: File-level selection"
	@echo "Files: $(PUBLISH_FILES)"
	@echo ""
	@$(MAKE) --no-print-directory publish-files
else
	@echo "Publishing mode: Analysis-level selection"
	@echo "Analyses: $(PUBLISH_ANALYSES)"
	@echo ""
	@$(MAKE) --no-print-directory publish-figures publish-tables
endif
	@if [ -f .publish_marker ]; then \
		echo ""; \
		echo "=========================================="; \
		echo "✓ Publishing complete!"; \
		echo "=========================================="; \
		echo ""; \
		echo "Updated: paper/provenance.yml"; \
		echo ""; \
		rm -f .publish_marker; \
	else \
		echo ""; \
		echo "=========================================="; \
		echo "✓ Nothing to publish - all up-to-date"; \
		echo "=========================================="; \
		echo ""; \
		echo "Published analyses: $(PUBLISH_ANALYSES)"; \
		echo "  - paper/figures/"; \
		echo "  - paper/tables/"; \
		echo "  - paper/provenance.yml"; \
		echo ""; \
		echo "To force re-publish: make publish-force"; \
		echo ""; \
	fi

# Force re-publish even if up-to-date
publish-force:
	@rm -rf $(PUBLISH_STAMP_DIR)
	@$(MAKE) publish

# Publish all figures (prints header, then processes individual stamps)
.PHONY: publish-figures
publish-figures:
	@echo "Figures:"
	@$(MAKE) --no-print-directory -s $(addprefix $(PUBLISH_STAMP_DIR)/,$(addsuffix .figures.stamp,$(PUBLISH_ANALYSES)))

# Publish all tables (prints header, then processes individual stamps)
.PHONY: publish-tables
publish-tables:
	@echo "Tables:"
	@$(MAKE) --no-print-directory -s $(addprefix $(PUBLISH_STAMP_DIR)/,$(addsuffix .tables.stamp,$(PUBLISH_ANALYSES)))

# Publish specific files (file-level selection)
.PHONY: publish-files
publish-files:
	@for file in $(PUBLISH_FILES); do [ -f "$$file" ] || { echo "Error: File not found: $$file"; exit 1; }; done
	@$(REPRO_PUBLISH) --paper-root $(PAPER_DIR) \
	  --files "$(PUBLISH_FILES)" \
	  --allow-dirty 0 \
	  --require-not-behind 1 \
	  --require-current-head $(REQUIRE_CURRENT_HEAD)
	@touch .publish_marker

# Individual stamp files (for incremental publishing)
$(PUBLISH_STAMP_DIR)/%.figures.stamp: $(OUT_FIG_DIR)/%.pdf $(OUT_PROV_DIR)/%.yml
	@mkdir -p $(PUBLISH_STAMP_DIR) $(PAPER_FIG_DIR)
	@$(REPRO_PUBLISH) --paper-root $(PAPER_DIR) \
	  --kind figures \
	  --analyses "$*" \
	  --allow-dirty 0 \
	  --require-not-behind 1 \
	  --require-current-head $(REQUIRE_CURRENT_HEAD)
	@touch $@
	@touch .publish_marker

$(PUBLISH_STAMP_DIR)/%.tables.stamp: $(OUT_TBL_DIR)/%.tex $(OUT_PROV_DIR)/%.yml
	@mkdir -p $(PUBLISH_STAMP_DIR) $(PAPER_TBL_DIR)
	@$(REPRO_PUBLISH) --paper-root $(PAPER_DIR) \
	  --kind tables \
	  --analyses "$*" \
	  --allow-dirty 0 \
	  --require-not-behind 1 \
	  --require-current-head $(REQUIRE_CURRENT_HEAD)
	@touch $@
	@touch .publish_marker

# ==============================================================================
# JOURNAL SUBMISSION PACKAGE
# ==============================================================================
# BEGIN AUTHOR-ONLY

.PHONY: journal-package
journal-package:
	@echo "Creating journal submission package with git repository..."
	@echo ""
	@echo "Excluding directories listed in JOURNAL_EXCLUDE:"
	@grep '^[a-z]' JOURNAL_EXCLUDE 2>/dev/null || echo "  (JOURNAL_EXCLUDE file not found)"
	@echo ""
	@rm -rf replication-package
	@mkdir -p replication-package
	@git archive --format=tar HEAD | tar -x -C replication-package/
	@echo "Copying git submodules (repro-tools)..."
	@mkdir -p replication-package/lib
	@cp -r lib/repro-tools replication-package/lib/
	@echo "Removing excluded directories..."
	@cd replication-package && rm -rf data-construction notes paper JOURNAL_EXCLUDE .github .vscode .dir-locals.el .editorconfig .mypy_cache .ruff_cache logs TEMPLATE_USAGE.md COAUTHOR_SETUP.md 2>/dev/null || true
	@echo "Generating clean Makefile (removing AUTHOR-ONLY sections)..."
	@sed '/^# BEGIN AUTHOR-ONLY/,/^# END AUTHOR-ONLY/d' Makefile > replication-package/Makefile.tmp
	@mv replication-package/Makefile.tmp replication-package/Makefile
	@echo "Initializing git repository..."
	@cd replication-package && git init
	@cd replication-package && git add -A
	@cd replication-package && git commit -m "Initial commit: Replication package for journal submission"
	@echo ""
	@echo "✓ Created: replication-package/ (git repository)"
	@echo ""
	@echo "Repository status:"
	@cd replication-package && git log --oneline
	@cd replication-package && echo "" && git status
	@echo ""
	@echo "Verification:"
	@test ! -d replication-package/data-construction && test ! -d replication-package/notes && test ! -d replication-package/paper && echo "  ✓ Excluded directories removed" || echo "  ✗ WARNING: Some excluded directories still present"
	@grep -q "journal-package" replication-package/Makefile && echo "  ✗ WARNING: journal-package target still in Makefile" || echo "  ✓ Clean Makefile for journal editors"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Review: cd replication-package && git log -p"
	@echo "  2. Test: cd replication-package && make environment && make all"
	@echo "  3. Create GitHub repo: gh repo create your-project-replication --public --source=replication-package --push"
	@echo "  4. Or create archive: make journal-package-tarball"
	@echo ""

.PHONY: journal-package-tarball
journal-package-tarball:
	@if [ -d replication-package ]; then \
		EXISTED=1; \
	else \
		EXISTED=0; \
		$(MAKE) journal-package; \
	fi; \
	echo "Creating tarball from journal package..."; \
	tar czf replication-package.tar.gz replication-package/; \
	if [ $$EXISTED -eq 0 ]; then \
		rm -rf replication-package; \
	fi; \
	echo "✓ Created: replication-package.tar.gz"

.PHONY: journal-package-zip
journal-package-zip:
	@if [ -d replication-package ]; then \
		EXISTED=1; \
	else \
		EXISTED=0; \
		$(MAKE) journal-package; \
	fi; \
	echo "Creating ZIP from journal package..."; \
	zip -rq replication-package.zip replication-package/; \
	if [ $$EXISTED -eq 0 ]; then \
		rm -rf replication-package; \
	fi; \
	echo "✓ Created: replication-package.zip"

.PHONY: clean-journal
clean-journal:
	@echo "Removing journal package artifacts..."
	@rm -rf replication-package replication-package.tar.gz replication-package.zip
	@echo "✓ Cleaned journal package"

# END AUTHOR-ONLY

# ==============================================================================
# Help & Info Targets
# ==============================================================================

# Default target: brief guidance
.PHONY: default
default:
	@echo ""
	@echo "=========================================="
	@echo "  Reproducible Research Template"
	@echo "=========================================="
	@echo ""
	@echo "ESSENTIAL COMMANDS:"
	@echo "  make environment        Setup Python/Julia/Stata (~10 min)"
	@echo "  make update-environment Get latest updates + reinstall environment"
	@echo "  make all                Run all analyses (~5 min)"
	@echo "  make verify             Quick environment check (~1 min)"
	@echo "  make test               Run test suite"
	@echo "  make check              Run all quality checks (lint + format + type + test)"
	@echo "  make publish            Publish to paper/"
	@echo "  make clean              Remove outputs"
	@echo ""
	@echo "HELP:"
	@echo "  make help             Show all available commands"
	@echo "  make info             Show comprehensive project information"
	@echo "  make list-analyses    List all available analyses"
	@echo "  make show-analysis-<name>  Show config for specific analysis"
	@echo ""
	@echo "VS CODE USERS:"
	@echo "  Prefer GUI? See GETTING_STARTED_VSCODE.md"
	@echo "  Press Ctrl+Shift+P → 'Tasks: Run Task' to browse all tasks"
	@echo "  Press Ctrl+Shift+B to build everything"
	@echo ""
	@echo "DOCUMENTATION:"
	@echo "  README.md             Project overview and quick start"
	@echo "  QUICKSTART.md         5-minute getting started guide"
	@echo "  GETTING_STARTED_VSCODE.md  VS Code integration guide"
	@echo "  docs/                 Complete documentation"
	@echo ""

.PHONY: help
help:
	@echo ""
	@echo "================================================================"
	@echo "  Research Template Makefile"
	@echo "================================================================"
	@echo ""
	@echo "ENVIRONMENT:"
	@echo "  make environment        Setup Python 3.11 + Julia + Stata (~10 min)"
	@echo "  make update-environment Get latest updates + reinstall environment"
	@echo "  make verify             Quick environment check (~1 min)"
	@echo "  make examples           Run example scripts (Python/Julia)"
	@echo "  make sample-python      Run Python example"
	@echo "  make sample-julia       Run Julia example"
	@echo "  make sample-juliacall   Run Python/Julia interop example"
	@echo "  make sample-stata       Run Stata example (if installed)"
	@echo ""
	@echo "BUILD:"
	@echo "  make all              Run all analyses (~5 min)"
	@echo "  make price_base       Run price_base analysis only"
	@echo "  make remodel_base     Run remodel_base analysis only"
	@echo ""
	@echo "VERIFICATION:"
	@echo "  make test-outputs     Verify all expected outputs exist"
	@echo "  make test             Run test suite (pytest)"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make system-info      Log computational environment"
	@echo "  make diff-outputs     Compare current vs published outputs"
	@echo ""
	@echo "PUBLISH:"
	@echo "  make publish          Publish all analyses to paper/"
	@echo "  make publish PUBLISH_ANALYSES='price_base'  # Publish specific analyses"
	@echo "  make publish PUBLISH_FILES='output/figures/x.pdf output/tables/y.tex'  # Publish specific files"
	@echo "  make publish REQUIRE_CURRENT_HEAD=1  # Strict mode (require current HEAD)"
	@echo "  make publish-force    Force re-publish even if up-to-date"
	@echo ""
	@echo "TESTING & QUALITY:"
	@echo "  make test             Run pytest test suite"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make lint             Run code linter (ruff)"
	@echo "  make format           Auto-format code (ruff format + fixes)"
	@echo "  make format-check     Check formatting without changes"
	@echo "  make type-check       Run type checker (mypy)"
	@echo "  make check            Run all quality checks (lint + format + type + test)"
	@echo "  make diff-outputs     Compare current vs published outputs"
	@echo "  make pre-submit       Run pre-submission checklist"
	@echo "  make pre-submit-strict  Strict pre-submission checks"
	@echo "  make replication-report  Generate replication report (HTML)"
	@echo ""
	@echo "JOURNAL SUBMISSION (AUTHOR-ONLY):"
	@echo "  make journal-package         Create clean replication package"
	@echo "  make journal-package-tarball Create .tar.gz archive"
	@echo "  make journal-package-zip     Create .zip archive"
	@echo "  make clean-journal           Remove package artifacts"
	@echo ""
	@echo "CLEANUP:"
	@echo "  make clean            Remove all outputs"
	@echo "  make cleanall         Remove outputs + environments"
	@echo ""
	@echo "HELP:"
	@echo "  make                  Show brief guidance"
	@echo "  make help             Show this detailed command reference"
	@echo "  make info             Show comprehensive project information"
	@echo ""
	@echo "UTILITY COMMANDS:"
	@echo "  make list-analyses    List all available analyses"
	@echo "  make show-analysis-<name>  Show detailed config for specific analysis"
	@echo "  make check-deps         Check Python/Julia/data dependencies"
	@echo "  make dryrun             Show what would be built (without building)"
	@echo "  make update-submodules  Update repro-tools (submodule only)"
	@echo "  make update-environment Update repro-tools AND reinstall environment"
	@echo ""

.PHONY: info
info:
	@echo "=============================================================================="
	@echo "  Reproducible Research Template - Project Information"
	@echo "=============================================================================="
	@echo ""
	@echo "PROJECT STRUCTURE:"
	@echo "  env/                     Software environments (Python/Julia/Stata)"
	@echo "  data/                    Input datasets (CSV files)"
	@echo "  build_*.py               Analysis scripts (figure + table per script)"
	@echo "  output/                  Build outputs (ephemeral, can be rebuilt)"
	@echo "    ├─ figures/            Generated PDFs"
	@echo "    ├─ tables/             Generated LaTeX tables"
	@echo "    ├─ provenance/         Per-artifact build records"
	@echo "    └─ logs/               Build logs"
	@echo "  paper/                   Published artifacts (permanent)"
	@echo "    ├─ figures/            Published figures"
	@echo "    ├─ tables/             Published tables"
	@echo "    └─ provenance.yml      Aggregated publication provenance"
	@echo "  env/                     Environment setup (Python/Julia/Stata)"
	@echo "  docs/                    Documentation (10 guides)"
	@echo "  tests/                   Test suite (pytest)"
	@echo "  env/examples/            Sample scripts (Python/Julia/Stata)"
	@echo ""
	@echo "PIPELINE FLOW:"
	@echo "  1. make environment      → Install Python 3.11, Julia, Stata packages"
	@echo "     Runtime: ~10 min      → Creates .env/ (~2GB), .julia/ (~500MB)"
	@echo ""
	@echo "  2. make verify           → Quick smoke test"
	@echo "     Runtime: ~1 min       → Checks environment, packages, data"
	@echo ""
	@echo "  3. make all              → Run all analyses"
	@echo "     Runtime: ~5 min       → Creates figures, tables, provenance"
	@echo "     ├─ make price_base    → Price analysis (Figure + Table)"
	@echo "     └─ make remodel_base  → Remodel analysis (Figure + Table)"
	@echo ""
	@echo "  4. make test-outputs     → Verify outputs exist"
	@echo "     Runtime: <1 min       → Checks all expected files present"
	@echo ""
	@echo "  5. make publish          → Publish to paper/"
	@echo "     Runtime: <1 min       → Copies outputs + updates provenance"
	@echo ""
	@echo "EXPECTED OUTPUTS:"
	@echo "  Figures:  2 PDFs (price_base.pdf, remodel_base.pdf)"
	@echo "  Tables:   2 LaTeX files (price_base.tex, remodel_base.tex)"
	@echo "  Provenance: 2 YAML files (build records)"
	@echo "  Total runtime: ~15 min first run (10 min environment + 5 min build)"
	@echo "  Disk usage:    ~3 GB (2 GB environment + 1 GB data/cache)"
	@echo ""
	@echo "SYSTEM REQUIREMENTS:"
	@echo "  OS:        Linux, macOS (Windows via WSL2)"
	@echo "  RAM:       8 GB minimum, 16 GB recommended"
	@echo "  CPU:       Multi-core recommended (parallel: make -j4)"
	@echo "  Software:  Git, Make 4.3+, Conda/Mamba (auto-installed if missing)"
	@echo ""
	@echo "KEY DOCUMENTATION:"
	@echo "  Quick start:         README.md, QUICKSTART.md"
	@echo "  Journal editors:     docs/journal_editor_readme.md (1-page guide)"
	@echo "  Paper → outputs:     docs/paper_output_mapping.md"
	@echo "  Expected results:    docs/expected_outputs.md"
	@echo "  Environment setup:   docs/environment.md"
	@echo "  Provenance system:   docs/provenance.md"
	@echo "  Publishing workflow: docs/publishing.md"
	@echo "  Troubleshooting:     docs/troubleshooting.md"
	@echo "  Data access:         DATA_AVAILABILITY.md"
	@echo "  Directory structure: docs/directory_structure.md"
	@echo ""
	@echo "TECHNOLOGY STACK:"
	@echo "  Primary:   Python 3.11 (pandas, matplotlib, pyyaml, pytest)"
	@echo "  Backend:   Julia 1.10-1.12 (via juliacall, auto-installed)"
	@echo "  Optional:  Stata (for Stata examples only, not required)"
	@echo "  Tools:     GNU Make 4.3+, Git, conda/micromamba"
	@echo ""
	@echo "PROVENANCE TRACKING:"
	@echo "  Build time:    Records git state, input/output SHA256, command, timestamp"
	@echo "  Publish time:  Aggregates build records, tracks publication event"
	@echo "  Verification:  SHA256 checksums detect any modifications"
	@echo "  Safety checks: Refuses to publish from dirty tree or outdated branch"
	@echo ""
	@echo "COMMANDS OVERVIEW:"
	@echo "  make                 Show brief guidance"
	@echo "  make help            Show detailed command reference"
	@echo "  make info            Show this comprehensive information"
	@echo ""
	@echo "GETTING HELP:"
	@echo "  Issues:     Check docs/troubleshooting.md first"
	@echo "  Logs:       Check output/logs/ for detailed error traces"
	@echo "  Tests:      make test (run test suite)"
	@echo "  Examples:   make examples (test environment)"
	@echo ""

# ==============================================================================
# Utility Targets
# ==============================================================================
# Inspired by housing-analysis/Makefile utility commands

.PHONY: list-analyses list-analyses-verbose show-analysis

# List all available analyses
list-analyses:
	@echo "Available analyses:"
	@$(foreach analysis,$(ANALYSES), \
		echo "  - $(analysis)"; \
	)

# List analyses with more detail
list-analyses-verbose:
	@echo "Available analyses (with configuration):"
	@$(foreach analysis,$(ANALYSES), \
		echo "  - $(analysis)"; \
		echo "      Script:  $($(analysis).script)"; \
		echo "      Runner:  $($(analysis).runner)"; \
		echo "      Outputs: $(words $($(analysis).outputs)) files"; \
		echo ""; \
	)

# Show detailed configuration for a specific analysis
# Usage: make show-analysis-price_base
show-analysis-%:
	@echo "========================================"
	@echo "Analysis: $*"
	@echo "========================================"
	@echo "Script:  $($*.script)"
	@echo "Runner:  $($*.runner)"
	@echo ""
	@echo "Inputs:"
	@$(foreach input,$($*.inputs),echo "  - $(input)";)
	@echo ""
	@echo "Outputs:"
	@$(foreach output,$($*.outputs),echo "  - $(output)";)
	@echo ""
	@echo "Arguments:"
	@echo "  $($*.args)" | sed 's/--/\n  --/g'
	@echo ""
	@echo "To build:"
	@echo "  make $*"
	@echo ""
	@echo "To view logs:"
	@echo "  cat $(OUT_LOG_DIR)/$*.log"
	@echo "========================================"
