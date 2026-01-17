# Top-level Makefile
# - `make all` builds all figures+tables into output/
# - `make price_base` builds only price_base (figure+table+provenance)
# - `make publish` publishes built artifacts into paper/ and writes paper/provenance.yml

SHELL := /bin/bash

# Environment script paths
PYTHON := env/scripts/runpython
JULIA  := env/scripts/runjulia
STATA  := env/scripts/runstata

ARTIFACTS := price_base remodel_base
DATA := data/housing_panel.csv

OUT_FIG_DIR := output/figures
OUT_TBL_DIR := output/tables
OUT_PROV_DIR := output/provenance
OUT_LOG_DIR := output/logs

PAPER_DIR := paper
PAPER_FIG_DIR := $(PAPER_DIR)/figures
PAPER_TBL_DIR := $(PAPER_DIR)/tables

# Default target
.DEFAULT_GOAL := help

# All targets
.PHONY: all
all: $(ARTIFACTS)

# Environment setup
.PHONY: environment
environment:
	@echo "Setting up software environment..."
	$(MAKE) -C env all-env
	@echo "✓ Environment ready (Python + Julia + Stata packages)"

# Example targets
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

# Build subsets: allow `make price_base`, etc.
.PHONY: $(ARTIFACTS)
$(ARTIFACTS): %: $(OUT_FIG_DIR)/%.pdf $(OUT_TBL_DIR)/%.tex $(OUT_PROV_DIR)/%.yml

# Grouped targets: one run produces figure + table + provenance.
# Requires GNU Make >= 4.3.
$(OUT_FIG_DIR)/%.pdf $(OUT_TBL_DIR)/%.tex $(OUT_PROV_DIR)/%.yml &: \
  analysis/build_%.py $(DATA) scripts/provenance.py $(PYTHON)
	@mkdir -p $(OUT_FIG_DIR) $(OUT_TBL_DIR) $(OUT_PROV_DIR) $(OUT_LOG_DIR)
	@$(PYTHON) analysis/build_$*.py \
	  --data $(DATA) \
	  --out-fig $(OUT_FIG_DIR)/$*.pdf \
	  --out-table $(OUT_TBL_DIR)/$*.tex \
	  --out-meta $(OUT_PROV_DIR)/$*.yml \
	  2>&1 | tee $(OUT_LOG_DIR)/$*.log

# Publishing
PUBLISH_ARTIFACTS ?= $(ARTIFACTS)

.PHONY: publish
publish: publish-figures publish-tables

.PHONY: publish-figures
publish-figures: $(addprefix $(OUT_FIG_DIR)/,$(addsuffix .pdf,$(PUBLISH_ARTIFACTS))) \
                 $(addprefix $(OUT_PROV_DIR)/,$(addsuffix .yml,$(PUBLISH_ARTIFACTS)))
	@mkdir -p $(PAPER_FIG_DIR)
	@$(PYTHON) scripts/publish_artifacts.py \
	  --paper-root $(PAPER_DIR) \
	  --kind figures \
	  --names "$(PUBLISH_ARTIFACTS)" \
	  --allow-dirty 0 \
	  --require-not-behind 1

.PHONY: publish-tables
publish-tables: $(addprefix $(OUT_TBL_DIR)/,$(addsuffix .tex,$(PUBLISH_ARTIFACTS))) \
                $(addprefix $(OUT_PROV_DIR)/,$(addsuffix .yml,$(PUBLISH_ARTIFACTS)))
	@mkdir -p $(PAPER_TBL_DIR)
	@$(PYTHON) scripts/publish_artifacts.py \
	  --paper-root $(PAPER_DIR) \
	  --kind tables \
	  --names "$(PUBLISH_ARTIFACTS)" \
	  --allow-dirty 0 \
	  --require-not-behind 1

.PHONY: clean
clean:
	rm -rf output/figures output/tables output/provenance output/logs

.PHONY: info
info:
	@echo ""
	@echo "================================================================"
	@echo "  Reproducible Research Template"
	@echo "================================================================"
	@echo ""
	@echo "QUICK START"
	@echo "  1. First time setup:"
	@echo "       make environment"
	@echo ""
	@echo "  2. Test with examples:"
	@echo "       make examples"
	@echo ""
	@echo "  3. Build all analyses:"
	@echo "       make all"
	@echo ""
	@echo "  4. Publish to paper/:"
	@echo "       make publish"
	@echo ""
	@echo "See 'make help' for complete command reference."
	@echo ""

.PHONY: help
help:
	@echo ""
	@echo "================================================================"
	@echo "  Research Template Makefile"
	@echo "================================================================"
	@echo ""
	@echo "QUICK START:"
	@echo "  make environment      # One-time setup"
	@echo "  make examples         # Test with example scripts"
	@echo "  make all              # Build all artifacts"
	@echo "  make publish          # Publish to paper/"
	@echo ""
	@echo "BUILD TARGETS:"
	@echo "  make all              # Build all artifacts"
	@echo "  make price_base       # Build price_base artifact"
	@echo "  make remodel_base     # Build remodel_base artifact"
	@echo ""
	@echo "PUBLISH:"
	@echo "  make publish          # Publish all artifacts to paper/"
	@echo ""
	@echo "EXAMPLES:"
	@echo "  make examples         # Run all example scripts"
	@echo "  make sample-python    # Run Python example"
	@echo "  make sample-julia     # Run Julia example"
	@echo "  make sample-juliacall # Run Python/Julia interop example"
	@echo "  make sample-stata     # Run Stata example"
	@echo ""
	@echo "UTILITIES:"
	@echo "  make clean            # Remove all outputs"
	@echo "  make info             # Show quick start guide"
	@echo ""
