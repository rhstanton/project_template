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
# FILE STRUCTURE
# ==============================================================================
#
#   QUICK NAVIGATION - Jump to line number in your editor (Ctrl+G / Cmd+L):
#
#     30: Shell & Environment Variables (JULIA_NUM_THREADS, paths)
#     60: Analysis Definitions (ANALYSES, DATA, directories)
#    110: Main Build Targets (all, environment)
#    165: Example Scripts (sample-python, sample-julia, etc.)
#    190: Build Rules (macro-based analysis build system)
#    270: Publishing (publish, publish-force, file/analysis-level)
#    388: Cleanup (clean, cleanall)
#    401: Verification & Testing (verify, test, diff-outputs)
#    525: Journal Submission (journal-package, archives)
#    604: Help & Info (default, help, info targets)
#    788: Utility Commands (list-analyses, show-analysis-*, check-deps)
#
#   OVERVIEW:
#   1. CONFIGURATION (lines 30-80)
#      - Shell options, paths, environment variables, analysis definitions
#
#   2. BUILD RULES (lines 110-180)
#      - Pattern rules for building analyses (figures, tables, provenance)
#
#   3. PUBLISHING (lines 190-260)
#      - Publishing artifacts to paper/ with provenance tracking
#
#   4. TESTING & VERIFICATION (lines 270-350)
#      - Environment verification, output comparison, pre-submission checks
#
#   5. UTILITY COMMANDS (lines 360+)
#      - Help, info, list-analyses, show-analysis-*, clean, etc.
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

OUT_FIG_DIR := output/figures
OUT_TBL_DIR := output/tables
OUT_PROV_DIR := output/provenance
OUT_LOG_DIR := output/logs

PAPER_DIR := paper
PAPER_FIG_DIR := $(PAPER_DIR)/figures
PAPER_TBL_DIR := $(PAPER_DIR)/tables

# Default target
.DEFAULT_GOAL := default

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

# Environment setup
.PHONY: environment
environment:
	@echo ""
	@echo "=========================================="
	@echo "Setting up software environment..."
	@echo "=========================================="
	@echo ""
	@echo "📦 Initializing git submodules..."
	@git submodule update --init --recursive 2>/dev/null || echo "  ⚠️  Warning: git submodule update failed (not critical if already initialized)"
	@echo ""
	$(MAKE) -C env all-env
	@echo ""
	@echo "✓ Environment ready!"
	@echo ""
	@echo "  Python 3.11:    .env/bin/python"
	@echo "  Julia:          .julia/pyjuliapkg/install/bin/julia"
	@echo "  Stata packages: .stata/ado/plus/ (if Stata installed)"
	@echo "  repro-tools:    lib/repro-tools/ (git submodule)"
	@echo ""
	@echo "Next: make all (to build all artifacts)"
	@echo ""

# ==============================================================================
# Example Scripts
# ==============================================================================

.PHONY: sample-python sample-julia sample-juliacall sample-stata examples

sample-python: | $(OUT_LOG_DIR)
	@echo "Running Python example..."
	$(PYTHON) examples/sample_python.py 2>&1 | tee $(OUT_LOG_DIR)/sample_python.log

sample-julia: | $(OUT_LOG_DIR)
	@echo "Running Julia example..."
	$(JULIA) examples/sample_julia.jl 2>&1 | tee $(OUT_LOG_DIR)/sample_julia.log

sample-juliacall: | $(OUT_LOG_DIR)
	@echo "Running Python/Julia interop example (juliacall)..."
	$(PYTHON) examples/sample_juliacall.py 2>&1 | tee $(OUT_LOG_DIR)/sample_juliacall.log

sample-stata: | $(OUT_LOG_DIR)
	@echo "Running Stata example..."
	$(STATA) examples/sample_stata.do 2>&1 | tee $(OUT_LOG_DIR)/sample_stata.log

examples: sample-python sample-julia sample-juliacall
	@echo "✓ All examples complete (Stata skipped - run 'make sample-stata' if Stata is installed)"

# ==============================================================================
# Build Rules
# ==============================================================================
# Uses a macro/template system for flexibility:
# - Each analysis explicitly defines its script, inputs, and outputs
# - No rigid naming conventions required
# - Can have different numbers or types of outputs per analysis
# - Easier to add new analyses with non-standard configurations
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
price_base.script  := build_price_base.py
price_base.runner  := $(PYTHON)
price_base.inputs  := $(DATA)
price_base.outputs := $(OUT_FIG_DIR)/price_base.pdf $(OUT_TBL_DIR)/price_base.tex $(OUT_PROV_DIR)/price_base.yml
price_base.args    := --data $(DATA) --out-fig $(OUT_FIG_DIR)/price_base.pdf --out-table $(OUT_TBL_DIR)/price_base.tex

