# env/Makefile - Environment setup for Python and Julia
.ONESHELL:
SHELL := /bin/bash

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

# Optional Julia GPU support. Set JULIA_ENABLE_CUDA=1 to install CUDA.jl into a
# gitignored, machine-local env (.julia/gpu-env); default 0 = CPU only. run_did.py
# auto-detects that env and uses the GPU at runtime when it is present.
JULIA_ENABLE_CUDA ?= 0
export JULIA_ENABLE_CUDA

# Paths
ENV_DIR := $(strip $(CURDIR))
REPO_ROOT := $(abspath $(ENV_DIR)/..)
# Python environment is a uv-managed virtualenv (.venv) at the repo root,
# built from pyproject.toml + uv.lock.
VENV := $(abspath $(ENV_DIR)/../.venv)

# Julia configuration
export JULIA_PROJECT := $(strip $(ENV_DIR))
export JULIAPKG_PROJECT := $(JULIA_PROJECT)
# keep depot local to the repo (../.julia at repo root)
export JULIA_DEPOT_PATH := $(abspath $(ENV_DIR)/../.julia)
export PYTHON_JULIACALL_HANDLE_SIGNALS := yes
# Force juliacall/juliapkg to use the repo-local depot for its own project
export PYTHON_JULIAPKG_PROJECT := $(JULIA_DEPOT_PATH)

.PHONY: python-env python-check python-clean \
        julia-env julia-install-via-python ensure-uv \
        stata-env stata-clean stata-check \
        all-env environment

# Ensure uv is installed (installs to ~/.local/bin if missing)
ensure-uv:
	@command -v uv >/dev/null 2>&1 || bash $(ENV_DIR)/scripts/install_uv.sh

# Install Julia via Python (triggers juliacall auto-install).
#
# env/juliapkg.json pins the Julia *binary* version and is copied into the
# juliapkg project before the install runs. Without it, juliapkg takes whatever
# Julia satisfies PythonCall's loose compat bound -- so two clones of the same
# commit, built a month apart, can end up on different Julia versions with
# nothing recording that they differ.
julia-install-via-python:
	@echo ">> Pinning Julia binary version from env/juliapkg.json"
	@mkdir -p "$(JULIA_DEPOT_PATH)"
	@cp "$(CURDIR)/juliapkg.json" "$(JULIA_DEPOT_PATH)/juliapkg.json"
	@echo ">> Installing Julia via juliacall..."
	@cd $(REPO_ROOT) && JULIA_ENABLE_CUDA=$(JULIA_ENABLE_CUDA) env/scripts/runpython env/scripts/install_julia.py

# Instantiate env/Project.toml against the committed env/Manifest.toml.
#
# The Manifest is the pin that matters. Project.toml alone admits any
# FixedEffectModels 1.x, and "any 1.x" is not hypothetical drift: between two
# runs of a real project seven months apart, the Julia stack moved 61 packages
# under exactly such bounds -- including FixedEffects 2.4.1 -> 3.3.0 and CUDA
# 5.9.6 -> 6.2.1, both major bumps, in the stack that computes the results.
#
# Kept separate from julia-install-via-python because that step populates the
# *juliapkg* project (PythonCall), a different environment from this one.
.PHONY: julia-instantiate
julia-instantiate:
	@echo ">> Instantiating env/ from Manifest.toml"
	@cd $(REPO_ROOT) && env/scripts/runjulia -e 'using Pkg; Pkg.instantiate()'

all-env: python-env julia-install-via-python julia-instantiate stata-env

# Main entry point
environment: all-env
	@echo ""
	@echo "=========================================================================="
	@echo "Environment setup complete!"
	@echo "=========================================================================="
	@echo ""
	@echo "Python environment: $(VENV)"
	@echo "Julia binary:       env/pyjuliapkg/install/"
	@echo "Julia packages:     .julia/packages/"
	@echo "Stata packages:     .stata/"
	@echo ""
	@echo "Everything is ready! To test:"
	@echo "  make examples"
	@echo "  make price_base"
	@echo ""
	@echo "=========================================================================="

# ---------- Python / uv ----------
python-env: ensure-uv
	@echo ">> Syncing Python environment with uv -> $(VENV)"
	@cd $(REPO_ROOT) && uv sync

python-check:
	@echo ">> checking Python can import juliacall from $(VENV)"
	@cd $(REPO_ROOT) && $(REPO_ROOT)/env/scripts/runpython -c 'import sys; print("PY:", sys.executable); import juliacall; print("OK: juliacall", getattr(juliacall, "__version__", ""))'

python-clean:
	@echo ">> removing $(VENV)"
	rm -rf "$(VENV)"

