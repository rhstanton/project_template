"""bootstrap must prune the DOCUMENTATION for a removed language, not just the code.

The gap this guards: bootstrap deleted `env/scripts/runjulia` and the
`sample-julia` target, and left every document that told the reader to run them.
A generated `--python-only` project shipped instructions for a language it did
not have, and nothing failed -- the command sweep skipped itself in pruned
projects, so the suite was green precisely where the docs were wrong.

Three mechanisms, because Markdown has two kinds of place a language can hide:

1. `<!-- julia:start -->` / `<!-- julia:end -->` block markers, for prose.
2. Exact-basename removal of directory-tree rows, because an HTML comment
   inside a fenced code block renders as literal text and splitting a tree
   diagram into one fence per language would shred the drawing.
3. Exact-name removal from `ANALYSES :=` lines, for the same reason.

2 and 3 match names bootstrap itself just deleted, never prose.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bootstrap import (  # noqa: E402
    JULIA_FILES,
    STATA_FILES,
    TEMPLATE_ONLY_FILES,
    prunable_docs,
    prune_analysis_names,
    prune_tree_lines,
    strip_marked_doc_sections,
)

MARKER = re.compile(r"<!--\s*(\w+):(start|end)\s*-->")
LANGUAGES = ("julia", "stata")
# Stripped on EVERY bootstrap, not per language: instantiating the template is
# the moment its self-description stops being true.
ALL_MARKERS = LANGUAGES + ("template-only",)


# ---------------------------------------------------------------- the stripper


def test_strips_a_marked_block():
    text = "keep\n<!-- julia:start -->\ndrop\n<!-- julia:end -->\nkeep2\n"
    assert strip_marked_doc_sections(text, "julia") == "keep\nkeep2\n"


def test_strips_every_occurrence():
    text = (
        "a\n<!-- julia:start -->\nx\n<!-- julia:end -->\n"
        "b\n<!-- julia:start -->\ny\n<!-- julia:end -->\nc\n"
    )
    out = strip_marked_doc_sections(text, "julia")
    assert "x" not in out and "y" not in out
    assert "a" in out and "b" in out and "c" in out


def test_leaves_other_languages_alone():
    text = "<!-- stata:start -->\nstata stuff\n<!-- stata:end -->\n"
    assert strip_marked_doc_sections(text, "julia") == text


def test_unclosed_marker_raises():
    """Silently keeping the rest of the file would ship the very content the
    marker exists to remove."""
    with pytest.raises(RuntimeError, match="no matching"):
        strip_marked_doc_sections("<!-- julia:start -->\nx\n", "julia", "f.md")


def test_stray_end_marker_raises():
    with pytest.raises(RuntimeError, match="no matching"):
        strip_marked_doc_sections("x\n<!-- julia:end -->\n", "julia", "f.md")


def test_no_markers_is_a_no_op():
    text = "# Title\n\nSome prose about nothing in particular.\n"
    assert strip_marked_doc_sections(text, "julia") == text


# ------------------------------------------------------------- tree diagrams


def test_prunes_a_tree_row_by_exact_basename():
    tree = "├── runpython\n├── runjulia\n└── runstata\n"
    out = prune_tree_lines(tree, {"runjulia"})
    assert "runjulia" not in out
    assert "runpython" in out and "runstata" in out


def test_repairs_the_terminator_when_the_last_row_goes():
    """Dropping a `└──` row would otherwise leave a tree with no terminator."""
    tree = "├── sample_python.py\n└── sample_julia.jl\n"
    out = prune_tree_lines(tree, {"sample_julia.jl"})
    assert out == "└── sample_python.py\n"


def test_ignores_a_matching_name_that_is_not_a_tree_row():
    """The match is only trusted on a line carrying a tree connector."""
    prose = "Run `runjulia` to execute a script.\n"
    assert prune_tree_lines(prose, {"runjulia"}) == prose


def test_tolerates_the_trailing_comment_column():
    tree = "├── runpython          # Python wrapper\n└── runjulia           # Julia wrapper\n"
    out = prune_tree_lines(tree, {"runjulia"})
    assert "runjulia" not in out
    assert out == "└── runpython          # Python wrapper\n"


def test_directory_rows_match_without_their_slash():
    tree = "├── data/\n└── .stata/\n"
    out = prune_tree_lines(tree, {".stata"})
    assert ".stata" not in out


def test_pruning_nothing_changes_nothing_in_the_real_docs():
    """The terminator-repair pass must agree with every hand-drawn tree here.

    If it rewrites a diagram nobody asked it to touch, it is guessing, and it
    would corrupt trees on any future run.
    """
    for md in prunable_docs(REPO_ROOT):
        before = md.read_text()
        assert prune_tree_lines(before, set()) == before, (
            f"{md} rewritten by a no-op prune"
        )


# --------------------------------------------------------- ANALYSES := lines


def test_prunes_an_analysis_name():
    line = "ANALYSES := price_base correlation julia_demo my_analysis"
    assert prune_analysis_names(line, {"julia_demo"}) == (
        "ANALYSES := price_base correlation my_analysis"
    )


def test_prunes_inside_a_commented_example():
    line = "# ANALYSES := price_base julia_demo custom"
    assert (
        prune_analysis_names(line, {"julia_demo"}) == "# ANALYSES := price_base custom"
    )


def test_leaves_prose_mentioning_the_name_alone():
    prose = "The julia_demo notebook calls Julia from Python."
    assert prune_analysis_names(prose, {"julia_demo"}) == prose


# ------------------------------------------------------------ which files


def test_prunable_docs_excludes_generated_copies():
    """replication-package/ and paper/ are build output; pruning them edits
    files the next `make` overwrites."""
    names = {str(p.relative_to(REPO_ROOT)) for p in prunable_docs(REPO_ROOT)}
    assert not any(n.startswith("replication-package/") for n in names)
    assert not any(n.startswith("paper/") for n in names)
    assert not any(n.startswith("lib/") for n in names)
    assert not any(n.startswith("notes/") for n in names)
    assert "CHANGELOG.md" not in names


def test_prunable_docs_includes_the_documentation():
    names = {str(p.relative_to(REPO_ROOT)) for p in prunable_docs(REPO_ROOT)}
    for expected in ("README.md", "QUICKSTART.md", "docs/environment.md"):
        assert expected in names, f"{expected} is not being pruned"


def test_prunable_docs_visits_each_real_file_once():
    """AGENTS.md, CLAUDE.md and .github/copilot-instructions.md can be three
    symlinks to one file; editing it three times applies each edit three times."""
    resolved = [p.resolve() for p in prunable_docs(REPO_ROOT)]
    assert len(resolved) == len(set(resolved))


# ------------------------------------------------------- the markers in situ


@pytest.mark.parametrize("lang", ALL_MARKERS)
def test_markers_are_balanced_and_unnested(lang):
    """An unbalanced pair makes bootstrap raise; a nested one silently strips
    the wrong span and leaves a stray end marker. Both have happened."""
    for md in prunable_docs(REPO_ROOT):
        depth = 0
        opened = None
        for i, line in enumerate(md.read_text().split("\n"), 1):
            for m in MARKER.finditer(line):
                if m.group(1) != lang:
                    continue
                if m.group(2) == "start":
                    assert depth == 0, f"{md}:{i}: {lang} marker nested inside {opened}"
                    depth, opened = 1, i
                else:
                    assert depth == 1, f"{md}:{i}: {lang} end marker with no start"
                    depth = 0
        assert depth == 0, f"{md}: {lang} section opened at line {opened} never closed"


def test_no_marker_sits_inside_a_code_fence():
    """An HTML comment inside ``` renders as literal text to the reader."""
    offenders = []
    for md in prunable_docs(REPO_ROOT):
        if md in {REPO_ROOT / p for p in TEMPLATE_ONLY_FILES}:
            continue  # documents the marker syntax; its examples are the point
        fence = 0  # length of the open fence, 0 when outside one
        for i, line in enumerate(md.read_text().split("\n"), 1):
            ticks = len(line) - len(line.lstrip("`"))
            if fence == 0 and ticks >= 3:
                fence = ticks
            elif fence and ticks >= fence and not line.strip("`").strip():
                fence = 0
            elif fence and MARKER.search(line):
                offenders.append(f"{md.relative_to(REPO_ROOT)}:{i}")
    assert not offenders, "markers inside code fences: " + ", ".join(offenders)


