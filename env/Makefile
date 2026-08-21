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
        stata-env stata-clean stata-check stata-vendored-clean \
        all-env environment

# Ensure uv is installed (installs to ~/.local/bin if missing)
ensure-uv:
	@command -v uv >/dev/null 2>&1 || bash $(ENV_DIR)/scripts/install_uv.sh

# Install Julia via Python (triggers juliacall auto-install).
#
# env/juliapkg.json is copied into the juliapkg project before the install runs.
# It pins PythonCall.
#
# It deliberately does NOT pin the Julia binary version, and that is worth
# explaining because pinning it is the obvious thing to want. juliacall declares
# OpenSSL_jll as "<=python", tying it to the OpenSSL of the host Python -- and
# the resulting OpenSSL_jll carries its own Julia compat bound. On one machine
# that admits Julia 1.12; on a GitHub runner it resolves to a build supporting
# only "1.0.0 - 1.11". A pin of "=1.12.4" therefore produced:
#
#   ✗ Error: 'julia' compat entries have empty intersection:
#     - '=1.12.4'      at env/juliapkg.json
#     - '1.0.0 - 1.11' at …/juliacall/juliapkg.json (OpenSSL_jll)
#     - '^1.10.3'      at …/juliacall/juliapkg.json
#
# So the achievable Julia range is a property of the machine's Python, not of
# this repo, and an exact binary pin is not portable by construction. What Julia
# a build actually used is still recorded -- env/Manifest.toml carries
# julia_version -- which is provenance rather than constraint, and is the honest
# thing to offer here. A project that knows its platforms can add a "julia" key
# back; a template cannot.
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
# A Manifest pins packages *for the Julia version it was resolved with*. On a
# different Julia, Pkg emits
#
#   ┌ Warning: The active manifest file has dependencies that were resolved with
#   │ a different julia version (1.12.4). Unexpected behavior may occur.
#   ┌ Warning: The project dependencies or compat requirements have changed
#   │ since the manifest was last resolved.
#
# and then RE-RESOLVES and carries on. The build goes green while reproducing
# versions other than the pinned ones, and the only evidence is two warnings
# several hundred lines into a log nobody reads. So say it plainly at the end,
# where it is visible: a green build that is not reproducing the pin should not
# look identical to one that is.
.PHONY: julia-instantiate
julia-instantiate:
	@echo ">> Instantiating env/ from Manifest.toml"
	# Refuse to instantiate without a manifest. Ported from fire 2026-08-18.
	#
	# Pkg.instantiate() with no Manifest.toml does not fail -- it RESOLVES from
	# Project.toml and writes a new manifest. Since Project.toml admits a range
	# (any FixedEffectModels 1.x, say), that silently produces whatever versions
	# are current today and calls the build a success. A missing pin is a
	# different problem from an unsatisfiable one and deserves its own message,
	# rather than being converted into a fresh resolution nobody asked for.
	@if [ ! -f "$(JULIA_PROJECT)/Manifest.toml" ]; then \
		echo "ERROR: env/Manifest.toml missing -- Julia versions would float."; \
		echo "       Restore it from git, or regenerate it deliberately with"; \
		echo "       'make -C env julia-relock' and re-run the acceptance test."; \
		exit 1; \
	fi
	cd $(REPO_ROOT) && env/scripts/runjulia -e 'using Pkg; Pkg.instantiate()'
	# Ask git, not the file's own contents.
	#
	# Comparing the manifest's julia_version against the running Julia does not
	# work, because Pkg REWRITES Manifest.toml when it cannot honor it: on a
	# runner with Julia 1.11.9 the committed 1.12.4 manifest was silently
	# replaced by a 1.11.9 one, so by the time anything looked, the two agreed
	# and the check reported a match. The evidence had been overwritten by the
	# thing being checked.
	#
	# git still knows what was committed. A dirty Manifest.toml after a build IS
	# the symptom -- the pin was not honored, it was replaced -- and it detects
	# the case regardless of which Julia is involved.
	cd $(REPO_ROOT) && if git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
	   && git ls-files --error-unmatch env/Manifest.toml >/dev/null 2>&1; then
	  if git diff --quiet -- env/Manifest.toml; then
	    echo ">> Manifest.toml unchanged: the committed package versions were installed."
	  else
	    echo ""
	    echo "  ================================================================"
	    echo "  NOT REPRODUCING THE PINNED VERSIONS"
	    echo "  The build REWROTE env/Manifest.toml, so the installed package"
	    echo "  versions are not the committed ones. Pkg does this instead of"
	    echo "  failing when it cannot satisfy the manifest -- usually because"
	    echo "  this machine runs a different Julia than the manifest was"
	    echo "  resolved with."
	    echo ""
	    echo "  git diff --stat env/Manifest.toml   # what moved"
	    echo "  git checkout env/Manifest.toml      # discard, keep the pin"
	    echo "  ================================================================"
	    echo ""
	  fi
	else
	  echo ">> (not a git work tree, or Manifest.toml untracked -- pin NOT verified)"
	fi

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
# --frozen is load-bearing: install what uv.lock says, and never rewrite it.
#
# Plain `uv sync` re-resolves whenever it judges the lockfile out of date and
# writes the result back. On a GitHub runner that happened on every build, so
# `make environment` left uv.lock modified -- caught 2026-08-18 by the publish
# gate refusing a dirty tree, having gone unnoticed here because the same
# re-resolution on one developer machine tends to be a no-op.
#
# A build that can silently change its own pins is the defect this project's
# whole toolchain policy exists to prevent: it is what conda did, re-solving
# python.yml on every `conda env create`, and it is why the environment behind a
# submitted paper turned out not to be reconstructible.
#
# With --frozen, a lockfile that no longer matches pyproject.toml is an ERROR
# rather than a silent update. That is the point. Re-pinning is a deliberate
# act: `make -C env python-relock`, then re-run the acceptance test.
python-env: ensure-uv
	@echo ">> Syncing Python environment with uv -> $(VENV)"
	@cd $(REPO_ROOT) && uv sync --frozen

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
# The rules live in repro-tools so there is one copy rather than one per
# project. They were hoisted on 2026-08-18 because the two copies had stayed
# almost identical -- stata-requirements shared 23 of 25 recipe lines with
# fire's, stata-check 17 of 25, and the package stamp rule was byte-identical --
# while the Python and Julia sections around them had diverged too far to share.
#
# Override STATA_DIR or STATA before this line to change where packages install
# or which binary does it.
REPRO_TOOLS_LIB := $(abspath $(ENV_DIR)/../lib/repro-tools/src/repro_tools/lib)
ifeq ($(wildcard $(REPRO_TOOLS_LIB)/stata.mk),)
  $(error Missing $(REPRO_TOOLS_LIB)/stata.mk -- run: git submodule update --init --recursive)
