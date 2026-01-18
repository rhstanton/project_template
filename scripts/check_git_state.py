#!/usr/bin/env python
"""Check git state before publishing - fail fast with clean error."""

import argparse
from pathlib import Path
import yaml
from scripts.provenance import git_state


def load_yml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-dirty", type=int, default=0)
    parser.add_argument("--require-not-behind", type=int, default=1)
    parser.add_argument("--require-current-head", type=int, default=0)
    parser.add_argument("--artifacts", type=str, default="", help="Space-separated artifact names")
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[1]
    state = git_state(repo_root)
    
    if not state.get("is_git_repo", False):
        return  # No git, allow
    
    # Check current working tree
    if state.get("dirty", False) and not args.allow_dirty:
        raise SystemExit(
            "Refusing to publish from a dirty working tree. Commit/stash, or set ALLOW_DIRTY=1."
        )
    
    if args.require_not_behind:
        behind = state.get("behind", None)
        if behind is not None and behind > 0:
            raise SystemExit(
                f"Refusing to publish: your branch is behind upstream by {behind} commit(s). "
                "Pull/rebase first, or set REQUIRE_NOT_BEHIND=0."
            )
    
    # Check artifacts were built from clean tree
    artifact_names = [n for n in args.artifacts.split() if n.strip()]
    if artifact_names:
        prov_dir = repo_root / "output" / "provenance"
        dirty_artifacts = []
        for name in artifact_names:
            meta_path = prov_dir / f"{name}.yml"
            if meta_path.exists():
                meta = load_yml(meta_path)
                git_info = meta.get("git", {})
                if git_info.get("dirty", False):
                    dirty_artifacts.append(name)
        
        if dirty_artifacts and not args.allow_dirty:
            msg = "Refusing to publish: some artifacts were built from a dirty working tree:\n"
            for name in dirty_artifacts:
                msg += f"  {name}\n"
            msg += "\nRebuild from a clean tree: git commit/stash, then make clean && make all\n"
            msg += "Or set ALLOW_DIRTY=1 to allow."
            raise SystemExit(msg)
        
        # Check artifacts from current HEAD if required
        if args.require_current_head:
            current_commit = state.get("commit", "")
            if current_commit:
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
                    msg += "\nRun: make clean && make all\nOr set REQUIRE_CURRENT_HEAD=0 to allow."
                    raise SystemExit(msg)


if __name__ == "__main__":
    main()