# remodel_base analysis
remodel_base.script  := build_remodel_base.py
remodel_base.runner  := $(PYTHON)
remodel_base.inputs  := $(DATA)
remodel_base.outputs := $(OUT_FIG_DIR)/remodel_base.pdf $(OUT_TBL_DIR)/remodel_base.tex $(OUT_PROV_DIR)/remodel_base.yml
remodel_base.args    := --data $(DATA) --out-fig $(OUT_FIG_DIR)/remodel_base.pdf --out-table $(OUT_TBL_DIR)/remodel_base.tex

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
	$($(1).runner) $($(1).script) $($(1).args) 2>&1 | tee $(OUT_LOG_DIR)/$(1).log
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
# Cleanup Targets
# ==============================================================================

.PHONY: clean
clean:
	rm -rf output/figures output/tables output/provenance output/logs .publish_stamps
	@rm -f .publish_marker .make_build_marker

.PHONY: cleanall
cleanall: clean
	@rm -rf .env .julia .stata

# ==============================================================================
# Verification & Testing
# ==============================================================================

.PHONY: verify
verify:
	@echo ""
	@echo "========================================"
	@echo "  Quick Verification (~1 minute)"
	@echo "========================================"
	@echo ""
	@echo "1. Checking Python environment..."
	@if [ -f .env/bin/python ]; then \
		.env/bin/python --version | sed 's/^/   /' && echo "   ✓"; \
	else \
		echo "   ✗ Python environment not found"; \
		echo "   Run: make environment"; \
		exit 1; \
	fi
	@echo ""
	@echo "2. Checking key packages..."
	@.env/bin/python -c "import pandas; print('   pandas', pandas.__version__, '✓')" || echo "   ✗ pandas missing"
	@.env/bin/python -c "import matplotlib; print('   matplotlib', matplotlib.__version__, '✓')" || echo "   ✗ matplotlib missing"
	@.env/bin/python -c "import yaml; print('   pyyaml ✓')" || echo "   ✗ pyyaml missing"
	@.env/bin/python -c "import juliacall; print('   juliacall ✓')" || echo "   ✗ juliacall missing"
	@echo ""
	@echo "3. Checking data availability..."
	@if [ -f $(DATA) ]; then \
		echo "   $(DATA) ✓"; \
		sha256sum $(DATA) | awk '{print "   SHA256: " substr($$1,1,16) "... ✓"}'; \
	else \
		echo "   ✗ Data file not found: $(DATA)"; \
		exit 1; \
	fi
	@echo ""
	@echo "========================================"
	@echo "  ✓ Verification Complete"
	@echo "========================================"
	@echo ""
	@echo "Environment is ready. Next steps:"
	@echo "  make all              # Run all analyses"
	@echo "  make price_base       # Run single analysis"
	@echo "  make system-info      # Log computational environment"
	@echo ""

.PHONY: system-info
system-info:
	@echo "Logging computational environment..."
	@$(REPRO_SYSINFO) --output output/system_info.yml \
	  --repo-root $(REPO_ROOT)
	@echo ""
	@echo "System information saved to output/system_info.yml"
	@echo "This file contains OS, Python, Julia versions and package lists."
	@echo ""

.PHONY: test
test:
	@echo "Running test suite..."
	@$(PYTHON) -m pytest tests/ -v
	@echo ""
	@echo "✓ Tests complete"
	@echo ""

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	@$(PYTHON) -m pytest tests/ --cov=scripts --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report: htmlcov/index.html"
	@echo ""

.PHONY: diff-outputs
diff-outputs:
	@echo "Comparing current outputs with published outputs..."
	@$(REPRO_COMPARE) --reference paper \
	  --current-dir output
	@echo ""

.PHONY: pre-submit
pre-submit:
	@echo "Running pre-submission checklist..."
	@$(REPRO_CHECK) --pre-submit
	@echo ""

.PHONY: pre-submit-strict
pre-submit-strict:
	@echo "Running pre-submission checklist (strict mode)..."
	@$(REPRO_CHECK) --pre-submit --strict
	@echo ""

