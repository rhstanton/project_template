"""A module must not rebind `pytestmark`, and every marker must be registered.

Two separate `pytestmark = ...` statements do not combine. The second rebinds the
name and the first is lost, with no warning from Python or pytest. On 2026-08-20
adding `pytestmark = pytest.mark.needs_env` to a module that already had
`pytestmark = pytest.mark.julia` erased the julia marker, so those tests ran in a
--python-only project and failed with "no recipe for julia-instantiate" -- correct
behavior reported as a defect, in CI only, because the local variant runner had
skipped the module for the other reason.

Losing a skip marker is the dangerous direction: the test runs where it cannot
work. Losing it the other way would merely skip something.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PYPROJECT = TESTS_DIR.parent / "pyproject.toml"
CONFTEST = TESTS_DIR / "conftest.py"
ASSIGN = re.compile(r"^pytestmark\s*=", re.M)
USED = re.compile(r"pytest\.mark\.([a-z_][a-z0-9_]*)")

# pytest's own markers, which need no registration.
BUILTIN = {"skip", "skipif", "xfail", "parametrize", "usefixtures", "filterwarnings"}


def test_files():
    return sorted(TESTS_DIR.glob("test_*.py"))


@pytest.mark.parametrize("path", test_files(), ids=lambda p: p.name)
def test_module_assigns_pytestmark_at_most_once(path):
    """Use a list to combine markers, never a second assignment."""
    n = len(ASSIGN.findall(path.read_text()))
    assert n <= 1, (
        f"{path.name} assigns pytestmark {n} times; the last one wins and the "
        "others are silently discarded. Combine them: "
        "pytestmark = [pytest.mark.a, pytest.mark.b]"
    )


def registered_markers() -> set:
    """Markers are declared in TWO places, and both count.

    pyproject.toml [tool.pytest.ini_options].markers holds the static ones;
    conftest.py registers the capability markers with addinivalue_line, next to
    the code that decides when to skip them. Reading only the first reports
    julia and stata as unregistered.
    """
    declared = set(re.findall(r'^\s*"([a-z_][a-z0-9_]*):', PYPROJECT.read_text(), re.M))
    declared |= set(re.findall(r'"([a-z_][a-z0-9_]*): ', CONFTEST.read_text()))
    return declared


def test_every_marker_used_is_registered():
    """--strict-markers turns an unregistered marker into an error, but only for
    markers pytest actually sees; one lost by rebinding is never checked at all.
    """
    declared = registered_markers()
    unknown = {}
    for path in test_files():
        # This file names `pytest.mark.a` and `.b` inside a message showing how
        # to combine markers. Scanning it finds its own prose and reports two
        # markers that do not exist -- the same "prose read as code" mistake
        # this repository keeps making. It has no real markers of its own.
        if path.name == Path(__file__).name:
            continue
        for name in USED.findall(path.read_text()):
            if name not in BUILTIN and name not in declared:
                unknown.setdefault(name, []).append(path.name)
    assert not unknown, f"markers used but not registered in pyproject.toml: {unknown}"


def test_the_registry_is_not_empty():
    """Guard the guard: an empty parse would pass the test above trivially."""
    declared = registered_markers()
    assert {"julia", "stata", "needs_env"} <= declared, (
        f"expected the known markers to be registered; parsed {sorted(declared)}"
    )
