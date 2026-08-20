"""
Comprehensive tests for Jupyter notebook integration.

Tests cover:
- Notebook execution via papermill
- Parameter injection
- Provenance generation from notebooks
- Environment configuration (runnotebook wrapper)
- Julia integration via juliacall
- Makefile integration
- Output verification
"""

import os
import subprocess
from pathlib import Path

import nbformat
import pytest
import yaml

# ==============================================================================
# Fixtures and Helpers
# ==============================================================================


# Every test here shells out through env/scripts/, so it needs a built
# environment. Marked rather than left to fail: without `make environment` the
# wrapper reports "Python env not found", which reads like a bug in the test.
pytestmark = pytest.mark.needs_env


@pytest.fixture
def repo_root():
    """Get repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def notebook_dir(repo_root):
    """Get notebooks directory."""
    return repo_root / "notebooks"


@pytest.fixture
def output_dir(repo_root):
    """Get output directory."""
    return repo_root / "output"


@pytest.fixture
def runnotebook_wrapper(repo_root):
    """Get path to runnotebook wrapper script."""
    return repo_root / "env" / "scripts" / "runnotebook"


@pytest.fixture
def sample_notebook(notebook_dir, tmp_path):
    """Create a minimal test notebook with proper structure."""
    nb = nbformat.v4.new_notebook()

    # Add kernel metadata (required for papermill)
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    }

    # Add markdown cell
    nb.cells.append(nbformat.v4.new_markdown_cell("# Test Notebook"))

    # Add parameters cell (tagged)
    params_cell = nbformat.v4.new_code_cell('study = "test"\nout_file = "output.txt"')
    params_cell.metadata["tags"] = ["parameters"]
    nb.cells.append(params_cell)

    # Add simple computation
    nb.cells.append(
        nbformat.v4.new_code_cell('result = 1 + 1\nprint(f"Result: {result}")')
    )

    # Write notebook
    nb_path = tmp_path / "test_notebook.ipynb"
    with open(nb_path, "w") as f:
        nbformat.write(nb, f)

    return nb_path


def run_command(
    cmd: list[str], cwd: Path = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command and return result."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


# ==============================================================================
# Environment Configuration Tests
# ==============================================================================


class TestNotebookEnvironment:
    """Test notebook environment configuration."""

    def test_runnotebook_exists(self, runnotebook_wrapper):
        """Test that runnotebook wrapper script exists."""
        assert runnotebook_wrapper.exists(), "runnotebook wrapper not found"

    def test_runnotebook_executable(self, runnotebook_wrapper):
        """Test that runnotebook wrapper is executable."""
        import os

        assert os.access(runnotebook_wrapper, os.X_OK), "runnotebook not executable"

    def test_runnotebook_unsets_cdpath(self, runnotebook_wrapper):
        """Test that runnotebook unsets CDPATH to prevent path pollution."""
        with open(runnotebook_wrapper) as f:
            content = f.read()
        assert "unset CDPATH" in content, "runnotebook doesn't unset CDPATH"

    def test_env_sh_sets_the_whole_bridge(self, repo_root):
        """env/env.sh must export a complete Julia/Python bridge.

        Checks the resulting environment, not the text of a script. The version
        of this test that grepped runnotebook for variable NAMES passed for the
        entire time runnotebook was missing JULIA_LOAD_PATH -- because the list
        it grepped for did not happen to include it. A test that inspects the
        mechanism can only ever verify the part of the mechanism it was told
        about; running the thing and looking at the result cannot miss a
        variable that way.
        """
        env_sh = repo_root / "env" / "env.sh"
        assert env_sh.is_file(), f"missing {env_sh}"

        wanted = [
            "PYTHON_JULIACALL_HANDLE_SIGNALS",
            "PYTHON_JULIAPKG_PROJECT",
            "JULIA_PROJECT",
            "JULIA_DEPOT_PATH",
            "JULIA_LOAD_PATH",
            "JULIA_CONDAPKG_BACKEND",
            "JULIA_NUM_THREADS",
            "PYTHONPATH",
            "DATA_DIR",
        ]
        probe = "; ".join(f'echo "{v}=${{{v}:-}}"' for v in wanted)
        result = subprocess.run(
            ["bash", "-c", f"source '{env_sh}' >/dev/null 2>&1; {probe}"],
            capture_output=True,
            text=True,
            check=True,
        )
        values = dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )
        missing = [v for v in wanted if not values.get(v)]
        assert not missing, f"env/env.sh left these unset: {', '.join(missing)}"

    def test_env_sh_ignores_a_polluted_ambient_environment(self, repo_root):
        """Project-scoped values must not be inherited from the calling shell.

        DATA_DIR written as ${DATA_DIR:-default} once caused a run in one
        project to read a DIFFERENT project's licensed data, because that other
        project's direnv had exported it. `:-` defers to whatever the shell
        happens to hold, and the shell holds whatever project you were last in,
        so for project-scoped settings it is not a default at all.
        """
        env_sh = repo_root / "env" / "env.sh"
        polluted = {
            "DATA_DIR": "/somewhere/else/entirely",
            "JULIA_NUM_THREADS": "32",
        }
        probe = "; ".join(f'echo "{v}=${{{v}:-}}"' for v in polluted)
        result = subprocess.run(
            ["bash", "-c", f"source '{env_sh}' >/dev/null 2>&1; {probe}"],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, **polluted},
        )
        values = dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )
        assert values["DATA_DIR"] != polluted["DATA_DIR"], (
            "DATA_DIR was inherited from the ambient environment; "
            "it must be set from the project root, with env/local.sh as the "
            "only sanctioned override"
        )
        assert values["JULIA_NUM_THREADS"] == "1", (
            "JULIA_NUM_THREADS was inherited; thread count changes "
            "floating-point reduction order, so it must not vary with whatever "
            f"the calling shell held (got {values['JULIA_NUM_THREADS']})"
        )

    def test_wrappers_do_not_restate_the_environment(self, repo_root):
        """Each wrapper must source env/env.sh and export no bridge var itself.

        This is the anti-drift invariant, and drift is precisely what happened:
        four wrappers each carried their own copy and they disagreed -- one
        omitted JULIA_LOAD_PATH, another exported JULIAPKG_PROJECT (a name
        juliapkg does not read) pointing somewhere different again. A wrapper
        that starts exporting these again has restarted that process.
        """
        bridge_vars = [
            "PYTHON_JULIACALL_HANDLE_SIGNALS",
            "PYTHON_JULIAPKG_PROJECT",
            "PYTHON_JULIAPKG_EXE",
            "JULIA_PROJECT",
            "JULIA_DEPOT_PATH",
            "JULIA_LOAD_PATH",
            "JULIA_CONDAPKG_BACKEND",
            "JULIA_PYTHONCALL_EXE",
        ]
        wrappers = [
            p for p in (repo_root / "env" / "scripts").glob("run*") if p.is_file()
        ]
        assert wrappers, "no run* wrappers found"

        for wrapper in wrappers:
            content = wrapper.read_text()
            assert "env.sh" in content, f"{wrapper.name} does not source env/env.sh"
            for var in bridge_vars:
                assert f"export {var}=" not in content, (
                    f"{wrapper.name} exports {var} itself; "
                    "it belongs in env/env.sh so the wrappers cannot disagree"
                )

    def test_runnotebook_executes_papermill(self, runnotebook_wrapper):
        """Test that runnotebook executes papermill."""
        with open(runnotebook_wrapper) as f:
            content = f.read()
        assert "papermill" in content, "runnotebook doesn't execute papermill"


# ==============================================================================
# Notebook Structure Tests
# ==============================================================================


class TestNotebookStructure:
    """Test notebook file structure and metadata."""

    def test_correlation_notebook_exists(self, notebook_dir):
        """Test that correlation example notebook exists."""
        nb_path = notebook_dir / "correlation_analysis.ipynb"
        assert nb_path.exists(), "correlation_analysis.ipynb not found"

    @pytest.mark.julia
    def test_julia_demo_notebook_exists(self, notebook_dir):
        """Test that Julia demo notebook exists."""
        nb_path = notebook_dir / "julia_demo.ipynb"
        assert nb_path.exists(), "julia_demo.ipynb not found"

    def test_notebook_has_kernel_metadata(self, notebook_dir):
        """Test that notebooks have proper kernel metadata."""
        nb_path = notebook_dir / "correlation_analysis.ipynb"
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        assert "kernelspec" in nb.metadata, "Notebook missing kernelspec"
        assert "name" in nb.metadata["kernelspec"], "Kernel name not specified"

    def test_notebook_has_parameters_cell(self, notebook_dir):
        """Test that notebooks have a tagged parameters cell."""
        nb_path = notebook_dir / "correlation_analysis.ipynb"
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        params_cells = [
            cell
            for cell in nb.cells
            if "tags" in cell.metadata and "parameters" in cell.metadata["tags"]
        ]

        assert len(params_cells) > 0, "No parameters cell found"

    def test_notebook_parameters_cell_has_required_vars(self, notebook_dir):
        """Test that parameters cell defines required variables."""
        nb_path = notebook_dir / "correlation_analysis.ipynb"
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        params_cells = [
            cell
            for cell in nb.cells
            if "tags" in cell.metadata and "parameters" in cell.metadata["tags"]
        ]

        params_source = params_cells[0].source
        required_vars = ["study", "data_file", "out_fig", "out_table", "out_meta"]

        for var in required_vars:
            assert var in params_source, f"Parameters cell missing {var}"


# ==============================================================================
# Notebook Execution Tests
# ==============================================================================


class TestNotebookExecution:
    """Test notebook execution via papermill."""

    def test_sample_notebook_executes(self, sample_notebook, tmp_path, repo_root):
        """Test that a simple notebook executes successfully."""
        output_nb = tmp_path / "executed.ipynb"

        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runnotebook"),
                str(sample_notebook),
                str(output_nb),
                "-p",
                "study",
                "test_exec",
            ],
            cwd=repo_root,
        )

        assert result.returncode == 0, f"Notebook execution failed: {result.stderr}"
        assert output_nb.exists(), "Executed notebook not created"

    def test_parameter_injection(self, sample_notebook, tmp_path, repo_root):
        """Test that papermill injects parameters correctly."""
        output_nb = tmp_path / "executed.ipynb"

        run_command(
            [
                str(repo_root / "env" / "scripts" / "runnotebook"),
                str(sample_notebook),
                str(output_nb),
                "-p",
                "study",
                "injected_value",
                "-p",
                "out_file",
                "custom_output.txt",
            ],
            cwd=repo_root,
        )

        # Read executed notebook
        with open(output_nb) as f:
            nb = nbformat.read(f, as_version=4)

        # Find injected parameters cell
        for cell in nb.cells:
            if cell.cell_type == "code" and "injected-parameters" in cell.metadata.get(
                "tags", []
            ):
                assert "injected_value" in cell.source, "Parameter not injected"
                assert "custom_output.txt" in cell.source, (
                    "Custom parameter not injected"
                )
                break
        else:
            pytest.fail("Injected parameters cell not found")

    def test_correlation_notebook_builds(self, repo_root):
        """Test that correlation notebook builds via make."""
        # Clean outputs first
        fig_path = repo_root / "output" / "figures" / "correlation.pdf"
        if fig_path.exists():
            fig_path.unlink()

        result = run_command(["make", "correlation"], cwd=repo_root, check=False)

        assert result.returncode == 0, f"Make failed: {result.stderr}"
        assert fig_path.exists(), "correlation.pdf not created"

    @pytest.mark.julia
    def test_julia_demo_notebook_builds(self, repo_root):
        """Test that Julia demo notebook builds via make."""
        # Clean outputs first
        fig_path = repo_root / "output" / "figures" / "julia_demo.pdf"
        if fig_path.exists():
            fig_path.unlink()

        result = run_command(["make", "julia_demo"], cwd=repo_root, check=False)

        assert result.returncode == 0, f"Make failed: {result.stderr}"
        assert fig_path.exists(), "julia_demo.pdf not created"


# ==============================================================================
# Provenance Tests
# ==============================================================================


class TestNotebookProvenance:
    """Test provenance generation from notebooks."""

    def test_provenance_file_created(self, repo_root):
        """Test that provenance file is created for notebook builds."""
        prov_path = repo_root / "output" / "provenance" / "correlation.yml"

        # Build if not exists
        if not prov_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        assert prov_path.exists(), "Provenance file not created"

    def test_provenance_structure(self, repo_root):
        """Test that provenance file has correct structure."""
        prov_path = repo_root / "output" / "provenance" / "correlation.yml"

        # Build if not exists
        if not prov_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        with open(prov_path) as f:
            prov = yaml.safe_load(f)

        # Check required fields
        assert "artifact" in prov, "Missing artifact field"
        assert prov["artifact"] == "correlation", "Wrong artifact name"
        assert "built_at_utc" in prov, "Missing timestamp"
        assert "command" in prov, "Missing command"
        assert "git" in prov, "Missing git state"
        assert "inputs" in prov, "Missing inputs"
        assert "outputs" in prov, "Missing outputs"

    def test_provenance_records_notebook_command(self, repo_root):
        """Test that provenance records papermill command."""
        prov_path = repo_root / "output" / "provenance" / "correlation.yml"

        if not prov_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        with open(prov_path) as f:
            prov = yaml.safe_load(f)

        # Command should reference papermill or notebook
        cmd_str = " ".join(prov.get("command", []))
        assert "papermill" in cmd_str or "notebook" in cmd_str.lower(), (
            "Provenance doesn't record notebook execution"
        )

    def test_provenance_includes_inputs(self, repo_root):
        """Test that provenance includes input files."""
        prov_path = repo_root / "output" / "provenance" / "correlation.yml"

        if not prov_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        with open(prov_path) as f:
            prov = yaml.safe_load(f)

        assert len(prov["inputs"]) > 0, "No inputs recorded"

        # Check that data file is included
        input_paths = [inp["path"] for inp in prov["inputs"]]
        assert any("panel_data.csv" in path for path in input_paths), (
            "Data file not in inputs"
        )

    def test_provenance_includes_outputs(self, repo_root):
        """Test that provenance includes all output files."""
        prov_path = repo_root / "output" / "provenance" / "correlation.yml"

        if not prov_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        with open(prov_path) as f:
            prov = yaml.safe_load(f)

        assert len(prov["outputs"]) >= 2, "Missing outputs (should have figure + table)"

        output_paths = [out["path"] for out in prov["outputs"]]
        assert any("correlation.pdf" in path for path in output_paths), (
            "Figure not in outputs"
        )
        assert any("correlation.tex" in path for path in output_paths), (
            "Table not in outputs"
        )


# ==============================================================================
# Julia Integration Tests
# ==============================================================================


@pytest.mark.julia
class TestJuliaIntegration:
    """Test Julia integration via juliacall in notebooks."""

    def test_juliacall_imports(self, repo_root):
        """Test that juliacall can be imported in notebook environment."""
        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runpython"),
                "-c",
                "from juliacall import Main as jl; print(jl.VERSION)",
            ],
            cwd=repo_root,
            check=False,
        )

        assert result.returncode == 0, f"juliacall import failed: {result.stderr}"
        assert result.stdout.strip(), "Julia version not printed"

    def test_julia_statistics_loads(self, repo_root):
        """Test that Julia Statistics package can be loaded."""
        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runpython"),
                "-c",
                "from juliacall import Main as jl; "
                'jl.seval("using Statistics"); '
                'print("OK")',
            ],
            cwd=repo_root,
            check=False,
        )

        assert result.returncode == 0, f"Statistics load failed: {result.stderr}"
        assert "OK" in result.stdout, "Statistics didn't load successfully"

    def test_julia_functions_callable(self, repo_root):
        """Test that Julia functions can be called from Python."""
        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runpython"),
                "-c",
                "from juliacall import Main as jl; "
                'jl.seval("using Statistics"); '
                "import numpy as np; "
                "arr = np.array([1, 2, 3, 4, 5]); "
                "mean_val = jl.mean(arr); "
                'print(f"Mean: {mean_val}")',
            ],
            cwd=repo_root,
            check=False,
        )

        assert result.returncode == 0, f"Julia function call failed: {result.stderr}"
        assert "Mean: 3" in result.stdout, "Julia mean() didn't return expected value"

    def test_julia_demo_uses_juliacall(self, notebook_dir):
        """Test that julia_demo notebook uses juliacall."""
        nb_path = notebook_dir / "julia_demo.ipynb"

        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Check that notebook has juliacall import
        has_juliacall = False
        for cell in nb.cells:
            if cell.cell_type == "code" and "juliacall" in cell.source:
                has_juliacall = True
                break

        assert has_juliacall, "julia_demo.ipynb doesn't use juliacall"


# ==============================================================================
# Output Verification Tests
# ==============================================================================


class TestNotebookOutputs:
    """Test that notebook outputs are created correctly."""

    def test_executed_notebook_saved(self, repo_root):
        """Test that executed notebook is saved to output directory."""
        exec_nb_path = (
            repo_root
            / "output"
            / "executed_notebooks"
            / "correlation_analysis_executed.ipynb"
        )

        # Build if not exists
        if not exec_nb_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        assert exec_nb_path.exists(), "Executed notebook not saved"

    def test_executed_notebook_has_outputs(self, repo_root):
        """Test that executed notebook contains cell outputs."""
        exec_nb_path = (
            repo_root
            / "output"
            / "executed_notebooks"
            / "correlation_analysis_executed.ipynb"
        )

        if not exec_nb_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        with open(exec_nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Check that at least some cells have outputs
        cells_with_outputs = [
            cell
            for cell in nb.cells
            if cell.cell_type == "code" and cell.get("outputs", [])
        ]

        assert len(cells_with_outputs) > 0, "Executed notebook has no cell outputs"

    def test_figure_created(self, repo_root):
        """Test that notebook creates PDF figure."""
        fig_path = repo_root / "output" / "figures" / "correlation.pdf"

        if not fig_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        assert fig_path.exists(), "Figure not created"
        assert fig_path.stat().st_size > 0, "Figure is empty"

    def test_table_created(self, repo_root):
        """Test that notebook creates LaTeX table."""
        table_path = repo_root / "output" / "tables" / "correlation.tex"

        if not table_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        assert table_path.exists(), "Table not created"
        assert table_path.stat().st_size > 0, "Table is empty"

    def test_log_created(self, repo_root):
        """Test that build log is created."""
        log_path = repo_root / "output" / "logs" / "correlation.log"

        if not log_path.exists():
            run_command(["make", "correlation"], cwd=repo_root)

        assert log_path.exists(), "Log file not created"


# ==============================================================================
# Makefile Integration Tests
# ==============================================================================


class TestMakefileIntegration:
    """Test Makefile integration for notebooks."""

    @pytest.mark.julia
    def test_notebook_in_analyses_list(self, repo_root):
        """Test that notebook analyses are in ANALYSES variable."""
        makefile = repo_root / "Makefile"
        with open(makefile) as f:
            content = f.read()

        # Find ANALYSES variable
        for line in content.split("\n"):
            if line.startswith("ANALYSES"):
                assert "correlation" in line, "correlation not in ANALYSES"
                assert "julia_demo" in line, "julia_demo not in ANALYSES"
                break
        else:
            pytest.fail("ANALYSES variable not found in Makefile")

    def test_notebook_variables_defined(self, repo_root):
        """Test that notebook variables are defined in Makefile."""
        makefile = repo_root / "Makefile"
        with open(makefile) as f:
            content = f.read()

        required_vars = [
            "correlation.script",
            "correlation.runner",
            "correlation.inputs",
            "correlation.outputs",
            "correlation.args",
        ]

        for var in required_vars:
            assert var in content, f"{var} not defined in Makefile"

    def test_notebook_uses_notebook_runner(self, repo_root):
        """Test that .ipynb files use $(NOTEBOOK) runner."""
        makefile = repo_root / "Makefile"
        with open(makefile) as f:
            content = f.read()

        # Find correlation.runner definition
        for line in content.split("\n"):
            if "correlation.runner" in line:
                assert "$(NOTEBOOK)" in line or "$(RUNNOTEBOOK)" in line, (
                    "Notebook doesn't use NOTEBOOK runner"
                )
                break

    def test_make_correlation_succeeds(self, repo_root):
        """Test that 'make correlation' runs without error."""
        result = run_command(["make", "correlation"], cwd=repo_root, check=False)

        # Should either succeed or report "Nothing to be done"
        success = (
            result.returncode == 0
            or "Nothing to be done" in result.stdout
            or "up to date" in result.stdout.lower()
        )

        assert success, f"make correlation failed: {result.stderr}"

    @pytest.mark.julia
    def test_make_julia_demo_succeeds(self, repo_root):
        """Test that 'make julia_demo' runs without error."""
        result = run_command(["make", "julia_demo"], cwd=repo_root, check=False)

        success = (
            result.returncode == 0
            or "Nothing to be done" in result.stdout
            or "up to date" in result.stdout.lower()
        )

        assert success, f"make julia_demo failed: {result.stderr}"


# ==============================================================================
# Error Handling Tests
# ==============================================================================


class TestNotebookErrorHandling:
    """Test error handling in notebook execution."""

    def test_notebook_with_error_fails_build(self, tmp_path, repo_root):
        """Test that notebook with errors causes build to fail."""
        # Create notebook with deliberate error
        nb = nbformat.v4.new_notebook()
        nb.metadata = {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            }
        }

        params_cell = nbformat.v4.new_code_cell('study = "error_test"')
        params_cell.metadata["tags"] = ["parameters"]
        nb.cells.append(params_cell)

        # Add cell that will error
        nb.cells.append(nbformat.v4.new_code_cell('raise ValueError("Test error")'))

        nb_path = tmp_path / "error_notebook.ipynb"
        with open(nb_path, "w") as f:
            nbformat.write(nb, f)

        # Try to execute - should fail
        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runnotebook"),
                str(nb_path),
                str(tmp_path / "executed.ipynb"),
            ],
            cwd=repo_root,
            check=False,
        )

        assert result.returncode != 0, "Notebook with error should fail"
        assert "ValueError" in result.stderr or "error" in result.stderr.lower(), (
            "Error not reported in stderr"
        )

    def test_missing_parameters_cell_fails(self, tmp_path, repo_root):
        """Test that notebook without parameters cell fails with clear error."""
        # Create notebook without parameters cell
        nb = nbformat.v4.new_notebook()
        nb.metadata = {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            }
        }
        nb.cells.append(nbformat.v4.new_code_cell('print("Hello")'))

        nb_path = tmp_path / "no_params.ipynb"
        with open(nb_path, "w") as f:
            nbformat.write(nb, f)

        # Try to execute with parameters - should fail or warn
        result = run_command(
            [
                str(repo_root / "env" / "scripts" / "runnotebook"),
                str(nb_path),
                str(tmp_path / "executed.ipynb"),
                "-p",
                "study",
                "test",
            ],
            cwd=repo_root,
            check=False,
        )

        # Papermill may succeed but warn, or may fail
        # Either way, it shouldn't silently ignore the issue
        assert (
            result.returncode != 0
            or "warning" in result.stderr.lower()
            or "parameter" in result.stderr.lower()
        ), "Missing parameters cell should cause warning or error"


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
