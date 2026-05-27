# AGENTS.md

Guidance for AI coding agents (Claude Code, GitHub Copilot, Codex, etc.) working in this repository. This file is the **single source of truth**; tool-specific files are symlinks to it (see "Agent tool wiring" at the bottom).

> **Private local instructions.** If a file named `AGENTS.local.md` exists in the repo root, read it and follow it as additional, private instructions that take precedence over this file. It is gitignored (a symlink into the `private/` overlay) and never shipped — so it is the place for maintainer- or machine-specific guidance. See "Agent tool wiring" for the overlay layout.

## What this is

A template for reproducible empirical research. The core idea is a **build → publish separation with provenance tracking**: analysis scripts write artifacts (figure + table + provenance YAML) to `output/`, and `make publish` is the *only* sanctioned way to copy them into `paper/` (intended to be a separate git repo with an Overleaf remote). Supports Python, Julia, and Stata in one environment.

## Common commands

All workflows go through Make. The `$(PYTHON)` etc. in recipes resolve to the env wrappers below.

```bash
make environment      # One-time setup: Python/Julia/Stata + git submodule init (~10-15 min)
make verify           # Quick smoke test that env + data are OK
make all              # Build every artifact in ANALYSES
make price_base       # Build one artifact (figure + table + provenance, atomically)
make publish          # Copy output/ -> paper/ with git safety checks
make publish PUBLISH_ANALYSES="price_base"  # Publish specific artifact(s)

make test             # Run full pytest suite
make lint             # ruff check
make format           # ruff fixes + ruff format (NOT black, despite some doc text)
make type-check       # mypy on run_analysis.py and shared/*.py
make check            # lint + format-check + type-check + test (run before committing)
make clean            # Remove output/
```

Run a single test (Make has no per-test target — call the wrapper directly so PYTHONPATH/Julia env are set):

```bash
env/scripts/runpython -m pytest tests/test_defaults.py -v
env/scripts/runpython -m pytest tests/test_defaults.py::TestName::test_case -v
```

## Critical environment facts

- **GNU Make 4.3+ is required** and this is a real trap on macOS (ships 3.81). The build uses grouped targets (`&:`) so a single script invocation produces figure + table + provenance atomically. With old Make, `make all` silently misbehaves. Install via `brew install make` and run `gmake`.
- **Never invoke `python`/`julia`/`stata` directly.** Always use the wrappers in `env/scripts/` (`runpython`, `runjulia`, `runstata`, `runnotebook`). `runpython` sets `PYTHONPATH` to the repo root (so `from shared import config` and `import repro_tools` resolve), points juliacall at the bundled Julia in `.julia/`, and disables CondaPkg (`JULIA_CONDAPKG_BACKEND=Null`) to avoid a duplicate Python.
- Python lives in a uv-managed virtualenv at `.venv/`. Julia auto-installs to `.julia/` via juliacall. Stata packages install locally to `.stata/`. None are global.

## Architecture

**The `repro-tools` submodule does most of the heavy lifting.** It is a git submodule at `lib/repro-tools/` and provides two things the project depends on:

1. **The `repro_tools` Python package** — imported directly in analysis scripts: `auto_build_record`, `friendly_docopt`, `print_config`, `validate_study_config`, `setup_environment`, etc. (Note: the local `scripts/` dir only has `check_prerequisites.sh`; older docs referencing `scripts/provenance.py` and `scripts/publish_artifacts.py` are stale — that code now lives in `repro_tools`.)
2. **Core Make targets** — the project `Makefile` does `include lib/repro-tools/src/repro_tools/lib/common.mk` (around line 151). `test`, `lint`, `format`, `type-check`, `check`, `verify`, `publish`, `test-outputs`, `pre-submit`, `replication-report` are all defined *there*, not in the project Makefile. To understand or change those targets, edit/read `common.mk`, not `Makefile`.

**Two kinds of analysis scripts:**

