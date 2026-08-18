"""Tests for the Julia helpers in test_environment.py.

These guard the test suite against itself. Two tests in test_environment.py
could not fail before 2026-08-17, and both failures were in the helper logic
rather than in the thing being tested:

  * availability was inferred from the failure of the command under test, so a
    broken environment reported "Julia not available" and skipped;
  * "is CUDA a dependency?" was answered with `"CUDA" not in project_toml_text`,
    a substring search over the whole file. The only occurrences of "CUDA" in
    env/Project.toml are inside a comment saying CUDA is deliberately NOT a
    dependency -- so the guard read a denial as a declaration.

A helper that answers those questions wrongly turns every test built on it into
decoration, silently. Hence a dedicated file.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from tests.test_environment import (
    REPO_ROOT,
    julia_project_deps,
    require_julia,
    run_julia,
)

JULIA_PROJECT_TOML = REPO_ROOT / "env" / "Project.toml"

# bootstrap.py --remove-julia deletes env/Project.toml and env/scripts/runjulia,
# and the CI "Bootstrap variants" workflow builds exactly that variant. These
# tests describe the Julia environment, so in a project with no Julia they have
# no subject -- skipping is correct, whereas failing would mean a legitimately
# pruned project could never have a green suite.
needs_julia_project = pytest.mark.skipif(
    not JULIA_PROJECT_TOML.is_file(),
    reason="env/Project.toml absent (Julia pruned by bootstrap.py --remove-julia)",
)


@needs_julia_project
class TestJuliaProjectDeps:
    """julia_project_deps() must read declarations, not prose."""

    def test_returns_the_declared_dependencies(self):
        deps = julia_project_deps()
        assert "FixedEffectModels" in deps
        assert "DataFrames" in deps

    def test_cuda_is_not_reported_as_a_dependency(self):
        """The exact bug: CUDA appears only in a comment denying it is one.

        If this ever fails, check whether CUDA was genuinely added to
        env/Project.toml (in which case the GPU design changed and
        docs/platform_compatibility.md needs updating too) or whether the
        helper has regressed to substring matching.
        """
        assert "CUDA" not in julia_project_deps()

    def test_the_file_really_does_mention_cuda(self):
        """Guard the guard.

        Without this, deleting the comment would make the test above pass for
        the wrong reason and the regression would stop being covered.
        """
        text = (REPO_ROOT / "env" / "Project.toml").read_text()
        assert "CUDA" in text, (
            "env/Project.toml no longer mentions CUDA, so the substring-matching "
            "regression is no longer reproducible here; re-point this test"
        )

    def test_compat_entries_are_not_mistaken_for_deps(self):
        """[compat] names a package without depending on it.

        `julia` is the clearest case: it is always in [compat] and is never a
        package to load.
        """
        assert "julia" not in julia_project_deps()

    def test_parses_a_synthetic_project_toml(self, tmp_path, monkeypatch):
        """Behavior is pinned against a file whose contents we control."""
        project = tmp_path / "env"
        project.mkdir()
        (project / "Project.toml").write_text(
            textwrap.dedent("""
                # CUDA is intentionally not a dependency.
                [deps]
                Real = "00000000-0000-0000-0000-000000000001"

                [compat]
                Real = "1"
                julia = "1.10"
            """)
        )
        monkeypatch.setattr("tests.test_environment.REPO_ROOT", tmp_path)
        assert julia_project_deps() == {"Real"}

    def test_missing_project_toml_yields_empty_set(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tests.test_environment.REPO_ROOT", tmp_path)
        assert julia_project_deps() == set()


class TestRequireJulia:
    """require_julia() must skip only for genuine absence."""

    def test_skips_when_the_wrapper_is_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "tests.test_environment.RUNJULIA", tmp_path / "no-such-runjulia"
        )
        with pytest.raises(pytest.skip.Exception, match="runjulia wrapper not found"):
            require_julia()

    def test_skips_when_julia_cannot_start(self, monkeypatch, tmp_path):
        """A wrapper that exists but fails is 'Julia not installed', not a pass.

        RUNJULIA is pointed at a real file so the earlier wrapper-existence
        check passes and this exercises the branch it is about. Without that,
        the test silently measured the wrong branch in any project where Julia
        had been pruned -- which is precisely what happened in the no-julia
        bootstrap variant.
        """
        wrapper = tmp_path / "runjulia"
        wrapper.write_text("#!/bin/sh\nexit 1\n")
        wrapper.chmod(0o755)
        monkeypatch.setattr("tests.test_environment.RUNJULIA", wrapper)
        monkeypatch.setattr(
            "tests.test_environment.run_julia",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="julia: command not found"
            ),
        )
        with pytest.raises(pytest.skip.Exception, match="cannot start"):
            require_julia()

    def test_does_not_skip_when_julia_works(self, monkeypatch, tmp_path):
        """The property that makes every later assertion meaningful."""
        wrapper = tmp_path / "runjulia"
        wrapper.write_text("#!/bin/sh\nexit 0\n")
        wrapper.chmod(0o755)
        monkeypatch.setattr("tests.test_environment.RUNJULIA", wrapper)
        monkeypatch.setattr(
            "tests.test_environment.run_julia",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[], returncode=0, stdout="1.12.4", stderr=""
            ),
        )
        require_julia()  # must not raise

    def test_probe_does_not_touch_project_dependencies(self):
        """Availability must not be confounded with what callers go on to test.

        require_julia() runs `print(VERSION)`. If it ever probed with a package
        load, a missing package would masquerade as a missing Julia -- which is
        precisely the bug this file exists to prevent.
        """
        source = Path(REPO_ROOT / "tests" / "test_environment.py").read_text()
        body = source.split("def require_julia()", 1)[1].split("\ndef ", 1)[0]
        assert "print(VERSION)" in body
        assert "using " not in body


class TestRunJulia:
    """run_julia() must go through the wrapper, never a bare interpreter."""

    def test_invokes_the_repo_wrapper(self):
        source = Path(REPO_ROOT / "tests" / "test_environment.py").read_text()
        body = source.split("def run_julia(", 1)[1].split("\ndef ", 1)[0]
        assert "RUNJULIA" in body, (
            "run_julia must call env/scripts/runjulia; a bare `julia` would "
            "resolve packages from a different project or the user's global depot"
        )

    def test_returns_output_from_a_real_run(self):
        require_julia()
        result = run_julia('print("marker-7f3a")')
        assert result.returncode == 0, result.stderr
        assert "marker-7f3a" in result.stdout
