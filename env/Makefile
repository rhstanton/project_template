# env/Makefile - Environment setup for Python and Julia
.ONESHELL:
SHELL := /bin/bash

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

# Optional Julia GPU support: set JULIA_ENABLE_CUDA=1 to install CUDA.jl
JULIA_ENABLE_CUDA ?= 0
export JULIA_ENABLE_CUDA

# Paths
CONDA  ?= conda
MICROMAMBA ?= micromamba

ENV_DIR := $(strip $(CURDIR))
PY_YML  := $(strip $(ENV_DIR))/python.yml
PY_PREFIX := $(abspath $(ENV_DIR)/../.env)

# Detect which conda-like tool we're using
CONDA_TOOL := $(shell basename "$(CONDA)")

# Force conda to use the fast solver by default
export CONDA_SOLVER := libmamba

# Julia configuration
export JULIA_PROJECT := $(strip $(ENV_DIR))
export JULIAPKG_PROJECT := $(JULIA_PROJECT)
# keep depot local to the repo (../.julia at repo root)
export JULIA_DEPOT_PATH := $(abspath $(ENV_DIR)/../.julia)
export PYTHON_JULIACALL_HANDLE_SIGNALS := yes
# Force juliacall/juliapkg to use the repo-local depot for its own project
export PYTHON_JULIAPKG_PROJECT := $(JULIA_DEPOT_PATH)

.PHONY: python-env python-check python-clean \
        julia-env julia-install-via-python conda-check \
        stata-env stata-clean stata-check \
        all-env environment

# Check/install conda (micromamba if needed)
conda-check:
	@echo "=========================================================================="
	@echo "Checking for conda/mamba/micromamba..."
	@echo "=========================================================================="
	@bash $(ENV_DIR)/scripts/install_micromamba.sh

# Install Julia via Python (triggers juliacall auto-install)
julia-install-via-python:
	@echo ">> Installing Julia via juliacall..."
	@cd $(REPO_ROOT) && JULIA_ENABLE_CUDA=$(JULIA_ENABLE_CUDA) env/scripts/runpython env/scripts/install_julia.py

all-env: conda-check python-env julia-install-via-python stata-env

# Main entry point
environment: all-env
	@echo ""
	@echo "=========================================================================="
	@echo "Environment setup complete!"
	@echo "=========================================================================="
	@echo ""
	@echo "Python environment: $(PY_PREFIX)"
	@echo "Julia binary:       env/pyjuliapkg/install/"
	@echo "Julia packages:     .julia/packages/"
	@echo "Stata packages:     .stata/"
	@echo ""
	@echo "Everything is ready! To test:"
	@echo "  make examples"
	@echo "  make price_base"
	@echo ""
	@echo "=========================================================================="

# ---------- Python / Conda ----------
python-env:
	@echo ">> Detecting conda/mamba/micromamba..."
	@CONDA_CMD=$$(command -v micromamba || command -v mamba || command -v conda); \
	if [ -z "$$CONDA_CMD" ]; then \
		echo "ERROR: No conda-like tool found after conda-check!"; \
		exit 1; \
	fi; \
	CONDA_TOOL=$$(basename "$$CONDA_CMD"); \
	echo ">> Using $$CONDA_TOOL at $$CONDA_CMD"; \
	echo ">> Creating environment from $(PY_YML) -> $(PY_PREFIX)"; \
	if [ "$$CONDA_TOOL" = "micromamba" ]; then \
		if [ -d "$(PY_PREFIX)" ]; then \
			$$CONDA_CMD install -p "$(PY_PREFIX)" -f "$(PY_YML)" -y 2>&1 | grep -v "pip.*additional package manager" | grep -v "Be aware that packages" || true; \
		else \
			$$CONDA_CMD env create -p "$(PY_PREFIX)" -f "$(PY_YML)" -y 2>&1 | grep -v "pip.*additional package manager" | grep -v "Be aware that packages" || true; \
		fi; \
	else \
		$$CONDA_CMD env update --prune -p "$(PY_PREFIX)" -f "$(PY_YML)"; \
	fi

python-check:
	@echo ">> checking Python can import juliacall from $(PY_PREFIX)"
	@cd $(REPO_ROOT) && env/scripts/runpython - <<'PY'
import sys
print("PY:", sys.executable)
try:
	import juliacall; print("OK: juliacall", getattr(juliacall, "__version__", ""))
except Exception as e:
	print("FAIL: juliacall import ->", e); raise SystemExit(1)
PY

python-clean:
	@echo ">> removing $(PY_PREFIX)"
	rm -rf "$(PY_PREFIX)"

# ---------- Julia ----------
julia-env: julia-install-via-python
	@echo ">> Julia environment ready (installed via juliacall)"

# Clean juliacall/PythonCall auto-install cache
juliacall-clean:
	@echo ">> Cleaning juliacall auto-install cache..."
	@if [ -d "pyjuliapkg" ]; then \
		echo "   Removing pyjuliapkg/"; \
		rm -rf pyjuliapkg; \
	fi
	@if [ -d "../.env/lib/python3.*/site-packages/juliacall" ]; then \
		echo "   Clearing juliacall package cache..."; \
		find ../.env/lib/python*/site-packages/juliacall -name "*.pyc" -delete 2>/dev/null || true; \
		find ../.env/li

# ---------- Stata ----------
STATA_LOCAL := ../.stata/ado/plus

# Read package list - only take first word of each line
STATA_PACKAGES := $(shell awk '{print $$1}' stata-packages.txt 2>/dev/null)

# Create a stamp file for each package
STATA_STAMPS := $(addprefix ../.stata/., $(addsuffix .stamp, $(STATA_PACKAGES)))

stata-env: $(STATA_STAMPS)
	@echo "All Stata packages installed in $(STATA_LOCAL)"
	@echo "Use env/scripts/runstata to run your .do files"

# Rule to install each package
../.stata/.%.stamp: stata-packages.txt | $(STATA_LOCAL)
	@mkdir -p ../.stata
	@echo "Installing Stata package: $*"
	@VERSION=$$(awk '$$1 == "$*" {print $$2}' stata-packages.txt); \
	echo 'sysdir set PLUS "$(CURDIR)/../.stata/ado/plus"' > /tmp/stata_install_$*.do; \
	if [ -n "$$VERSION" ]; then \
		echo "  with version $$VERSION"; \
		echo "cap noi ssc install $* $$VERSION, replace all" >> /tmp/stata_install_$*.do; \
	else \
		echo "cap noi ssc install $*, replace all" >> /tmp/stata_install_$*.do; \
	fi; \
	echo 'exit, clear STATA' >> /tmp/stata_install_$*.do; \
	(cd /tmp && stata-mp -b do /tmp/stata_install_$*.do > /dev/null 2>&1) || true; \
	rm -f /tmp/stata_install_$*.do /tmp/stata_install_$*.do.log
	@touch $@

# Create the local Stata directory structure
$(STATA_LOCAL):
	@mkdir -p $(STATA_LOCAL)

stata-clean:
	rm -rf ../.stata
	rm -f /tmp/stata_install_*.do /tmp/stata_install_*.do.log

stata-check:
	@echo "Installed Stata packages:"
	@find ../.stata/ado/plus -name "*.ado" -exec basename {} \; 2>/dev/null | sort | uniq || echo "No packages installed"b/python*/site-packages/juliacall -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
	fi
	@echo "   Done."
