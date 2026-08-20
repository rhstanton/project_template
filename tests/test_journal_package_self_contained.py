"""The replication package must work for someone with a ZIP and no git.

A journal editor receives an archive. They have no clone, no remotes, no
credentials, and often no network on the machine that runs the replication. So
the package may not contain a submodule, may not require `git submodule update`,
and may not instruct anyone to fetch anything.

`git archive` writes a GITLINK for a submodule, not its contents, so every
submodule arrives as an empty directory unless the packaging step vendors it
back. This repository's rule named lib/repro-tools explicitly and copied it with
`cp -r`, which took the whole working tree including a 79 MB .venv full of
absolute symlinks into the author's home directory. The hardcoded-name half of
that bug shipped an empty directory in fire on 2026-08-19, where the package then
told its reader to run `git submodule update --init --recursive` -- an
instruction the recipient of an archive cannot follow.

These tests read the packaging rule rather than building the package, which takes
minutes. The build itself asserts the same properties at the end of the recipe;
this is the fast guard that fails a PR.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = (REPO_ROOT / "Makefile").read_text()


def test_vendoring_reads_gitmodules_rather_than_naming_submodules():
    """A hardcoded list silently omits the next submodule anyone adds."""
    assert "git config -f .gitmodules --get-regexp" in MAKEFILE, (
        "the packaging rule does not enumerate submodules from .gitmodules; "
        "a hardcoded name silently ships the next submodule as an empty directory"
    )


def test_every_submodule_would_be_vendored():
    """Read .gitmodules and confirm nothing is special-cased away."""
    gitmodules = REPO_ROOT / ".gitmodules"
    if not gitmodules.is_file():
        return
    paths = re.findall(r"^\s*path\s*=\s*(.+)$", gitmodules.read_text(), re.M)
    assert paths, ".gitmodules declares no submodule paths"
    # The rule must not mention any of them by name in the vendoring branch;
    # naming one is how the other got forgotten.
    vendor_block = MAKEFILE[MAKEFILE.index("Vendor EVERY submodule"):]
    vendor_block = vendor_block[: vendor_block.index("Verification:")]
    for p in paths:
        p = p.strip()
        assert f'cp -r {p} ' not in vendor_block, (
            f"{p} is vendored by name; use the .gitmodules loop so the next "
            "submodule is handled without editing this rule"
        )


def test_the_package_build_asserts_self_containment():
    """The recipe must check its own output, not merely intend to.

    Three properties, each a silent failure: an empty directory under lib/, a
    surviving .gitmodules, and a Makefile that still reports a missing submodule.
    """
    for probe in (
        "-type d -empty",
        ".gitmodules survived into the package",
        "symlinks in the package",
    ):
        assert probe in MAKEFILE, f"the packaging rule does not check for: {probe}"


def test_the_missing_machinery_warning_is_audience_aware():
    """`git submodule update` is not an instruction a ZIP recipient can follow.

    In a checkout it is exactly right, so the message branches on .gitmodules --
    which the packaging step deletes precisely because nothing is a submodule
    there any more.
    """
    assert "ifeq ($(wildcard .gitmodules),)" in MAKEFILE, (
        "the missing-machinery error does not distinguish a checkout from a "
        "replication package"
    )
    # Here it is a hard $(error), so a wrong instruction is the last thing the
    # recipient of a package would ever see.
    assert "please report it to the authors" in MAKEFILE
    assert "git clone --recursive" in MAKEFILE, "the checkout branch lost its advice"


def test_packaging_refuses_an_unchecked_out_submodule():
    """Vendoring an empty directory would produce a broken package quietly."""
    assert "is not checked out; run: git submodule update" in MAKEFILE


def test_the_package_build_rejects_symlinks():
    """Symlinks do not survive every reviewer's platform or unzip tool, and a
    `cp -r` of a submodule is how a virtualenv full of absolute symlinks got in."""
    assert "symlinks in the package" in MAKEFILE
