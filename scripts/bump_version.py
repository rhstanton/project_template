#!/usr/bin/env python
"""
bump_version.py — set this project's version everywhere it appears, at once.

Works for this template AND for any project derived from it: the current
version and the package name are read from pyproject.toml (the source of
truth), so the tool adapts to your renamed project. Every other file is updated
only if its pattern is actually present, and skipped (not errored) otherwise —
so a derived project that has edited or removed the template's docs still bumps
cleanly.

Updated when present:
  • pyproject.toml   [project] version                 (required)
  • uv.lock          this project's package entry        (matched by name)
  • _version.py      __version__
  • CITATION.cff     version:  +  date-released: <today>
  • README.md        **Current version: X**
  • QUICKSTART.md    template vX
  • CHANGELOG.md     ## [Unreleased]  ->  ## [X] - <today>  (+ fresh Unreleased)

Usage:
    python scripts/bump_version.py <version>            # dry run: show the plan
    python scripts/bump_version.py <version> --apply    # write the changes
    python scripts/bump_version.py <version> --apply --date 2026-05-27

Or via Make:
    make bump-version VERSION=2.1.0

Stdlib-only, so it runs from anywhere (even before `make environment`). It does
NOT git-commit, tag, or publish — that stays a deliberate, reviewable step.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def project_field(pyproject: str, key: str) -> str | None:
    """Read `key = "..."` from the [project] table of pyproject.toml."""
    table = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[)", pyproject)
    body = table.group(1) if table else pyproject
    match = re.search(rf'(?m)^{key}\s*=\s*"([^"]+)"', body)
    return match.group(1) if match else None


def normalize(name: str) -> str:
    """PEP 503 package-name normalization (matches how uv.lock spells it)."""
    return re.sub(r"[-_.]+", "-", name).lower()


class Edit:
    """One find/replace against a file. Optional files are skipped silently."""

    def __init__(self, rel, find, replace, *, required=False, regex=False):
        self.rel = rel
        self.find = find
        self.replace = replace
        self.required = required
        self.regex = regex

    def run(self, write: bool) -> int:
        path = REPO_ROOT / self.rel
        if not path.exists():
            return 0
        text = path.read_text()
        if self.regex:
            new_text, count = re.subn(self.find, self.replace, text, count=1)
        else:
            count = 1 if self.find in text else 0
            new_text = text.replace(self.find, self.replace, 1)
        if count and write:
            path.write_text(new_text)
        return count


def plan(current: str, new: str, name: str, date: str) -> list[Edit]:
    norm = normalize(name)
    return [
        Edit(
            "pyproject.toml",
            f'version = "{current}"',
            f'version = "{new}"',
            required=True,
        ),
        Edit(
            "uv.lock",
            f'name = "{norm}"\nversion = "{current}"',
            f'name = "{norm}"\nversion = "{new}"',
        ),
        Edit("_version.py", f'__version__ = "{current}"', f'__version__ = "{new}"'),
        Edit("CITATION.cff", f"version: {current}", f"version: {new}"),
        Edit(
            "CITATION.cff",
            r"(?m)^date-released: .*",
            f"date-released: {date}",
            regex=True,
        ),
        Edit(
            "README.md",
            f"**Current version: {current}**",
            f"**Current version: {new}**",
        ),
        Edit("QUICKSTART.md", f"template v{current}", f"template v{new}"),
        Edit(
            "CHANGELOG.md",
            "## [Unreleased]\n",
            f"## [Unreleased]\n\n## [{new}] - {date}\n",
        ),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Bump this project's version everywhere.")
    ap.add_argument("version", help="new version, e.g. 2.1.0")
    ap.add_argument(
        "--apply", action="store_true", help="write changes (default: dry run)"
    )
    ap.add_argument(
        "--date",
        default=datetime.date.today().isoformat(),
        help="release date for CITATION.cff / CHANGELOG (default: today)",
    )
    args = ap.parse_args()

    new = args.version
    if not SEMVER_RE.match(new):
        sys.exit(f"error: '{new}' is not a valid X.Y.Z version")

    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    current = project_field(pyproject, "version")
    name = project_field(pyproject, "name")
    if not current or not name:
        sys.exit("error: could not read name/version from pyproject.toml [project]")
    if new == current:
        sys.exit(f"error: version is already {current}")

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"{name}: {current} -> {new}  (date {args.date})  [{mode}]\n")

    failed_required = False
    for edit in plan(current, new, name, args.date):
        if edit.run(args.apply):
            print(f"  ✓ {edit.rel}")
        elif edit.required:
            print(f"  ✗ {edit.rel}: REQUIRED pattern not found")
            failed_required = True
        else:
            print(f"  · {edit.rel}: no match — skipped")

    print()
    if not args.apply:
        print(
            "Dry run — nothing written. "
            "Re-run with --apply (or: make bump-version VERSION=...)."
        )
    else:
        print(f"Done. Review `git diff`, then commit and tag v{new} when ready.")
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
