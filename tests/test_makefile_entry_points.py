"""Makefile recipes must invoke interpreters through the wrappers.

The house rule -- stated in CLAUDE.md and in every generated project -- is that
python, julia and stata are reached through env/scripts/run*, which source
env/env.sh and therefore set PYTHONPATH, DATA_DIR, SOURCE_DATE_EPOCH and the
Julia bridge variables. A bare `python` resolves from PATH instead: a different
interpreter reading a different environment, producing results that differ for
reasons nobody logged.

The rule lived only in prose, and both repositories were breaking it:

    project_template  Makefile:413  @python3 scripts/remove_analysis.py ...
    fire              Makefile:271  cd build-data && python config.py

Neither was noticed, because prose does not fail a build. This scans every
recipe line in the makefiles this project actually uses, including the shared
fragments it includes from repro-tools.

stata-mp is deliberately exempt: the Stata package-install rules have to name
the binary, and they do so knowingly through $(STATA).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REPRO_LIB = REPO_ROOT / "lib/repro-tools/src/repro_tools/lib"
MAKEFILES = [
    REPO_ROOT / "Makefile",
    REPO_ROOT / "env" / "Makefile",
    REPRO_LIB / "common.mk",
    REPRO_LIB / "stata.mk",
]

BARE = re.compile(r"(^|[\s;&|(@])(python3?|julia|jupyter)[\s]")
ALLOWED = re.compile(
    r"runpython|runjulia|runstata|runnotebook|command -v|"
    r"\$\(PYTHON\)|\$\(JULIA\)|\$\(STATA\)|\$\(NOTEBOOK\)"
)


def recipe_lines(path: Path) -> list[tuple[int, str]]:
    out = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.startswith("\t"):
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "@#")):
            continue
        out.append((number, stripped))
    return out


@pytest.mark.parametrize(
    "path",
    MAKEFILES,
    ids=lambda p: p.name if p.name != "Makefile" else str(p.parent.name or "root"),
)
def test_no_bare_interpreter_invocations(path):
    if not path.is_file():
        pytest.skip(f"{path} not present")
    offenders = [
        f"{path.name}:{n}: {line}"
        for n, line in recipe_lines(path)
        if BARE.search(line) and not ALLOWED.search(line)
    ]
    assert not offenders, (
        "recipes must invoke interpreters through env/scripts/run*, which "
        "source env/env.sh:\n  " + "\n  ".join(offenders)
    )


def test_the_detector_would_catch_a_violation():
    """Guard the guard: a regex matching nothing passes everything."""
    assert BARE.search("\tcd build-data && python config.py")
    assert BARE.search("\t@python3 scripts/remove_analysis.py")
    assert ALLOWED.search("\t@$(PYTHON) scripts/remove_analysis.py")


def test_every_makefile_scanned_actually_exists():
    """A path typo would silently reduce this to testing nothing."""
    missing = [str(p) for p in MAKEFILES if not p.is_file()]
    assert not missing, f"makefiles not found: {missing}"
