"""Integration tests for shared utilities with run_analysis.py."""

import subprocess


class TestRunAnalysisIntegration:
    """Test run_analysis.py with new shared utilities."""

    def test_run_analysis_list(self):
        """Test --list option works."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "--list"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Available studies:" in result.stdout
        assert "price_base" in result.stdout
        assert "remodel_base" in result.stdout

    def test_run_analysis_version(self):
        """Test --version option works."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "--version"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "run_analysis 1.0" in result.stdout

    def test_run_analysis_unknown_option_suggests(self):
        """Test that unknown options provide suggestions."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "--lists"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "Unknown option --lists" in result.stdout
        assert "Did you mean --list?" in result.stdout

    def test_run_analysis_unknown_study(self):
        """Test error message for unknown study."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "nonexistent_study"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Unknown study 'nonexistent_study'" in result.stdout
        assert "Available studies:" in result.stdout

    def test_run_analysis_shows_configuration(self):
        """Test that configuration is displayed before execution."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "price_base"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "RUNNING STUDY: PRICE_BASE" in result.stdout
        assert "Study" in result.stdout
        assert "Data" in result.stdout
        assert "Y Variable" in result.stdout
        assert "X Variable" in result.stdout

    def test_run_analysis_shows_environment(self):
        """Test that execution environment is displayed."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "price_base"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Execution environment:" in result.stdout
        assert "terminal" in result.stdout or "batch" in result.stdout

    def test_run_analysis_no_arguments(self):
        """Test that no arguments shows usage."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py"],
            capture_output=True,
            text=True,
        )

        # Should show usage and exit with error
        assert result.returncode != 0
        assert "Usage:" in result.stdout or "Usage:" in result.stderr

    def test_run_analysis_help(self):
        """Test --help flag."""
        result = subprocess.run(
            ["env/scripts/runpython", "run_analysis.py", "--help"],
            capture_output=True,
            text=True,
        )

        # Help should exit successfully
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Options:" in result.stdout
        assert (
            "<study>" in result.stdout
        )  # Check for the actual argument name in docstring


class TestConfigImport:
    """Test that config is properly imported from shared."""

    def test_config_imports_from_shared(self):
        """Test that config module is in shared."""
        from shared import config

        assert hasattr(config, "STUDIES")
        assert hasattr(config, "DATA_FILES")
        assert hasattr(config, "REPO_ROOT")
        assert hasattr(config, "OUTPUT_DIR")

    def test_config_studies_structure(self):
        """Test STUDIES dictionary has expected structure.

        Note: Studies may inherit some values from DEFAULTS, so we check
        that required study-specific fields are present.
        """
        from shared.config import DEFAULTS, STUDIES

        assert "price_base" in STUDIES
        assert "remodel_base" in STUDIES

        for study_name, study in STUDIES.items():
            # Required fields that must be study-specific
            assert "yvar" in study, f"{study_name} missing 'yvar'"
            assert "figure" in study, f"{study_name} missing 'figure'"
            assert "table" in study, f"{study_name} missing 'table'"

            # These can come from DEFAULTS or study
            # Check they exist after merging (simulating build_config logic)
            merged = DEFAULTS.copy()
            merged.update(study)
            assert "data" in merged
            assert "xlabel" in merged
            assert "ylabel" in merged
            assert "xvar" in merged

    def test_config_paths_correct(self):
        """Test that config paths are correct relative to project root."""
        from shared.config import DATA_DIR, OUTPUT_DIR, REPO_ROOT

        # REPO_ROOT should be the project root, not shared/
        assert REPO_ROOT.name == "project_template"
        assert (REPO_ROOT / "shared" / "config.py").exists()

        # Paths should be correct
        assert DATA_DIR == REPO_ROOT / "data"
        assert OUTPUT_DIR == REPO_ROOT / "output"
        assert DATA_DIR.exists()


class TestValidationIntegration:
    """Test validation catches real configuration errors."""

    def test_validation_catches_missing_data_file(self, tmp_path, monkeypatch):
        """Test that validation catches missing data files before execution."""
        # This would require modifying STUDIES to have a bad config
        # For now, we test the validation function directly
        from repro_tools import validate_study_config

        bad_config = {
            "data": "nonexistent.csv",
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": "y",
            "xvar": "x",
            "figure": "output/fig.pdf",
            "table": "output/table.tex",
        }

        errors = validate_study_config(bad_config, "test_study")
        assert len(errors) > 0
        assert any("Input file not found" in error for error in errors)