- `run_analysis.py` — the unified, config-driven script. It does not contain study logic per se; it reads a study name as an argument and pulls all parameters from `shared/config.py`'s `STUDIES` dict. Config resolves with priority: `config.DEFAULTS` < `config.STUDIES[study]` < command-line args. It produces a grouped-by-x aggregate table and a grouped line plot, then calls `auto_build_record()`.
- `run_did.py` — a standalone difference-in-differences script demonstrating **Julia/Python backend interop**: it runs the regression via Julia `FixedEffectModels.jl` (through juliacall) by default and falls back to Python `pyfixest` if Julia is unavailable. Note it sets `PYTHON_JULIAPKG_PROJECT` before importing juliacall.

**The Makefile artifact pattern.** Each artifact is declared by a 5-line block of variables, then `ANALYSES := ...` drives a `foreach` that generates the rules:

```makefile
ANALYSES := price_base remodel_base correlation julia_demo

price_base.script  := run_analysis.py
price_base.runner  := $(PYTHON)       # or $(NOTEBOOK) for .ipynb
price_base.inputs  := $(DATA)
price_base.outputs := $(OUT_FIG_DIR)/price_base.pdf $(OUT_TBL_DIR)/price_base.tex $(OUT_PROV_DIR)/price_base.yml
price_base.args    := price_base
```

Notebooks (`correlation`, `julia_demo`) use `$(NOTEBOOK)` (`runnotebook`, executes via papermill) and a `.ipynb` script.

**Provenance chain.** Build records (`output/provenance/<name>.yml`) capture git commit/branch/dirty state, the command, and SHA256 of every input and output. `make publish` aggregates these into `paper/provenance.yml` and enforces git safety: clean working tree, branch not behind upstream, and (by default) artifacts built from the current HEAD. Disable individual checks via `make publish ALLOW_DIRTY=1` / `REQUIRE_NOT_BEHIND=0` / `REQUIRE_CURRENT_HEAD=0`.

## Adding a new analysis

1. Add an entry to `STUDIES` in `shared/config.py` (only specify what differs from `DEFAULTS`; `figure`, `table`, and `yvar` are typically required).
2. Add the name to `ANALYSES` in `Makefile` and add the 5-line pattern block shown above.
3. `make <name>` to build, then `make publish PUBLISH_ANALYSES="<name>"`.

## Conventions

- **Never edit `paper/` by hand** — always `make publish`, or the provenance chain breaks.
- `env/Project.toml` is a Julia *environment*, not a package (no `name`/`uuid`/`version`). `env/Manifest.toml` is gitignored (platform-specific).
- Do not manually copy `lib/repro-tools/` when creating a project from this template — `make environment` initializes it as a submodule. Update with `make update-submodules` (or `make update-environment` to also reinstall).
- Run `make check` before committing.

## Agent tool wiring

This file is canonical. To keep every assistant reading the same instructions with no duplication:

- **Codex** reads `AGENTS.md` directly — nothing else needed.
- **Claude Code** reads `CLAUDE.md` → symlinked to `AGENTS.md`.
- **GitHub Copilot** reads `.github/copilot-instructions.md` → symlinked to `AGENTS.md`.

To wire up another tool, add a symlink from its expected path to this file (e.g. `ln -s AGENTS.md .cursorrules`) rather than copying the content.

### Private overlay

Maintainer-only files that must **never** ship publicly (working notes, private agent instructions, per-user tool config) live in `private/` — a *separate, nested git repo* that this repo gitignores. Gitignored symlinks at the public root point into it, so tools find everything at its normal path while git never tracks it. Set it up (or repair it) with `make private-init`; full details in TEMPLATE_USAGE.md → "Keeping private maintainer files".

- `AGENTS.local.md` → `private/ai/AGENTS.local.md` — canonical private agent instructions, loaded via the callout at the top of this file. **Agents: never commit `private/` or any of these symlinks to the public repo, and never copy private content into public files.**
- `.claude/settings.local.json` → `private/.claude/settings.local.json` — per-user Claude Code config. The committed, shared defaults live in `.claude/settings.json`.
- `dev-notes`, `COAUTHOR_SETUP.md`, and (when present) maintainer-only docs under `docs/`/`tests/` are wired the same way.