endif
include $(REPRO_TOOLS_LIB)/stata.mk
# ---------- end Stata ----------

# ==============================================================================
# Re-pinning and inspection
# ==============================================================================
#
# Until 2026-08-17 this template had NO supported way to re-pin its environment:
# `uv lock --upgrade`, `Pkg.update()` and the word "relock" appeared nowhere in
# any Makefile. A project generated from it could install a pinned environment
# and then had no sanctioned route to update one -- awkward for a scaffold whose
# whole argument is that pins are load-bearing, and an invitation to run
# something ad hoc that leaves the lockfile and the installed environment
# disagreeing.
#
# Re-pinning is deliberate and never automatic. Nothing here runs as part of
# `make environment` or `make all`; each target rewrites a pin and then tells
# you to re-run the acceptance test, because that is the only thing that can say
# whether the new pin still produces the same numbers.

.PHONY: python-relock
python-relock:
	@cd "$(REPO_ROOT)" && uv lock --upgrade
	@echo ""
	@echo ">> uv.lock rewritten."
	@echo "   Install it:      make python-env"
	@echo "   Then verify:     make check-baseline"
	@echo "   A rewritten lockfile that has not been checked against the"
	@echo "   published numbers is an untested change to every result."

# Rewrites env/Manifest.toml, which is the pin that matters most for results:
# env/Project.toml alone admits any FixedEffectModels 1.x, and Julia computes
# the estimates. Uses the repo-local bundled Julia, never a global juliaup one.
.PHONY: julia-relock
julia-relock:
	@JULIA_DEPOT_PATH="$(JULIA_DEPOT_PATH)" JULIA_CONDAPKG_BACKEND=Null \
	  "$(JULIA_DEPOT_PATH)/pyjuliapkg/install/bin/julia" --project="$(JULIA_PROJECT)" \
	  -e 'using Pkg; Pkg.update()'
	@echo ""
	@echo ">> env/Manifest.toml rewritten."
	@echo "   Verify with:     make verify && make check-baseline"
	@echo "   Then review 'git diff env/Manifest.toml' before committing --"
	@echo "   a major bump under a permissive [compat] range is easy to miss."

