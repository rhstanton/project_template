"""Tests for shared CLI utilities."""

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from shared import (
    ConfigBuilder,
    filter_ipython_args,
    friendly_docopt,
    get_execution_environment,
    parse_csv_list,
    parse_float_or_auto,
    parse_int_or_auto,
    parse_string_or_auto,
    print_config,
)


class TestFriendlyDocopt:
    """Test friendly_docopt with enhanced error messages."""

    def test_friendly_docopt_basic(self):
        """Test basic docopt parsing."""
        doc = """Usage: test.py <arg>"""
        with patch.object(sys, "argv", ["test.py", "value"]):
            args = friendly_docopt(doc)
            assert args["<arg>"] == "value"

    def test_friendly_docopt_with_flags(self):
        """Test parsing with flags."""
        doc = """Usage: test.py [--flag]
        
        Options:
          --flag  A flag
        """
        with patch.object(sys, "argv", ["test.py", "--flag"]):
            args = friendly_docopt(doc)
            assert args["--flag"] is True

    def test_friendly_docopt_typo_suggestion(self, capsys):
        """Test that typos suggest corrections."""
        doc = """Usage: test.py [--list]
        
        Options:
          --list  Show list
        """
        with patch.object(sys, "argv", ["test.py", "--lists"]):
            with pytest.raises(SystemExit) as exc_info:
                friendly_docopt(doc)
            
            assert exc_info.value.code == 2
            captured = capsys.readouterr()
            assert "Unknown option --lists" in captured.out
            assert "Did you mean --list?" in captured.out

    def test_friendly_docopt_version(self, capsys):
        """Test version flag."""
        doc = """Usage: test.py
        
        Options:
          --version  Show version
        """
        with patch.object(sys, "argv", ["test.py", "--version"]):
            with pytest.raises(SystemExit):
                friendly_docopt(doc, version="1.0")
            
            captured = capsys.readouterr()
            assert "1.0" in captured.out


class TestParseFunctions:
    """Test parse utility functions."""

    def test_parse_csv_list_basic(self):
        """Test parsing comma-separated list."""
        result = parse_csv_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_csv_list_with_spaces(self):
        """Test CSV parsing with spaces."""
        result = parse_csv_list("a, b , c")
        assert result == ["a", "b", "c"]

    def test_parse_csv_list_empty(self):
        """Test empty string returns empty list."""
        assert parse_csv_list("") == []
        assert parse_csv_list(None) == []

    def test_parse_int_or_auto(self):
        """Test integer or auto parsing."""
        assert parse_int_or_auto("42") == 42
        assert parse_int_or_auto("auto") is None
        assert parse_int_or_auto("auto", default=10) == 10
        assert parse_int_or_auto(None, default=5) == 5

    def test_parse_float_or_auto(self):
        """Test float or auto parsing."""
        assert parse_float_or_auto("3.14") == 3.14
        assert parse_float_or_auto("auto") is None
        assert parse_float_or_auto("auto", default=1.5) == 1.5
        assert parse_float_or_auto(None, default=2.5) == 2.5

    def test_parse_string_or_auto(self):
        """Test string or auto parsing."""
        assert parse_string_or_auto("hello") == "hello"
        assert parse_string_or_auto("auto") is None
        assert parse_string_or_auto("auto", default="default") == "default"
        assert parse_string_or_auto(None, default="fallback") == "fallback"

    def test_parse_int_or_auto_invalid(self):
        """Test that invalid integer raises ValueError."""
        with pytest.raises(ValueError):
            parse_int_or_auto("not-a-number")

    def test_parse_float_or_auto_invalid(self):
        """Test that invalid float raises ValueError."""
        with pytest.raises(ValueError):
            parse_float_or_auto("not-a-float")

    def test_parse_csv_list_single_item(self):
        """Test CSV with single item."""
        assert parse_csv_list("single") == ["single"]

    def test_parse_csv_list_empty_items(self):
        """Test CSV with empty items (should be filtered)."""
        result = parse_csv_list("a,,b,  ,c")
        assert result == ["a", "b", "c"]


