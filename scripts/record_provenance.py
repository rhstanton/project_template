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
        print("Usage: record_provenance.py <artifact_name>")
        sys.exit(1)
    
    artifact_name = sys.argv[1]
    
    if artifact_name not in config.ARTIFACTS:
        print(f"Error: Unknown artifact '{artifact_name}'")
        print(f"Known artifacts: {', '.join(config.ARTIFACTS.keys())}")
        sys.exit(1)
    
    art_cfg = config.ARTIFACTS[artifact_name]
    
    write_build_record(
        out_meta=art_cfg["outputs"]["provenance"],
        artifact_name=artifact_name,
        command=["make", artifact_name],
        repo_root=config.REPO_ROOT,
        inputs=art_cfg["inputs"],
        outputs=[art_cfg["outputs"]["figure"], art_cfg["outputs"]["table"]],
    )


if __name__ == "__main__":
    main()
