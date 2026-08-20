"""
Tests for environment setup and update functionality.

Tests environment installation, configuration, and updates.

A NOTE ON SKIPPING, WHICH THIS FILE GETS WRONG EASILY

Julia and Stata are optional in this template, so tests that need them must
skip on a machine that does not have them. That is legitimate. What is not
legitimate is deciding "not available" from the failure of the very command
under test: `using DataFrames` failing means the environment is broken far more
often than it means Julia is missing, and reporting it as a skip turns a broken
environment into silence.

Two tests here did exactly that until 2026-08-17, and both had an unreachable
`assert` sitting after the skip. The rule this file now follows:

  * decide availability up front, from its own evidence (`require_julia`)
  * after that point, a failure is a failure

`git log -S "Julia not available"` finds the change and its reasoning.
"""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
RUNJULIA = REPO_ROOT / "env" / "scripts" / "runjulia"


# Every test here shells out through env/scripts/, so it needs a built
# environment. Marked rather than left to fail: without `make environment` the
# wrapper reports "Python env not found", which reads like a bug in the test.
pytestmark = pytest.mark.needs_env

def run_julia(
    code: str, *, timeout: int = 120, env=None
) -> subprocess.CompletedProcess:
    """Run a Julia snippet through the repo's runjulia wrapper.

    Always the wrapper, never a bare `julia`: the wrapper is what sets
    JULIA_PROJECT, JULIA_DEPOT_PATH and JULIA_LOAD_PATH, so a bare interpreter
    would resolve packages from a different project (or the user's global depot)
    and report on an environment this repository does not control.
    """
    return subprocess.run(
        [str(RUNJULIA), "-e", code],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def require_julia() -> None:
    """Skip the calling test unless a working Julia is reachable.

    "Working" is established by a trivial snippet that touches no project
    dependency, so the answer cannot be confounded with the thing a caller is
    about to test. A caller that has passed this point is entitled to treat any
    later failure as a real failure.
    """
    if not RUNJULIA.exists():
        pytest.skip("runjulia wrapper not found (Julia support not installed)")

    try:
        result = run_julia("print(VERSION)", timeout=120)
    except subprocess.TimeoutExpired:  # pragma: no cover - environment-dependent
        pytest.skip("Julia did not start within the timeout")

    if result.returncode != 0:
        pytest.skip(
            "Julia is not installed or cannot start "
            f"(run `make environment`): {result.stderr.strip()[:400]}"
        )


def julia_project_deps() -> set[str]:
    """Package names declared in env/Project.toml [deps].

    Parsed as TOML rather than searched for as substrings. The substring version
    of this question is what made the CUDA test unrunnable: "CUDA" appears in
    env/Project.toml only inside a comment saying CUDA is deliberately not a
    dependency, and a substring check cannot tell a declaration from prose
    denying it.
    """
    project_toml = REPO_ROOT / "env" / "Project.toml"
    if not project_toml.is_file():
        return set()
    return set(tomllib.loads(project_toml.read_text()).get("deps", {}))


class TestPythonEnvironment:
    """Test Python environment setup."""

    def test_python_env_exists(self):
        """Python environment directory should exist."""
        env_dir = REPO_ROOT / ".venv"
        if not env_dir.exists():
            pytest.skip("Python environment not installed (run 'make environment')")

        assert env_dir.is_dir()

    def test_python_executable_exists(self):
        """Python executable should exist in environment."""
        python_exe = REPO_ROOT / ".venv" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        assert python_exe.exists()
        assert python_exe.is_file()

    def test_python_version(self):
        """Python should be version 3.12."""
        python_exe = REPO_ROOT / ".venv" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        version_str = result.stdout + result.stderr
        assert "Python 3.12" in version_str

    @pytest.mark.julia
    def test_required_packages_installed(self):
        """Required Python packages should be installed."""
        python_exe = REPO_ROOT / ".venv" / "bin" / "python"
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        required_packages = [
            "pandas",
            "matplotlib",
            "yaml",  # pyyaml package imports as 'yaml'
            "jinja2",
            "juliacall",
        ]

        for package in required_packages:
            # Use runpython for juliacall to avoid segfault (needs PYTHON_JULIACALL_HANDLE_SIGNALS=yes)
            if package == "juliacall" and runpython.exists():
                cmd = [str(runpython), "-c", f"import {package}"]
            else:
                cmd = [str(python_exe), "-c", f"import {package}"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0, (
                f"Package {package} not installed: {result.stderr}"
            )

    def test_repro_tools_installed(self):
        """repro_tools should be installed in editable mode."""
        python_exe = REPO_ROOT / ".venv" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        # Check that repro_tools imports
        result = subprocess.run(
            [
                str(python_exe),
                "-c",
                "import repro_tools; print(repro_tools.__version__)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"repro_tools not installed: {result.stderr}"
        assert len(result.stdout.strip()) > 0  # Version string should be present

    def test_pyproject_exists(self):
        """Python environment spec (pyproject.toml) should exist and define deps."""
        import tomllib

        pyproject = REPO_ROOT / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"

        with open(pyproject, "rb") as f:
            config = tomllib.load(f)

        assert "project" in config
        assert isinstance(config["project"].get("dependencies"), list)


@pytest.mark.julia
class TestJuliaEnvironment:
    """Test Julia environment setup."""

    def test_julia_depot_exists(self):
        """Julia depot directory should exist if Julia installed."""
        julia_dir = REPO_ROOT / ".julia"
        if not julia_dir.exists():
            pytest.skip("Julia not installed")

        assert julia_dir.is_dir()

    def test_julia_binary_exists(self):
        """Julia binary should exist in pyjuliapkg installation."""
        julia_exe = REPO_ROOT / ".julia" / "pyjuliapkg" / "install" / "bin" / "julia"
        if not julia_exe.exists():
            pytest.skip("Julia not installed via juliacall")

        assert julia_exe.exists()
        assert julia_exe.is_file()

    def test_julia_version(self):
        """Julia should be version 1.10+."""
        julia_exe = REPO_ROOT / ".julia" / "pyjuliapkg" / "install" / "bin" / "julia"
        if not julia_exe.exists():
            pytest.skip("Julia not installed")

        result = subprocess.run(
            [str(julia_exe), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Check for Julia 1.10, 1.11, or 1.12
        assert "julia version 1.1" in result.stdout.lower()

    def test_julia_project_toml_exists(self):
        """Julia Project.toml should exist."""
        project_toml = REPO_ROOT / "env" / "Project.toml"
        assert project_toml.exists(), "env/Project.toml not found"

    def test_julia_packages_installed(self):
        """Every package declared in env/Project.toml [deps] must actually load.

        Julia is optional in this template, so a machine without it skips. But
        once Julia IS installed, a package that will not load is a broken
        environment and must fail.

        This test used to end with:

            if result.returncode != 0:
                pytest.skip(f"Julia not available: {result.stderr}")
            assert result.returncode == 0, ...

        which reported EVERY failure -- a missing package, a corrupt depot, an
        incompatible version -- as "Julia not available", and left the assert on
        the next line unreachable. It could not fail. `require_julia()` now makes
        the availability decision once, up front, on its own evidence, so
        anything after it is a real assertion.

        It also checks the whole [deps] table rather than DataFrames alone: the
        old version would have passed with every other dependency missing.
        """
        require_julia()

        # PythonCall is deliberately absent from env/Project.toml -- juliacall
        # manages it in .julia/pyjuliapkg/. See docs/julia_python_integration.md
        # and test_pythoncall_not_in_env_project below.
        deps = sorted(julia_project_deps())
        assert deps, "env/Project.toml declares no [deps] to check"

        result = run_julia("; ".join(f"using {name}" for name in deps))
        assert result.returncode == 0, (
            f"declared Julia dependencies failed to load: {deps}\n{result.stderr}"
        )

    def test_condapkg_disabled(self):
        """CondaPkg should be disabled."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        if not runpython.exists():
            pytest.skip("runpython wrapper not found")

        # Check that JULIA_CONDAPKG_BACKEND is set to Null
        result = subprocess.run(
            [
                str(runpython),
                "-c",
                "import os; print(os.environ.get('JULIA_CONDAPKG_BACKEND', ''))",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Null" in result.stdout

    def test_pythoncall_not_in_env_project(self):
        """CRITICAL: PythonCall must NOT be in env/Project.toml [deps] or [compat]."""
        project_toml = REPO_ROOT / "env" / "Project.toml"
        if not project_toml.exists():
            pytest.skip("env/Project.toml not found")

        content = project_toml.read_text()

        # Parse TOML sections
        import re

        # Check [deps] section - PythonCall should NOT be there
        deps_match = re.search(r"\[deps\](.*?)(?:\[|$)", content, re.DOTALL)
        if deps_match:
            deps_section = deps_match.group(1)
            assert not re.match(r"^\s*PythonCall\s*=", deps_section, re.MULTILINE), (
                "CRITICAL ERROR: PythonCall found in [deps] section of env/Project.toml! "
                "This causes installation failures. PythonCall is managed by "
                "juliacall and should ONLY be in .julia/pyjuliapkg/"
            )

        # Check [compat] section - PythonCall should NOT be there
        compat_match = re.search(r"\[compat\](.*?)(?:\[|$)", content, re.DOTALL)
        if compat_match:
            compat_section = compat_match.group(1)
            assert not re.match(r"^\s*PythonCall\s*=", compat_section, re.MULTILINE), (
                "CRITICAL ERROR: PythonCall found in [compat] section of env/Project.toml! "
                "This causes installation failures. PythonCall is managed by "
                "juliacall and should ONLY be in .julia/pyjuliapkg/"
            )

    def test_pythoncall_in_pyjuliapkg(self):
        """PythonCall should be in juliacall-managed environment (.julia/Project.toml)."""
        # juliacall creates .julia/Project.toml as its shared environment
        julia_project = REPO_ROOT / ".julia" / "Project.toml"
        if not julia_project.exists():
            pytest.skip("Julia not installed via juliacall yet")

        content = julia_project.read_text()

        # PythonCall SHOULD be in juliacall's Project.toml
        assert "PythonCall" in content, (
            "PythonCall not found in .julia/pyjuliapkg/Project.toml. "
            "This is managed by juliacall."
        )

    def test_juliacall_can_import(self):
        """Test that juliacall can be imported from Python."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        if not runpython.exists():
            pytest.skip("runpython wrapper not found")

        result = subprocess.run(
            [
                str(runpython),
                "-c",
                "from juliacall import Main as jl; print(jl.VERSION)",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"juliacall import failed: {result.stderr}"
        assert len(result.stdout.strip()) > 0, "Julia version not printed"

    def test_cuda_available_if_enabled(self):
        """If the opt-in GPU environment exists, CUDA.jl must load from it.

        HOW GPU SUPPORT ACTUALLY WORKS HERE, because the previous version of
        this test looked for it in the wrong place:

        CUDA.jl is never a dependency in env/Project.toml. `JULIA_ENABLE_CUDA=1
        make environment` installs it into `.julia/gpu-env`, which is gitignored,
        and run_did.py appends that directory to JULIA_LOAD_PATH when
        `.julia/gpu-env/Project.toml` exists. A machine without a GPU never
        installs it and stays CPU-only with no switching. So the presence of
        that Project.toml -- not any string in env/Project.toml -- is what
        "GPU support was enabled" means.

        The old gate was:

            content = (REPO_ROOT / "env" / "Project.toml").read_text()
            if "CUDA" not in content:
                pytest.skip("CUDA not in Project.toml - GPU support not enabled")

        a substring search over the entire file. The only occurrences of "CUDA"
        in env/Project.toml are in a comment explaining that CUDA is
        intentionally NOT a dependency -- so the guard read a comment saying
        "CUDA is not here" as evidence that it was, fell through to `using
        CUDA`, failed, and skipped with "Julia not available: ...". Julia was
        available; it was 1.12.4 and working. Measured 2026-08-17.

        A test whose enabling condition is satisfied by prose about the feature
        being absent is testing the documentation, not the environment.
        """
        require_julia()

        gpu_env = REPO_ROOT / ".julia" / "gpu-env"
        if not (gpu_env / "Project.toml").is_file():
            pytest.skip(
                "GPU support not enabled: no .julia/gpu-env/Project.toml "
                "(enable with `JULIA_ENABLE_CUDA=1 make environment`)"
            )

        # No load-path juggling here on purpose. env.sh appends gpu-env when it
        # exists, so every entry point -- runjulia, runpython/juliacall, make --
        # sees the same environment, and this test exercises the real one. Doing
        # it in the test instead would test the test.
        # See repro-tools tests/test_env_sh_julia_load_path.py.
        result = run_julia("using CUDA; println(CUDA.functional())", timeout=900)
        assert result.returncode == 0, (
            f"the GPU environment exists but CUDA.jl will not load: {result.stderr}"
        )
        # CUDA.functional() is False on a machine with the package but no usable
        # device. That is a legitimate state -- the package loading is the claim
        # being tested here -- so its value is reported, not asserted.
        assert result.stdout.strip() in {"true", "false"}, (
            f"CUDA.functional() printed something unexpected: {result.stdout!r}"
        )


class TestEnvironmentWrappers:
    """Test environment wrapper scripts."""

    def test_runpython_exists(self):
        """runpython wrapper should exist and be executable."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        assert runpython.exists(), "runpython wrapper not found"
        assert os.access(runpython, os.X_OK), "runpython not executable"

    @pytest.mark.julia
    def test_runjulia_exists(self):
        """runjulia wrapper should exist and be executable."""
        runjulia = REPO_ROOT / "env" / "scripts" / "runjulia"
        assert runjulia.exists(), "runjulia wrapper not found"
        assert os.access(runjulia, os.X_OK), "runjulia not executable"

    @pytest.mark.stata
    def test_runstata_exists(self):
        """runstata wrapper should exist and be executable."""
        runstata = REPO_ROOT / "env" / "scripts" / "runstata"
        assert runstata.exists(), "runstata wrapper not found"
        assert os.access(runstata, os.X_OK), "runstata not executable"

    def test_runpython_sets_pythonpath(self):
        """runpython should set PYTHONPATH to include repo root."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        if not runpython.exists():
            pytest.skip("runpython wrapper not found")

        result = subprocess.run(
            [str(runpython), "-c", "import sys; print(':'.join(sys.path))"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert str(REPO_ROOT) in result.stdout

    def test_runpython_can_import_repro_tools(self):
        """runpython should allow importing repro_tools."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        if not runpython.exists():
            pytest.skip("runpython wrapper not found")

        result = subprocess.run(
            [str(runpython), "-c", "from repro_tools import git_state"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Cannot import repro_tools: {result.stderr}"


class TestSubmodules:
    """Test git submodule setup."""

    def test_repro_tools_submodule_exists(self):
        """repro-tools submodule directory should exist."""
        submodule_dir = REPO_ROOT / "lib" / "repro-tools"
        assert submodule_dir.exists(), "lib/repro-tools not found"
        assert submodule_dir.is_dir()

    def test_repro_tools_has_content(self):
        """repro-tools submodule should have content (not empty)."""
        submodule_dir = REPO_ROOT / "lib" / "repro-tools"
        if not submodule_dir.exists():
            pytest.skip("repro-tools submodule not found")

        # Check for key files
        assert (submodule_dir / "pyproject.toml").exists()
        assert (submodule_dir / "src" / "repro_tools").exists()

    def test_gitmodules_file_exists(self):
        """.gitmodules file should exist."""
        gitmodules = REPO_ROOT / ".gitmodules"
        assert gitmodules.exists(), ".gitmodules not found"

        # Check content references repro-tools
        content = gitmodules.read_text()
        assert "repro-tools" in content


class TestEnvironmentUpdate:
    """Test environment update scenarios."""

    def test_python_env_can_be_updated(self):
        """Python environment should support listing packages via uv."""
        import shutil

        python_exe = REPO_ROOT / ".venv" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")
        if shutil.which("uv") is None:
            pytest.skip("uv not on PATH")

        # uv manages the venv (no pip inside it); `uv pip list` is the basic operation.
        result = subprocess.run(
            ["uv", "pip", "list", "--python", str(python_exe)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0

    def test_make_update_submodules_command_exists(self):
        """Makefile should have update-submodules target."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "update-submodules" in content

    def test_make_update_environment_command_exists(self):
        """Makefile should have update-environment target."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "update-environment" in content


class TestEnvironmentIsolation:
    """Test that environments are properly isolated."""

    def test_python_env_is_local(self):
        """Python environment should be local to repo, not global."""
        env_dir = REPO_ROOT / ".venv"
        if not env_dir.exists():
            pytest.skip("Python environment not installed")

        # Environment should be inside repo
        assert env_dir.parent == REPO_ROOT

    @pytest.mark.julia
    def test_julia_depot_is_local(self):
        """Julia depot should be local to repo."""
        julia_dir = REPO_ROOT / ".julia"
        if not julia_dir.exists():
            pytest.skip("Julia not installed")

        # Julia depot should be inside repo
        assert julia_dir.parent == REPO_ROOT

    @pytest.mark.stata
    def test_stata_packages_are_local(self):
        """Stata packages should be local to repo if Stata is used."""
        stata_dir = REPO_ROOT / ".stata"
        if not stata_dir.exists():
            pytest.skip("Stata not installed")

        # Stata packages should be inside repo
        assert stata_dir.parent == REPO_ROOT


class TestEnvironmentReproducibility:
    """Test that environment setup is reproducible."""

    def test_pyproject_pins_python_version(self):
        """Python version should be constrained in pyproject.toml."""
        import tomllib

        pyproject = REPO_ROOT / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pyproject.toml not found")

        with open(pyproject, "rb") as f:
            config = tomllib.load(f)

        requires_python = config.get("project", {}).get("requires-python", "")
        assert "3.12" in requires_python, (
            "Python 3.12 not constrained in requires-python"
        )

    def test_project_toml_has_compat_section(self):
        """Project.toml should have [compat] section for version constraints."""
        project_toml = REPO_ROOT / "env" / "Project.toml"
        if not project_toml.exists():
            pytest.skip("env/Project.toml not found")

        import tomli

        with open(project_toml, "rb") as f:
            config = tomli.load(f)

        assert "compat" in config, "No [compat] section in Project.toml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
