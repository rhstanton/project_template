# bootstrap.py prunes the documentation for a removed language

**Found 2026-08-19** by porting fire's documented-command sweep here: the test
passed on this repository and failed on every pruned variant. **Fixed the same
day** with option 1 below.

## What was happening

`bootstrap.py --python-only` (and `--remove-julia`, `--remove-stata`) removed the
language's scripts, its Makefile targets, its environment files and its tests. It
did not touch the documentation. A generated python-only project therefore
shipped instructions to run commands that did not exist there — `make
sample-julia`, `make -C env julia-install-via-python`, `env/scripts/runstata`.

Worse than the broken commands was what guarded them: `tests/test_documented_
commands_exist.py` **skipped itself** in a pruned project. The suite was green
exactly where the docs were wrong. That skip is now gone, and the sweep runs in
pruned projects too — it is what will catch the next unmarked Julia command.

## What was built

Three mechanisms, because a language hides in two different kinds of place.

**1. Block markers, for prose.**

```markdown
<!-- julia:start -->
### Check Julia installation
...
<!-- julia:end -->
```

`strip_marked_doc_sections()` removes the whole span. An unbalanced marker
**raises** rather than being skipped: a start with no end used to mean "keep
everything after it", which ships the content the marker exists to remove.

**2. Exact-basename removal of directory-tree rows.**

Markers are HTML comments, and an HTML comment inside a fenced code block renders
as literal text to the reader. So markers cannot reach a single line of

```
│   └── scripts/
│       ├── runpython          # Python wrapper
│       ├── runjulia           # Julia wrapper
│       └── runstata           # Stata wrapper
```

and splitting a tree diagram into one fence per language shreds the drawing.
`prune_tree_lines()` instead matches the **exact basenames bootstrap just
deleted** (`JULIA_FILES` / `STATA_FILES`, now module constants so there is one
list, not two), and only on lines carrying a `├── ` or `└── ` connector — the one
place in Markdown where a bare filename is the whole content of a line. It then
repairs the terminator, so removing a `└── ` row does not leave a tree dangling.

`test_pruning_nothing_changes_nothing_in_the_real_docs` pins that repair: pruning
an empty set must be a byte-for-byte no-op on every tree in the repo. It caught
the first version, whose "spacer" rule handled a bare `│` but not `│   │`, and
which therefore wanted to rewrite `docs/README.md`.

**3. Exact-name removal from `ANALYSES :=` lines**, for the same fenced-code
reason, keyed on the analyses bootstrap removes (`julia_demo`, `did_example`).

## Which files get pruned

`prunable_docs()`: every `.md` in the repo except those in a generated, vendored
or environment directory. Two details, both learned the hard way:

- The test is on the **directory**, not the file. `replication-package/` is a
  whole generated copy of the repo and `paper/` is build output — both gitignored,
  both would be pruned pointlessly and overwritten by the next `make`. But
  `AGENTS.md` and `CLAUDE.md` are gitignored *files* in a tracked directory, and
  they are exactly what an agent reads first. A "tracked files only" rule skips
  them; an "all files" rule edits build output.
- `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md` are three
  **symlinks to one file** in the `private/` overlay. Resolve, drop anything
  landing outside the repo, and visit each real file once — otherwise every edit
  is applied three times to a file that is not part of the project.

`lib/` and `notes/` are excluded by name (submodule content; institutional
memory that *quotes* commands rather than instructing), and `CHANGELOG.md`
because pruning a historical record rewrites what past releases contained.

## Two bugs this found in the writing of it

- **`_ignored_dirs` failed open.** `git check-ignore` exits 128 on a path inside
  a submodule; the first version caught that and returned an empty set, silently
  turning the whole directory filter off. It now raises for any failure except
  "not a git repository". A check that cannot fail is the recurring defect in
  this repo's machinery, and this was one more.
- **Nested markers.** Wrapping a `.stata/` section that already contained a
  marked pair produced `start ... start ... end ... end`; stripping matched the
  first `end`, leaving a stray one and aborting bootstrap. Caught by the
  unbalanced-marker guard, now pinned by
  `test_markers_are_balanced_and_unnested`.

## Known limits

- Marking is line-based, so an **inline** mention inside a sentence ("packages
  install to `.venv/` and `.julia/`") cannot be marked. Those were reworded where
  cheap and left otherwise; they are inaccurate prose in a pruned project, not a
  broken instruction.
- `README.md`'s own description of the template ("one, two, or three languages —
  your choice") survives into generated projects. That is a separate question —
  how much of the template's self-description a generated project should inherit
  — and is not about pruning.
- The residual is bounded by `test_the_marked_files_actually_lose_their_commands`,
  which asserts that after stripping, no document still names a wrapper or a
  `make sample-<lang>` target for the removed language.

## Options considered

1. **Block markers** — chosen. Explicit, reviewable, and the marks document what
   a section is about even when nothing is pruned.
2. **Split the docs by language** (`docs/julia/...`) and delete directories.
   Simplest to implement, worst to read: the multi-language story fragments.
3. **A note at the top of each affected file** saying some commands will not
   exist in a pruned project. Cheap, honest, and does not fix the reader's
   actual problem.
