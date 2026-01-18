from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _run_git(args: List[str], cwd: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", *args], cwd=str(cwd), stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return None


def git_state(repo_root: Path) -> Dict[str, Any]:
    """Return git commit + dirty flag if repo_root is a git repo."""
    commit = _run_git(["rev-parse", "HEAD"], cwd=repo_root)
    if commit is None:
        return {"is_git_repo": False}

    dirty = False
    # uncommitted changes
    try:
        subprocess.check_call(["git", "diff", "--quiet"], cwd=str(repo_root))
        subprocess.check_call(
            ["git", "diff", "--cached", "--quiet"], cwd=str(repo_root)
        )
    except Exception:
        dirty = True

    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    upstream = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo_root
    )

    ahead = behind = None
    if upstream:
        lr = _run_git(
            ["rev-list", "--left-right", "--count", f"HEAD...{upstream}"], cwd=repo_root
        )
        if lr and "\t" in lr:
            left, right = lr.split("\t")
            # left = commits only in HEAD (ahead), right = commits only in upstream (behind)
            ahead, behind = int(left), int(right)

    return {
        "is_git_repo": True,
        "commit": commit,
        "branch": branch,
        "dirty": dirty,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
    }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_build_record(
    *,
    out_meta: Path,
    artifact_name: str,
    command: List[str],
    repo_root: Path,
    inputs: List[Path],
    outputs: List[Path],
) -> None:
    """Write a per-artifact YAML record describing what produced the outputs."""
    out_meta.parent.mkdir(parents=True, exist_ok=True)

    input_records: List[Dict[str, Any]] = []
    for p in inputs:
        p = p.resolve()
        input_records.append(
            {
                "path": str(p),
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
                "mtime": p.stat().st_mtime,
            }
        )

    output_records: List[Dict[str, Any]] = []
    for p in outputs:
        p = p.resolve()
        output_records.append(
            {
                "path": str(p),
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
                "mtime": p.stat().st_mtime,
            }
        )

    record: Dict[str, Any] = {
        "artifact": artifact_name,
        "built_at_utc": now_utc_iso(),
        "command": command,
        "git": git_state(repo_root),
        "inputs": input_records,
        "outputs": output_records,
    }

    tmp = out_meta.with_suffix(out_meta.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(record, f, sort_keys=False)
    tmp.replace(out_meta)
