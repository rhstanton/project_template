"""A journal data editor must be able to build this without uv.

The replication constitution is explicit:

    "uv is how the authors *author* the environment. It must never be what a
     journal data editor is required to install."

and requires uv.lock to be exported to hash-pinned requirements.txt files that
plain pip can install, with that path tested with uv absent from PATH.

This template shipped NEITHER target until 2026-08-18, so every project
generated from it violated that clause on arrival: the only documented way to
build the environment needed uv. Both were ported from fire.

THE PART THAT IS EASY TO GET WRONG

"Tested with uv absent" reads as a test of INSTALLATION, and installation is not
the claim. Measured here on 2026-08-18: a venv built from the export alone
installed 149 packages with hashes verified, and then could not run anything --
`import repro_tools` raised ModuleNotFoundError, because the export deliberately
omits repro-tools (a local path, meaningless to pip elsewhere) while the
analysis imports it. Installing succeeded; replicating did not.

So python-env-pip also installs the local submodule with --no-deps, and the
end-to-end check is that an analysis RUNS, not that packages appear.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_MAKEFILE = REPO_ROOT / "env" / "Makefile"
REQUIREMENTS = REPO_ROOT / "env" / "requirements" / "base.txt"

pytestmark = pytest.mark.skipif(
    not ENV_MAKEFILE.is_file(), reason="env/Makefile absent"
)


# Every test here shells out through env/scripts/, so it needs a built
# environment. Marked rather than left to fail: without `make environment` the
# wrapper reports "Python env not found", which reads like a bug in the test.
pytestmark = pytest.mark.needs_env


def recipe(target: str) -> str:
    text = ENV_MAKEFILE.read_text()
    match = re.search(
        rf"^{re.escape(target)}:.*\n((?:[\t ].*\n|\n)+)", text, re.MULTILINE
    )
    assert match, f"no recipe for {target}"
    return match.group(1)


class TestTargetsExist:
    """Without these, a generated project cannot be replicated without uv."""

    def test_python_export_exists(self):
        assert re.search(r"^python-export:", ENV_MAKEFILE.read_text(), re.MULTILINE)

    def test_python_env_pip_exists(self):
        assert re.search(r"^python-env-pip:", ENV_MAKEFILE.read_text(), re.MULTILINE)

    def test_the_pip_path_never_invokes_uv(self):
        """It is the path for someone who does not have uv."""
        body = recipe("python-env-pip")
        invocations = []
        for line in body.splitlines():
            stripped = line.strip()
            # Prose is not an invocation. The recipe legitimately says
            # "(uv was not used)" in its final message, and the staleness check
            # legitimately runs `command -v uv` to decide whether it CAN compare
            # against uv.lock -- neither builds anything with uv.
            if stripped.startswith(("#", "echo ", "@echo ")) or "echo " in stripped:
                continue
            if "command -v uv" in stripped:
                continue
            if re.search(r"(^|[^-\w./])uv\s", stripped):
                invocations.append(stripped)
        assert not invocations, f"python-env-pip calls uv: {invocations}"


class TestTheExport:
    def test_export_is_committed(self):
        """A replicator gets it from the repository, not by running uv."""
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "env/requirements/base.txt"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            "env/requirements/base.txt is not tracked, so a data editor without "
            "uv has nothing to install from"
        )

    def test_export_is_hash_pinned(self):
        """Without hashes it is a version list, not a reproducible install."""
        text = REQUIREMENTS.read_text()
        assert text.count("--hash=sha256:") > 100

    def test_export_leaks_no_local_paths(self):
        """file:// URLs from this machine are meaningless to anyone else."""
        text = REQUIREMENTS.read_text()
        assert "file://" not in text
        assert str(REPO_ROOT) not in text

    def test_install_requires_hashes(self):
        body = recipe("python-env-pip")
        assert "--require-hashes" in body


class TestStaleness:
    def test_refuses_an_export_older_than_the_lock(self):
        """Otherwise it silently builds an environment nobody pinned."""
        body = recipe("python-env-pip")
        assert "-nt" in body and "uv.lock" in body

    def test_refuses_to_overwrite_an_existing_venv(self):
        """Mixing pip into a uv-built venv yields one matching neither."""
        body = recipe("python-env-pip")
        assert "already exists" in body and "FORCE" in body


class TestItCanActuallyRun:
    """Installing is not the claim; running is."""

    def test_local_package_is_installed_too(self):
        body = recipe("python-env-pip")
        assert "--no-deps" in body and "lib/repro-tools" in body, (
            "the export omits repro-tools as a local path, so without this the "
            "environment installs cleanly and then cannot import it"
        )

    def test_local_install_uses_no_deps(self):
        """Resolving its deps would pull unpinned versions into a pinned env."""
        body = recipe("python-env-pip")
        line = next(ln for ln in body.splitlines() if "lib/repro-tools" in ln)
        assert "--no-deps" in line

    def test_checks_the_new_venv_can_start(self):
        """Ported from fire, where a symlink-shim interpreter produced a venv
        that could not find the stdlib -- and every later error was confusing."""
        body = recipe("python-env-pip")
        assert "cannot start" in body

    def test_requires_the_pinned_python_minor_version(self):
        """Another interpreter resolves different wheels and fails the hash
        check in a way that reads as corruption rather than wrong Python."""
        body = recipe("python-env-pip")
        assert "3.12" in body and "PYTHON_312" in body
