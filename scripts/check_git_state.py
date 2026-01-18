#!/usr/bin/env python
"""Check git state before publishing - fail fast with clean error."""

import argparse
from pathlib import Path
from scripts.provenance import git_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-dirty", type=int, default=0)
    parser.add_argument("--require-not-behind", type=int, default=1)
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[1]
    state = git_state(repo_root)
    
    if not state.get("is_git_repo", False):
        return  # No git, allow
    
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


if __name__ == "__main__":
    main()