@pytest.mark.parametrize("lang", ALL_MARKERS)
def test_stripping_leaves_valid_markdown_fences(lang):
    """Splitting a fence to place markers around part of it is easy to get
    wrong: an odd number of ``` afterwards means the rest of the page renders
    as code."""
    for md in prunable_docs(REPO_ROOT):
        text = md.read_text()
        if f"<!-- {lang}:start -->" not in text:
            continue
        stripped = strip_marked_doc_sections(text, lang, md.name)
        fences = sum(1 for line in stripped.split("\n") if line.startswith("```"))
        assert fences % 2 == 0, f"{md}: odd fence count after stripping {lang}"


@pytest.mark.parametrize("lang", LANGUAGES)
def test_the_marked_files_actually_lose_their_commands(lang):
    """The end-to-end claim, without running bootstrap: after stripping, no
    document may still instruct the reader to run the removed language."""
    wrapper = {"julia": "runjulia", "stata": "runstata"}[lang]
    files = JULIA_FILES if lang == "julia" else STATA_FILES
    removed = {Path(p).name for p in files}
    # Documents bootstrap deletes outright need no markers inside them.
    deleted = {REPO_ROOT / p for p in files + TEMPLATE_ONLY_FILES}
    offenders = []
    for md in prunable_docs(REPO_ROOT):
        if md in deleted:
            continue
        stripped = strip_marked_doc_sections(md.read_text(), lang, md.name)
        stripped = prune_tree_lines(stripped, removed)
        for i, line in enumerate(stripped.split("\n"), 1):
            if wrapper in line or f"make sample-{lang}" in line:
                offenders.append(
                    f"{md.relative_to(REPO_ROOT)}:{i}: {line.strip()[:60]}"
                )
    assert not offenders, f"{lang} commands survive pruning:\n" + "\n".join(offenders)


