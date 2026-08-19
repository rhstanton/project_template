"""Files documented as machine-local must actually be gitignored.

env/env.sh sources env/local.sh last, so it can override anything, and says in
its own comments that the file "is gitignored and optional". In
project_template that was false until 2026-08-19: .gitignore never mentioned it,
and the allowlist's `!*.sh` made it TRACKED. A DATA_DIR pointing at someone's
private path -- or any other machine-specific setting -- would have been
committed by the next `git add -A`.

This is the second time in two days that a file has asserted something about
itself that no rule enforced: env.sh also named a .envrc the template did not
ship. Documentation describing a mechanism is not the mechanism.

Asked of git rather than by reading .gitignore, because ORDER decides the answer
in an allowlist-style file -- a rule placed before `!*.sh` would be silently
overridden, and reading the file would not show that.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Paths that must never be committed, whether or not they exist right now.
MACHINE_LOCAL = ["env/local.sh"]


def is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=120,
    )
    return result.returncode == 0


@pytest.mark.parametrize("path", MACHINE_LOCAL)
def test_machine_local_file_is_ignored(path):
    assert is_ignored(path), (
        f"{path} is not gitignored, so machine-specific settings would be "
        f"committed by `git add -A`"
    )


@pytest.mark.parametrize("path", MACHINE_LOCAL)
def test_it_is_not_already_tracked(path):
    """An ignore rule does nothing for a file already in the index."""
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode != 0, (
        f"{path} is tracked; the ignore rule will not help until it is removed "
        f"with `git rm --cached {path}`"
    )


def test_env_sh_still_claims_it_is_gitignored():
    """Guard the guard: if the claim goes, this test is testing nothing.

    The tests above are here because env/env.sh makes a promise about this file.
    If someone removes the promise, they should notice that these exist.
    """
    text = (REPO_ROOT / "env" / "env.sh").read_text()
    assert "local.sh" in text and "gitignored" in text


def test_the_ignore_survives_the_allowlist():
    """Both repos use allowlist-style .gitignore (`*` then `!` exceptions).

    A rule placed before `!*.sh` would be overridden by it. Checking with git
    rather than by grepping is what makes this meaningful, but assert the shape
    too so the reason is visible.
    """
    text = (REPO_ROOT / ".gitignore").read_text()
    lines = [line.strip() for line in text.splitlines()]
    if "!*.sh" not in lines:
        pytest.skip("no !*.sh exception in this .gitignore")
    assert lines.index("env/local.sh") > lines.index("!*.sh") or is_ignored(
        "env/local.sh"
    )
