"""Check generated tables against the numbers this project published.

WHY THIS EXISTS

`make diff-outputs` compares `output/` against `paper/`, and that is a good
check -- but `paper/` is gitignored by design, because the template intends it
to be a *separate* repository synced with Overleaf. So the reference is not in
this repository at all. On a CI runner, or in a fresh clone, there is nothing to
compare against and the comparison silently has no work to do.

That is exactly how a real project lost track of its own numbers: the published
values lived only in a manuscript kept elsewhere, an output tree from an unknown
date sat in the working copy looking authoritative, and nothing in the analysis
repository recorded what had actually been sent out. Recovering it took a full
session of archaeology against PDF creation dates.

The fix is not a better directory comparison. It is to keep a small, committed
record of the published numbers *inside* the analysis repository, so the claim
"the code still produces what we published" can be checked by anyone who clones
it, with no manuscript present.

    make check-baseline          # the acceptance test
    make check-baseline-record   # (re)record -- read the warning it prints

WHAT COUNTS AS A FAILURE

Any cell that differs from the baseline and is not listed under `deviations`.
A deviation must carry a reason; an undeclared difference is a failure even if
someone believes it is fine. The point is that changes to published numbers are
noticed and explained, not that they never happen.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASELINE = REPO / "env" / "baseline" / "published.json"
TABLES = REPO / "output" / "tables"


def parse_table(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return (header, rows) from a booktabs LaTeX tabular.

    Deliberately tolerant about what surrounds the data and strict about the
    data itself: everything between \\midrule and \\bottomrule is a row, cells
    split on unescaped `&`, and trailing `\\\\` is dropped. It does not try to
    understand multicolumn or nested tabulars -- if a project's tables outgrow
    this, replacing this one function is the intended way to adapt.
    """
    text = path.read_text(encoding="utf-8")

    body = text
    if "\\midrule" in text and "\\bottomrule" in text:
        body = text.split("\\midrule", 1)[1].split("\\bottomrule", 1)[0]

    header: list[str] = []
    if "\\toprule" in text and "\\midrule" in text:
        head_text = text.split("\\toprule", 1)[1].split("\\midrule", 1)[0]
        header = _cells(head_text)

    rows = []
    for line in body.splitlines():
        cells = _cells(line)
        if cells:
            rows.append(cells)
    return header, rows


def _cells(chunk: str) -> list[str]:
    """Split one LaTeX row into stripped cells, or [] if it holds no data."""
    line = chunk.strip()
    if not line or line.startswith("%"):
        return []
    line = line.replace("\\\\", "")
    # Split on & that is not escaped as \&.
    cells = [c.strip() for c in re.split(r"(?<!\\)&", line)]
    if not any(cells):
        return []
    return cells


def load_baseline() -> dict:
    if not BASELINE.exists():
        print(f"No baseline at {BASELINE}.")
        print("")
        print("This project has not recorded its published numbers yet. Once")
        print("there are outputs worth pinning, record them with:")
        print("    make check-baseline-record")
        print("")
        print("Not a failure: a project with nothing published yet has nothing")
        print("to have drifted from.")
        sys.exit(0)
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _deviation_index(entry: dict) -> dict[tuple[int, int], dict]:
    """Map (row, column) -> declared deviation for one table."""
    out = {}
    for dev in entry.get("deviations", []):
        out[(dev["row"], dev["column"])] = dev
    return out


def check(baseline: dict) -> int:
    problems = 0
    declared = 0
    checked = 0

    for name, entry in sorted(baseline.get("tables", {}).items()):
        path = TABLES / entry["output_tex"]
        if not path.exists():
            print(f"FAIL {name}: {path} was not generated")
            problems += 1
            continue

        header, rows = parse_table(path)
        devs = _deviation_index(entry)

        if header and entry.get("header") and header != entry["header"]:
            print(f"FAIL {name}: header changed")
            print(f"       published {entry['header']}")
            print(f"       current   {header}")
            problems += 1

        want_rows = entry["rows"]
        if len(rows) != len(want_rows):
            print(
                f"FAIL {name}: {len(want_rows)} published rows, {len(rows)} generated"
            )
            problems += 1

        for i, want in enumerate(want_rows):
            got = rows[i] if i < len(rows) else []
            for j, want_cell in enumerate(want):
                checked += 1
                got_cell = got[j] if j < len(got) else "<absent>"
                if got_cell == want_cell:
                    continue
                dev = devs.get((i, j))
                if dev and dev.get("current") == got_cell:
                    declared += 1
                    continue
                label = f"row {i} col {j}"
                if want and len(want) > 0:
                    label = f"row {want[0]!r} col {j}"
                print(f"FAIL {name}: {label}")
                print(f"       published {want_cell!r}")
                print(f"       current   {got_cell!r}")
                if dev:
                    print(
                        f"       (a deviation is declared here, but it expects "
                        f"{dev.get('current')!r})"
                    )
                problems += 1

    print("")
    print(f"{checked} cells checked against {BASELINE.name}")
    if declared:
        print(f"{declared} declared deviation(s) accepted")
    if problems:
        print(f"{problems} undeclared difference(s).")
        print("")
        print("Either the change is wrong, or it is right and belongs in the")
        print("`deviations` list with a reason. Both are fine; silence is not.")
        return 1
    print("No undeclared differences.")
    return 0


def record() -> int:
    """Write the current outputs into the baseline."""
    print("RECORDING the current outputs as the published baseline.")
    print("")
    print("Read this before trusting the result. A baseline recorded from the")
    print("pipeline agrees with the pipeline BY CONSTRUCTION -- it can only")
    print("detect future drift, never confirm that today's numbers match what")
    print("a manuscript actually prints. If numbers have already been sent")
    print("somewhere, transcribe them from that document instead of running")
    print("this, or you are pinning the wrong thing and will not find out.")
    print("")

    if not TABLES.exists():
        print(f"No tables at {TABLES}; run `make all` first.")
        return 1

    tables = {}
    for path in sorted(TABLES.glob("*.tex")):
        header, rows = parse_table(path)
        if not rows:
            print(f"  skipped {path.name}: no data rows parsed")
            continue
        tables[path.stem] = {
            "output_tex": path.name,
            "header": header,
            "rows": rows,
            "deviations": [],
        }
        print(f"  recorded {path.name}: {len(rows)} rows")

    if not tables:
        print("Nothing recorded.")
        return 1

    payload = {
        "_comment": (
            "Numbers this project published. Committed inside the analysis "
            "repository on purpose: paper/ is gitignored and may live in a "
            "different repository, so it cannot serve as the reference here. "
            "Checked by `make check-baseline`."
        ),
        "_deviation_format": (
            "Each entry in a table's `deviations` list is "
            "{row, column, published, current, why}. `why` is required: an "
            "undeclared difference fails the check."
        ),
        "tables": tables,
    }
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("")
    print(f"Wrote {BASELINE}")
    print("Commit it. A baseline that is not committed protects nothing.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--record",
        action="store_true",
        help="write current outputs as the baseline (read the warning)",
    )
    args = ap.parse_args(argv)

    if args.record:
        return record()
    return check(load_baseline())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
