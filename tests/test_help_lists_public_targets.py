"""Every public target must appear in `make help`.

WHY THIS EXISTS

A template's targets are its interface. One that `make help` never names is
findable only by reading the Makefile -- which is the thing a template exists to
save people from.

Nothing tied the help listing to the targets that actually exist, and on
2026-08-21 eleven were missing from it, including most of the template-only
workflow:

    instance, instance-list, instance-clean   the disposable bootstrap instances
    test-variants                             the pruned-variant suite
    remove-analysis                           the guarded analysis remover
    publish-figures, publish-tables, publish-files
    check-baseline-record, list-analyses-verbose

The sibling `fire` repository had the same gap, found the same day: `peer-hoaonly`
had no top-level target at all while three documents called the variant
"opt-in", naming no way to opt in.

WHAT THIS DOES NOT CHECK

That each description is accurate. `tests/test_documented_commands_exist.py`
covers the other direction -- every command named in the docs must resolve --
so between them a target and its documentation cannot drift apart unnoticed.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"

# Targets deliberately absent from help, each with the reason. A bare list would
# grow silently; pairing each with a justification makes an addition a decision.
EXEMPT = {
    "help": "it is the listing itself",
    "default": "the no-argument target, which prints brief guidance",
}


def phony_targets() -> set[str]:
    """Every target declared .PHONY in the top-level Makefile.

    `.PHONY` is the closest thing the file has to a declaration of intent: a
    name listed there is one the author meant to be invoked.

    Names containing `$` are dropped. The Makefile has a `define` block that
    declares `.PHONY: $(1)` for a generated per-analysis target, and `$(1)` is a
    macro parameter rather than a target anyone can type.
    """
    text = MAKEFILE.read_text()
    names: set[str] = set()
    for line in re.findall(r"^\.PHONY:(.*)$", text, re.M):
        # Trailing `## comment` annotations are used for grouping in some rules.
        names.update(line.split("##")[0].split())
    return {n for n in names if "$" not in n}


def help_output() -> str:
    proc = subprocess.run(
        ["make", "help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, f"`make help` failed:\n{proc.stderr}"
    return proc.stdout


def test_there_are_phony_targets_to_check():
    """Guard the guard: a parse returning nothing would pass every check below."""
    found = phony_targets()
    assert len(found) > 25, (
        f"parsed only {len(found)} .PHONY targets from {MAKEFILE}; the check "
        "below iterates that set and would pass trivially"
    )


def test_help_emits_no_make_warnings():
    """`make help` must be clean on stderr.

    Until 2026-08-21 it opened with "warning: overriding recipe for target
    'bump-version'" -- a local recipe shadowed by the one in tools.mk, included
    after it. The local one had never run since the lib split.
    """
    proc = subprocess.run(
        ["make", "help"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=300
    )
    warnings = [ln for ln in proc.stderr.splitlines() if "warning:" in ln]
    assert not warnings, "make emitted warnings:\n" + "\n".join(warnings)


def test_every_exemption_names_a_real_target():
    """An exemption for a target that no longer exists hides a later addition of
    the same name, and reads as though the omission had been considered."""
    stale = sorted(set(EXEMPT) - phony_targets())
    assert not stale, f"EXEMPT names targets that do not exist: {stale}"


@pytest.mark.parametrize("target", sorted(phony_targets()))
def test_target_appears_in_help(target):
    if target in EXEMPT:
        pytest.skip(f"exempt: {EXEMPT[target]}")
    assert target in help_output(), (
        f"`{target}` is a .PHONY target but `make help` never names it. Either "
        f"add it to the help listing or record why it is internal in EXEMPT."
    )
