"""Test-suite hygiene: markers that survive, and skips that are honest.

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


def discovered_modules() -> list[Path]:
    """Every test module in this directory.

    Deliberately NOT named with a `test_` prefix: pytest collects anything so
    named, and this helper used to be, which meant a function returning a list
    was reported as a passing test that asserted nothing.
    """
    return sorted(TESTS_DIR.glob("test_*.py"))


def test_there_are_modules_to_check():
    """Guard the guard: an empty glob makes every check below vacuous.

    The parametrized check would then generate zero cases and the marker scan
    would loop over nothing -- both reported green.
    """
    found = discovered_modules()
    assert len(found) > 5, (
        f"found only {len(found)} test modules in {TESTS_DIR}; the checks in "
        "this file scan that list and would pass trivially"
    )


@pytest.mark.parametrize("path", discovered_modules(), ids=lambda p: p.name)
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
    for path in discovered_modules():
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


# ---------------------------------------------------------------------------
# Skips must be honest
# ---------------------------------------------------------------------------

IMPORTORSKIP = re.compile(r"importorskip\(\s*[\"']([A-Za-z0-9_.]+)[\"']")

# Third-party packages that genuinely may be absent. Anything else named in an
# importorskip is a module this repository ships, and a failure to import one is
# a defect rather than an absent capability.
OPTIONAL_THIRD_PARTY = {
    "matplotlib",
    "ipython",
    "papermill",
    "nbformat",
    "juliacall",
    "cupy",
    "jax",
}

REPO_ROOT = TESTS_DIR.parent


def test_importorskip_is_never_used_on_an_in_repo_module():
    """A skip must mean "this capability is absent", never "this is broken".

    Found in the sibling `fire` repository on 2026-08-21: a test module put only
    one of two needed roots on sys.path and then `importorskip`-ed a module that
    lived under the other. The import failed on every run and pytest reported
    twelve SKIPPED tests. Nothing was red, so nothing was investigated -- for as
    long as nobody read the skip reasons, which is indefinitely.

    `pytest.importorskip` is the right tool for an optional third-party
    dependency and the wrong one for anything shipped here.
    """
    offenders: dict[str, list[str]] = {}
    for path in discovered_modules():
        if path.name == Path(__file__).name:
            continue
        for name in IMPORTORSKIP.findall(path.read_text()):
            root = name.split(".")[0]
            if root in OPTIONAL_THIRD_PARTY:
                continue
            if (REPO_ROOT / root).exists() or (REPO_ROOT / f"{root}.py").exists():
                offenders.setdefault(name, []).append(path.name)
    assert not offenders, (
        "importorskip used on modules this repository ships, which turns a "
        f"broken import into a green skip: {offenders}. Import them directly."
    )


def test_the_optional_list_is_not_a_blanket_exemption():
    """Guard the guard: an over-broad allowlist would empty the check above."""
    assert len(OPTIONAL_THIRD_PARTY) < 20, (
        "OPTIONAL_THIRD_PARTY has grown large enough to exempt most imports; "
        "it should name genuinely optional third-party packages only"
    )
    for name in OPTIONAL_THIRD_PARTY:
        assert not (REPO_ROOT / name).exists(), (
            f"{name!r} is exempted as third-party but exists in this repository"
        )
