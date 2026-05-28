#!/usr/bin/env python
"""
remove_analysis.py — cleanly remove an example/analysis from the project.

This is the inverse of "Adding a new analysis" (see README.md). An analysis is
spread across several places, and deleting it by hand easily leaves the build
referencing a study that no longer exists (`make all` then breaks). This removes
all of it together:

  • the name in `ANALYSES :=` and its pattern block in the Makefile
  • its entry in shared/config.py STUDIES (if it has one)
  • its example-specific script — a notebook or run_did.py — but NEVER the shared
    run_analysis.py engine, nor a script still used by another analysis
  • its built artifacts under output/ (figure, table, provenance, log, and the
    executed notebook for notebook analyses)

What it deliberately does NOT touch:

  • tests/ — hand-written assertions are unsafe to rewrite; it reports which test
    files still mention the name so you can finish by hand.
  • paper/ — publish-only. If you'd published this analysis, re-run `make publish`
    to refresh paper/.

Usage:
    python scripts/remove_analysis.py <name>           # dry run (default): show the plan
    python scripts/remove_analysis.py <name> --apply   # actually remove it

Run it from anywhere; it uses only the Python standard library, so it works
before `make environment` too.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Scripts that are project infrastructure, never an example to delete, even if no
# remaining analysis references them.
INFRASTRUCTURE_SCRIPTS = {"run_analysis.py"}


def repo_root() -> Path:
    # scripts/ lives directly under the repo root.
    return Path(__file__).resolve().parent.parent


def parse_analyses(makefile: str) -> list[str]:
    m = re.search(r"^ANALYSES\s*:=\s*(.*)$", makefile, flags=re.M)
    return m.group(1).split() if m else []


def parse_scripts(makefile: str) -> dict[str, str]:
    """Map analysis name -> its `.script` value, as written in the Makefile."""
    return {
        m.group(1): m.group(2).strip()
        for m in re.finditer(r"^(\w+)\.script\s*:=\s*(.+)$", makefile, flags=re.M)
    }


def remove_from_analyses_line(makefile: str, name: str) -> str:
    def repl(m: re.Match[str]) -> str:
        names = [n for n in m.group(1).split() if n != name]
        return "ANALYSES := " + " ".join(names)

    return re.sub(r"^ANALYSES\s*:=\s*(.*)$", repl, makefile, count=1, flags=re.M)


def remove_makefile_block(makefile: str, name: str) -> str:
    """Drop the `# <name> ...` comment + contiguous `<name>.<var> := ...` lines."""
    lines = makefile.splitlines(keepends=True)
    dotted = re.compile(rf"^{re.escape(name)}\.\w+\s*:=")

    start = next((i for i, ln in enumerate(lines) if dotted.match(ln)), None)
    if start is None:
        return makefile

    end = start
    while end + 1 < len(lines) and dotted.match(lines[end + 1]):
        end += 1

    # Absorb an immediately-preceding `# <name> ...` comment line.
    if start > 0 and lines[start - 1].strip().startswith(f"# {name}"):
        start -= 1
    # Absorb one trailing blank line so we don't leave a double blank.
    if end + 1 < len(lines) and lines[end + 1].strip() == "":
        end += 1

    del lines[start : end + 1]
    return "".join(lines)


def remove_study_entry(config: str, name: str) -> tuple[str, bool]:
    """Remove the brace-balanced `"name": { ... },` entry from STUDIES, if present."""
    lines = config.splitlines(keepends=True)
    key = re.compile(rf'^\s*"{re.escape(name)}"\s*:\s*\{{')
    start = next((i for i, ln in enumerate(lines) if key.match(ln)), None)
    if start is None:
        return config, False

    depth = 0
    end = start
    for i in range(start, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if depth == 0:
            end = i
            break

    del lines[start : end + 1]
    return "".join(lines), True


def output_artifacts(root: Path, name: str, script: str) -> list[Path]:
    out = root / "output"
    candidates = [
        out / "figures" / f"{name}.pdf",
        out / "tables" / f"{name}.tex",
        out / "provenance" / f"{name}.yml",
        out / "logs" / f"{name}.log",
    ]
    if script.endswith(".ipynb"):
        stem = Path(script).stem
        candidates.append(out / "executed_notebooks" / f"{stem}_executed.ipynb")
    return [p for p in candidates if p.exists()]


def test_references(root: Path, name: str) -> list[Path]:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    hits = []
    tests = root / "tests"
    if tests.is_dir():
        for f in sorted(tests.rglob("*")):
            if f.suffix in {".py", ".md"} and pattern.search(
                f.read_text(encoding="utf-8", errors="ignore")
            ):
                hits.append(f)
    return hits


def remove_analysis(name: str, *, root: Path | None = None, apply: bool = False) -> int:
    """Cleanly remove one analysis everywhere it's wired in.

    Programmatic entry point shared by the CLI (`main`) and `bootstrap.py`.
    Returns 0 on success (or dry run), 1 if `name` is not in ANALYSES.
    """
    if root is None:
        root = repo_root()
    makefile_path = root / "Makefile"
    config_path = root / "shared" / "config.py"

    makefile = makefile_path.read_text()
    analyses = parse_analyses(makefile)
    if name not in analyses:
        print(f"❌ '{name}' is not in ANALYSES.")
        print(f"   Known analyses: {', '.join(analyses) or '(none)'}")
        return 1

    scripts_map = parse_scripts(makefile)
    script = scripts_map.get(name, "")
    script_basename = Path(script).name if script else ""

    # Decide whether the script is example-owned (safe to delete) or shared/infra.
    remaining = [a for a in analyses if a != name]
    still_used_by = [a for a in remaining if scripts_map.get(a) == script]
    is_infra = script_basename in INFRASTRUCTURE_SCRIPTS
    script_path = (root / script) if script else None
    delete_script = bool(
        script
        and not is_infra
        and not still_used_by
        and script_path is not None
        and script_path.exists()
    )

    artifacts = output_artifacts(root, name, script)
    tests = test_references(root, name)
    config = config_path.read_text()
    new_config, has_study = remove_study_entry(config, name)

    mode = "APPLYING" if apply else "DRY RUN (use --apply to execute)"
    tag = "" if apply else "[would] "
    print(f"\n=== remove-analysis: {name} — {mode} ===\n")

    print(f"{tag}Makefile: drop '{name}' from ANALYSES and remove its pattern block")
    print(
        f"{tag}config.py STUDIES: "
        + ("remove entry" if has_study else "no entry (skip)")
    )

    if script:
        if delete_script:
            print(f"{tag}delete example script: {script}")
        elif is_infra:
            print(f"keep script {script} (shared engine — never deleted)")
        elif still_used_by:
            print(f"keep script {script} (still used by: {', '.join(still_used_by)})")
        else:
            print(f"keep script {script} (not found on disk)")

    if artifacts:
        for p in artifacts:
            print(f"{tag}delete artifact: {p.relative_to(root)}")
    else:
        print("no built artifacts under output/ to delete")

    if tests:
        print("\n⚠️  These test files still mention the name — review/edit by hand:")
        for f in tests:
            print(f"     {f.relative_to(root)}")
    if has_study or name in ("price_base", "remodel_base"):
        print(
            "⚠️  If you'd published this analysis, re-run `make publish` to refresh paper/."
        )

    if not apply:
        print("\nDry run only — nothing changed. Re-run with --apply to remove.\n")
        return 0

    # --- apply ---------------------------------------------------------------
    makefile = remove_from_analyses_line(makefile, name)
    makefile = remove_makefile_block(makefile, name)
    makefile_path.write_text(makefile)
    if has_study:
        config_path.write_text(new_config)
    if delete_script and script_path is not None:
        script_path.unlink()
    for p in artifacts:
        p.unlink()

    print(f"\n✅ Removed '{name}'. Run `make all` to confirm the build still works.")
    if tests:
        print("   Remember to clean up the test references listed above.\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cleanly remove an example/analysis from the project."
    )
    parser.add_argument("name", help="Analysis name (as listed in ANALYSES)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove it (default is a dry run that only prints the plan)",
    )
    args = parser.parse_args()
    return remove_analysis(args.name, apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())
