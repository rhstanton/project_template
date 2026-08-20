"""Every repro-tools command the Makefiles invoke must accept the flags passed.

WHY

The Makefiles were written against a CLI that did not exist, and nothing noticed
for months because `$(PYTHON) -m repro_tools.cli` had no module entry point: it
imported the module, ignored every argument, and exited 0. Make saw success and
touched the stamps recording the work as done.

When the entry point was fixed on 2026-08-17, four separate mismatches surfaced
at once, all of them long-standing:

  * `$(REPRO_CHECK) --pre-submit` -- repro-check has no such flag; it IS the
    pre-submission checklist.
  * `$(REPRO_CHECK) --allow-dirty ... --require-not-behind ... --artifacts ...`
    in the publish target -- all of those belong to repro-publish.
  * `$(REPRO_PUBLISH) --kind figures --analyses "$*"` -- `analyses` is a
    required subcommand and its names are positional; --kind was not exposed at
    all.
  * `$(REPRO_PUBLISH) --files "..."` -- likewise positional.

This test compares what the Makefiles pass against what each command's own
--help reports, so the two cannot drift apart again silently.

WHAT IT CHECKS

Long option names only. Nothing is executed, so nothing publishes or writes.
That is enough to catch every error above, all of which were names that did not
exist. It does not verify that a command would succeed against real data.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# Globbed, not listed. When the Stata rules were hoisted into
# repro-tools/lib/stata.mk on 2026-08-18, stata-list stopped being found here and
# two tests failed for a reason that had nothing to do with the target. The fix
# then was to add stata.mk to the list -- and on 2026-08-19, when common.mk was
# split into tools/repro/git/layout.mk, twenty-four tests failed the same way for
# the same reason. Enumerating the shared fragments makes every reorganization of
# them look like a product bug. Glob instead.
MAKEFILES = [
    REPO_ROOT / "Makefile",
    *sorted((REPO_ROOT / "lib/repro-tools/src/repro_tools/lib").glob("*.mk")),
]

VAR_TO_COMMAND = {
    "REPRO_CHECK": "check",
    "REPRO_PUBLISH": "publish",
    "REPRO_COMPARE": "compare",
    "REPRO_SYSINFO": "sysinfo",
    "REPRO_REPORT": "report",
}

RUNPYTHON = REPO_ROOT / "env" / "scripts" / "runpython"


# Needs a built environment: every case runs the repro_tools CLI to ask whether
# a flag exists. Without .venv the invocation fails, which reads as "this flag is
# wrong" rather than "there is no interpreter".
pytestmark = pytest.mark.needs_env

def invocations() -> list[tuple[str, str, str]]:
    """(makefile, variable, folded command line) for each $(REPRO_*) call."""
    found = []
    for path in MAKEFILES:
        if not path.is_file():
            continue
        # Fold make/shell line continuations so one call is one line.
        text = re.sub(r"\\\n\s*", " ", path.read_text())
        for line in text.splitlines():
            stripped = line.strip().lstrip("@").strip()
            if stripped.startswith("#"):
                continue
            for var in VAR_TO_COMMAND:
                if stripped.startswith(f"$({var})"):
                    found.append((path.name, var, stripped))
                    break
    return found


def help_text(command: str, subcommand: str | None = None) -> str:
    args = [command] + ([subcommand] if subcommand else []) + ["--help"]
    result = subprocess.run(
        [str(RUNPYTHON), "-m", "repro_tools.cli", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )
    assert result.returncode == 0, f"`{' '.join(args)}` failed:\n{result.stderr}"
    return result.stdout


def test_makefiles_contain_invocations_to_check():
    """Guard the guard: a parser finding nothing would pass silently."""
    found = invocations()
    assert len(found) >= 5, (
        f"only found {len(found)} $(REPRO_*) invocations across "
        f"{[p.name for p in MAKEFILES]}; the parser is probably broken"
    )


@pytest.mark.skipif(not RUNPYTHON.exists(), reason="runpython wrapper not found")
@pytest.mark.parametrize(
    "makefile,var,line",
    invocations(),
    ids=[f"{m}:{v}" for m, v, _ in invocations()],
)
def test_every_flag_passed_is_a_flag_that_exists(makefile, var, line):
    command = VAR_TO_COMMAND[var]
    tokens = line.split()

    subcommand = None
    if len(tokens) > 1 and tokens[1] in {"analyses", "files"}:
        subcommand = tokens[1]

    text = help_text(command, subcommand)

    for token in tokens[1:]:
        if not token.startswith("--"):
            continue
        option = token.split("=", 1)[0]
        if "$" in option:  # a make variable holding a value, not an option name
            continue
        assert option in text, (
            f"{makefile} passes `{option}` to `{command}"
            f"{' ' + subcommand if subcommand else ''}`, which does not accept it.\n"
            f"  invocation: {line}\n"
            f"  real usage: {text.splitlines()[0] if text else '(none)'}"
        )


@pytest.mark.skipif(not RUNPYTHON.exists(), reason="runpython wrapper not found")
def test_publish_always_names_a_subcommand():
    """`repro-publish` requires `analyses` or `files`; omitting it is an error.

    The Makefile omitted it for months. That only looked harmless because the
    module ignored everything it was given.
    """
    for makefile, var, line in invocations():
        if var != "REPRO_PUBLISH":
            continue
        tokens = line.split()
        assert len(tokens) > 1 and tokens[1] in {"analyses", "files"}, (
            f"{makefile}: `{line}` does not name a publish subcommand"
        )


@pytest.mark.skipif(not RUNPYTHON.exists(), reason="runpython wrapper not found")
def test_publish_always_passes_project_root():
    """--project-root is required, and every documented example once omitted it."""
    for makefile, var, line in invocations():
        if var != "REPRO_PUBLISH":
            continue
        assert "--project-root" in line, (
            f"{makefile}: `{line}` omits the required --project-root"
        )


@pytest.mark.skipif(not RUNPYTHON.exists(), reason="runpython wrapper not found")
def test_module_invocation_is_not_a_silent_success():
    """The root cause, asserted directly from the project that suffered it.

    If this ever passes an impossible flag with status 0 again, every target
    built on $(REPRO_*) has quietly become a no-op.
    """
    result = subprocess.run(
        [
            str(RUNPYTHON),
            "-m",
            "repro_tools.cli",
            "check",
            "--nonsense-flag-that-cannot-exist",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )
    assert result.returncode != 0, (
        "`python -m repro_tools.cli check --nonsense-flag` exited 0; the CLI is "
        "not parsing arguments, so make targets using it do nothing and report "
        "success"
    )
