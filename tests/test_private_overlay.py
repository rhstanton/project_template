"""Tests for the private maintainer overlay (see TEMPLATE_USAGE.md).

The overlay's whole purpose is to keep maintainer-only files OUT of the public
repo while still tracking them (in the nested `private/` repo) and exposing them
at their normal paths (via symlinks). The privacy guarantee rests entirely on
`.gitignore` *ordering* — the broad `!*.md` / `!*/` includes near the top would
otherwise track the `.md` symlinks and let git descend into `private/`. These
tests pin that down so a future `.gitignore` edit can't silently start tracking
private content.

They consult ignore *rules* via `git check-ignore`, so they pass on a fresh
checkout where the overlay has never been set up (no `private/`, no symlinks).
"""

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths that MUST be ignored by the public repo (real files or symlinks into
# the private overlay). Keep in sync with scripts/init-private.sh.
PRIVATE_PATHS = [
    "private",
    "dev-notes",
    "AGENTS.local.md",
    "COAUTHOR_SETUP.md",
    ".claude/settings.local.json",
]

# Paths that MUST stay tracked/public (the shared seam of the overlay).
PUBLIC_PATHS = [
    ".claude/settings.json",
]


def _is_ignored(path: str) -> bool:
    """True if `path` is ignored by the repo's gitignore rules."""
    # check-ignore exits 0 when ignored, 1 when not ignored.
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return result.returncode == 0


class TestPrivateOverlayNeverLeaks:
    """The public repo must never track private overlay content."""

    def test_private_paths_are_ignored(self):
        not_ignored = [p for p in PRIVATE_PATHS if not _is_ignored(p)]
        assert not not_ignored, (
            f"These private paths are NOT gitignored and could leak into the "
            f"public repo: {not_ignored}. Check .gitignore ordering — the "
            f"re-ignores must come after the `!*.md` and `!*/` includes."
        )

    def test_shared_claude_settings_stays_public(self):
        wrongly_ignored = [p for p in PUBLIC_PATHS if _is_ignored(p)]
        assert not wrongly_ignored, (
            f"These shared/public files are gitignored but should be tracked: "
            f"{wrongly_ignored}."
        )


class TestSharedClaudeSettings:
    """The committed shared Claude config ships as valid JSON."""

    def test_settings_json_is_valid(self):
        settings = REPO_ROOT / ".claude" / "settings.json"
        assert settings.is_file(), f"{settings} is missing"
        data = json.loads(settings.read_text())
        assert "permissions" in data
        assert isinstance(data["permissions"].get("allow"), list)


class TestInitPrivateScript:
    """The setup helper is present, executable, and syntactically valid."""

    def test_script_exists_and_executable(self):
        script = REPO_ROOT / "scripts" / "init-private.sh"
        assert script.is_file(), f"{script} is missing"
        import os

        assert os.access(script, os.X_OK), f"{script} is not executable"

    def test_script_parses(self):
        script = REPO_ROOT / "scripts" / "init-private.sh"
        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"
