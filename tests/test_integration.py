"""
Integration tests for build workflow.

Tests that artifacts can be built and provenance is correctly recorded.
"""
import subprocess
import sys
from pathlib import Path
import yaml
import pytest


REPO_ROOT = Path(__file__).parent.parent


class TestBuildWorkflow:
    """Test complete build workflow."""
    
    def test_environment_available(self):
        """Python environment should be available."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")
        
        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Python 3.11" in result.stdout or "Python 3.11" in result.stderr
    
    def test_data_files_exist(self):
        """Required data files should exist."""
        data_file = REPO_ROOT / "data" / "housing_panel.csv"
        assert data_file.exists(), "housing_panel.csv not found"
    
    def test_provenance_module_imports(self):
        """repro_tools module should import without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "from repro_tools import git_state, sha256_file, write_build_record"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
    
    def test_example_script_runs(self):
        """Example Python script should run successfully."""
        python_exe = REPO_ROOT / "env" / "scripts" / "runpython"
        if not python_exe.exists():
            pytest.skip("runpython wrapper not found")
        
        result = subprocess.run(
            [str(python_exe), "examples/sample_python.py"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=30,
        )
        assert result.returncode == 0, f"Example failed: {result.stderr}"


class TestProvenanceIntegration:
    """Test provenance tracking in real builds."""
    
    def test_provenance_files_exist(self):
        """Provenance files should exist for built artifacts."""
        prov_dir = REPO_ROOT / "output" / "provenance"
        
        if not prov_dir.exists():
            pytest.skip("No provenance directory (artifacts not built)")
        
        # Check for at least one provenance file
        prov_files = list(prov_dir.glob("*.yml"))
        if not prov_files:
            pytest.skip("No provenance files (artifacts not built)")
        
        assert len(prov_files) > 0
    
    def test_provenance_file_valid(self):
        """Provenance files should be valid YAML with required fields."""
        prov_dir = REPO_ROOT / "output" / "provenance"
        
        if not prov_dir.exists():
            pytest.skip("No provenance directory")
        
        prov_files = list(prov_dir.glob("*.yml"))
        if not prov_files:
            pytest.skip("No provenance files")
        
        # Check first provenance file
        prov_file = prov_files[0]
        
        with open(prov_file) as f:
            data = yaml.safe_load(f)
        
        # Check required fields
        assert "built_at_utc" in data
        assert "command" in data
        assert "git" in data
        assert "inputs" in data
        assert "outputs" in data
        
        # Validate structure
        assert isinstance(data["inputs"], list)
        assert isinstance(data["outputs"], list)
        
        if len(data["inputs"]) > 0:
            assert "sha256" in data["inputs"][0]
        
        if len(data["outputs"]) > 0:
            assert "sha256" in data["outputs"][0]


class TestOutputs:
    """Test that outputs are generated correctly."""
    
    def test_output_directories_exist(self):
        """Output directories should exist if anything has been built."""
        output_dir = REPO_ROOT / "output"
        
        if not output_dir.exists():
            pytest.skip("No output directory (nothing built yet)")
        
        # If output/ exists, check subdirectories
        assert (output_dir / "figures").exists()
        assert (output_dir / "tables").exists()
        assert (output_dir / "provenance").exists()
    
    def test_outputs_match_provenance(self):
        """Output files referenced in provenance should exist."""
        prov_dir = REPO_ROOT / "output" / "provenance"
        
        if not prov_dir.exists():
            pytest.skip("No provenance directory")
        
        prov_files = list(prov_dir.glob("*.yml"))
        if not prov_files:
            pytest.skip("No provenance files")
        
        for prov_file in prov_files:
            with open(prov_file) as f:
                data = yaml.safe_load(f)
            
            # Check that output files exist
            for output in data.get("outputs", []):
                output_path = Path(output["path"])
                assert output_path.exists(), f"Output file missing: {output_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
