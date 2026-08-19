"""The Julia bootstrap has three failure modes it must survive.

env/scripts/install_julia.py sets up Julia through juliacall. Three things it
does are load-bearing and easy to lose in a refactor, and each corresponds to a
breakage that actually happened.

1. JULIA_LOAD_PATH IS CLEARED BEFORE THE BOOTSTRAP.

   env.sh exports JULIA_LOAD_PATH so both projects are visible at run time, and
   runpython sources it before this script runs. But that variable REPLACES the
   load path wholesale, overriding the `--project=<depot>` juliapkg passes when
   it bootstraps PythonCall -- so the bootstrap resolves against env/ instead.

   The two projects are pinned differently on purpose: env/Manifest.toml pins a
   tree, the juliapkg project re-resolves against the live registry. They agree
   until the registry moves. In fire, pixi_jll went 0.63.2+0 -> 0.76.2+0 on
   2026-08-13 and a clean clone died with "Package pixi_jll is required but does
   not seem to be installed" -- it WAS installed, at a version the manifest did
   not name. A time bomb, not a flake: it passes until the registry moves.

2. THE COMMITTED MANIFEST IS RESTORED, EVEN IF THE BUILD DIES.

   Manifest.toml is moved aside for the juliacall import (it references
   PythonCall, which the depot does not have yet) and moved back afterwards.
   That leaves a window: a build interrupted in between -- Ctrl-C, a crash, a
   killed CI job -- leaves the repository with NO Manifest.toml and a stray
   Manifest.toml.backup. The pin is the file the whole arrangement exists to
   protect. An atexit handler now closes that window.

   An earlier version DELETED the manifest instead of moving it, "to let
   Pkg.instantiate() generate a fresh one" -- silently discarding the committed
   pin on every build.

3. A BOOTSTRAP THAT RESOLVES WITHOUT INSTALLING IS REPAIRED, NOT FATAL.

   juliapkg does registry-update, add, resolve and precompile in one command. If
   the registry moves mid-flight, precompile runs against a dependency recorded
   but not installed. Julia's own error names the fix, and Pkg.instantiate() is
   idempotent, so the script runs it and retries once.

WHAT THESE TESTS DO NOT DO

They read the script rather than running it: a real exercise needs a clean depot
and takes minutes, and the crash path needs the process killed at a specific
moment. Structure is what a refactor loses, and structure is what is asserted.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / "env" / "scripts" / "install_julia.py"

pytestmark = pytest.mark.julia


@pytest.fixture(scope="module")
def source() -> str:
    return INSTALLER.read_text()


class TestLoadPathIsolation:
    def test_load_path_is_cleared(self, source):
        assert 'os.environ.pop("JULIA_LOAD_PATH", None)' in source

    def test_it_is_cleared_before_the_juliacall_import(self, source):
        """Order is the whole property. Clearing it afterwards does nothing."""
        clear = source.index('os.environ.pop("JULIA_LOAD_PATH", None)')
        first_import = source.index("from juliacall import Main as jl")
        assert clear < first_import, (
            "JULIA_LOAD_PATH must be cleared BEFORE juliacall is imported; "
            "the bootstrap happens during that import"
        )

    def test_the_reason_is_recorded(self, source):
        """This looks removable to anyone who does not know the history."""
        assert "pixi_jll" in source


class TestManifestIsProtected:
    def test_manifest_is_moved_not_deleted(self, source):
        assert "shutil.move(manifest_path, manifest_backup)" in source
        assert "os.remove(manifest_path)" not in source
        assert "os.unlink(manifest_path)" not in source

    def test_an_atexit_handler_restores_it(self, source):
        assert "atexit.register(_restore_manifest)" in source

    def test_the_handler_is_registered_immediately_after_the_move(self, source):
        """Registering it later would leave exactly the window it closes."""
        move = source.index("shutil.move(manifest_path, manifest_backup)")
        register = source.index("atexit.register(_restore_manifest)")
        first_import = source.index("from juliacall import Main as jl")
        assert move < register < first_import, (
            "the handler must be registered after the move and before anything "
            "that can fail"
        )

    def test_the_handler_does_not_clobber_a_restored_manifest(self, source):
        """The success path restores first; atexit must then be a no-op."""
        tree = ast.parse(source)
        func = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_restore_manifest"
        )
        body = ast.unparse(func)
        assert "not os.path.exists(manifest_path)" in body


class TestRetryPathKeepsThePin:
    """The recovery path must not destroy what it is recovering.

    A separate retry, further down, cleans up after a failed package install and
    used to `os.remove(manifest_path)` so the retry could resolve afresh. On a
    generated project -- which commits its manifest -- that silently destroyed
    the pin and rebuilt against whatever the registry offered that day. The
    build then usually succeeded, against different package versions, having
    printed only "Retrying after cleanup".

    fire had the identical bug, and there it mattered more: its manifest is
    committed and Julia computes every coefficient in the paper. Both fixed
    2026-08-18 by moving rather than deleting.
    """

    def test_the_retry_moves_rather_than_deletes(self, source):
        assert "os.remove(manifest_path)" not in source, (
            "the retry path must not delete the manifest; a project that commits "
            "it loses its pin to a transient install failure"
        )
        assert ".before-retry" in source

    def test_it_warns_that_the_result_is_not_a_reproduction(self, source):
        """Silence here is what made the old behavior dangerous."""
        assert "does NOT reproduce the committed pin" in source

    def test_it_says_how_to_restore(self, source):
        assert "julia-instantiate" in source


class TestBootstrapRepair:
    def test_the_repair_function_exists(self, source):
        tree = ast.parse(source)
        names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        assert "_retry_after_instantiate" in names

    def test_it_runs_instantiate(self, source):
        assert "Pkg.instantiate(); Pkg.precompile()" in source

    def test_it_retries_the_import_only_once(self, source):
        """A loop here would hide a genuinely broken environment behind delay."""
        assert source.count("from juliacall import Main as jl") == 2

    def test_it_clears_half_initialized_modules_before_retrying(self, source):
        """Without this the retry re-uses the failed import from sys.modules."""
        assert 'in ("juliacall", "juliapkg")' in source

    def test_it_gives_up_when_nothing_was_installed(self, source):
        """If there is no Julia yet, this is a different failure entirely."""
        assert "if not os.path.isfile(julia):" in source


class TestNoStaleCondaClaims:
    def test_does_not_claim_a_conda_environment(self, source):
        """This project has used uv since 2026-05-27."""
        assert "conda environment Python" not in source
