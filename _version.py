"""Version information for project_template.

This is the version of the template itself, not the repro-tools submodule.
repro-tools has its own versioning in lib/repro-tools/pyproject.toml
"""

__version__ = "2.2.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Release information
__author__ = "Richard Stanton"
__license__ = "MIT"
__url__ = "https://github.com/rhstanton/project_template"

# No REPRO_TOOLS_VERSION here.
#
# It said "0.3.3" while repro-tools' own pyproject.toml said 0.2.0 — a version
# that was never released — and nothing read the value. A hand-maintained
# restatement of a dependency's version has no way to stay right and every
# opportunity to drift, which is what it did across 87 commits.
#
# The submodule commit in git IS the pin, and it is exact. For the human-readable
# version, ask the dependency:
#
#     grep '^version' lib/repro-tools/pyproject.toml
