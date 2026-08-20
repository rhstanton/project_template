"""env/Manifest.toml is the pin that decides which package versions run.

Julia, not Python, computes the estimates in the projects this template is for,
so the Julia package set is the one whose drift changes results. Two distinct
ways that pin can be lost, each needing its own guard, and each of which
previously produced a SUCCESSFUL build:

1. THE MANIFEST IS MISSING.

   `Pkg.instantiate()` with no Manifest.toml does not fail -- it resolves from
   Project.toml and writes a new one. Project.toml admits ranges (any
   FixedEffectModels 1.x), so this silently installs whatever is current today
   and reports success. Guard ported from fire, 2026-08-18.

2. THE MANIFEST IS REWRITTEN.

   Pkg REWRITES a manifest it cannot honor rather than failing. On a runner with
   Julia 1.11.9, a committed 1.12.4 manifest was silently replaced by a 1.11.9
   one -- so comparing the manifest's julia_version against the running Julia
   found them in agreement. The evidence had been overwritten by the thing being
   checked. The check therefore asks git what was committed, and treats a dirty
   Manifest.toml after a build as the symptom.

These tests read the recipe rather than running Julia, so they work in CI where
instantiating takes minutes and a second Julia may not exist. What they pin is
that both guards are present and that the second asks git rather than the file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_MAKEFILE = REPO_ROOT / "env" / "Makefile"
MANIFEST = REPO_ROOT / "env" / "Manifest.toml"

# Use the project's own marker rather than a bespoke skipif. conftest.py already
# derives "does this project have Julia?" from env/Project.toml and skips marked
# tests accordingly, which is what bootstrap.py --python-only produces. Three of
# my new modules reinvented that check before I noticed it existed.
pytestmark = pytest.mark.julia


# Needs a built environment: env/Manifest.toml is produced by `make environment`
# and is deliberately not committed in this template (a manifest pins only for
# the Julia it was resolved with, which a template cannot control). Asserting it
# exists in an unbuilt tree tests the build, not the pin.
pytestmark = pytest.mark.needs_env

def recipe(target: str) -> str:
    text = ENV_MAKEFILE.read_text()
    match = re.search(
        rf"^{re.escape(target)}:.*\n((?:[\t ].*\n|\n)+)", text, re.MULTILINE
    )
    assert match, f"no recipe for {target}"
    return match.group(1)


class TestManifestIsCommitted:
    def test_manifest_exists(self):
        assert MANIFEST.is_file(), (
            "env/Manifest.toml is the pin that decides package versions; "
            "Project.toml alone admits ranges"
        )

    def test_this_template_deliberately_does_not_track_it(self):
        """A gitignored manifest pins nothing -- and here that is the point.

        This is an exception recorded in the replication constitution, not an
        oversight. A Julia manifest pins packages only for the Julia it was
        resolved with; on any other Julia, Pkg rewrites it rather than failing.
        A template cannot control which Julia a machine can install, because
        juliacall declares OpenSSL_jll as "<=python", tying the maximum usable
        Julia to the host Python. A manifest resolved on 1.12 is unusable on a
        runner capped at 1.11, and committing one made CI report "NOT
        REPRODUCING THE PINNED VERSIONS" on every single run.

        The rule stands for PROJECTS, which know their platforms; it cannot bind
        a template, which does not. The template ships the machinery and
        instructs each project to commit its own manifest.

        If this fails, either the exception was reversed deliberately -- update
        the constitution too -- or someone committed the manifest without
        noticing why it was not.
        """
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "env/Manifest.toml"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "env/Manifest.toml is now tracked in the TEMPLATE, reversing a "
            "documented exception; see the constitution's 'Compliance note, "
            "2026-08-16'."
        )

    def test_the_untracked_case_is_reported_rather_than_passed(self):
        """The manifest is untracked here, so the git check cannot verify.

        It must SAY so. Silence would read as a pass, and speaking up is the
        whole point of this check in a generated project.
        """
        body = recipe("julia-instantiate")
        assert "NOT verified" in body or "not verified" in body

    def test_manifest_records_the_julia_it_was_resolved_with(self):
        """julia_version is what makes a later rewrite explicable."""
        assert "julia_version" in MANIFEST.read_text()


class TestMissingManifestGuard:
    def test_instantiate_refuses_without_a_manifest(self):
        body = recipe("julia-instantiate")
        assert "Manifest.toml" in body and "exit 1" in body, (
            "julia-instantiate must refuse when the manifest is missing; "
            "Pkg.instantiate() would otherwise resolve fresh versions and "
            "report success"
        )

    def test_the_guard_runs_before_instantiate(self):
        """Order is the property: checking afterwards is checking nothing.

        By then Pkg has already written a manifest, so the file exists and the
        guard would pass while the pin has been replaced by a fresh resolution.
        """
        body = recipe("julia-instantiate")
        guard = body.index("Manifest.toml missing")
        # Match the COMMAND, not any mention: the explanatory comment above the
        # guard names Pkg.instantiate() too, and matching that made this test
        # fail against a correctly ordered recipe.
        instantiate = body.index("runjulia -e 'using Pkg; Pkg.instantiate()'")
        assert guard < instantiate, "the missing-manifest guard runs too late"

    def test_the_message_points_at_the_deliberate_path(self):
        body = recipe("julia-instantiate")
        assert "julia-relock" in body, (
            "tell the reader how to regenerate the pin deliberately"
        )


class TestRewrittenManifestCheck:
    def test_the_check_asks_git(self):
        """Not the manifest's own julia_version -- that gets overwritten."""
        body = recipe("julia-instantiate")
        assert "git diff" in body and "env/Manifest.toml" in body

    def test_the_check_runs_after_instantiate(self):
        """A rewrite can only be detected once the rewrite has had its chance."""
        body = recipe("julia-instantiate")
        instantiate = body.index("runjulia -e 'using Pkg; Pkg.instantiate()'")
        check = body.index("git diff")
        assert instantiate < check

    def test_it_does_not_compare_julia_version_against_the_running_julia(self):
        """The approach that looked obvious and could not work.

        If this ever reappears, the check has regressed to asking the file about
        itself after the file has been rewritten.
        """
        body = recipe("julia-instantiate")
        # Word-precise: the warning text contains "PINNED VERSIONS", so a bare
        # substring search for "VERSION" matches a correct recipe.
        assert not re.search(r"\bVERSION\b", body), (
            "comparing the manifest's julia_version to the running Julia cannot "
            "detect a rewrite -- Pkg makes them agree by rewriting"
        )

    def test_an_untracked_manifest_is_reported_as_unverified(self):
        """Silence would read as a pass."""
        body = recipe("julia-instantiate")
        assert "NOT verified" in body or "not verified" in body

    def test_the_warning_says_what_it_means_for_results(self):
        body = recipe("julia-instantiate")
        assert "NOT REPRODUCING THE PINNED VERSIONS" in body
