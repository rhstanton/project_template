# Bootstrap and the documentation markers

How `bootstrap.py` turns this template into a project, and the one convention
you must follow when you edit the documentation.

This file describes instantiation, so **bootstrap deletes it** — a generated
project has already been through this and will never run bootstrap again.

---

## What bootstrap does

Run it **once, before `make environment`**:

```bash
python3 bootstrap.py --interactive     # choose languages, rename the project
python3 bootstrap.py --python-only     # or state the choice directly
python3 bootstrap.py --remove-julia
python3 bootstrap.py --remove-stata
```

It makes four passes.

**1. Files.** Deletes the removed language's wrappers, examples, environment
files and version pins — for Julia that is `env/Project.toml`,
`env/Manifest.toml`, `env/juliapkg.json`, `env/scripts/runjulia`,
`env/scripts/install_julia.py` and the two Julia examples; for Stata,
`env/stata-packages.txt`, `env/stata-requirements.txt`, `env/scripts/runstata`,
`env/scripts/execute.ado`, the sample `.do` file, and the vendored
`.stata/ado/plus` package tree.

Leaving a pin behind would be worse than leaving nothing: a committed manifest
for a language the project does not have looks authoritative and describes
nothing.

**2. Example analyses.** Some examples need a specific language, so removing the
language removes them too — via `scripts/remove_analysis.py`, which drops the
`ANALYSES` entry, the Makefile pattern block, the `shared/config.py` study
entry, the script or notebook, and any built artifacts. The result still builds:
`make all` on a pruned project is expected to succeed, and is tested.

**3. Documentation.** Marked sections are removed, and directory diagrams and
`ANALYSES :=` lines lose the names of things that no longer exist. See
[The markers](#the-markers) below.

**4. The template's self-description.** Text that tells a reader to *instantiate
the template* is removed on every bootstrap, whatever the language flags —
instantiating is exactly the moment that text stops being true. A finished
project should not be telling its reader to click "Use this template".

Customization guidance is deliberately **kept**: `TEMPLATE_USAGE.md` loses only
its "Starting a New Project" chapter and keeps everything about adapting the
project you now have. `template-origin.toml` records the template commit you
started from.

## Why the order matters

- **Bootstrap before `make environment`.** Bootstrap edits `pyproject.toml`
  (dropping the `juliacall` dependency), the Makefiles, `shared/config.py` and
  the docs. Running it afterwards means rebuilding a multi-gigabyte environment
  you just built.
- **Clone with `--recursive`.** Without it, `lib/repro-tools/` is empty and the
  `include` in the Makefile fails. Recover with
  `git submodule update --init --recursive`.
- **Bootstrap is not designed to be run twice.** It is idempotent about files
  that are already gone, but it is not a configuration system.

---

## The markers

Documentation is pruned by explicit markers, not by guessing from prose. If you
add documentation for an optional language, you must mark it, and the test suite
will tell you if you forget.

### Block markers, for prose

```markdown
<!-- julia:start -->
### Checking the Julia installation

Run `env/scripts/runjulia -e 'using Pkg; Pkg.status()'`.
<!-- julia:end -->
```

Valid names are `julia`, `stata` and `template-only`. HTML comments are
invisible in rendered Markdown, so a marked file reads normally when nothing has
been pruned.

Rules:

- Markers must be **balanced**. An unmatched start or end aborts bootstrap with
  an error naming the file. This is deliberate: a start with no end used to mean
  "delete everything after it", and silently keeping the rest of a file is worse
  than stopping.
- Markers must **not nest**. `julia` inside `julia` strips the wrong span.
- Markers must sit on their **own line, outside code fences** — see below.

### Markers do not work inside code fences

An HTML comment inside a ` ``` ` block renders as **literal text** to the
reader. So this is wrong:

````markdown
```bash
make sample-python
<!-- julia:start -->
make sample-julia
<!-- julia:end -->
```
````

Split the fence instead, and put the markers between the blocks:

````markdown
```bash
make sample-python
```
<!-- julia:start -->
```bash
make sample-julia
```
<!-- julia:end -->
````

`tests/test_bootstrap_doc_pruning.py` fails on any marker found inside a fence,
and separately checks that stripping leaves an even number of fences — splitting
a block is easy to get half-right, and an odd fence count renders the rest of
the page as code.

### Directory diagrams and `ANALYSES` lines are handled for you

Because markers cannot reach a single line inside a fence, two things are pruned
by exact name instead:

- A row of a directory tree — a line carrying `├── ` or `└── ` — whose filename
  is one bootstrap just deleted. The tree's last-child connector is repaired, so
  removing a `└── ` row does not leave a dangling branch.
- A name in an `ANALYSES :=` line, when that analysis was removed.

Both match **only** names bootstrap itself deleted, and the tree rule applies
only to lines with a tree connector, which is the one place in Markdown where a
bare filename is the whole content of a line. Neither pattern-matches prose, so
a sentence mentioning `runjulia` is left alone — mark it yourself.

### Which files are pruned

Every Markdown file in the repository except those in a generated or vendored
directory. The test is on the **directory**, not the file: `paper/` and
`replication-package/` are build output and are skipped, while `AGENTS.md` and
`CLAUDE.md` are gitignored *files* in a tracked directory and are pruned
normally.

`lib/` and `notes/` are excluded by name — submodule content is not ours to
rewrite, and `notes/` holds design records that *quote* commands rather than
instructing anyone to run them. `CHANGELOG.md` is excluded because pruning a
historical record would rewrite what past releases contained.

---

## Checking your work

```bash
make test-fast                                   # includes every check below
python3 -m pytest tests/test_bootstrap_doc_pruning.py -v
python3 -m pytest tests/test_documented_commands_exist.py -v
```

The command sweep runs **in pruned projects too**. That is the check that
catches a language-specific command you documented without marking: it would
survive into a project that cannot run it.

To see the result rather than trust it, build a throwaway instantiation:

```bash
make instance          # a bootstrapped copy in a sibling directory
```

Regenerate that rather than maintaining one. A hand-kept example rots, and
debugging against a rotted example is worse than having none, because you
believe the answer.