# ---------- Julia ----------
julia-env: julia-install-via-python
	@echo ">> Julia environment ready (installed via juliacall)"

# Clean juliacall/PythonCall auto-install cache.
#
# This recipe was truncated mid-line ("find ../.env/li") from the initial commit
# on 2026-01-16 until 2026-08-15, and its severed tail had been spliced onto the
# end of stata-check, taking that target out too. Both were broken in every
# project ever generated from this template. The paths also still said .env,
# which was the conda prefix; uv builds .venv.
.PHONY: juliacall-clean
juliacall-clean:
	@echo ">> Cleaning juliacall auto-install cache..."
	@if [ -d "pyjuliapkg" ]; then \
		echo "   Removing pyjuliapkg/"; \
		rm -rf pyjuliapkg; \
	fi
	@site=$$(echo ../.venv/lib/python*/site-packages/juliacall); \
	if [ -d "$$site" ]; then \
		echo "   Clearing juliacall package cache..."; \
		find "$$site" -name "*.pyc" -delete 2>/dev/null || true; \
		find "$$site" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \
	fi
	@echo "   Done."

# ---------- Stata ----------
#
# SSC has no versioned install: `ssc install pkg 3.1.2` is not "install version
# 3.1.2", it is a syntax error (varlist not allowed, r(101)), and SSC serves only
# whatever is current today. So a version number in stata-packages.txt could
# never have been enforced by anything -- and the rule that read it printed
# "with version 3.1.2" while issuing an unversioned install, or nothing at all.
#
# The only real pinning is to commit the ado files. That is what .stata/ado/plus
# is for, and it follows AEA Data Editor guidance: "provide copies of such
# packages/modules when the package repository does not allow you to specify a
# version." stata-env therefore installs NOTHING when the files are vendored;
# `make stata-update` refreshes from SSC deliberately.
#
# Versions live in stata-requirements.txt, generated from what is actually
# installed and checked by `make stata-check` -- machine-checkable, unlike a
# number typed into a list by hand.
STATA_LOCAL := ../.stata/ado/plus

# First word of each non-comment, non-blank line. The comment/blank filter is
# load-bearing: a bare `{print $$1}` turns a "#" comment line into a package
# named "#", and then a stamp target for it.
STATA_PACKAGES := $(shell awk '!/^[[:space:]]*#/ && NF {print $$1}' stata-packages.txt 2>/dev/null)
STATA_STAMPS := $(addprefix ../.stata/., $(addsuffix .stamp, $(STATA_PACKAGES)))

.PHONY: stata-env
stata-env: $(STATA_STAMPS)
	@echo "All Stata packages present in $(STATA_LOCAL)"
	@echo "Use env/scripts/runstata to run your .do files"

# Install one package.
#
# Fails loudly, which the version this replaces did not: it wrapped the install
# in `cap noi`, sent output to /dev/null, appended `|| true`, and touched the
# stamp -- and under .ONESHELL that touch is the SAME shell, so the recipe's exit
# status was touch's. "All Stata packages installed" printed on a machine with no
# Stata at all.
../.stata/.%.stamp: stata-packages.txt | $(STATA_LOCAL)
	@mkdir -p ../.stata
	ado=$$(find "$(CURDIR)/../.stata/ado/plus" -name '$*.ado' 2>/dev/null | head -1)
	if [ -n "$$ado" ] && [ -z "$$STATA_UPDATE" ]; then
	  echo "  vendored: $* $$(grep -m1 '^\*!' "$$ado" | sed 's/^\*! *//')"
	  touch $@
	  exit 0
	fi
	echo "Installing Stata package from SSC: $*"
	if ! command -v stata-mp >/dev/null 2>&1; then
	  echo "ERROR: stata-mp not found on PATH; cannot install $*." >&2
	  exit 1
	fi
	d=$$(mktemp -d)
	echo 'sysdir set PLUS "$(CURDIR)/../.stata/ado/plus"' > $$d/install.do
	echo 'ssc install $*, replace all' >> $$d/install.do
	echo 'exit, clear STATA' >> $$d/install.do
	(cd $$d && stata-mp -b do install.do >/dev/null 2>&1) || true
	# Judge by the LOG, not the exit status. Stata returns 0 even when a
	# do-file aborts, so trusting $$? here produces a check that always passes.
	if [ ! -f $$d/install.log ] || grep -qE '^r\([0-9]+\);' $$d/install.log; then
	  echo "ERROR: stata-mp failed while installing $*. Log:" >&2
	  sed -n '1,40p' $$d/install.log >&2 2>/dev/null || echo "  (no log produced)" >&2
	  rm -rf $$d
	  exit 1
	fi
	rm -rf $$d
	ado=$$(find "$(CURDIR)/../.stata/ado/plus" -name '$*.ado' 2>/dev/null | head -1)
	if [ -z "$$ado" ]; then
	  echo "ERROR: $* installed without error, but $*.ado is not in $(STATA_LOCAL)." >&2
	  exit 1
	fi
	echo "  installed: $$(grep -m1 '^\*!' "$$ado" | sed 's/^\*! *//')"
	touch $@

