#!/usr/bin/env python
"""Generate or verify data/CHECKSUMS.txt.

WHY THIS EXISTS

data/CHECKSUMS.txt was written by hand on 2026-01-17 and then drifted: the
committed housing_panel.csv stopped matching its recorded hash, and
panel_data.csv was never listed at all, so it was unverified. Nobody noticed,
because the only thing that reads the file is `make pre-submit`, and that
command was a silent no-op until 2026-08-17 (repro_tools.cli had no __main__
block, so every argument was ignored and it exited 0).

A record that is maintained by hand drifts from what it describes. This makes
regenerating it a single command, so the file can be kept true rather than
carefully edited.

USAGE

    make data-checksums          # rewrite data/CHECKSUMS.txt from the files
    make data-checksums-check    # verify without writing (exit 1 on mismatch)

WHAT IT COVERS

Every file matching --pattern under --data-dir, sorted, so the output is stable
across machines and filesystems. Large or gitignored data is a project-specific
question: point --data-dir and --pattern wherever the inputs that must not
change silently actually live.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

HEADER = """\
# SHA256 Checksums for Data Files
# Generated: {today} by scripts/update_checksums.py
#
# Verify with: make data-checksums-check
# Or by hand:  cd data && sha256sum -c CHECKSUMS.txt
#
# Regenerate with `make data-checksums` -- do not edit by hand. This file was
# hand-maintained until 2026-08-17 and had drifted from the data it describes.
#
# Checksums are also recorded per artifact in output/provenance/*.yml at build
# time; this file pins the INPUTS, those record what a given result was built
# from.
"""


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(data_dir: Path, patterns: list[str]) -> list[Path]:
    found: set[Path] = set()
    for pattern in patterns:
        found.update(p for p in data_dir.glob(pattern) if p.is_file())
    return sorted(found)


def render(data_dir: Path, files: list[Path], today: str) -> str:
    lines = [HEADER.format(today=today)]
    for path in files:
        lines.append(f"{sha256_file(path)}  {path.relative_to(data_dir)}")
    return "\n".join(lines) + "\n"


def parse_recorded(text: str) -> dict[str, str]:
    recorded = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            recorded[" ".join(parts[1:])] = parts[0]
    return recorded


def verify(data_dir: Path, output: Path, patterns: list[str]) -> int:
    if not output.is_file():
        print(f"{output} does not exist; run `make data-checksums`.")
        return 1

    recorded = parse_recorded(output.read_text())
    present = {str(p.relative_to(data_dir)): p for p in collect(data_dir, patterns)}

    problems = 0
    for name, expected in sorted(recorded.items()):
        path = present.pop(name, None)
        if path is None:
            print(f"missing: {name} is recorded but not present")
            problems += 1
            continue
        actual = sha256_file(path)
        if actual != expected:
            print(f"changed: {name}")
            print(f"    recorded {expected}")
            print(f"    actual   {actual}")
            problems += 1

    for name in sorted(present):
        print(f"unrecorded: {name} matches --pattern but is not in {output.name}")
        problems += 1

    if problems:
        print("")
        print(f"{problems} problem(s). A changed input invalidates every result")
        print("built from it. If the change is intended, rerun")
        print("`make data-checksums` and commit the new file; if not, restore")
        print("the data.")
        return 1

    print(f"{len(recorded)} data file(s) match {output}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data")
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        help="Glob under --data-dir; repeatable. Default: *.csv",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify without writing; exit 1 on any mismatch",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Date stamp to write (default: today). Set for reproducible output.",
    )
    args = parser.parse_args(argv)

    patterns = args.patterns or ["*.csv"]
    output = args.output or (args.data_dir / "CHECKSUMS.txt")

    if not args.data_dir.is_dir():
        print(f"No such data directory: {args.data_dir}")
        return 1

    if args.check:
        return verify(args.data_dir, output, patterns)

    files = collect(args.data_dir, patterns)
    if not files:
        print(f"No files matching {patterns} under {args.data_dir}; nothing written.")
        return 1

    output.write_text(
        render(args.data_dir, files, args.today or date.today().isoformat())
    )
    print(f"Wrote {output} covering {len(files)} file(s):")
    for path in files:
        print(f"  {path.relative_to(args.data_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
