"""The project's version must be the same number everywhere it appears.

Found 2026-08-19 while capturing output for a how-to: `make info` printed
"Version: 2.0.2" while pyproject.toml, _version.py and CITATION.cff all said
2.2.0. lib/repro-tools/scripts/bump_version.py updates those three plus the CHANGELOG, and never
knew about the Makefile's hardcoded copy — so every release since 2.0.2 widened
the gap silently, and the one command a user runs to ask "what am I on?" gave
the wrong answer.

The fix removed the second source of truth (the Makefile now reads
pyproject.toml). These tests exist so a THIRD one cannot appear unnoticed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def declared_version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version = "([^"]+)"', text, re.M)
    assert m, "pyproject.toml has no version"
    return m.group(1)


def test_version_py_agrees():
    text = (REPO_ROOT / "_version.py").read_text()
    m = re.search(r'__version__ = "([^"]+)"', text)
    assert m, "_version.py has no __version__"
    assert m.group(1) == declared_version()


def test_citation_cff_agrees():
    text = (REPO_ROOT / "CITATION.cff").read_text()
    m = re.search(r"^version: (.+)$", text, re.M)
    assert m, "CITATION.cff has no version"
    assert m.group(1).strip() == declared_version()


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_info_agrees():
    """The regression itself: `make info` is what a user runs to ask."""
    out = subprocess.run(
        ["make", "-s", "--no-print-directory", "info"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert out.returncode == 0, out.stderr
    assert f"Version: {declared_version()}" in out.stdout


def test_the_makefile_does_not_hardcode_a_version():
    """A literal version in the Makefile is a second source of truth, and the
    bump script does not know about it."""
    # Comment lines are excluded: the comment above the fix quotes the literal
    # it replaced, and a test that flags its own explanation is noise. Only what
    # make actually executes counts.
    hardcoded = [
        line.strip()
        for line in (REPO_ROOT / "Makefile").read_text().splitlines()
        if not line.lstrip().startswith("#")
        and re.search(r'echo "\s*Version:\s*\d+\.\d+\.\d+', line)
    ]
    assert not hardcoded, f"Makefile hardcodes a version: {hardcoded}"


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_info_describes_files_that_exist():
    """`make info` described `build_*.py` analysis scripts long after the layout
    became run_analysis.py + notebooks/. A structure listing that names absent
    files sends a reader looking for them."""
    out = subprocess.run(
        ["make", "-s", "--no-print-directory", "info"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert "build_*.py" not in out.stdout
    for name in ("run_analysis.py", "notebooks/"):
        assert name in out.stdout, f"make info no longer mentions {name}"
        assert (REPO_ROOT / name.rstrip("/")).exists(), f"{name} does not exist"
