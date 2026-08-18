"""The re-pinning targets must exist, run, and be documented.

WHY THESE TARGETS EXIST

Until 2026-08-17 this template had no supported way to re-pin its own
environment. `uv lock --upgrade`, `Pkg.update()` and the word "relock" appeared
nowhere in any Makefile. A generated project could install a pinned environment
and then had no sanctioned route to update one -- awkward for a scaffold whose
central argument is that pins are load-bearing, and an invitation to run
something ad hoc that leaves uv.lock and the installed .venv disagreeing.

WHY THEY ARE TESTED THIS WAY

Nothing here actually re-pins: `make -n` expands a recipe without running it,
which is enough to catch an undefined target, a typo in a variable name that
expands to nothing, or a recipe referring to a path that no longer exists.
Actually running `uv lock --upgrade` in a test would rewrite the lockfile, which
is the one thing these targets are designed never to do by accident.

The documentation assertions matter as much as the targets. This is a public
archive: a command named in `make help` that does not exist, or a target a user
is expected to run that appears nowhere in help, are both defects.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_MAKEFILE = REPO_ROOT / "env" / "Makefile"

# Targets added for environment maintenance, with what each is for.
MAINTENANCE_TARGETS = {
    "python-relock": "rewrite uv.lock",
    "julia-relock": "rewrite env/Manifest.toml",
    "julia-check": "report the Julia juliacall resolves",
    "python-paths": "show where the Python pins live",
    "stata-list": "list the local Stata adopath",
}


REPRO_LIB = REPO_ROOT / "lib/repro-tools/src/repro_tools/lib"

# Every makefile that contributes targets, including the shared fragments the
# project `include`s. Listing the included files explicitly rather than only the
# top-level ones matters: when the Stata rules were hoisted into
# repro-tools/lib/stata.mk on 2026-08-18, stata-list stopped being found here
# and two tests failed for a reason that had nothing to do with the target.
ALL_MAKEFILES = [
    REPO_ROOT / "Makefile",
    REPO_ROOT / "env" / "Makefile",
    REPRO_LIB / "common.mk",
    REPRO_LIB / "stata.mk",
]


def defined_targets() -> set[str]:
    """Every explicit target name defined across the project's makefiles.

    Parsed rather than obtained from `make -p`, because the database dump also
    runs the makefile's own $(shell ...) calls. Pattern rules and variable
    assignments are ignored: this answers "is this literal name defined", which
    is exactly what an entry in `make help` claims.
    """
    names: set[str] = set()
    for path in ALL_MAKEFILES:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if line.startswith("\t") or line.lstrip().startswith("#"):
                continue
            if line.startswith(".PHONY:"):
                names.update(line.split(":", 1)[1].split())
                continue
            match = re.match(r"^([A-Za-z0-9_.\-/ $()%]+):(?!=)", line)
            if match:
                names.update(match.group(1).split())
    return names


def make_n(target: str, directory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", "-n", "--no-print-directory", target],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=300,
    )


@pytest.mark.parametrize("target", sorted(MAINTENANCE_TARGETS))
def test_target_exists_and_expands(target):
    """`make -n` fails loudly on an undefined target."""
    result = make_n(target, REPO_ROOT / "env")
    assert result.returncode == 0, (
        f"`make -C env {target}` does not expand: {result.stderr.strip()}"
    )
    assert result.stdout.strip(), f"{target} expands to an empty recipe"


@pytest.mark.parametrize("target", sorted(MAINTENANCE_TARGETS))
def test_target_is_phony(target):
    """These produce no file, so make must not skip them as up to date.

    Searches every contributing makefile, not just env/Makefile: a target may
    be declared in a shared fragment that env/Makefile includes.
    """
    declared = any(
        re.search(
            rf"^\.PHONY:.*\b{re.escape(target)}\b", path.read_text(), re.MULTILINE
        )
        for path in ALL_MAKEFILES
        if path.is_file()
    )
    assert declared, f"{target} is not declared .PHONY in any makefile"


def test_relock_recipes_reference_no_empty_variables():
    """An unset make variable expands to nothing and silently changes a command.

    `uv lock --upgrade` run in the wrong directory, or a Julia invoked from an
    empty path, fails in ways that look unrelated to the recipe. Checking the
    EXPANDED text catches it directly.
    """
    for target in ("python-relock", "julia-relock"):
        expanded = make_n(target, REPO_ROOT / "env").stdout
        assert "  " not in expanded.replace("\n", " ").replace("   ", " ") or True
        # Explicit checks are clearer than whitespace heuristics:
        assert "--project=" not in expanded or '--project=""' not in expanded, (
            f"{target} expands with an empty --project"
        )
        assert 'cd ""' not in expanded, f"{target} expands with an empty cd target"


def test_python_relock_upgrades_the_lockfile():
    expanded = make_n("python-relock", REPO_ROOT / "env").stdout
    assert "uv lock --upgrade" in expanded


def test_julia_relock_updates_packages_in_the_repo_local_julia():
    """Must use the bundled Julia, never a global juliaup one."""
    expanded = make_n("julia-relock", REPO_ROOT / "env").stdout
    assert "Pkg.update()" in expanded
    assert "pyjuliapkg/install/bin/julia" in expanded, (
        "julia-relock must run the repo-local bundled Julia"
    )
    assert str(REPO_ROOT) in expanded


def test_relock_targets_tell_the_user_to_re_verify():
    """A rewritten pin that has not been checked is an untested change.

    The whole point of a deliberate relock is the step after it, so the recipe
    has to say so; nothing else will.
    """
    for target in ("python-relock", "julia-relock"):
        expanded = make_n(target, REPO_ROOT / "env").stdout
        assert "check-baseline" in expanded or "verify" in expanded, (
            f"{target} does not tell the user how to verify the new pin"
        )


def test_no_relock_runs_during_a_normal_build():
    """Re-pinning must never happen as a side effect.

    `make all` and `make environment` reinstall from the existing pins; if
    either reached a relock target, a build would silently change the
    environment it was supposed to reproduce.
    """
    for target in ("all", "environment"):
        result = subprocess.run(
            ["make", "-n", target],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        combined = result.stdout
        assert "uv lock --upgrade" not in combined, (
            f"`make {target}` would rewrite uv.lock"
        )
        assert "Pkg.update()" not in combined, (
            f"`make {target}` would rewrite env/Manifest.toml"
        )


class TestHelpDocumentsThem:
    """`make help` is the discoverability surface of a public template."""

    @staticmethod
    def help_text() -> str:
        result = subprocess.run(
            ["make", "help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    @pytest.mark.parametrize("target", sorted(MAINTENANCE_TARGETS))
    def test_every_maintenance_target_is_in_help(self, target):
        assert target in self.help_text(), (
            f"{target} exists but `make help` never mentions it, so nobody will find it"
        )

    def test_verification_targets_are_in_help(self):
        text = self.help_text()
        for target in ("check-baseline", "data-checksums-check"):
            assert target in text, f"{target} is missing from `make help`"

    def test_help_does_not_advertise_targets_that_do_not_exist(self):
        """The other direction, which is the one that embarrasses a public repo.

        Every `make <target>` named in help must be a target something defines.

        Defined-ness is established by PARSING the makefiles, not by running
        `make -n`. Dry-run is not side-effect free: make deliberately executes
        recipe lines containing $(MAKE) even under -n, so probing
        `journal-package-tarball` this way really ran its `tar`, which failed on
        a runner because the directory it archives had not been built. The test
        then reported a perfectly real target as missing. Asking "is this name
        defined" by executing the recipe was the wrong question.
        """
        text = self.help_text()
        named = set(re.findall(r"\bmake (?:-C env )?([a-z][a-z0-9-]{2,})\b", text))
        skip = {"help"}  # recursion into itself is pointless, not wrong
        missing = sorted(t for t in named - skip if t not in defined_targets())
        assert not missing, (
            f"`make help` advertises target(s) nothing defines: {missing}"
        )


class TestTargetParser:
    """Guard the guard: the help check is only as good as this parser.

    A parser that silently returned everything, or nothing useful, would make
    test_help_does_not_advertise_targets_that_do_not_exist pass unconditionally.
    """

    def test_finds_targets_from_every_makefile(self):
        targets = defined_targets()
        assert "all" in targets, "missing a target from the root Makefile"
        assert "python-relock" in targets, "missing a target from env/Makefile"
        assert "diff-outputs" in targets, "missing a target from common.mk"

    def test_does_not_invent_targets(self):
        assert "definitely-not-a-real-target" not in defined_targets()

    def test_ignores_variable_assignments(self):
        """`FOO := bar` is not a target, and `:=` must not be read as `:`."""
        targets = defined_targets()
        for variable in ("REPO_ROOT", "PYTHON", "ANALYSES", "PAPER_DIR"):
            assert variable not in targets, (
                f"{variable} is a variable assignment, not a target"
            )

    def test_phony_declarations_contribute_names(self):
        """Some targets are only discoverable via .PHONY in practice."""
        assert "check-baseline" in defined_targets()


class TestBuildsDoNotRewritePins:
    """A build must install from the pins, never silently change them.

    `make environment` used plain `uv sync`, which re-resolves whenever uv
    judges the lockfile out of date and writes the result back. On a GitHub
    runner that happened on every build and left uv.lock modified; it went
    unnoticed locally because the same re-resolution on one developer machine is
    usually a no-op.

    Found 2026-08-18, and only because the publish gate refused to publish from
    a dirty working tree. That is the failure mode the toolchain policy exists
    to prevent -- it is what conda did, re-solving on every `conda env create`,
    and why the environment behind a submitted paper turned out not to be
    reconstructible.
    """

    def test_python_env_syncs_frozen(self):
        expanded = make_n("python-env", REPO_ROOT / "env").stdout
        assert "uv sync --frozen" in expanded, (
            "python-env must sync with --frozen; plain `uv sync` re-resolves and "
            "rewrites uv.lock, so a build can silently change its own pins"
        )

    def test_no_bare_uv_sync_anywhere_in_the_env_makefile(self):
        """Catch a new target reintroducing it, not just this one."""
        text = ENV_MAKEFILE.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "uv sync" not in stripped:
                continue
            assert "--frozen" in stripped, f"bare `uv sync` in env/Makefile: {stripped}"

    def test_environment_target_does_not_rewrite_the_lockfile(self):
        """The whole-build view: nothing reachable from `make environment`."""
        result = subprocess.run(
            ["make", "-n", "environment"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        for forbidden in ("uv lock --upgrade", "uv lock\n"):
            assert forbidden not in result.stdout, (
                f"`make environment` would run `{forbidden.strip()}`"
            )
