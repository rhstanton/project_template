"""
Shared utilities for reproducible research template.

Copyright (c) 2026 Richard Stanton
License: MIT
"""

from . import config
from .cli import (
    ConfigBuilder,
    filter_ipython_args,
    friendly_docopt,
    get_execution_environment,
    parse_csv_list,
    parse_float_or_auto,
    parse_int_or_auto,
    parse_string_or_auto,
    print_config,
    print_header,
    setup_environment,
)
from .config_validator import print_validation_errors, validate_config

__all__ = [
    "config",
    "ConfigBuilder",
    "filter_ipython_args",
    "friendly_docopt",
    "get_execution_environment",
    "parse_csv_list",
    "parse_float_or_auto",
    "parse_int_or_auto",
    "parse_string_or_auto",
    "print_config",
    "print_header",
    "print_validation_errors",
    "setup_environment",
    "validate_config",
]