def test_no_document_tells_a_generated_project_to_instantiate_the_template():
    """A generated project inherited "click Use this template" and
    `python bootstrap.py --python-only` -- instructions for creating the project
    the reader is already standing in. Re-running bootstrap there is at best
    confusing and at worst destructive.
    """
    deleted = {REPO_ROOT / p for p in TEMPLATE_ONLY_FILES}
    offenders = []
    for md in prunable_docs(REPO_ROOT):
        if md in deleted:
            continue  # bootstrap removes the whole file, markers or not
        stripped = strip_marked_doc_sections(md.read_text(), "template-only", md.name)
        for i, line in enumerate(stripped.split("\n"), 1):
            if "bootstrap.py" in line or "Use this template" in line:
                offenders.append(
                    f"{md.relative_to(REPO_ROOT)}:{i}: {line.strip()[:60]}"
                )
    assert not offenders, "template-only prose survives:\n" + "\n".join(offenders)


def test_the_template_itself_still_explains_how_to_instantiate_it():
    """Guard the guard: marking everything would pass the test above while
    making the template unusable for its actual purpose."""
    readme = (REPO_ROOT / "README.md").read_text()
    assert "Use this template" in readme
    assert "bootstrap.py" in readme


def test_every_template_only_file_is_actually_deleted():
    """Guard the exemptions above: they only make sense if bootstrap really
    removes these files. An entry naming a file bootstrap keeps would silently
    exempt a live document from every marker check."""
    for rel in TEMPLATE_ONLY_FILES:
        assert (REPO_ROOT / rel).is_file(), f"{rel} is listed but does not exist"
    text = (REPO_ROOT / "bootstrap.py").read_text()
    assert "for rel in TEMPLATE_ONLY_FILES:" in text
    assert "path.unlink()" in text


def test_prose_about_tree_rows_is_not_treated_as_one():
    """`├── ` inside a sentence is not a directory entry.

    The first detector asked only whether a connector appeared anywhere in the
    line, so documentation explaining the tree rules matched its own examples
    and the terminator repair rewrote the prose.
    """
    prose = "A row carrying `├── ` or `└── ` is a tree row.\n"
    assert prune_tree_lines(prose, {"anything"}) == prose
