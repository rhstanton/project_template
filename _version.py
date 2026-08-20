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
# It said "0.3.3" and nothing read the value. Removed because a hand-maintained
# restatement of a dependency's version has no way to stay right — but note that
# it was NOT the thing that was wrong. v0.3.3 was a real tag; repro-tools'
# pyproject.toml was the record that had drifted, sitting at 0.2.0 through four
# tagged releases. This constant was the only place in either repository stating
# the truth, and it stated it by accident, having been copied from a tag name.
#
# Which is the argument for deleting it rather than fixing it: a value that is
# right by luck and unreadable by any check is not a record.
#
# The submodule commit in git IS the pin, and it is exact. For the human-readable
# version, ask the dependency:
#
#     grep '^version' lib/repro-tools/pyproject.toml
