#!/usr/bin/env python
"""
Publish specific output files to paper/ directory.

This script handles file-level selective publishing, allowing you to publish
only specific figures, tables, or other outputs without publishing entire analyses.

Usage:
    python publish_specific_files.py \\
        --paper-root paper \\
        --files "output/figures/fig1.pdf output/tables/tab1.tex" \\
        --allow-dirty 0 \\
        --require-not-behind 1 \\
        --require-current-head 0
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any, Dict

import yaml

from scripts.provenance import git_state, sha256_file, now_utc_iso


def load_yml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yml(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False)
    tmp.replace(path)


def copy_if_changed(src: Path, dst: Path) -> bool:
    """Copy src -> dst if dst missing or content differs. Returns True if copied."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and sha256_file(src) == sha256_file(dst):
        return False
    shutil.copy2(src, dst)
    return True


def infer_analysis_name(output_path: Path, project_root: Path) -> str | None:
    """
    Try to infer analysis name from output path by checking provenance files.
    Returns None if cannot be determined.
    """
    prov_dir = project_root / "output" / "provenance"
    if not prov_dir.exists():
        return None
    
    # Look for provenance files that list this output
    for prov_file in prov_dir.glob("*.yml"):
        try:
            meta = load_yml(prov_file)
            outputs = meta.get("outputs", [])
            for out_info in outputs:
                if Path(out_info.get("path", "")).resolve() == output_path.resolve():
                    return prov_file.stem  # The analysis name
        except Exception:
            continue
    
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper-root", type=Path, required=True)
    ap.add_argument("--files", type=str, required=True, 
                    help="Space-separated output file paths")
    ap.add_argument("--allow-dirty", type=int, default=0)
    ap.add_argument("--require-not-behind", type=int, default=1)
    ap.add_argument("--require-current-head", type=int, default=0)
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    paper_root = args.paper_root.resolve()

    gitinfo = git_state(project_root)

    # Parse file list
    files = [f.strip() for f in args.files.split() if f.strip()]
    if not files:
        raise SystemExit("No files provided.")

    # Load paper provenance
    prov_path = paper_root / "provenance.yml"
    prov = load_yml(prov_path) if prov_path.exists() else {}
    prov.setdefault("paper_provenance_version", 1)
    prov.setdefault("last_updated_utc", now_utc_iso())
    prov.setdefault("analysis_git", gitinfo)
    
    # File-level publishing uses 'files' section; clear 'artifacts' section
    # since we're explicitly selecting individual files, not publishing full analyses
    prov["files"] = {}
    if "artifacts" in prov:
        # Remove stale analysis-level tracking when switching to file-level
        del prov["artifacts"]

    output_dir = project_root / "output"
    
    for file_path_str in files:
        src = Path(file_path_str)
        if not src.is_absolute():
            src = project_root / src
        
        if not src.exists():
            raise SystemExit(f"Source file not found: {src}")
        
        # Determine destination based on source location
        try:
            rel_path = src.relative_to(output_dir)
        except ValueError:
            raise SystemExit(
                f"File {src} is not in output/ directory. "
                "Only output files can be published."
            )
        
        # Preserve directory structure in paper/
        dst = paper_root / rel_path
        
        # Try to find associated provenance
        analysis_name = infer_analysis_name(src, project_root)
        build_record = None
        if analysis_name:
            prov_file = project_root / "output" / "provenance" / f"{analysis_name}.yml"
            if prov_file.exists():
                build_record = load_yml(prov_file)
        
        # Copy file
        copied = copy_if_changed(src, dst)
        
        # Print status
        status = "Published" if copied else "Up-to-date"
        rel_dst = dst.relative_to(paper_root)
        print(f"  {rel_dst!s:40s}  {status}")
        
        # Record in provenance
        file_key = str(rel_path)
        prov["files"][file_key] = {
            "published_at_utc": now_utc_iso(),
            "copied": copied,
            "src": str(src.resolve()),
            "dst": str(dst.resolve()),
            "dst_sha256": sha256_file(dst),
            "analysis_name": analysis_name,
            "build_record": build_record,
        }
    
    prov["last_updated_utc"] = now_utc_iso()
    save_yml(prov_path, prov)


if __name__ == "__main__":
    main()
