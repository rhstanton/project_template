#!/usr/bin/env python
"""
Bootstrap script for customizing project_template after cloning.

This script helps you customize the template by removing unwanted languages
and optionally renaming the project. Python is always kept — it's the substrate
the whole harness runs on — so "one language" means Python-only.

Removing a language also removes the example analyses that depend on it (e.g.
julia_demo and did_example need Julia), so `make all` still builds cleanly
afterwards. This is the only safe way to drop a language; deleting files by hand
leaves the build referencing a backend that's gone.

Usage:
    python bootstrap.py --remove-julia --remove-stata
    python bootstrap.py --python-only
    python bootstrap.py --rename "My Research Project"
    python bootstrap.py --interactive
    python bootstrap.py --help

Examples:
    # Remove Julia support (keeps Python and Stata)
    python bootstrap.py --remove-julia

    # Remove Stata support (keeps Python and Julia)
    python bootstrap.py --remove-stata

    # Python-only project (same as --remove-julia --remove-stata)
    python bootstrap.py --python-only

    # Rename project
    python bootstrap.py --rename "Housing Market Analysis"

    # Interactive mode (prompts for each option)
    python bootstrap.py --interactive

    # Combine options
    python bootstrap.py --remove-stata --rename "My Project"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from pathlib import PurePath as pathlib_PurePath

# Example analyses whose backend is a specific language. Dropping the language
# must also drop these, or `make all` will try to build an analysis whose runtime
# is gone (e.g. julia_demo's `import juliacall`). Stata ships only a sample .do
# file — no analysis — so its list is empty.
JULIA_ANALYSES: tuple[str, ...] = ("julia_demo", "did_example")
STATA_ANALYSES: tuple[str, ...] = ()


def remove_language_analyses(repo_root: Path, names: tuple[str, ...]) -> None:
    """Remove example analyses that depend on a now-removed language.

    Delegates to scripts/remove_analysis.py, which drops each analysis from the
    Makefile (ANALYSES line + pattern block), its shared/config.py STUDIES entry,
    its example script, and its built artifacts — leaving a project that still
    builds with `make all`. Analyses already absent are skipped (idempotent).
    """
    if not names:
        return

    sys.path.insert(0, str(repo_root / "scripts"))
    from remove_analysis import parse_analyses, remove_analysis

    present = set(parse_analyses((repo_root / "Makefile").read_text()))
    for name in names:
        if name in present:
            remove_analysis(name, root=repo_root, apply=True)

    # The docs name these analyses too -- in directory diagrams and in the
    # example `ANALYSES :=` lines. Removing the build entry and leaving those
    # is the same defect this whole pass exists to fix.
    remove_analysis_doc_mentions(repo_root, names)


# What removing a language deletes. Module constants because two things consume
# them: the unlink loop below, and remove_tree_lines(), which prunes the same
# names out of the directory diagrams in the docs. A second hand-maintained list
# would drift, and the drift would be invisible -- a tree diagram naming a file
# that bootstrap deleted still renders perfectly.
JULIA_FILES = [
    "env/Project.toml",
    # The two pins that go with Project.toml. Leaving them behind would give
    # a Python-only project a committed Julia manifest and a pinned Julia
    # binary version for a language it does not have -- files that look
    # authoritative and describe nothing.
    "env/Manifest.toml",
    "env/juliapkg.json",
    "env/scripts/runjulia",
    "env/scripts/install_julia.py",
    "env/examples/sample_julia.jl",
    "env/examples/sample_juliacall.py",
    # Wholly about Julia from its title down, so there is nothing in it to
    # keep. Marking it section by section would leave an empty file whose
    # name still promises content.
    "docs/julia_python_integration.md",
]

STATA_FILES = [
    "env/stata-packages.txt",
    # The pin record that goes with the vendored packages. Leaving it would
    # give a project a checkable version manifest for a language it does not
    # have -- and `make stata-check` would then fail on a tree that was
    # correctly removed.
    "env/stata-requirements.txt",
    "env/scripts/runstata",
    "env/scripts/execute.ado",
    "env/examples/sample_stata.do",
]


def remove_julia_files(repo_root: Path) -> None:
    """Remove Julia-specific files from the project."""
    print("\n🗑️  Removing Julia files...")

    files_to_remove = JULIA_FILES

    for file_path in files_to_remove:
        full_path = repo_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"  ✓ Removed {file_path}")
        else:
            print(f"  ⚠ Not found: {file_path}")

    # Documentation too. Removing the targets and leaving the docs that tell
    # people to run them is how a generated project ended up instructing its
    # reader to `make sample-julia`.
    remove_language_doc_sections(repo_root, "julia")
    # ".julia" is the depot directory: not in JULIA_FILES because bootstrap does
    # not delete it (a fresh clone has none), but it must still go from the
    # diagrams -- same reasoning as ".stata" below.
    remove_language_tree_lines(repo_root, JULIA_FILES + [".julia"])


def remove_stata_files(repo_root: Path) -> None:
    """Remove Stata-specific files from the project."""
    print("\n🗑️  Removing Stata files...")

    files_to_remove = STATA_FILES

    for file_path in files_to_remove:
        full_path = repo_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"  ✓ Removed {file_path}")
        else:
            print(f"  ⚠ Not found: {file_path}")

    # The vendored ado tree: 84 files and 2 MB of Stata packages, committed so
    # the versions can be pinned at all. A project without Stata should not carry
    # them, and unlike everything above this is a directory, so unlink() is not
    # enough -- the earlier version of this function silently left it behind.
    vendored = repo_root / ".stata"
    if vendored.is_dir():
        n = sum(1 for _ in vendored.rglob("*") if _.is_file())
        shutil.rmtree(vendored)
        print(f"  ✓ Removed .stata/ (vendored packages, {n} files)")

    remove_language_doc_sections(repo_root, "stata")
    remove_language_tree_lines(repo_root, STATA_FILES + [".stata"])


def update_pyproject(repo_root: Path, remove_julia: bool) -> None:
    """Remove the juliacall dependency from pyproject.toml if requested."""
    if not remove_julia:
        return

    print("\n📝 Updating pyproject.toml...")
    pyproject = repo_root / "pyproject.toml"

    if not pyproject.exists():
        print("  ⚠ pyproject.toml not found")
        return

    content = pyproject.read_text()

    # Remove the juliacall dependency line (keeps the rest of dependencies intact)
    content = re.sub(r'\n\s*"juliacall[^"\n]*",', "\n", content)

    pyproject.write_text(content)
    print("  ✓ Removed juliacall dependency (run `uv lock` to refresh the lockfile)")


TEMPLATE_ORIGIN_FILE = "template-origin.toml"


def _git(repo_root: Path, *args: str) -> str:
    """Run git in repo_root, returning stdout stripped, or '' on failure."""
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def _own_git_repo(repo_root: Path) -> bool:
    """True only if repo_root is itself the top of a git repo.

    git searches UPWARDS for a repository, so running it in a directory with no
    .git of its own cheerfully answers about some ancestor. That is not an edge
    case here: a template exported with `git archive` has no history, and if it
    is unpacked anywhere beneath another repo -- a projects directory that is
    itself versioned, say -- then `git rev-parse HEAD` returns that repo's commit
    and the provenance file records a confident, entirely wrong origin.

    Wrong provenance is worse than none: absent provenance asks a question,
    while wrong provenance answers it incorrectly and is believed.
    """
    top = _git(repo_root, "rev-parse", "--show-toplevel")
    if not top:
        return False
    try:
        return Path(top).resolve() == repo_root.resolve()
    except OSError:
        return False


def write_template_origin(repo_root: Path, args) -> None:
    """Record which template version this project was generated from.

    This is the missing primitive for propagating template fixes. Without it,
    nothing in a generated project says where it came from, so no tool can work
    out which template changes have not yet been applied -- `_version.py` is the
    TEMPLATE's version, and a project bumps that as its own the first time it
    releases, erasing the origin.

    Deliberately a separate file that the project never bumps: it records where
    the project CAME FROM, not what it is now. `make template-diff` reads it.
    """
    # An explicit commit always wins: `make instance` exports the template with
    # `git archive`, which carries no history, so it passes the real one in.
    commit = args.template_commit or ""
    sub_commit = ""
    if not commit and _own_git_repo(repo_root):
        commit = _git(repo_root, "rev-parse", "HEAD")
        sub_commit = _git(repo_root, "rev-parse", "HEAD:lib/repro-tools")

    flags = []
    if args.remove_julia:
        flags.append("--remove-julia")
    if args.remove_stata:
        flags.append("--remove-stata")
    if args.rename:
        flags.append("--rename")

    version = "unknown"
    version_py = repo_root / "_version.py"
    if version_py.is_file():
        m = re.search(r'__version__\s*=\s*"([^"]+)"', version_py.read_text())
        if m:
            version = m.group(1)

    # Date comes from the template's own commit rather than the clock, so
    # re-running bootstrap on the same checkout is reproducible and the file does
    # not churn. Same repo guard as above: a date from an ancestor repo's HEAD
    # would be as wrong as the commit, and less obviously so.
    created = ""
    if _own_git_repo(repo_root):
        created = _git(repo_root, "log", "-1", "--format=%ad", "--date=short", "HEAD")

    lines = [
        "# Where this project came from. Written by bootstrap.py at creation.",
        "#",
        "# Do NOT edit or bump this by hand. It records the template version this",
        "# project was generated from, which is what `make template-diff` needs to",
        "# work out which template changes have not been applied here yet. Your",
        "# project's own version lives in _version.py and moves independently.",
        "",
        "[template]",
        'name = "project_template"',
        'url = "https://github.com/rhstanton/project_template"',
        f'version = "{version}"',
        f'commit = "{commit}"',
        f'created = "{created}"',
        f"bootstrap_flags = {json.dumps(flags)}",
        "",
        "[repro_tools]",
        f'commit = "{sub_commit}"',
        "",
    ]
    path = repo_root / TEMPLATE_ORIGIN_FILE
    path.write_text("\n".join(lines))

    if not commit:
        print(f"  ⚠ wrote {TEMPLATE_ORIGIN_FILE} without a commit (not a git repo?)")
    else:
        print(f"\n📌 Recorded template origin in {TEMPLATE_ORIGIN_FILE} ({commit[:8]})")


# Every env/Makefile target that exists only because Julia does. Listed here
# rather than inline so adding a Julia target is one edit, not two in different
# files -- `julia-instantiate` was added to env/Makefile and immediately produced
# a --python-only project whose all-env still called the deleted runjulia.
#
# The CI variant matrix is what catches an omission here: it asserts that a
# pruned tree's `make -n environment` plans no Julia work at all.
JULIA_MAKE_TARGETS = (
    "julia-install-via-python",
    "julia-instantiate",
    "julia-env",
    "juliacall-clean",
)

# Same for Stata. These names appear in the combined .PHONY list and in all-env,
# both of which sit ABOVE the "# ---------- Stata ----------" banner, so removing
# the section does not remove them.
STATA_MAKE_TARGETS = (
    "stata-env",
    "stata-check",
    "stata-clean",
    "stata-requirements",
    "stata-update",
)


def strip_marked_section(content: str, name: str) -> str:
    """Remove everything between `# ---------- NAME ----------` and its end marker.

    Both markers are explicit, and a missing end marker is an error rather than
    a best guess. The version this replaces ended the match at a lookahead for
    the next `\\n.PHONY` or `\\n# ---`, which silently truncated the moment the
    section itself grew a `.PHONY:` line -- and it did. `--remove-stata` then cut
    the section in half, leaving stata-env, the stamp rule and stata-check behind
    while deleting the variables they referenced.

    Anchoring to a delimiter that the content can contain is the recurring bug in
    this file. An explicit end marker cannot be produced by accident.
    """
    start = f"# ---------- {name} ----------"
    end = f"# ---------- end {name} ----------"
    i = content.find(start)
    if i == -1:
        return content
    j = content.find(end, i)
    if j == -1:
        raise RuntimeError(
            f"env/Makefile has '{start}' but no '{end}'. Refusing to guess where "
            f"the section ends: guessing is what silently left half the {name} "
            "rules behind, referencing variables that had just been deleted."
        )
    return content[:i] + content[j + len(end) :].lstrip("\n")


# Markdown that bootstrap prunes: every .md in the repo except those living in a
# generated, vendored or environment directory.
#
# Ignored-*directory* is the test, not ignored-file, and the distinction is
# load-bearing. replication-package/ is a whole generated copy of the repo and
# paper/ is build output -- both gitignored, both would be pruned pointlessly and
# then overwritten by the next `make`. But AGENTS.md and CLAUDE.md are gitignored
# *files* in a tracked directory, and they are exactly the documentation an agent
# reads before touching the project. A "tracked files only" rule would skip them.
NEVER_WALK = {".git", ".venv", ".julia", ".stata", "__pycache__", "node_modules"}

# Excluded by name rather than by git, because they are tracked and must still
# not be edited:
#   lib/    -- submodule content; not ours to rewrite (and asking git about a
#              path inside a submodule makes check-ignore exit 128)
#   notes/  -- institutional memory. A design note quoting `make sample-julia`
#              is describing the template, not instructing the reader.
DOC_PRUNE_SKIP_DIRS = {"lib", "notes"}
# A historical record: pruning it would rewrite what past releases contained.
DOC_PRUNE_SKIP_FILES = {"CHANGELOG.md"}


def _ignored_dirs(repo_root: Path, dirs: list) -> set:
    """Ask git which of these directories are ignored.

    Returns an empty set when this is not a git checkout -- name-based skipping
    then carries the whole load. Any *other* git failure raises: an earlier
    version returned an empty set on error, so a single unqueryable path (one
    inside a submodule, which makes check-ignore exit 128) silently turned the
    directory filter off and pruned generated copies of the repo.
    """
    if not dirs:
        return set()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "check-ignore", "--stdin"],
            input="\n".join(dirs),
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return set()  # no git installed
    if proc.returncode == 128 and "not a git repository" in proc.stderr:
        return set()
    # check-ignore exits 1 when nothing matches, which is not an error.
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def prunable_docs(repo_root: Path) -> list:
    """Every Markdown file bootstrap is allowed to prune."""
    found = []
    for md in sorted(repo_root.rglob("*.md")):
        rel = md.relative_to(repo_root)
        parts = set(rel.parts[:-1])
        if parts & NEVER_WALK or parts & DOC_PRUNE_SKIP_DIRS:
            continue
        if rel.name in DOC_PRUNE_SKIP_FILES:
            continue
        if md.is_file():
            found.append((md, rel))

    dirs = sorted({str(rel.parent) for _, rel in found if str(rel.parent) != "."})
    ignored = _ignored_dirs(repo_root, dirs)

    out = []
    seen = set()
    root = repo_root.resolve()
    for md, rel in found:
        ancestors = {
            str(pathlib_PurePath(*rel.parts[:k])) for k in range(1, len(rel.parts))
        }
        if ancestors & ignored:
            continue
        # AGENTS.md, CLAUDE.md and .github/copilot-instructions.md are three
        # symlinks to ONE file in the private/ maintainer overlay. Rewriting the
        # same file once per link applies each edit three times, and private/ is
        # deliberately outside the project. Resolve, skip anything landing
        # outside the repo, and visit each real file once.
        target = md.resolve()
        try:
            target.relative_to(root)
        except ValueError:
            continue
        if target in seen:
            continue
        seen.add(target)
        out.append(md)
    return out


def strip_marked_doc_sections(content: str, name: str, source: str = "") -> str:
    """Remove `<!-- NAME:start -->` ... `<!-- NAME:end -->` blocks from Markdown.

    The documentation analogue of strip_marked_section() above, and it follows
    the same rule for the same reason: BOTH markers are explicit, and an
    unbalanced pair is an error rather than a best guess.

    WHY THIS EXISTS

    bootstrap removed a language's scripts, Makefile targets, environment files
    and tests, and left docs/ untouched. A generated `--python-only` project
    therefore shipped documentation telling the reader to run `make
    sample-julia` and `make -C env julia-check`, neither of which existed there.
    Seven files were affected. Found 2026-08-19 when fire's documented-command
    sweep was ported here: it passed on the template and failed on every pruned
    variant in CI.

    WHY MARKERS RATHER THAN PATTERN MATCHING

    Deleting a Makefile target is one line; pruning prose is not. Most of these
    files discuss all three languages in the same paragraph, and several explain
    the Python/Julia bridge as a way of explaining the environment as a whole. A
    heuristic that stripped paragraphs mentioning "julia" would leave dangling
    references and half-sentences -- worse than a command that does not exist.
    An author marks what is genuinely language-specific, and the marks document
    that fact even when nothing is pruned.

    HTML comments are used because they are invisible in rendered Markdown, so
    the full template's documentation reads normally.
    """
    start = f"<!-- {name}:start -->"
    end = f"<!-- {name}:end -->"

    while True:
        i = content.find(start)
        if i == -1:
            break
        j = content.find(end, i)
        if j == -1:
            where = f" in {source}" if source else ""
            raise RuntimeError(
                f"found '{start}'{where} with no matching '{end}'. Refusing to "
                f"guess where the section ends -- guessing is what silently left "
                f"half a section behind when this was done for Makefiles."
            )
        # Take the whole lines the markers sit on, so no blank marker line is
        # left behind, and collapse the blank run that would otherwise double up.
        line_start = content.rfind("\n", 0, i) + 1
        line_end = content.find("\n", j)
        line_end = len(content) if line_end == -1 else line_end + 1
        content = content[:line_start] + content[line_end:]
        content = content.replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

    stray = content.find(end)
    if stray != -1:
        where = f" in {source}" if source else ""
        raise RuntimeError(
            f"found '{end}'{where} with no matching '{start}'. An end marker "
            f"alone means a section boundary was lost."
        )
    return content


TREE_CONNECTORS = ("├── ", "└── ")


def prune_tree_lines(content: str, basenames: set) -> str:
    """Drop directory-diagram lines naming a file that no longer exists.

    The block markers used elsewhere in this module are HTML comments, which
    render as literal text inside a fenced code block -- so they cannot reach
    individual lines of the directory trees in README.md and QUICKSTART.md.
    Splitting a tree into one fence per language would shred the drawing.

    This does not pattern-match prose. It matches the *exact basenames* that
    bootstrap just deleted (JULIA_FILES / STATA_FILES), and only on lines that
    are unambiguously tree rows -- ones carrying a `├── ` or `└── ` connector.
    A tree row is the one place in Markdown where a bare filename is the whole
    content of the line, so an exact-name match there is not a guess.

    The connector on the final child of a directory is then repaired: removing
    a `└── ` row would otherwise leave the tree with a dangling `├── ` and no
    terminator. A row is last when no later row shares its exact indent before
    the tree returns to a shallower one.

    Known limitation: a basename that is also the name of a *kept* file
    elsewhere in the tree would be dropped from both. Nothing in the current
    lists collides, and the lists are short enough to check by eye when they
    change.
    """
    lines = content.split("\n")
    kept = []
    for line in lines:
        conn = next((c for c in TREE_CONNECTORS if c in line), None)
        if conn is None:
            kept.append(line)
            continue
        entry = line.split(conn, 1)[1]
        # Strip the trailing "# comment" column and any directory slash.
        name = entry.split("#", 1)[0].strip().rstrip("/")
        if name in basenames:
            continue
        kept.append(line)

    # Repair terminators: walk each row and decide whether it is now last.
    indents = []
    for line in kept:
        conn = next((c for c in TREE_CONNECTORS if c in line), None)
        indents.append(len(line.split(conn)[0]) if conn else None)

    for i, line in enumerate(kept):
        if indents[i] is None:
            continue
        conn = next(c for c in TREE_CONNECTORS if c in line)
        is_last = True
        for j in range(i + 1, len(kept)):
            if indents[j] is None:
                # Blank lines and pure box-drawing continuations (`│`, `│   │`)
                # sit *between* siblings and must not end the run. Anything
                # else -- prose, a closing fence -- ends the tree.
                if set(kept[j]) <= {"│", " ", "\t"}:
                    continue
                break
            if indents[j] < indents[i]:
                break
            if indents[j] == indents[i]:
                is_last = False
                break
        want = "└── " if is_last else "├── "
        if conn != want:
            kept[i] = line.replace(conn, want, 1)

    return "\n".join(kept)


def prune_analysis_names(content: str, names) -> str:
    """Drop a removed analysis from the illustrative `ANALYSES :=` lines in docs.

    Same reasoning as prune_tree_lines: these sit inside fenced code blocks
    where an HTML marker would render literally, and the match is on the exact
    analysis name bootstrap just removed, on a line that declares the Makefile
    variable -- not on prose.
    """
    out = []
    for line in content.split("\n"):
        if "ANALYSES" in line and ":=" in line:
            head, _, tail = line.partition(":=")
            kept = [t for t in tail.split() if t not in names]
            if len(kept) != len(tail.split()):
                line = f"{head}:= " + " ".join(kept)
        out.append(line)
    return "\n".join(out)


def remove_analysis_doc_mentions(repo_root: Path, names) -> None:
    """Prune removed analyses from tree diagrams and ANALYSES lines in the docs."""
    names = set(names)
    remove_language_tree_lines(
        repo_root, [f"{n}.ipynb" for n in names] + [f"{n}.py" for n in names]
    )
    targets = prunable_docs(repo_root)
    for md in targets:
        if not md.is_file():
            continue
        before = md.read_text()
        after = prune_analysis_names(before, names)
        if after != before:
            md.write_text(after)
            print(f"  ✓ Pruned analysis names from {md.relative_to(repo_root)}")


def remove_language_tree_lines(repo_root: Path, paths: list) -> None:
    """Apply prune_tree_lines to every Markdown file in the project."""
    basenames = {Path(p).name for p in paths}
    targets = prunable_docs(repo_root)
    for md in targets:
        if not md.is_file():
            continue
        before = md.read_text()
        after = prune_tree_lines(before, basenames)
        if after != before:
            md.write_text(after)
            n = len(before.split("\n")) - len(after.split("\n"))
            print(f"  ✓ Pruned {n} tree line(s) from {md.relative_to(repo_root)}")


def remove_language_doc_sections(repo_root: Path, name: str) -> None:
    """Strip `name`-marked sections from every Markdown file in the project."""
    targets = prunable_docs(repo_root)
    changed = []
    for path in targets:
        original = path.read_text(encoding="utf-8")
        stripped = strip_marked_doc_sections(original, name, source=path.name)
        if stripped != original:
            path.write_text(stripped, encoding="utf-8")
            changed.append(path.name)
    if changed:
        print(f"  Removed {name} sections from: {', '.join(changed)}")


def strip_make_prereq(content: str, name: str) -> str:
    """Remove `name` from dependency and .PHONY lists, never crossing a newline.

    The character class is `[ \\t]`, not `\\s`, and that is the whole point. The
    original used `\\s+` + name, which happily ate the newline and indent before
    a name sitting at the start of a continuation line, welding two lines
    together:

        .PHONY: julia-env julia-install-via-python ensure-uv \\
                stata-env stata-clean stata-check \\

    became `julia-env ensure-uv \\ stata-clean stata-check \\` -- and `\\ ` is an
    escaped space, not a line continuation, so the .PHONY list silently ended
    there. `\\s` in a multiline substitution is nearly always a bug; bound it to
    the line unless crossing one is what you actually mean.
    """
    return re.sub(rf"[ \t]+{re.escape(name)}\b", "", content)


def strip_make_target(content: str, target: str) -> str:
    """Remove a rule: its comment block, its `target:` line, and its recipe.

    Line-anchored, for the reason above. Removing the bare NAME everywhere also
    hit the rule's own definition line, deleting `julia-install-via-python` from
    `julia-install-via-python:` but leaving the orphaned `:` to glue itself onto
    the comment above -- and re-parenting the recipe onto whichever rule came
    before. In a --python-only project that put the Julia installer inside
    `ensure-uv`, so `make environment` tried to install Julia before the venv
    existed and failed pointing at a target with nothing to do with Julia.
    """
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not re.match(rf"^{re.escape(target)}\s*:", lines[i]):
            out.append(lines[i])
            i += 1
            continue

        # Drop the comment block directly above the rule, if any.
        while out and out[-1].lstrip().startswith("#"):
            out.pop()

        i += 1  # the `target:` line itself
        # A make recipe line must start with a tab. Blank lines belong to the
        # recipe only when another tab-indented line follows; otherwise the
        # blank is the separator before the next rule and must survive.
        while i < len(lines):
            if lines[i].startswith("\t"):
                i += 1
            elif (
                not lines[i].strip()
                and i + 1 < len(lines)
                and lines[i + 1].startswith("\t")
            ):
                i += 1
            else:
                break
    return "".join(out)


def update_env_makefile(
    repo_root: Path, remove_julia: bool, remove_stata: bool
) -> None:
    """Update env/Makefile to remove language-specific targets."""
    if not (remove_julia or remove_stata):
        return

    print("\n📝 Updating env/Makefile...")
    env_makefile = repo_root / "env" / "Makefile"

    if not env_makefile.exists():
        print("  ⚠ env/Makefile not found")
        return

    content = env_makefile.read_text()
    original = content

    if remove_julia:
        for target in JULIA_MAKE_TARGETS:
            content = strip_make_prereq(content, target)
            content = strip_make_target(content, target)
        print(f"  ✓ Removed Julia targets ({', '.join(JULIA_MAKE_TARGETS)})")

    if remove_stata:
        # Prerequisite and .PHONY entries first: the section removal takes the
        # rules, but the names also appear in the combined .PHONY list and in
        # all-env, which live above the banner.
        for target in STATA_MAKE_TARGETS:
            content = strip_make_prereq(content, target)
        content = strip_marked_section(content, "Stata")
        print(f"  ✓ Removed Stata targets ({', '.join(STATA_MAKE_TARGETS)})")

    if content == original:
        raise RuntimeError(
            "env/Makefile was not modified. A pruning pattern matched nothing, "
            "which produces a project that still references a removed language. "
            "Check the target and banner names in env/Makefile against "
            "strip_make_target()/strip_make_prereq() in bootstrap.py."
        )

    env_makefile.write_text(content)


def update_main_makefile(
    repo_root: Path, remove_julia: bool, remove_stata: bool
) -> None:
    """Update main Makefile to remove language-specific runners."""
    if not (remove_julia or remove_stata):
        return

    print("\n📝 Updating Makefile...")
    makefile = repo_root / "Makefile"

    if not makefile.exists():
        print("  ⚠ Makefile not found")
        return

    content = makefile.read_text()

    if remove_julia:
        # Remove JULIA runner line
        content = re.sub(r"JULIA\s*:=.*?\n", "", content)
        print("  ✓ Removed JULIA runner")

    if remove_stata:
        # Remove STATA runner line
        content = re.sub(r"STATA\s*:=.*?\n", "", content)
        print("  ✓ Removed STATA runner")

    makefile.write_text(content)


def update_readme(
    repo_root: Path, remove_julia: bool, remove_stata: bool, new_name: str | None
) -> None:
    """Update README.md to reflect language choices and optionally rename project."""
    print("\n📝 Updating README.md...")
    readme = repo_root / "README.md"

    if not readme.exists():
        print("  ⚠ README.md not found")
        return

    content = readme.read_text()

    # Update title if renaming
    if new_name:
        # Replace first heading
        content = re.sub(r"^#\s+.*?\n", f"# {new_name}\n", content, count=1)
        print(f"  ✓ Updated title to '{new_name}'")

    # Update language list
    languages = ["Python 3.12"]
    if not remove_julia:
        languages.append("Julia 1.10-1.12")
    if not remove_stata:
        languages.append("Stata (optional)")

    lang_list = ", ".join(languages)

    # Update multi-language support line
    content = re.sub(
        r"- \*\*Multi-language support\*\*:.*?\n",
        f"- **Language support**: {lang_list}\n",
        content,
    )

    if remove_julia and remove_stata:
        print("  ✓ Updated to Python-only project")
    elif remove_julia:
        print("  ✓ Updated to Python + Stata project")
    elif remove_stata:
        print("  ✓ Updated to Python + Julia project")

    readme.write_text(content)


def rename_project(repo_root: Path, new_name: str) -> None:
    """Rename the project throughout documentation."""
    print(f"\n📝 Renaming project to '{new_name}'...")

    # Update README.md
    update_readme(repo_root, False, False, new_name)

    # Update QUICKSTART.md
    quickstart = repo_root / "QUICKSTART.md"
    if quickstart.exists():
        content = quickstart.read_text()
        content = re.sub(
            r"^#\s+.*?\n", f"# {new_name} - Quick Start\n", content, count=1
        )
        quickstart.write_text(content)
        print("  ✓ Updated QUICKSTART.md")

    # Update shared/config.py
    config_py = repo_root / "shared" / "config.py"
    if config_py.exists():
        content = config_py.read_text()
        # Update the project name comment if it exists
        content = re.sub(r"# Project:.*?\n", f"# Project: {new_name}\n", content)
        config_py.write_text(content)
        print("  ✓ Updated shared/config.py")


def interactive_mode(repo_root: Path) -> None:
    """Run in interactive mode, prompting for each option."""
    print("\n" + "=" * 60)
    print("Project Template Bootstrap - Interactive Mode")
    print("=" * 60)
    print()
    print("This will help you customize the template for your project.")
    print()

    # Ask about languages
    print("Which languages do you need? (default: all)")
    use_julia = input("  Include Julia? [Y/n]: ").strip().lower() != "n"
    use_stata = input("  Include Stata? [Y/n]: ").strip().lower() != "n"

    # Ask about renaming
    print()
    rename = input("Rename project? [y/N]: ").strip().lower() == "y"
    new_name = None
    if rename:
        new_name = input("  New project name: ").strip()
        if not new_name:
            print("  ⚠ No name provided, skipping rename")
            new_name = None

    # Confirm
    print()
    print("Summary of changes:")
    print("  - Python: ✓ (always included)")
    print(f"  - Julia: {'✓' if use_julia else '✗ (will be removed)'}")
    print(f"  - Stata: {'✓' if use_stata else '✗ (will be removed)'}")
    if new_name:
        print(f"  - Rename to: {new_name}")
    print()

    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("Cancelled.")
        sys.exit(0)

    # Apply changes
    remove_julia = not use_julia
    remove_stata = not use_stata

    if remove_julia:
        remove_julia_files(repo_root)
        update_pyproject(repo_root, remove_julia=True)
        remove_language_analyses(repo_root, JULIA_ANALYSES)

    if remove_stata:
        remove_stata_files(repo_root)
        remove_language_analyses(repo_root, STATA_ANALYSES)

    update_env_makefile(repo_root, remove_julia, remove_stata)
    update_main_makefile(repo_root, remove_julia, remove_stata)
    update_readme(repo_root, remove_julia, remove_stata, new_name)

    if new_name:
        rename_project(repo_root, new_name)

    print()
    print("=" * 60)
    print("✅ Bootstrap complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the changes: git status")
    print("  2. Set up environment: make environment")
    print("  3. Run sample analysis: make all")
    print("  4. (optional) Private maintainer overlay: make private-init")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap project_template after cloning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--remove-julia",
        action="store_true",
        help="Remove Julia support (files, dependencies, targets)",
    )
    parser.add_argument(
        "--remove-stata",
        action="store_true",
        help="Remove Stata support (files, dependencies, targets)",
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="Shorthand for --remove-julia --remove-stata (Python-only project)",
    )
    parser.add_argument(
        "--rename",
        metavar="NAME",
        help="Rename project (updates README, QUICKSTART, config.py)",
    )
    parser.add_argument(
        "--template-commit",
        metavar="SHA",
        help=(
            "Template commit to record in template-origin.toml. Needed when the "
            "tree has no git history of its own (e.g. a `git archive` export); "
            "otherwise read from HEAD."
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (prompts for each option)",
    )

    args = parser.parse_args()

    # --python-only is just a shorthand for removing both optional languages.
    if args.python_only:
        args.remove_julia = True
        args.remove_stata = True

    # Find repository root
    repo_root = Path(__file__).parent.resolve()

    # Interactive mode
    if args.interactive:
        interactive_mode(repo_root)
        return

    # Non-interactive mode. --template-commit counts as an action on its own:
    # a project that keeps all three languages still needs its origin recorded,
    # and that is exactly the full-variant case `make instance` produces.
    if not any(
        [args.remove_julia, args.remove_stata, args.rename, args.template_commit]
    ):
        parser.print_help()
        print()
        print("Error: No actions specified. Use --interactive or provide options.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Project Template Bootstrap")
    print("=" * 60)

    # Apply requested changes
    if args.remove_julia:
        remove_julia_files(repo_root)
        update_pyproject(repo_root, remove_julia=True)
        remove_language_analyses(repo_root, JULIA_ANALYSES)

    if args.remove_stata:
        remove_stata_files(repo_root)
        remove_language_analyses(repo_root, STATA_ANALYSES)

    if args.remove_julia or args.remove_stata:
        update_env_makefile(repo_root, args.remove_julia, args.remove_stata)
        update_main_makefile(repo_root, args.remove_julia, args.remove_stata)
        update_readme(repo_root, args.remove_julia, args.remove_stata, args.rename)

    if args.rename:
        rename_project(repo_root, args.rename)

    write_template_origin(repo_root, args)

    print()
    print("=" * 60)
    print("✅ Bootstrap complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the changes: git status")
    print("  2. Set up environment: make environment")
    print("  3. Run sample analysis: make all")
    print("  4. (optional) Private maintainer overlay: make private-init")
    print()


if __name__ == "__main__":
    main()
