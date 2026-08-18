"""runstata must find the do-file, detect failure, and never hang.

Three properties, each corresponding to something that was actually broken.
fire had all three; this template had one of them (the path bug) and reported
the resulting failure clearly enough that it looked like the do-file's fault.

1. THE DO-FILE IS RESOLVED BEFORE THE `cd`.

   runstata cd's to the repository root so adopath and relative data paths
   behave predictably. It then handed Stata the path it was given -- so
   `runstata examples/foo.do` from env/ asked Stata for examples/foo.do at the
   REPO ROOT and failed with r(601), a file-not-found presented as though the
   do-file were broken.

2. A FAILING DO-FILE IS DETECTED.

   Stata batch mode exits 0 for a do-file that failed, so the exit status cannot
   be trusted. execute.ado runs the do-file under `capture noisily`, records
   _rc, and prints "Error in do-file (return code: N)"; runstata greps for that.
   Without it a broken analysis is indistinguishable from a good one.

3. IT CANNOT HANG.

   With stdin left attached, an aborted do-file leaves Stata waiting for input
   forever. Measured in fire 2026-08-18: a deliberately broken do-file was still
   running after 300 seconds. `</dev/null` plus `timeout` prevent it.

Tests that need Stata skip without it; the ones that read the script's text run
anywhere, which is what makes this useful in CI where Stata is absent.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNSTATA = REPO_ROOT / "env" / "scripts" / "runstata"
EXECUTE_ADO = REPO_ROOT / "env" / "scripts" / "execute.ado"

# bootstrap.py --remove-stata (and --python-only) deletes env/scripts/runstata
# outright, and the "Bootstrap variants" workflow builds exactly that project.
# Two different absences have to be distinguished here:
#
#   * the SCRIPT is gone      -> this whole file has no subject; skip it.
#   * the BINARY is missing   -> the script exists and its text can still be
#                               checked; only the tests that invoke Stata skip.
#
# Getting that wrong the first time turned every test in this module into an
# ERROR on the no-stata variant, which is a worse signal than a failure: it
# looks like the suite is broken rather than the project legitimately lacking
# a feature.
# conftest.py derives Stata support from env/stata-packages.txt and skips
# marked tests when bootstrap has pruned it.
pytestmark = pytest.mark.stata

# Configured-for-Stata and able-to-run-Stata are different questions: CI commits
# the ado files but has no stata-mp.
needs_stata = pytest.mark.stata_binary


@pytest.fixture(scope="module")
def script() -> str:
    return RUNSTATA.read_text()


class TestScriptShape:
    """Readable without Stata, so these run everywhere."""

    def test_sources_env_sh(self, script):
        """One environment for every entry point, resolved in one place."""
        assert "source" in script and "env.sh" in script

    def test_closes_stdin(self, script):
        """Otherwise an aborted do-file waits for input forever."""
        assert "</dev/null" in script

    def test_uses_a_timeout(self, script):
        assert "timeout" in script and "STATA_TIMEOUT" in script

    def test_checks_for_the_error_marker(self, script):
        """The exit status cannot detect a failed do-file; this can."""
        assert "Error in do-file (return code:" in script

    def test_uses_pipestatus_not_the_pipeline_status(self, script):
        """`| tee` would otherwise mask Stata's real exit code."""
        assert "PIPESTATUS" in script

    def test_resolves_the_do_file_before_cd(self, script):
        """The order is the property; asserting both lines exist is not enough."""
        resolve = script.index('dirname -- "$DO_FILE"')
        change_dir = script.index('cd -- "$REPRO_PROJECT_ROOT"')
        assert resolve < change_dir, (
            "the do-file path must be made absolute BEFORE cd, or a "
            "caller-relative path resolves against the repo root"
        )

    def test_guards_a_missing_argument(self, script):
        """Under `set -u` a bare $1 aborts with an unbound-variable error."""
        assert "${1:-}" in script or "$# -lt 1" in script

    def test_reports_a_missing_stata_binary(self, script):
        assert "command -v stata-mp" in script


class TestExecuteAdo:
    def test_captures_the_return_code(self):
        """Plain `do` aborts the program, so the exit below never runs."""
        text = EXECUTE_ADO.read_text()
        assert "capture noisily do" in text

    def test_prints_the_marker_runstata_greps_for(self):
        """The two files agree on one string; if they drift, failures vanish."""
        assert "Error in do-file (return code:" in EXECUTE_ADO.read_text()
        assert "Error in do-file (return code:" in RUNSTATA.read_text()


@needs_stata
class TestAgainstRealStata:
    def test_usage_without_arguments(self):
        result = subprocess.run(
            [str(RUNSTATA)], capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 1
        assert "Usage" in result.stderr

    def test_a_working_do_file_succeeds(self):
        result = subprocess.run(
            [str(RUNSTATA), "env/examples/sample_stata.do"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert result.returncode == 0, result.stdout[-2000:]

    def test_a_relative_path_works_from_a_subdirectory(self):
        """The regression: this used to fail with r(601)."""
        result = subprocess.run(
            [str(RUNSTATA), "examples/sample_stata.do"],
            cwd=REPO_ROOT / "env",
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert result.returncode == 0, (
            "a caller-relative do-file path was not resolved before the cd\n"
            + result.stdout[-2000:]
        )

    def test_a_failing_do_file_fails(self, tmp_path):
        """And promptly: this is the case that used to hang forever."""
        broken = tmp_path / "broken.do"
        broken.write_text("regress no_such_variable_xyz\n")
        result = subprocess.run(
            [str(RUNSTATA), str(broken)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode != 0, (
            "a do-file that errored was reported as success; Stata batch mode "
            "exits 0, so the error marker is what has to catch this"
        )
        assert "failed with return code" in result.stderr

    def test_the_timeout_is_honored(self, tmp_path):
        """A stuck run must die rather than block a build indefinitely."""
        slow = tmp_path / "slow.do"
        slow.write_text("sleep 30000\n")  # Stata's sleep is milliseconds
        result = subprocess.run(
            [str(RUNSTATA), str(slow)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
            env={**__import__("os").environ, "STATA_TIMEOUT": "5"},
        )
        assert result.returncode == 124
        assert "timed out" in result.stderr
