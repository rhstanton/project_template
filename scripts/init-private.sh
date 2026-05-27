#!/usr/bin/env bash
# ==============================================================================
# init-private.sh — set up (or repair) this project's private maintainer overlay
# ==============================================================================
#
# Some files are "just for me, the maintainer" — working notes, private agent
# instructions, per-user editor/tool config — and must NEVER ship in the public
# repo. This script wires up a small pattern that keeps such files
#
#   * usable  — they live at their normal paths (via symlinks), so every tool
#               finds them where it expects;
#   * tracked — their real homes live inside `private/`, a SEPARATE git repo,
#               so they get version control and can be pushed to a private
#               backup remote;
#   * private — `private/` and every symlink name are gitignored by THIS
#               (public) repo, so none of it is ever committed or shipped.
#
# Layout it creates:
#
#   private/                          <- nested git repo, gitignored here
#   ├── README.md
#   ├── .gitignore
#   ├── dev-notes/                    <- maintainer working notes
#   ├── docs/  tests/                 <- homes for maintainer-only docs
#   ├── ai/AGENTS.local.md            <- private agent instructions (see below)
#   └── .claude/settings.local.json   <- per-user Claude Code config
#
#   dev-notes         -> private/dev-notes                (gitignored symlink)
#   AGENTS.local.md   -> private/ai/AGENTS.local.md        (gitignored symlink)
#   COAUTHOR_SETUP.md -> private/COAUTHOR_SETUP.md         (gitignored symlink)
#   .claude/settings.local.json -> ../private/.claude/settings.local.json
#
# AGENTS.local.md is the single canonical source of truth for private agent
# instructions. The public AGENTS.md tells every assistant to load it if
# present, so all AI tools pick it up without any tool-specific local file.
#
# The script is idempotent: safe to re-run any time. Run it via `make
# private-init` or directly. It never overwrites an existing real file.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PRIV="$REPO_ROOT/private"

cd "$REPO_ROOT"

echo "=============================================="
echo "Setting up private maintainer overlay"
echo "  repo:    $REPO_ROOT"
echo "  private: $PRIV"
echo "=============================================="
echo ""

# --- helpers -----------------------------------------------------------------

# make_symlink <link-relative-to-repo-root> <target-as-stored-in-symlink>
# Creates a relative symlink. Skips if already correct. Never clobbers a real
# file/dir (only replaces an existing symlink whose target is wrong).
make_symlink() {
    local link="$1" target="$2"
    local abs="$REPO_ROOT/$link"
    if [ -L "$abs" ]; then
        if [ "$(readlink "$abs")" = "$target" ]; then
            echo "  ✓ $link -> $target (already linked)"
            return
        fi
        echo "  ↻ $link was -> $(readlink "$abs"); relinking"
        rm "$abs"
    elif [ -e "$abs" ]; then
        echo "  ⚠ $link exists as a real file/dir — leaving it. Move it into"
        echo "     private/ by hand if you want it tracked privately."
        return
    fi
    mkdir -p "$(dirname "$abs")"
    ln -s "$target" "$abs"
    echo "  ✓ $link -> $target"
}

# seed_file <path> <<heredoc>  : write only if the file does not already exist.
seed_file() {
    local path="$1"
    if [ -e "$path" ]; then
        cat >/dev/null   # consume heredoc
        echo "  · kept existing $(echo "$path" | sed "s#^$REPO_ROOT/##")"
    else
        mkdir -p "$(dirname "$path")"
        cat >"$path"
        echo "  + created $(echo "$path" | sed "s#^$REPO_ROOT/##")"
    fi
}

# --- 1. nested git repo + directory skeleton ---------------------------------

echo "1. private/ git repo and directories"
mkdir -p "$PRIV"
if [ ! -d "$PRIV/.git" ]; then
    git -C "$PRIV" init -q
    echo "  ✓ initialized private/ as a nested git repo"
else
    echo "  ✓ private/ is already a git repo"
fi
mkdir -p "$PRIV/dev-notes" "$PRIV/docs" "$PRIV/tests" "$PRIV/ai" "$PRIV/.claude"
echo ""

# --- 2. seed template files (only when missing) ------------------------------

echo "2. template files"

seed_file "$PRIV/.gitignore" <<'EOF'
# This is the PRIVATE maintainer repo. It is intentionally separate from the
# public project repo (which gitignores this whole directory). Track whatever
# you like here; only the cruft below is ignored.

# OS / editor
.DS_Store
*~
.#*
\#*\#

# Python caches (in case private tooling lands here)
__pycache__/
*.pyc
EOF

seed_file "$PRIV/README.md" <<'EOF'
# Private maintainer overlay

