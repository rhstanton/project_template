"""Every relative link in the documentation must point at something that exists.

A dead link is the cheapest possible documentation failure and one of the most
irritating: the reader is following instructions and the trail simply stops.

Found 2026-08-20: six links in .vscode/WELCOME.md were written relative to the
repository root while the file lives in .vscode/, so every one of them resolved
to nothing for the person most likely to click them — someone reading it inside
the editor.

Links inside fenced code blocks are ignored. TEMPLATE_USAGE.md contains an
EXAMPLE documentation index in a ```markdown fence, whose entries name files a
user would write; treating those as real links reports six failures in a
correct document. That mistake -- reading a code block as prose -- is the same
one that has produced several bugs in this repository's own tooling.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def tracked_markdown() -> list[Path]:
    """Tracked .md files, excluding the submodule's own docs."""
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out.returncode != 0:
        return []
    return [
        REPO_ROOT / f
        for f in out.stdout.split()
        if not f.startswith("lib/") and (REPO_ROOT / f).is_file()
    ]


def prose_lines(text: str):
    """Yield lines outside fenced code blocks, handling nested fences."""
    fence = 0
    for line in text.split("\n"):
        ticks = len(line) - len(line.lstrip("`"))
        if fence == 0 and ticks >= 3:
            fence = ticks
            continue
        if fence and ticks >= fence and not line.strip("`").strip():
            fence = 0
            continue
        if not fence:
            yield line


def relative_links(path: Path):
    for line in prose_lines(path.read_text()):
        for text, target in LINK.findall(line):
            t = target.split("#")[0].strip()
            if not t or t.startswith(("http://", "https://", "mailto:")):
                continue
            yield text, t


@pytest.mark.parametrize("doc", tracked_markdown(), ids=lambda p: str(p.name))
def test_relative_links_resolve(doc):
    missing = [
        f"[{text}]({target})"
        for text, target in relative_links(doc)
        if not (doc.parent / target).resolve().exists()
    ]
    assert not missing, (
        f"{doc.relative_to(REPO_ROOT)} links to files that do not exist "
        f"(links are relative to THIS file, not the repo root): {missing}"
    )


def test_the_sweep_finds_links():
    """Guard the guard: a parser finding nothing would pass every document.

    Anchored to README.md rather than to a total count. A threshold calibrated
    on the template ("at least 50 links") fails in a GENERATED project, where
    bootstrap deletes documents and prunes marked sections -- reporting a broken
    parser when the only thing that changed was the number of documents. The
    invariant that holds everywhere is that the project's front page has links
    and this parser can see them.
    """
    readme = REPO_ROOT / "README.md"
    assert readme.is_file(), "README.md is missing"
    found = list(relative_links(readme))
    assert found, "no relative links found in README.md; the parser is likely broken"