# Report which Julia the bridge actually resolves, through juliacall rather than
# by inspecting paths. Cheap to run and the fastest way to catch a depot or
# bridge variable pointing somewhere unintended.
.PHONY: julia-check
julia-check:
	@echo ">> Checking Julia via juliacall..."
	@echo "JULIA_PROJECT=$(JULIA_PROJECT)"
	@echo "JULIA_DEPOT_PATH=$(JULIA_DEPOT_PATH)"
	@echo "PYTHON_JULIAPKG_PROJECT=$(PYTHON_JULIAPKG_PROJECT)"
	@$(abspath $(ENV_DIR))/scripts/runpython -c \
	  "import juliacall; print('Julia via juliacall:', juliacall.Main.VERSION)"

# Where the Python pins live and whether they exist. Prints paths rather than
# guessing at them, which matters because $(REPO_ROOT) is derived and a wrong
# value shows up much later as a mysterious import error.
.PHONY: python-paths
python-paths:
	@printf 'ENV_DIR     = %s\n' "$(ENV_DIR)"
	@printf 'REPO_ROOT   = %s\n' "$(REPO_ROOT)"
	@printf 'PYPROJECT   = %s\n' "$(REPO_ROOT)/pyproject.toml"
	@printf 'UV_LOCK     = %s\n' "$(REPO_ROOT)/uv.lock"
	@printf 'VENV        = %s\n' "$(REPO_ROOT)/.venv"
	@printf 'lock exists? '; [ -f "$(REPO_ROOT)/uv.lock" ] && echo yes || echo no
	@printf 'venv exists? '; [ -d "$(REPO_ROOT)/.venv" ] && echo yes || echo no


# ==============================================================================
# The replicator's path: hash-pinned requirements, installable by plain pip
# ==============================================================================
#
# Required by the replication constitution, which is explicit about it:
#
#   "uv is how the authors *author* the environment. It must never be what a
#    journal data editor is required to install."
#
# and requires uv.lock to be exported to hash-pinned requirements.txt files that
# plain pip can install, with that path tested with uv absent from PATH.
#
# This template shipped neither target until 2026-08-18, so every project
# generated from it violated that clause on arrival -- the only documented way
# to build the environment needed uv. fire had both; they are ported here.
#
# The exported file is a derived artifact of uv.lock and must be regenerated
# whenever the lock moves. python-env-pip refuses to run against an export older
# than uv.lock rather than installing a stale set quietly.

.PHONY: python-export
python-export:
	@command -v uv >/dev/null 2>&1 || { \
		echo "ERROR: uv is needed to EXPORT (not to install). See"; \
		echo "       https://docs.astral.sh/uv/"; \
		exit 1; \
	}
	@mkdir -p "$(ENV_DIR)/requirements"
	@# --no-emit-project: this project itself is not a dependency.
	@# --no-emit-package repro-tools: a local editable path, meaningless to pip
	@# on another machine; a replicator gets it as a git submodule.
	@cd "$(REPO_ROOT)" && uv export --no-emit-project --no-emit-package repro-tools \
		--format requirements-txt -o env/requirements/base.txt
	@echo ">> Wrote env/requirements/base.txt from uv.lock"
	@echo "   Commit it: it is the only environment a data editor can install"
	@echo "   without uv, and it is stale the moment uv.lock moves."

