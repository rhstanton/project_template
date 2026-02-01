"""
Tests for environment setup and update functionality.

Tests environment installation, configuration, and updates.
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent


class TestPythonEnvironment:
    """Test Python environment setup."""

    def test_python_env_exists(self):
        """Python environment directory should exist."""
        env_dir = REPO_ROOT / ".env"
        if not env_dir.exists():
            pytest.skip("Python environment not installed (run 'make environment')")

        assert env_dir.is_dir()

    def test_python_executable_exists(self):
        """Python executable should exist in environment."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        assert python_exe.exists()
        assert python_exe.is_file()

    def test_python_version(self):
        """Python should be version 3.11."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        version_str = result.stdout + result.stderr
        assert "Python 3.11" in version_str

    def test_required_packages_installed(self):
        """Required Python packages should be installed."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
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
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
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

    def test_python_yml_exists(self):
        """Python environment spec should exist."""
        python_yml = REPO_ROOT / "env" / "python.yml"
        assert python_yml.exists(), "env/python.yml not found"

        # Validate YAML structure
        with open(python_yml) as f:
            config = yaml.safe_load(f)

        assert "name" in config
        assert "dependencies" in config
        assert isinstance(config["dependencies"], list)


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
        """Required Julia packages should be installed."""
        runjulia = REPO_ROOT / "env" / "scripts" / "runjulia"
        if not runjulia.exists():
            pytest.skip("runjulia wrapper not found")

        # NOTE: PythonCall is managed by juliacall in .julia/pyjuliapkg/
        # It should NOT be in env/Project.toml (see docs/julia_python_integration.md)
        # We test juliacall integration separately in test_notebook_integration.py
        
        # Test DataFrames package (should be in env/Project.toml)
        result = subprocess.run(
            [str(runjulia), "-e", "using DataFrames"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"DataFrames not installed: {result.stderr}"

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
        """Test CUDA.jl is available if GPU support was enabled."""
        runjulia = REPO_ROOT / "env" / "scripts" / "runjulia"
        if not runjulia.exists():
            pytest.skip("Julia not installed")

        # Check if CUDA.jl is in Project.toml (indicates GPU support requested)
        project_toml = REPO_ROOT / "env" / "Project.toml"
        content = project_toml.read_text()

        if "CUDA" not in content:
            pytest.skip("CUDA not in Project.toml - GPU support not enabled")

        # CUDA should be loadable
        result = subprocess.run(
            [str(runjulia), "-e", "using CUDA; println(CUDA.functional())"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"CUDA.jl not functional: {result.stderr}"
        # Note: CUDA.functional() will be true if GPU is available, false if not
        # We just check it doesn't error


class TestEnvironmentWrappers:
    """Test environment wrapper scripts."""

    def test_runpython_exists(self):
        """runpython wrapper should exist and be executable."""
        runpython = REPO_ROOT / "env" / "scripts" / "runpython"
        assert runpython.exists(), "runpython wrapper not found"
        assert os.access(runpython, os.X_OK), "runpython not executable"

    def test_runjulia_exists(self):
        """runjulia wrapper should exist and be executable."""
        runjulia = REPO_ROOT / "env" / "scripts" / "runjulia"
        assert runjulia.exists(), "runjulia wrapper not found"
        assert os.access(runjulia, os.X_OK), "runjulia not executable"

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
        """Python environment should support updates."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        # Test that we can run pip list (basic operation)
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "list"],
            capture_output=True,
            text=True,
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
        env_dir = REPO_ROOT / ".env"
        if not env_dir.exists():
            pytest.skip("Python environment not installed")

        # Environment should be inside repo
        assert env_dir.parent == REPO_ROOT

    def test_julia_depot_is_local(self):
        """Julia depot should be local to repo."""
        julia_dir = REPO_ROOT / ".julia"
        if not julia_dir.exists():
            pytest.skip("Julia not installed")

        # Julia depot should be inside repo
        assert julia_dir.parent == REPO_ROOT

    def test_stata_packages_are_local(self):
        """Stata packages should be local to repo if Stata is used."""
        stata_dir = REPO_ROOT / ".stata"
        if not stata_dir.exists():
            pytest.skip("Stata not installed")

        # Stata packages should be inside repo
        assert stata_dir.parent == REPO_ROOT


class TestEnvironmentReproducibility:
    """Test that environment setup is reproducible."""

    def test_python_yml_pins_python_version(self):
        """Python version should be pinned in python.yml."""
        python_yml = REPO_ROOT / "env" / "python.yml"
        if not python_yml.exists():
            pytest.skip("env/python.yml not found")

        with open(python_yml) as f:
            config = yaml.safe_load(f)

        # Find python dependency
        deps = config.get("dependencies", [])
        python_deps = [d for d in deps if isinstance(d, str) and d.startswith("python")]

        assert len(python_deps) > 0, "Python not specified in dependencies"
        # Should specify version like "python=3.11"
        assert "=" in python_deps[0] or "3.11" in python_deps[0]

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