.PHONY: replication-report
replication-report:
	@echo "Generating replication report..."
	@$(REPRO_REPORT) --format html \
	  --output output/replication_report.html
	@echo ""
	@echo "Report generated: output/replication_report.html"
	@echo "Open in browser: file://$(REPO_ROOT)/output/replication_report.html"
	@echo ""

.PHONY: test-outputs
test-outputs:
	@echo "Verifying all expected outputs exist..."
	@echo ""
	@MISSING=0; \
	for analysis in $(ANALYSES); do \
		for file in $(OUT_FIG_DIR)/$${analysis}.pdf $(OUT_TBL_DIR)/$${analysis}.tex; do \
			if [ -f "$$file" ]; then \
				echo "  ✓ $$file"; \
			else \
				echo "  ✗ Missing $$file"; \
				MISSING=$$((MISSING + 1)); \
			fi; \
		done; \
	done; \
	echo ""; \
	if [ $$MISSING -eq 0 ]; then \
		echo "✓ All expected outputs present!"; \
		echo "  See docs/expected_outputs.md for details"; \
	else \
		echo "✗ $$MISSING file(s) missing. Run: make all"; \
		exit 1; \
	fi

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

# Default target: brief guidance
.PHONY: default
default:
	@echo ""
	@echo "=========================================="
	@echo "  Reproducible Research Template"
	@echo "=========================================="
	@echo ""
	@echo "ESSENTIAL COMMANDS:"
	@echo "  make environment      Setup Python/Julia/Stata (~10 min)"
	@echo "  make all              Build all artifacts (~5 min)"
	@echo "  make verify           Quick environment check (~1 min)"
	@echo "  make test             Run test suite"
	@echo "  make publish          Publish to paper/"
	@echo "  make clean            Remove outputs"
	@echo ""
	@echo "HELP:"
	@echo "  make help             Show all available commands"
	@echo "  make info             Show comprehensive project information"
	@echo "  make list-analyses    List all available analyses"
	@echo "  make show-analysis-<name>  Show config for specific analysis"
	@echo ""
	@echo "DOCUMENTATION:"
	@echo "  README.md             Project overview and quick start"
	@echo "  QUICKSTART.md         5-minute getting started guide"
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
	@echo "  make environment      Setup Python 3.11 + Julia + Stata (~10 min)"
	@echo "  make verify           Quick environment check (~1 min)"
	@echo "  make examples         Run example scripts (Python/Julia)"
	@echo "  make sample-python    Run Python example"
	@echo "  make sample-julia     Run Julia example"
	@echo "  make sample-juliacall Run Python/Julia interop example"
	@echo "  make sample-stata     Run Stata example (if installed)"
	@echo ""
	@echo "BUILD:"
	@echo "  make all              Build all artifacts (~5 min)"
	@echo "  make price_base       Build price_base artifact only"
	@echo "  make remodel_base     Build remodel_base artifact only"
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
	@echo "  make check-deps       Check Python/Julia/data dependencies"
	@echo "  make dryrun           Show what would be built (without building)"
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
	@echo "  examples/                Sample scripts (Python/Julia/Stata)"
	@echo ""
	@echo "PIPELINE FLOW:"
	@echo "  1. make environment      → Install Python 3.11, Julia, Stata packages"
	@echo "     Runtime: ~10 min      → Creates .env/ (~2GB), .julia/ (~500MB)"
	@echo ""
	@echo "  2. make verify           → Quick smoke test"
	@echo "     Runtime: ~1 min       → Checks environment, packages, data"
	@echo ""
	@echo "  3. make all              → Build all artifacts"
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

.PHONY: list-analyses list-analyses-verbose show-analysis check-deps dryrun

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

# Check that all dependencies are available
check-deps:
	@echo "Checking dependencies..."
	@echo -n "  Python: "
	@$(PYTHON) --version 2>&1 || echo "❌ ERROR: Python not available (run: make environment)"
	@echo -n "  Julia:  "
	@$(JULIA) --version 2>&1 | xargs echo || echo "❌ ERROR: Julia not available (run: make environment)"
	@echo -n "  Data files: "
	@if [ -f $(DATA) ]; then \
		echo "✓ $(DATA)"; \
	else \
		echo "❌ ERROR: Data file not found: $(DATA)"; \
	fi
	@echo ""
	@echo "Julia thread count: $(JULIA_NUM_THREADS)"
	@echo ""

# Show what would be built without actually building
dryrun:
	@echo "Dry run - showing what would be built:"
	@echo ""
	@$(MAKE) -n all 2>&1 | grep -E '^(Building|Running|======|✓)' || true