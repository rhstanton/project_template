#!/usr/bin/env python3
"""
Standalone script to record build provenance.
Called by Makefile after build scripts complete.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Disable auto-provenance since we're recording it explicitly
import scripts.provenance as prov
prov._should_record_provenance = False

import config
from scripts.provenance import write_build_record


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: record_provenance.py <analysis_name>")
        sys.exit(1)
    
    analysis_name = sys.argv[1]
    
    if analysis_name not in config.ANALYSES:
        print(f"Error: Unknown analysis '{analysis_name}'")
        print(f"Known analyses: {', '.join(config.ANALYSES.keys())}")
        sys.exit(1)
    
    analysis_cfg = config.ANALYSES[analysis_name]
    
    write_build_record(
        out_meta=analysis_cfg["outputs"]["provenance"],
        artifact_name=analysis_name,
        command=["make", analysis_name],
        repo_root=config.REPO_ROOT,
        inputs=analysis_cfg["inputs"],
        outputs=[analysis_cfg["outputs"]["figure"], analysis_cfg["outputs"]["table"]],
    )


if __name__ == "__main__":
    main()
