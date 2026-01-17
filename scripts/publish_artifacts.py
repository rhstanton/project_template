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


def enforce_git_policy(repo_root: Path, *, allow_dirty: bool, require_not_behind: bool) -> Dict[str, Any]:
    state = git_state(repo_root)
    if not state.get("is_git_repo", False):
        # No git info; allow but caller should understand traceability is limited.
        return state

    if state.get("dirty", False) and not allow_dirty:
        raise SystemExit(
            "Refusing to publish from a dirty working tree. Commit/stash, or set --allow-dirty 1."
        )

    if require_not_behind:
        behind = state.get("behind", None)
        if behind is not None and behind > 0:
            raise SystemExit(
                f"Refusing to publish: your branch is behind upstream by {behind} commit(s). "
                "Pull/rebase first, or set --require-not-behind 0."
            )

    return state


def check_artifacts_current(artifact_names: list[str], prov_dir: Path, current_commit: str) -> None:
    """Verify all artifacts were built from current HEAD commit."""
    stale = []
    for name in artifact_names:
        meta_path = prov_dir / f"{name}.yml"
        if meta_path.exists():
            meta = load_yml(meta_path)
            artifact_commit = meta.get("git_commit", "")
            if artifact_commit and artifact_commit != current_commit:
                stale.append((name, artifact_commit[:7], current_commit[:7]))
    
    if stale:
        msg = "Refusing to publish: some artifacts were not built from current HEAD:\n"
        for name, old, new in stale:
            msg += f"  {name}: built from {old}, but HEAD is {new}\n"
        msg += "\nRun: make clean && make all\nOr set --require-current-head 0 to allow."
        raise SystemExit(msg)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Publish built artifacts (figures or tables) into the paper repo with per-artifact provenance."
    )
    ap.add_argument("--paper-root", type=Path, required=True)
    ap.add_argument("--kind", choices=["figures", "tables"], required=True)
    ap.add_argument("--names", type=str, required=True, help="Space-separated artifact base names")
    ap.add_argument("--allow-dirty", type=int, default=0)
    ap.add_argument("--require-not-behind", type=int, default=1)
    ap.add_argument("--require-current-head", type=int, default=0, 
                    help="Require all artifacts built from current HEAD (default 0)")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    paper_root = args.paper_root.resolve()

    gitinfo = enforce_git_policy(
        project_root,
        allow_dirty=bool(args.allow_dirty),
        require_not_behind=bool(args.require_not_behind),
    )

    names = [n for n in args.names.split() if n.strip()]
    if not names:
        raise SystemExit("No artifact names provided.")

    # Locations in analysis repo
    out_fig_dir = project_root / "output" / "figures"
    out_tbl_dir = project_root / "output" / "tables"
    out_prov_dir = project_root / "output" / "provenance"

    # Check artifacts are from current HEAD if required
    if args.require_current_head and gitinfo.get("is_git_repo", False):
        current_commit = gitinfo.get("commit", "")
        if current_commit:
            check_artifacts_current(names, out_prov_dir, current_commit)

    # Destination
    dst_dir = paper_root / args.kind
    dst_dir.mkdir(parents=True, exist_ok=True)

    prov_path = paper_root / "provenance.yml"
    prov = load_yml(prov_path) if prov_path.exists() else {}
    prov.setdefault("paper_provenance_version", 1)
    prov.setdefault("last_updated_utc", now_utc_iso())
    prov.setdefault("analysis_git", gitinfo)
    prov.setdefault("artifacts", {})

    for name in names:
        meta_path = out_prov_dir / f"{name}.yml"
        if not meta_path.exists():
            raise SystemExit(
                f"Missing build record {meta_path}. Build it first (e.g., `make {name}`)."
            )
        meta = load_yml(meta_path)

        if args.kind == "figures":
            src = out_fig_dir / f"{name}.pdf"
            dst = dst_dir / f"{name}.pdf"
        else:
            src = out_tbl_dir / f"{name}.tex"
            dst = dst_dir / f"{name}.tex"

        if not src.exists():
            raise SystemExit(f"Missing source artifact {src}. Build it first.")

        copied = copy_if_changed(src, dst)

        prov["artifacts"].setdefault(name, {})
        prov["artifacts"][name][args.kind] = {
            "published_at_utc": now_utc_iso(),
            "copied": copied,
            "src": str(src.resolve()),
            "dst": str(dst.resolve()),
            "dst_sha256": sha256_file(dst),
            "build_record": meta,
        }

    prov["last_updated_utc"] = now_utc_iso()
    save_yml(prov_path, prov)


if __name__ == "__main__":
    main()