$(STATA_LOCAL):
	@mkdir -p $(STATA_LOCAL)

# Record the versions actually installed, in the format `require` reads. Written
# by require's own `list save` mode rather than hand-rolled, so it stays
# canonical and machine-checkable.
.PHONY: stata-requirements
stata-requirements:
	@if ! command -v stata-mp >/dev/null 2>&1; then
	  echo "ERROR: stata-mp not found; cannot generate requirements." >&2
	  exit 1
	fi
	d=$$(mktemp -d)
	echo 'sysdir set PLUS "$(CURDIR)/../.stata/ado/plus"' > $$d/gen.do
	echo "require using \"$$d/req.txt\", list save replace exact" >> $$d/gen.do
	echo 'exit, clear STATA' >> $$d/gen.do
	if ! (cd $$d && stata-mp -b do gen.do >/dev/null 2>&1) || [ ! -f $$d/req.txt ]; then
	  echo "ERROR: could not generate requirements. First 40 log lines:" >&2
	  sed -n '1,40p' $$d/gen.log >&2 2>/dev/null || true
	  rm -rf $$d; exit 1
	fi
	{
	  echo "# Stata package versions vendored in .stata/ado/plus, which is committed."
	  echo "# Generated by 'make stata-requirements' using require's own list mode."
	  echo "#"
	  echo "# Check the installed tree against this file:  make stata-check"
	  echo "#"
	  echo "# SSC serves only the current release, so these cannot be re-obtained by"
	  echo "# version; that is why the ado files themselves are committed."
	  awk '!/^[*#]/ && NF {print $$1, $$2, $$3}' $$d/req.txt | sort -u
	} > stata-requirements.txt
	rm -rf $$d
	echo ">> Wrote env/stata-requirements.txt"

# Assert the installed tree still matches stata-requirements.txt. This is the
# check the old "with version 3.1.2" console line only pretended to be.
.PHONY: stata-check
stata-check:
	@if [ ! -f stata-requirements.txt ]; then
	  echo "No env/stata-requirements.txt yet. Installed packages:"
	  find ../.stata/ado/plus -name "*.ado" -exec basename {} \; 2>/dev/null \
	    | sort -u | sed 's/^/     /' || echo "     (none)"
	  echo "Generate the pin record with: make stata-requirements"
	  exit 0
	fi
	if ! command -v stata-mp >/dev/null 2>&1; then
	  echo "ERROR: stata-mp not found; cannot check Stata packages." >&2
	  exit 1
	fi
	d=$$(mktemp -d)
	echo 'sysdir set PLUS "$(CURDIR)/../.stata/ado/plus"' > $$d/check.do
	echo "require using \"$(CURDIR)/stata-requirements.txt\"" >> $$d/check.do
	echo 'exit, clear STATA' >> $$d/check.do
	(cd $$d && stata-mp -b do check.do >/dev/null 2>&1) || true
	if [ ! -f $$d/check.log ]; then
	  echo "ERROR: stata-mp produced no log; it may not have run." >&2
	  rm -rf $$d; exit 1
	fi
	if grep -qE '^r\([0-9]+\);' $$d/check.log; then
	  echo "ERROR: installed Stata packages do NOT match env/stata-requirements.txt" >&2
	  grep -E 'require error|^r\([0-9]+\);' $$d/check.log >&2 || true
	  rm -rf $$d; exit 1
	fi
	echo ">> Stata packages match env/stata-requirements.txt:"
	sed -n '/^[^#]/p' stata-requirements.txt | sed 's/^/     /'
	rm -rf $$d

# Deliberately refresh from SSC, overwriting the committed ado files. Never
# automatic: it replaces reviewed versions with whatever SSC serves today.
.PHONY: stata-update
stata-update:
	@rm -f $(STATA_STAMPS)
	STATA_UPDATE=1 $(MAKE) --no-print-directory stata-env
	$(MAKE) --no-print-directory stata-requirements
	@echo ">> Refreshed from SSC. Review 'git diff' on .stata/ado/plus and"
	@echo "   env/stata-requirements.txt, then commit deliberately."

.PHONY: stata-clean
stata-clean:
	rm -rf ../.stata

# ---------- end Stata ----------