This is a **separate git repo** holding files that are *just for the maintainer*
and must never ship in the public project repo. The public repo gitignores this
entire `private/` directory plus the symlinks that point into it (see the public
repo's `.gitignore`), so nothing here is ever committed or published upstream.

`scripts/init-private.sh` (a.k.a. `make private-init`) creates/repairs the
symlinks that make these files usable at their normal paths. It is idempotent.

## What lives here

| Real file (here)                  | Symlinked into public repo as       | Purpose                                  |
|-----------------------------------|-------------------------------------|------------------------------------------|
| `dev-notes/`                      | `dev-notes`                         | Maintainer working/milestone notes       |
| `ai/AGENTS.local.md`              | `AGENTS.local.md`                   | Private agent instructions (all tools)   |
| `COAUTHOR_SETUP.md`               | `COAUTHOR_SETUP.md`                 | Private coauthor setup notes             |
| `.claude/settings.local.json`     | `.claude/settings.local.json`       | Per-user Claude Code config              |
| `docs/<name>.md`, `tests/<name>.md` | `docs/<name>.md`, `tests/<name>.md` | Maintainer-only docs (symlinked if present) |

`AGENTS.local.md` is the canonical home for private agent guidance. The public
`AGENTS.md` instructs every assistant to read `AGENTS.local.md` if it exists, so
all AI tools pick it up — no tool-specific local file needed.

To add a maintainer-only doc that sits in an otherwise-public directory (e.g.
`docs/IMPLEMENTATION_NOTES.md`), create it under `private/docs/` and re-run
`make private-init`; the script symlinks it into place automatically.

## Backing this up to a private remote (optional)

This repo has no remote by default. To back it up, create a **private** repo on
your host of choice and:

```bash
git -C private remote add origin git@github.com:<you>/<project>-private.git
git -C private add -A && git -C private commit -m "Update private overlay"
git -C private push -u origin main
```
EOF

seed_file "$PRIV/ai/AGENTS.local.md" <<'EOF'
# Private agent instructions (AGENTS.local.md)

Canonical, private addendum to the public `AGENTS.md`. The public `AGENTS.md`
tells every AI assistant to load this file when it exists, so anything here
applies on top of the public guidance — for **all** tools (Claude Code, Codex,
Copilot, …). This file is gitignored by the public repo and never shipped.

Put private context here, e.g.:

- Personal workflow preferences and shortcuts.
- Pointers to private data locations, internal URLs, or credentials handling
  (never paste secrets themselves).
- Coauthor- or project-specific conventions not meant for the public template.
- Reminders that should steer agents but shouldn't appear in the shipped repo.
EOF

seed_file "$PRIV/dev-notes/README.md" <<'EOF'
# dev-notes

Maintainer working notes, milestone write-ups, and scratch. Tracked in the
private overlay repo; never shipped in the public project. Symlinked into the
public repo root as `dev-notes/`.
EOF

seed_file "$PRIV/COAUTHOR_SETUP.md" <<'EOF'
# Coauthor setup (private)

Private setup notes for coauthors/collaborators (machine access, data drops,
credentials handling, etc.). Symlinked into the public repo as
`COAUTHOR_SETUP.md` but kept out of the public repo.

_Replace this placeholder with your own notes._
EOF
echo ""

# --- 3. relocate per-user Claude config into the overlay ---------------------

echo "3. .claude/settings.local.json (per-user Claude Code config)"
local_settings="$REPO_ROOT/.claude/settings.local.json"
priv_settings="$PRIV/.claude/settings.local.json"
if [ -f "$local_settings" ] && [ ! -L "$local_settings" ]; then
    if [ -e "$priv_settings" ]; then
        echo "  ⚠ a private copy already exists; leaving public file in place."
        echo "     Reconcile $local_settings and $priv_settings by hand."
    else
        mv "$local_settings" "$priv_settings"
        echo "  → moved existing settings.local.json into private/.claude/"
    fi
fi
# Ensure a target exists so the symlink is never dangling.
if [ ! -e "$priv_settings" ]; then
    printf '{\n  "permissions": {\n    "allow": []\n  }\n}\n' >"$priv_settings"
    echo "  + created empty private/.claude/settings.local.json"
fi
echo ""

# --- 4. symlinks (gitignored by the public repo) -----------------------------

echo "4. symlinks"
make_symlink "dev-notes"                   "private/dev-notes"
make_symlink "AGENTS.local.md"             "private/ai/AGENTS.local.md"
make_symlink "COAUTHOR_SETUP.md"           "private/COAUTHOR_SETUP.md"
make_symlink ".claude/settings.local.json" "../private/.claude/settings.local.json"

# Maintainer-only docs that sit inside otherwise-public dirs: link only when a
# private source actually exists (so we never create dangling links).
# Format: "<public-link> | <symlink-target> | <private-source-to-check>"
for spec in \
    "docs/NOTEBOOK_SUPPORT_IMPLEMENTATION.md|../private/docs/NOTEBOOK_SUPPORT_IMPLEMENTATION.md|private/docs/NOTEBOOK_SUPPORT_IMPLEMENTATION.md" \
    "tests/NOTEBOOK_TESTS_SUMMARY.md|../private/tests/NOTEBOOK_TESTS_SUMMARY.md|private/tests/NOTEBOOK_TESTS_SUMMARY.md" \
    "tests/TEST_IMPROVEMENTS.md|../private/tests/TEST_IMPROVEMENTS.md|private/tests/TEST_IMPROVEMENTS.md" \
; do
    link="${spec%%|*}"; rest="${spec#*|}"
    target="${rest%%|*}"; source="${rest#*|}"
    if [ -e "$REPO_ROOT/$source" ]; then
        make_symlink "$link" "$target"
    fi
done
echo ""

# --- 5. first commit in the overlay repo -------------------------------------

echo "5. private/ initial commit"
if ! git -C "$PRIV" rev-parse HEAD >/dev/null 2>&1; then
    git -C "$PRIV" add -A
    if git -C "$PRIV" commit -q -m "Initialize private maintainer overlay"; then
        echo "  ✓ created initial commit in private/"
    else
        echo "  ⚠ could not commit (is git user.name/email configured?)."
        echo "     Commit manually: git -C private add -A && git -C private commit"
    fi
else
    echo "  · private/ already has history — leaving commits to you."
fi
echo ""

echo "=============================================="
echo "✓ Private overlay ready."
echo ""
echo "  • Public repo ignores private/ and the symlinks above."
echo "  • Edit private files at their normal paths; real files live in private/."
echo "  • Optional backup remote: see private/README.md"
echo "=============================================="
