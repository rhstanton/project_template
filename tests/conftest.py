"""Shared test configuration.

The template ships its whole test suite to every generated project, including
projects that pruned a language. Before this file existed, `bootstrap.py
--python-only` produced a project whose suite asserted that `runjulia` exists and
that `juliacall` imports -- 14 failures on a project that was correctly built.

Deleting those tests during bootstrap would be the other option, and is worse:
the language tests are interleaved with Python ones inside shared files, and a
project that later adds Julia back would have silently lost its coverage. So they
stay and skip, and whether they skip is derived from the project itself rather
than from a flag someone has to remember to pass.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def has_julia() -> bool:
    """Julia is part of this project if bootstrap left its project file."""
    return (REPO_ROOT / "env" / "Project.toml").is_file()


def has_stata() -> bool:
    return (REPO_ROOT / "env" / "stata-packages.txt").is_file()


def stata_installed() -> bool:
    """Stata being *configured* and Stata being *runnable* are different.

    CI configures Stata (the ado files are committed) but has no stata-mp, so a
    test that needs to execute Stata must check for the binary as well.
    """
    return shutil.which("stata-mp") is not None


def _is_own_git_repo() -> bool:
    """Is REPO_ROOT the top level of a git checkout, rather than inside one?"""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if out.returncode != 0:
        return False
    return Path(out.stdout.strip()).resolve() == REPO_ROOT.resolve()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "julia: requires Julia; skipped when the project has no Julia"
    )
    config.addinivalue_line(
        "markers", "stata: requires Stata; skipped when the project has no Stata"
    )
    config.addinivalue_line(
        "markers", "stata_binary: requires a runnable stata-mp on PATH"
    )
    config.addinivalue_line(
        "markers",
        "needs_env: shells out through env/scripts/; skipped when .venv is absent",
    )
    config.addinivalue_line(
        "markers",
        "needs_own_git_repo: asserts what git tracks; needs this tree to BE a "
        "checkout, not merely to sit inside one",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    skip_julia = pytest.mark.skip(
        reason="no Julia in this project (env/Project.toml absent)"
    )
    skip_stata = pytest.mark.skip(
        reason="no Stata in this project (env/stata-packages.txt absent)"
    )
    skip_stata_bin = pytest.mark.skip(reason="stata-mp not on PATH")
    # Tests that invoke env/scripts/runpython and friends cannot work before
    # `make environment`. Without this they FAIL rather than skip, with a
    # confusing "Python env not found" from the wrapper -- 42 of them at once
    # when the suite is run against a freshly bootstrapped project, which buries
    # the handful of real failures that run is meant to surface.
    skip_no_env = pytest.mark.skip(
        reason="no built environment here (.venv absent); run `make environment`"
    )
    env_absent = not (REPO_ROOT / ".venv" / "bin" / "python").exists()

    # "Is this file tracked?" is unanswerable unless this tree is its own
    # checkout. A generated project unpacked inside another repository gets that
    # repository's answers -- git ls-files returns nothing for it, and an
    # assertion that vendored packages are committed fails for a reason that has
    # nothing to do with the packages. The same confusion silently disabled
    # bootstrap's doc pruning until 2026-08-20.
    skip_no_repo = pytest.mark.skip(
        reason="this tree is not its own git checkout; git-tracking assertions "
        "would answer for a containing repository"
    )
    own_repo_absent = not _is_own_git_repo()

    julia_absent = not has_julia()
    stata_absent = not has_stata()
    stata_bin_absent = not stata_installed()

    for item in items:
        if julia_absent and "julia" in item.keywords:
            item.add_marker(skip_julia)
        if stata_absent and "stata" in item.keywords:
            item.add_marker(skip_stata)
        if stata_bin_absent and "stata_binary" in item.keywords:
            item.add_marker(skip_stata_bin)
        if env_absent and "needs_env" in item.keywords:
            item.add_marker(skip_no_env)
        if own_repo_absent and "needs_own_git_repo" in item.keywords:
            item.add_marker(skip_no_repo)
