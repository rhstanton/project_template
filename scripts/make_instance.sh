#!/usr/bin/env bash
#
# Materialize a disposable, bootstrapped instantiation of this template.
#
# The template is also a working project, so `make all` here exercises the full
# three-language variant. What that does NOT exercise is bootstrap.py -- the
# pruning step every real project starts with. This script gives you a throwaway
# copy of what a user actually gets, so a bug reported against "a project made
# from the template" can be reproduced without hand-assembling one.
#
# Disposable is the point. Nothing here is meant to be kept in sync by hand: a
# maintained example rots, and debugging against a rotted example is worse than
# having none, because you trust the answer. Regenerate instead of updating.
#
#   scripts/make_instance.sh                      # full variant, default dest
#   scripts/make_instance.sh --variant python-only
#   scripts/make_instance.sh --variant no-julia --dest /tmp/pt-nj
#   scripts/make_instance.sh --dirty              # use the working tree, not HEAD
#   scripts/make_instance.sh --build              # also run `make environment`
#
# Environment isolation is deliberate and non-negotiable: the instance gets its
# own .venv and its own .julia depot. Sharing them with this checkout is exactly
# the PYTHON_JULIAPKG_EXE failure -- a tree built while another checkout's
# environment was loaded silently uses the OTHER repo's Julia and still reports
# success. An instance that borrows its parent's environment is not an instance.
# uv's package cache IS shared (that is a cache, not an environment), so a
# Python-only instance costs seconds and almost no disk.

set -euo pipefail

# This script is EXECUTED, so unset is correct here. In a file that is *sourced*
# this would mutate the caller's interactive shell; use `CDPATH= cd --` there.
# Without it, `$(cd ... && pwd)` returns two newline-separated paths whenever the
# target resolves through CDPATH, and the damage surfaces much later as a missing
# module or a stray second depot.
unset CDPATH

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

VARIANT="full"
DEST=""
DIRTY=0
BUILD=0
FORCE=0

usage() {
    sed -n '3,28p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
    echo
    echo "Variants: full, python-only, no-julia, no-stata"
    exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --variant) VARIANT="${2:?--variant needs a value}"; shift 2 ;;
        --dest)    DEST="${2:?--dest needs a value}"; shift 2 ;;
        --dirty)   DIRTY=1; shift ;;
        --build)   BUILD=1; shift ;;
        --force)   FORCE=1; shift ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage 1 ;;
    esac
done

case "$VARIANT" in
    full)        BOOTSTRAP_FLAGS=() ;;
    python-only) BOOTSTRAP_FLAGS=(--python-only) ;;
    no-julia)    BOOTSTRAP_FLAGS=(--remove-julia) ;;
    no-stata)    BOOTSTRAP_FLAGS=(--remove-stata) ;;
    *) echo "Unknown variant: $VARIANT" >&2; usage 1 ;;
esac

# Sibling of the repo, never inside it. The .gitignore here is allowlist-style
# ("*" then "!" exceptions), so an in-repo scratch tree is both invisible to
# `git status` and liable to be swept into a journal package by a glob. Keeping
# instances outside the repo removes that whole class of accident.
if [[ -z "$DEST" ]]; then
    DEST="$(dirname -- "$REPO_ROOT")/project_template-instances/$VARIANT"
fi
mkdir -p -- "$(dirname -- "$DEST")"
DEST="$(cd -- "$(dirname -- "$DEST")" && pwd)/$(basename -- "$DEST")"

