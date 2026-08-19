"""Editor configuration must name tools and paths that exist.

`.dir-locals.el` is loaded silently by Emacs. When it names a program that is
not installed or a directory that does not exist, nothing announces it -- the
feature just stops working, and the failure surfaces much later as "format on
save does nothing" or "the wrong pytest ran".

This template carried two such entries until 2026-08-19:

  * `(format-all-formatters . (("Python" black)))` -- black was dropped when the
    toolchain unified on ruff, so this named a program that is not installed.
  * `.env/bin/...` paths, from the conda era. The project has used uv and .venv
    since 2026-05-27.

The second was invisible on this machine for a specific and instructive reason:
a stale `.env/` directory from February 2026 was still sitting in the working
copy, so `locate-dominating-file` found it and the paths resolved to a conda
environment that had not been rebuilt in six months. Correct-looking, and wrong.

fire carried the identical pair and was fixed 2026-08-17; the template kept
them two days longer. These tests exist so neither drifts again after the next
toolchain change.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_LOCALS = REPO_ROOT / ".dir-locals.el"

pytestmark = pytest.mark.skipif(
    not DIR_LOCALS.is_file(), reason=".dir-locals.el not present"
)


@pytest.fixture(scope="module")
def text() -> str:
    return DIR_LOCALS.read_text()


def code(text: str) -> str:
    """Drop `;;` comment lines: they legitimately mention retired tools."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(";;")
    )


def test_no_conda_era_env_paths(text):
    """.env was the conda directory; uv creates .venv."""
    assert ".env/" not in code(text), (
        ".dir-locals.el still points at the conda-era .env/ directory"
    )


def test_does_not_name_black(text):
    """black is not installed here; naming it makes format-on-save fail."""
    assert "black" not in code(text)


def test_names_ruff_as_the_formatter(text):
    assert re.search(r'format-all-formatters.*"Python"\s+ruff', code(text)), (
        "the Python formatter should be ruff, matching pyproject.toml"
    )


def optional_only(tool: str) -> bool:
    """Is this tool declared ONLY in a non-default dependency group?

    ipython is the case in point: fire declares it in the `notebook` group,
    which a replication run deliberately does not install, while
    project_template has it among its defaults. A test that hardcoded either
    answer would be wrong in the other repository, so it is derived from
    pyproject.toml instead.
    """
    import tomllib

    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    project = data.get("project", {})
    default_groups = set(
        data.get("tool", {}).get("uv", {}).get("default-groups", ["dev"])
    )

    def mentions(entries) -> bool:
        return any(tool in str(entry) for entry in entries or [])

    if mentions(project.get("dependencies")):
        return False
    for name, entries in (data.get("dependency-groups") or {}).items():
        if mentions(entries) and name in default_groups:
            return False
    for entries in (project.get("optional-dependencies") or {}).values():
        if mentions(entries):
            return True
    for entries in (data.get("dependency-groups") or {}).values():
        if mentions(entries):
            return True
    return False


@pytest.mark.parametrize("tool", ["ruff", "pytest", "ipython", "mypy"])
def test_referenced_tools_exist_in_the_venv(text, tool):
    """Every tool the editor is pointed at must actually be installed.

    Skipped rather than failed when the environment is absent: a fresh clone
    has no .venv, and that is not a configuration error.
    """
    venv = REPO_ROOT / ".venv"
    if not venv.is_dir():
        pytest.skip("no .venv (run make environment)")
    if f"/{tool}" not in code(text):
        pytest.skip(f"{tool} is not referenced in .dir-locals.el")
    if not (venv / "bin" / tool).exists() and optional_only(tool):
        pytest.skip(f"{tool} is an optional dependency and is not installed")
    assert (venv / "bin" / tool).exists(), (
        f".dir-locals.el points at {tool}, which is not installed in .venv"
    )


def test_no_stale_env_claim_in_the_makefile():
    """`make info` told users the build creates .env/, which it has not since May."""
    text = (REPO_ROOT / "Makefile").read_text()
    assert "Creates .env/" not in text
