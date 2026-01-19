"""Tests for configuration validation."""

from pathlib import Path

import pytest

from repro_tools import print_validation_errors
from shared import validate_config


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_config_valid(self, tmp_path):
        """Test validation with valid configuration."""
        # Create a temporary data file
        data_file = tmp_path / "test_data.csv"
        data_file.write_text("x,y\n1,2\n3,4\n")
        
        config = {
            "data": str(data_file),
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": "y",
            "xvar": "x",
            "figure": str(tmp_path / "fig.pdf"),
            "table": str(tmp_path / "table.tex"),
        }
        
        errors = validate_config(config, "test_study")
        assert errors == []

    def test_validate_config_missing_required_keys(self):
        """Test validation catches missing required keys."""
        config = {
            "data": "test.csv",
            "xlabel": "X",
            # Missing ylabel, yvar, xvar, figure, table
        }
        
        errors = validate_config(config, "test_study")
        assert len(errors) > 0
        assert any("Missing required config" in error for error in errors)

    def test_validate_config_missing_data_file(self):
        """Test validation catches missing data file."""
        config = {
            "data": "nonexistent_file.csv",
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": "y",
            "xvar": "x",
            "figure": "output/fig.pdf",
            "table": "output/table.tex",
        }
        
        errors = validate_config(config, "test_study")
        assert any("Input file not found" in error for error in errors)

    def test_validate_config_invalid_variable_type(self):
        """Test validation catches non-string variable names."""
        config = {
            "data": "test.csv",
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": 123,  # Should be string
            "xvar": "x",
            "figure": "output/fig.pdf",
            "table": "output/table.tex",
        }
        
        errors = validate_config(config, "test_study")
        assert any("must be a string" in error for error in errors)

    def test_validate_config_invalid_aggregation(self):
        """Test validation catches invalid aggregation function."""
        config = {
            "data": "test.csv",
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": "y",
            "xvar": "x",
            "figure": "output/fig.pdf",
            "table": "output/table.tex",
            "table_agg": "invalid_agg",
        }
        
        errors = validate_config(config, "test_study")
        assert any("Invalid table_agg" in error for error in errors)

    def test_validate_config_valid_aggregations(self, tmp_path):
        """Test that valid aggregations pass validation."""
        data_file = tmp_path / "test_data.csv"
        data_file.write_text("x,y\n1,2\n")
        
        valid_aggs = ["mean", "sum", "median", "min", "max", "count", "std", "var"]
        
        for agg in valid_aggs:
            config = {
                "data": str(data_file),
                "xlabel": "X",
                "ylabel": "Y",
                "yvar": "y",
                "xvar": "x",
                "figure": str(tmp_path / "fig.pdf"),
                "table": str(tmp_path / "table.tex"),
                "table_agg": agg,
            }
            
            errors = validate_config(config, "test_study")
            assert errors == [], f"Aggregation '{agg}' should be valid but got errors: {errors}"

    def test_validate_config_creates_output_directories(self, tmp_path):
        """Test validation creates output directories if they don't exist."""
        data_file = tmp_path / "test_data.csv"
        data_file.write_text("x,y\n1,2\n")
        
        output_dir = tmp_path / "new_output_dir"
        
        config = {
            "data": str(data_file),
            "xlabel": "X",
            "ylabel": "Y",
            "yvar": "y",
            "xvar": "x",
            "figure": str(output_dir / "fig.pdf"),
            "table": str(output_dir / "table.tex"),
        }
        
        errors = validate_config(config, "test_study")
        assert errors == []
        assert output_dir.exists()


class TestPrintValidationErrors:
    """Test validation error printing."""

    def test_print_validation_errors_basic(self, capsys):
        """Test basic error printing."""
        errors = [
            "Missing required config: yvar",
            "Input file not found: data.csv",
        ]
        
        print_validation_errors(errors)
        
        captured = capsys.readouterr()
        assert "Configuration Validation Failed" in captured.out
        assert "Found 2 error(s)" in captured.out
        assert "1. Missing required config: yvar" in captured.out
        assert "2. Input file not found: data.csv" in captured.out

    def test_print_validation_errors_with_continuation(self, capsys):
        """Test error printing with continuation lines."""
        errors = [
            "Input file not found: data.csv",
            "  Expected location: /path/to/data.csv",
        ]
        
        print_validation_errors(errors)
        
        captured = capsys.readouterr()
        assert "1. Input file not found: data.csv" in captured.out
        assert "    Expected location: /path/to/data.csv" in captured.out
