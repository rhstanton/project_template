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