.PHONY: python-env-pip
python-env-pip:
	@REQ="$(ENV_DIR)/requirements/base.txt"; \
	if [ ! -f "$$REQ" ]; then \
		echo "ERROR: $$REQ missing. Run 'make -C env python-export' (needs uv)."; \
		exit 1; \
	fi; \
	if command -v uv >/dev/null 2>&1 && [ "$(REPO_ROOT)/uv.lock" -nt "$$REQ" ]; then \
		echo "ERROR: $$REQ is older than uv.lock -- regenerate it with"; \
		echo "       'make -C env python-export'. Installing a stale export"; \
		echo "       would build an environment nobody has pinned."; \
		exit 1; \
	fi; \
	PY="$${PYTHON_312:-python3.12}"; \
	command -v "$$PY" >/dev/null 2>&1 || { \
		echo "ERROR: python3.12 not found. These requirements are pinned for"; \
		echo "       Python 3.12 (see requires-python in pyproject.toml);"; \
		echo "       another version resolves different wheels and fails the"; \
		echo "       hash check confusingly. Set PYTHON_312=/path/to/python3.12"; \
		exit 1; \
	}; \
	VER=$$("$$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null); \
	if [ "$$VER" != "3.12" ]; then \
		echo "ERROR: $$PY reports version '$$VER', need 3.12"; exit 1; \
	fi; \
	if [ -e "$(VENV)" ] && [ -z "$${FORCE:-}" ]; then \
		echo "ERROR: $(VENV) already exists. Refusing to overwrite -- if it was"; \
		echo "       built by uv, mixing a pip install into it produces an"; \
		echo "       environment matching neither. Remove it, or set FORCE=1."; \
		exit 1; \
	fi; \
	echo ">> Building $(VENV) with $$PY and pip alone (no uv)"; \
	"$$PY" -m venv "$(VENV)"; \
	if ! "$(VENV)/bin/python" -c 'import sys' >/dev/null 2>&1; then \
		echo "ERROR: the venv just created by '$$PY' cannot start."; \
		echo "       This happens when \$$PY is a symlink shim -- a uv-managed"; \
		echo "       interpreter linked into ~/.local/bin, say: the venv records"; \
		echo "       that directory as its home and then cannot find the stdlib."; \
		echo "       Point PYTHON_312 at the REAL interpreter:"; \
		echo "       PYTHON_312=\$$(readlink -f \"$$PY\") make -C env python-env-pip"; \
		"$(VENV)/bin/python" -c 'import sys' 2>&1 | head -5; \
		exit 1; \
	fi; \
	"$(VENV)/bin/python" -m pip install --upgrade pip >/dev/null; \
	"$(VENV)/bin/python" -m pip install --require-hashes -r "$$REQ"; \
	echo ">> Installed from $$REQ with hashes verified"; \
	echo ">> Installing the local repro-tools submodule"; \
	"$(VENV)/bin/python" -m pip install --no-deps "$(REPO_ROOT)/lib/repro-tools"; \
	echo ">> Replicator environment ready (uv was not used)"

# --no-deps, and not optional.
#
# The export deliberately omits repro-tools: it is a local editable path, which
# means nothing to pip on someone else's machine. But the analysis IMPORTS it,
# so a venv built from requirements alone installs every dependency and then
# cannot run anything -- `import repro_tools` raises ModuleNotFoundError.
# Measured 2026-08-18 in a clean venv: 149 packages installed, hashes verified,
# and run_analysis.py could not start.
#
# That gap is easy to miss because the constitution's test -- "the replicator's
# path must be tested with uv absent from PATH" -- was read as a test of
# INSTALLATION. Installing is not the claim being made; running is.
#
# --no-deps because the dependency set is already pinned by hash above, and
# letting pip resolve repro-tools' own requirements would silently pull
# unpinned versions into an environment whose whole point is that it is pinned.
