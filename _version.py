"""Version information for project_template.

This is the version of the template itself, not the repro-tools submodule.
repro-tools has its own versioning in lib/repro-tools/pyproject.toml
"""

__version__ = "1.0.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Release information
__author__ = "Richard Stanton"
__license__ = "MIT"
__url__ = "https://github.com/rhstanton/project_template"

# Dependencies (for reference)
REPRO_TOOLS_VERSION = "0.2.0"  # See lib/repro-tools/pyproject.toml
