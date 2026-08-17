"""The acceptance test must be able to fail, and must accept only what is declared.

`make check-baseline` compares generated tables against env/baseline/published.json.
It exists because `make diff-outputs` compares against paper/, which is gitignored
and may live in a different repository -- so in CI and in a fresh clone that
comparison has no reference and quietly does nothing.

A check that cannot fail is worse than no check, because it is believed. So the
cases below are mostly failure cases: a changed cell, a missing table, a
deviation that does not match what the code now produces. The passing case is
one test; the rest establish that passing means something.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "env" / "scripts" / "check_baseline.py"

TABLE = """\\begin{tabular}{rr}
\\toprule
year & mean_outcome \\\\
\\midrule
2015 & 5.03 \\\\
2016 & 5.13 \\\\
\\bottomrule
\\end{tabular}
"""


def load_module(tmp_path: Path, tables_dir: Path, baseline: Path):
    """Import check_baseline with its module-level paths redirected at tmp_path.

    The script resolves REPO/BASELINE/TABLES at import time from its own
    location, which is right for the real project and useless for a test. So it
    is imported under a private name and those three constants are rebound.
    """
    spec = importlib.util.spec_from_file_location("check_baseline_undertest", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.TABLES = tables_dir
    mod.BASELINE = baseline
    return mod


@pytest.fixture
def env(tmp_path):
    tables = tmp_path / "output" / "tables"
    tables.mkdir(parents=True)
    (tables / "price_base.tex").write_text(TABLE)
    baseline = tmp_path / "env" / "baseline" / "published.json"
    baseline.parent.mkdir(parents=True)
    mod = load_module(tmp_path, tables, baseline)
    return mod, tables, baseline


def record_then_load(mod) -> dict:
    assert mod.record() == 0
    return json.loads(mod.BASELINE.read_text())


def test_records_and_then_passes(env):
    """A freshly recorded baseline matches the outputs it was recorded from."""
    mod, _, _ = env
    baseline = record_then_load(mod)
    assert mod.check(baseline) == 0


def test_changed_cell_fails(env):
    """The regression this whole file exists for."""
    mod, tables, _ = env
    baseline = record_then_load(mod)
    (tables / "price_base.tex").write_text(TABLE.replace("5.13", "9.99"))
    assert mod.check(baseline) == 1, (
        "a changed published number did not fail the acceptance test"
    )


def test_missing_table_fails(env):
    """An output that was not generated is a failure, not a skip."""
    mod, tables, _ = env
    baseline = record_then_load(mod)
    (tables / "price_base.tex").unlink()
    assert mod.check(baseline) == 1


def test_declared_deviation_is_accepted(env):
    """A difference with a reason attached passes."""
    mod, tables, _ = env
    baseline = record_then_load(mod)
    (tables / "price_base.tex").write_text(TABLE.replace("5.13", "9.99"))
    baseline["tables"]["price_base"]["deviations"] = [
        {
            "row": 1,
            "column": 1,
            "published": "5.13",
            "current": "9.99",
            "why": "corrected a filter bug; see DECISIONS.md",
        }
    ]
    assert mod.check(baseline) == 0


def test_deviation_must_match_the_current_value(env):
    """A stale deviation does not launder a second, different change.

    Without this, declaring a deviation once would permanently exempt that cell
    -- so a later unrelated change to the same number would pass silently. The
    declaration is about a specific value, not about a coordinate.
    """
    mod, tables, _ = env
    baseline = record_then_load(mod)
    (tables / "price_base.tex").write_text(TABLE.replace("5.13", "7.77"))
    baseline["tables"]["price_base"]["deviations"] = [
        {
            "row": 1,
            "column": 1,
            "published": "5.13",
            "current": "9.99",
            "why": "a different change than the one now present",
        }
    ]
    assert mod.check(baseline) == 1


def test_header_change_fails(env):
    """Renaming a column changes what the table says, so it must be noticed."""
    mod, tables, _ = env
    baseline = record_then_load(mod)
    (tables / "price_base.tex").write_text(TABLE.replace("mean_outcome", "mean_price"))
    assert mod.check(baseline) == 1


def test_missing_baseline_is_not_a_failure(env, capsys):
    """A project with nothing published yet has nothing to have drifted from."""
    mod, _, baseline = env
    assert not baseline.exists()
    with pytest.raises(SystemExit) as exc:
        mod.load_baseline()
    assert exc.value.code == 0
    assert "has not recorded its published numbers" in capsys.readouterr().out


def test_parser_ignores_rules_and_blank_lines(env):
    """Structure lines are not data rows."""
    mod, tables, _ = env
    header, rows = mod.parse_table(tables / "price_base.tex")
    assert header == ["year", "mean_outcome"]
    assert rows == [["2015", "5.03"], ["2016", "5.13"]]


def test_script_is_runnable_as_a_program(env):
    """`make check-baseline` invokes this as a script, not as an import."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "--record" in result.stdout
