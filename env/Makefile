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
	cd $(REPO_ROOT) && env/scripts/runjulia -e 'using Pkg; Pkg.instantiate()'
	# Ask git, not the file's own contents.
	#
	# Comparing the manifest's julia_version against the running Julia does not
	# work, because Pkg REWRITES Manifest.toml when it cannot honour it: on a
	# runner with Julia 1.11.9 the committed 1.12.4 manifest was silently
	# replaced by a 1.11.9 one, so by the time anything looked, the two agreed
	# and the check reported a match. The evidence had been overwritten by the
	# thing being checked.
	#
	# git still knows what was committed. A dirty Manifest.toml after a build IS
	# the symptom -- the pin was not honoured, it was replaced -- and it detects
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

# Assert the vendored ado tree still matches what is committed.
#
# Needs no Stata, and it is the check that catches the failure actually observed
# in a downstream project on 2026-08-17: estout/esttab modified, both .trk
# indexes rewritten, and require.ado DELETED -- SSC versions overwriting the
# pinned ones, which is precisely what committing them exists to prevent. A
# `make stata-update` does exactly this, by design; the defect was that nothing
# afterwards said so.
#
# It runs before the Stata-based check for two reasons. It is instant, and
# `stata-check` verifies versions by invoking Stata's `require` command -- which
# is itself one of the vendored packages. When require.ado is the file that went
# missing, the checker cannot report its own absence. Comparing against git has
# no such circularity.
.PHONY: stata-vendored-clean
stata-vendored-clean:
	@if ! git -C .. rev-parse --git-dir >/dev/null 2>&1; then \
	  echo ">> Not a git checkout; skipping vendored-tree comparison."; \
	  exit 0; \
	fi
	@if ! git -C .. ls-files --error-unmatch .stata/ado/plus >/dev/null 2>&1; then \
	  echo ">> No vendored Stata tree committed; nothing to compare."; \
	  exit 0; \
	fi
	@if ! git -C .. diff --quiet -- .stata/ado/plus 2>/dev/null; then \
	  echo "ERROR: the vendored Stata tree differs from what is committed." >&2; \
	  echo "" >&2; \
	  git -C .. status --short -- .stata/ado/plus >&2; \
	  echo "" >&2; \
	  echo "  These files are PINS. SSC serves no versioned install, so the ado" >&2; \
	  echo "  files themselves are the version record." >&2; \
	  echo "" >&2; \
	  echo "  To discard the drift:      git restore .stata/ado/plus" >&2; \
	  echo "  To adopt it deliberately:  make stata-requirements && review the diff" >&2; \
	  exit 1; \
	fi
	@echo ">> Vendored Stata tree matches HEAD."

# Assert the installed tree still matches stata-requirements.txt. This is the
# check the old "with version 3.1.2" console line only pretended to be.
.PHONY: stata-check
stata-check: stata-vendored-clean
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

# What is actually installed in the repo-local Stata adopath, as opposed to what
# env/stata-requirements.txt claims.
.PHONY: stata-list
stata-list:
	@echo "Installed Stata packages (.stata/ado/plus):"
	@find $(STATA_LOCAL) -name "*.ado" -exec basename {} \; 2>/dev/null \
	  | sort | uniq || echo "  none installed"
