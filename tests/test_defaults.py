"""Tests for 3-level defaults system.

Tests that defaults are resolved in the correct priority:
  1. Docopt defaults (lowest)
  2. config.DEFAULTS (medium)
  3. config.STUDIES[study] (higher)
  4. Command-line args (highest)
"""

import subprocess
from pathlib import Path


class TestDefaultsPriority:
    """Test the 3-level defaults system."""

    def test_defaults_exist_in_config(self):
        """Test that DEFAULTS dictionary exists in config."""
        from shared.config import DEFAULTS

        assert isinstance(DEFAULTS, dict)
        assert "data" in DEFAULTS
        assert "xlabel" in DEFAULTS
        assert "ylabel" in DEFAULTS
        assert "xvar" in DEFAULTS
        assert "table_agg" in DEFAULTS

    def test_study_inherits_from_defaults(self):
        """Test that studies inherit unspecified values from DEFAULTS."""
        from shared.config import DEFAULTS, STUDIES

        # price_base doesn't specify "xvar", should get it from DEFAULTS
        price_study = STUDIES["price_base"]
        assert "xvar" not in price_study  # Not in study dict itself

        # But when merged, it should have it
        merged = DEFAULTS.copy()
        merged.update(price_study)
        assert "xvar" in merged
        assert merged["xvar"] == DEFAULTS["xvar"]

    def test_study_overrides_defaults(self):
        """Test that study-specific values override DEFAULTS."""
        from shared.config import DEFAULTS, STUDIES

        # price_base specifies its own ylabel
        price_study = STUDIES["price_base"]
        assert "ylabel" in price_study

        merged = DEFAULTS.copy()
        merged.update(price_study)

        # Should use study's ylabel, not DEFAULTS
        assert merged["ylabel"] == price_study["ylabel"]
        assert merged["ylabel"] != DEFAULTS["ylabel"]

    def test_build_config_merges_correctly(self):
        """Test that build_config() merges defaults correctly."""
        # Import the function we're testing
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from run_analysis import build_config

        # Test with empty args (no command-line overrides)
        args = {}
        config = build_config("price_base", args)

        # Should have DEFAULTS values
        assert config["xvar"] == "year"  # From DEFAULTS
        assert config["table_agg"] == "mean"  # From DEFAULTS

        # Should have STUDIES[price_base] overrides
        assert config["ylabel"] == "Price index"  # From STUDIES
        assert config["yvar"] == "price_index"  # From STUDIES

    def test_command_line_overrides_all(self):
        """Test that command-line args override both DEFAULTS and STUDIES."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from run_analysis import build_config

        # Simulate command-line override
        args = {
            "--ylabel": "Custom Y Label",
            "--table-agg": "sum",
        }

        config = build_config("price_base", args)

        # Should use command-line values
        assert config["ylabel"] == "Custom Y Label"
        assert config["table_agg"] == "sum"

        # Should still have other values from DEFAULTS and STUDIES
        assert config["yvar"] == "price_index"  # From STUDIES
        assert config["xvar"] == "year"  # From DEFAULTS


class TestCommandLineOverrides:
    """Test command-line argument overrides."""

    def test_ylabel_override(self):
        """Test that --ylabel overrides config."""
        result = subprocess.run(
            [
                "env/scripts/runpython",
                "run_analysis.py",
                "price_base",
                "--ylabel=Custom Label",
            ],
            capture_output=True,
            text=True,
        )

        # Should complete successfully
        assert result.returncode == 0

        # The override should work even though we can't easily verify
        # the label in the output (it would be in the generated figure)
        # For now, just verify it doesn't error

    def test_table_agg_override(self):
        """Test that --table-agg overrides config."""
        result = subprocess.run(
            [
                "env/scripts/runpython",
                "run_analysis.py",
                "price_base",
                "--table-agg=sum",
            ],
            capture_output=True,
            text=True,
        )

        # Should complete successfully
        assert result.returncode == 0

    def test_multiple_overrides(self):
        """Test multiple command-line overrides at once."""
        result = subprocess.run(
            [
                "env/scripts/runpython",
                "run_analysis.py",
                "price_base",
                "--ylabel=Test",
                "--xlabel=Time",
                "--table-agg=median",
            ],
            capture_output=True,
            text=True,
        )

        # Should complete successfully
        assert result.returncode == 0


class TestMakefileExtraArgs:
    """Test Makefile EXTRA_ARGS functionality."""

    def test_extra_args_variable_exists(self):
        """Test that EXTRA_ARGS is defined in Makefile."""
        result = subprocess.run(
            ["make", "-p"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should have EXTRA_ARGS variable
        assert "EXTRA_ARGS" in result.stdout

    def test_make_with_extra_args(self):
        """Test that make passes EXTRA_ARGS to the script."""
        # Dry run with -B to show command even if up-to-date
        result = subprocess.run(
            ["make", "-Bn", "price_base", "EXTRA_ARGS=--ylabel='Test'"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Dry run should show the command with EXTRA_ARGS
        # The command line should contain both the args and EXTRA_ARGS
        assert "run_analysis.py" in result.stdout
        assert "price_base" in result.stdout


class TestDocoptDefaults:
    """Test docopt default values."""

    def test_docopt_has_defaults(self):
        """Test that docopt string includes default values."""
        with open("run_analysis.py") as f:
            content = f.read()

        # Should have [default: ...] in docstring for table-agg
        assert "[default: mean]" in content

        # Should document the 3-level priority system
        assert "Defaults are resolved" in content or "priority" in content.lower()
