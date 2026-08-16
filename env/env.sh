# env/env.sh — single source of truth for this project's environment.
#
# Sourced by env/scripts/run{python,julia,stata,notebook} and by .envrc, so an
# interactive shell (and Emacs, via envrc.el) sees exactly what `make` sees.
# Keeping one copy is the point: before this file existed the wrappers each
# carried their own block and had drifted apart -- runnotebook was missing
# JULIA_LOAD_PATH entirely, and runjulia set JULIAPKG_PROJECT where runpython set
# PYTHON_JULIAPKG_PROJECT, a different name AND a different value.
#
# It is deliberately thin. The toolchain half -- which Python, which Julia, how
# they are bridged -- lives in the repro-tools submodule and is shared by every
# project, so a fix there reaches projects that were created before it. Only
# genuinely project-specific settings belong below.
#
# CONTRACT: sourced, never executed. No `set -e`, no `exec`, no output on
# success. Must be safe to source repeatedly.

# --- repo root -----------------------------------------------------------
# Resolved relative to this file, so it is correct whether sourced by a wrapper
# in env/scripts/ or by .envrc at the root.
#
# CDPATH is cleared *inside* the command substitution, not with `unset CDPATH`.
# When `cd` resolves a target through CDPATH it echoes the directory, and inside
# a command substitution that output is captured -- so the variable silently gets
# two newline-separated paths and the damage surfaces much later as a missing
# module or a stray second Julia depot. `unset` would fix it here but would also
# mutate the interactive shell of anyone whose .envrc sourced this.
REPRO_PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export REPRO_PROJECT_ROOT

# --- shared toolchain ----------------------------------------------------
# Python interpreter, Julia bridge, PYTHON_JULIAPKG_EXE, PATH hygiene.
# See lib/repro-tools/src/repro_tools/lib/env.sh.
_project_shared_env="$REPRO_PROJECT_ROOT/lib/repro-tools/src/repro_tools/lib/env.sh"
if [[ -f "$_project_shared_env" ]]; then
    # shellcheck source=/dev/null
    source "$_project_shared_env"
else
    echo "env/env.sh: missing $_project_shared_env" >&2
    echo "  Run: git submodule update --init --recursive" >&2
fi
unset _project_shared_env

# --- input data ----------------------------------------------------------
# Assigned unconditionally, NOT as ${DATA_DIR:-...}. Written with `:-` this line
# inherited a DATA_DIR exported by a DIFFERENT project's direnv, so a run here
# pointed at that project's data directory -- in testing, at another repo's
# licensed inputs. Silently reading the wrong data is about the worst failure
# this file could cause, and the `:-` form invites exactly that: the ambient
# shell is not a statement of intent about THIS project.
#
# env/local.sh below is the sanctioned override, and it is sourced afterwards so
# a deliberate choice still wins over this default.
export DATA_DIR="$REPRO_PROJECT_ROOT/data"

# --- import path ---------------------------------------------------------
# This project's root, and nothing inherited. Appending to an existing
# PYTHONPATH looks harmless and is not: it puts ANOTHER project's root on
# sys.path, so `import shared` can resolve to the wrong shared/, and -- the way
# this was actually found -- juliapkg scans sys.path for juliapkg.json and
# happily picked up a different repo's Julia pin:
#
#   [juliapkg] Found dependencies: /…/fire/env/juliapkg.json
#   Error: 'version' entries have empty intersection:
#     '=0.9.34' at /…/this-project/env/juliapkg.json
#     '=0.9.31' at /…/fire/env/juliapkg.json
#
# A fresh clone therefore failed to build purely because of which directory the
# shell had been in. Same rule as DATA_DIR and JULIA_NUM_THREADS: the ambient
# environment is not a statement of intent about THIS project. Add extra entries
# from env/local.sh, which is sourced after this.
export PYTHONPATH="$REPRO_PROJECT_ROOT"

# --- machine-local overrides ---------------------------------------------
# env/local.sh is gitignored and optional, and is sourced LAST so it can
# override anything above -- that ordering is what makes the unconditional
# assignments safe rather than rigid.
#
# Sourced here rather than from .envrc so `make` and the wrappers pick it up
# too: direnv must never be required to get a correct run.
if [[ -f "$REPRO_PROJECT_ROOT/env/local.sh" ]]; then
    # shellcheck source=/dev/null
    source "$REPRO_PROJECT_ROOT/env/local.sh"
fi