# Refuse a destination inside the repo, however it was spelled.
case "$DEST/" in
    "$REPO_ROOT"/*)
        echo "ERROR: destination is inside the repo: $DEST" >&2
        echo "Instances must live outside it; see the note above." >&2
        exit 1 ;;
esac

if [[ -e "$DEST" ]]; then
    if [[ "$FORCE" != 1 ]]; then
        echo "ERROR: $DEST already exists. Pass --force to replace it." >&2
        exit 1
    fi
    echo "Replacing existing $DEST"
    rm -rf -- "$DEST"
fi

SUBMODULE="$REPO_ROOT/lib/repro-tools"
if [[ ! -f "$SUBMODULE/src/repro_tools/lib/common.mk" ]]; then
    echo "ERROR: lib/repro-tools is not checked out." >&2
    echo "The Makefile includes its common.mk, so the instance cannot parse" >&2
    echo "without it. Run: git submodule update --init --recursive" >&2
    exit 1
fi

echo "Template : $REPO_ROOT"
echo "Variant  : $VARIANT"
echo "Source   : $([[ "$DIRTY" == 1 ]] && echo 'working tree' || echo 'HEAD (what a user gets)')"
echo "Dest     : $DEST"
echo

mkdir -p -- "$DEST"

if [[ "$DIRTY" == 1 ]]; then
    # Tracked plus untracked-but-not-ignored: precisely the set that would exist
    # if you committed everything right now. rsync rather than tar because macOS
    # ships bsdtar, which does not take --null -T -.
    ( cd -- "$REPO_ROOT" && git ls-files -z --cached --others --exclude-standard ) \
        | rsync -a --from0 --files-from=- -- "$REPO_ROOT/" "$DEST/"
else
    ( cd -- "$REPO_ROOT" && git archive HEAD ) | tar -x -C "$DEST"
fi

# git archive skips gitlinks entirely, so the submodule directory does not even
# get created. Copy its content in separately; the instance is disposable, so it
# wants the files, not a working git repo.
#
# --dirty has to apply here too. Taking the superproject from the working tree
# but the submodule from its HEAD produces an instance that is neither state, and
# silently ignores exactly the submodule edit you are trying to test -- which is
# the case that matters now that the shared machinery lives in the submodule.
mkdir -p -- "$DEST/lib/repro-tools"
if [[ "$DIRTY" == 1 ]]; then
    ( cd -- "$SUBMODULE" && git ls-files -z --cached --others --exclude-standard ) \
        | rsync -a --from0 --files-from=- -- "$SUBMODULE/" "$DEST/lib/repro-tools/"
else
    ( cd -- "$SUBMODULE" && git archive HEAD ) | tar -x -C "$DEST/lib/repro-tools"
fi

N_FILES="$(find "$DEST" -type f | wc -l | tr -d ' ')"
echo "Materialized $N_FILES files."

# The template's real HEAD, passed to bootstrap explicitly. The instance is a
# `git archive` export with no history of its own, and git searches UPWARDS for a
# repository -- so left to itself, bootstrap.py records whatever ancestor
# directory happens to be a repo. That is not theoretical: the first run here
# stamped a commit from ~/01_work/research, an unrelated repo two levels up,
# as this project's template origin. Wrong provenance is worse than none.
TEMPLATE_COMMIT="$(cd -- "$REPO_ROOT" && git rev-parse HEAD 2>/dev/null || true)"

echo
if [[ ${#BOOTSTRAP_FLAGS[@]} -gt 0 ]]; then
    echo "Running bootstrap.py ${BOOTSTRAP_FLAGS[*]} ..."
else
    echo "Recording template origin (no pruning for the full variant) ..."
fi
# System interpreter on purpose: the instance has no environment yet, and
# bootstrap.py must run before one is built. It is stdlib-only.
( cd -- "$DEST" && python3 bootstrap.py "${BOOTSTRAP_FLAGS[@]}" \
    ${TEMPLATE_COMMIT:+--template-commit "$TEMPLATE_COMMIT"} )

if [[ "$BUILD" == 1 ]]; then
    echo
    echo "Building the instance environment (this is not fast) ..."
    ( cd -- "$DEST" && make environment && make verify )
fi

cat <<EOF

Instance ready: $DEST

  cd $DEST
  make environment     # its OWN .venv and .julia -- never shared with the template
  make all

Throw it away with:  rm -rf $DEST
EOF
