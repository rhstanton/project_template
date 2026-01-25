"""
Shared utilities for reproducible research template.

NOTE: Most CLI utilities (friendly_docopt, print_config, etc.) have been
moved to repro_tools package to avoid code duplication across projects.

Import from repro_tools:
  from repro_tools import friendly_docopt, print_config, validate_study_config, etc.

This module now only contains project-specific configuration.

Copyright (c) 2026 Richard Stanton
License: MIT
"""

from . import config

__all__ = [
    "config",
]