class TestPrintConfig:
    """Test configuration printing."""

    def test_print_config_basic(self, capsys):
        """Test basic configuration printing."""
        config = {"key1": "value1", "key2": "value2"}
        print_config(config)
        
        captured = capsys.readouterr()
        assert "CONFIGURATION" in captured.out
        assert "key1" in captured.out
        assert "value1" in captured.out
        assert "key2" in captured.out
        assert "value2" in captured.out
        assert "=" * 72 in captured.out

    def test_print_config_custom_title(self, capsys):
        """Test configuration with custom title."""
        config = {"test": "value"}
        print_config(config, title="CUSTOM TITLE")
        
        captured = capsys.readouterr()
        assert "CUSTOM TITLE" in captured.out

    def test_print_config_empty(self, capsys):
        """Test empty configuration."""
        print_config({})
        
        captured = capsys.readouterr()
        assert "(empty)" in captured.out


class TestConfigBuilder:
    """Test ConfigBuilder pattern."""

    def test_config_builder_basic(self):
        """Test basic ConfigBuilder usage."""
        args = {"--input": "test.csv", "--limit": "10"}
        builder = ConfigBuilder(args)
        builder.add("input_path", lambda: args["--input"])
        builder.add("limit", lambda: int(args["--limit"]))
        
        config = builder.build(print_output=False)
        assert config["input_path"] == "test.csv"
        assert config["limit"] == 10

    def test_config_builder_with_display_name(self):
        """Test ConfigBuilder with custom display names."""
        args = {"--val": "42"}
        builder = ConfigBuilder(args)
        builder.add("value", lambda: int(args["--val"]), display_name="Custom Value")
        
        config = builder.build(print_output=False)
        assert config["value"] == 42

    def test_config_builder_prints(self, capsys):
        """Test ConfigBuilder prints configuration."""
        args = {"--test": "value"}
        builder = ConfigBuilder(args)
        builder.add("test_key", lambda: args["--test"])
        
        config = builder.build(print_output=True)
        
        captured = capsys.readouterr()
        assert "CONFIGURATION" in captured.out
        assert "Test Key" in captured.out  # Auto-formatted from test_key
        assert "value" in captured.out

    def test_config_builder_error_propagation(self):
        """Test that errors in builders propagate."""
        args = {"--bad": "not-a-number"}
        builder = ConfigBuilder(args)
        builder.add("value", lambda: int(args["--bad"]))
        
        # Should raise ValueError when build is called
        with pytest.raises(ValueError):
            builder.build(print_output=False)


class TestEnvironmentDetection:
    """Test environment detection functions."""

    def test_get_execution_environment_terminal(self):
        """Test detection of terminal environment."""
        # When not in IPython/Jupyter, should detect terminal or batch
        env = get_execution_environment()
        assert env in ["terminal", "batch"]

    def test_filter_ipython_args(self):
        """Test filtering IPython-specific arguments."""
        original_argv = sys.argv.copy()
        
        try:
            sys.argv = [
                "script.py",
                "arg1",
                "--simple-prompt",
                "arg2",
                "--colors=NoColor",
                "arg3",
            ]
            
            filter_ipython_args()
            
            assert sys.argv == ["script.py", "arg1", "arg2", "arg3"]
        finally:
            sys.argv = original_argv

    def test_filter_ipython_args_preserves_normal_args(self):
        """Test that normal arguments are preserved."""
        original_argv = sys.argv.copy()
        
        try:
            # Use arguments that don't look like IPython flags
            sys.argv = ["script.py", "input.csv", "output.pdf"]
            
            filter_ipython_args()
            
            assert sys.argv == ["script.py", "input.csv", "output.pdf"]
        finally:
            sys.argv = original_argv
