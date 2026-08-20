# The shared machinery: what you inherit, and how to adopt it

Your project contains a copy of some things and a *reference* to others. The
difference decides whether a fix made upstream ever reaches you, so it is worth
five minutes.

---

## The two halves

**Copied at generation, frozen thereafter** — your `Makefile`, `env/`,
`scripts/`, your analyses, your docs. These are yours. Nothing will ever change
them behind your back, and no upstream fix arrives on its own.

**Referenced through `lib/repro-tools`** — a git submodule. Its `src/repro_tools/`
is the Python package (provenance recording, publishing, the pre-submission
checker) and its `src/repro_tools/lib/` holds shared `make` machinery your
Makefile `include`s. A fix here reaches you with one command:

```bash
make update-submodules      # fetch the newer repro-tools, stage the new commit
make update-environment     # the same, and reinstall the environment
```

Machinery copied into a project at creation is frozen there forever. That is why
the toolchain half lives where a fix can travel.

## The four layers, and why there are four

`lib/repro-tools/src/repro_tools/lib/` contains:

| file | requires | what it gives you |
|---|---|---|
| `tools.mk` | `$(PYTHON)` | `lint`, `format`, `format-check`, `type-check`, `check`, `test`, `test-fast`, `test-cov`, `system-info`, `dryrun` |
| `repro.mk` | `$(PYTHON)` + the package | `pre-submit`, `pre-submit-strict`, `diff-outputs`, `replication-report`, `template-diff` |
| `git.mk` | git | `init-submodules`, `update-submodules`, `update-environment` |
| `layout.mk` | your project's *shape* | `environment`, `verify`, `test-outputs`, `check-deps`, `clean`, `cleanall`, `examples`, `sample-*`, `list-analyses-names` |
| `common.mk` | — | includes all four |
| `stata.mk` | Stata | the vendored-package rules |

`make include` is all-or-nothing, which is the whole reason for the split.
`layout.mk` assumes a specific project shape: `$(DATA)` as a single input file,
`$(ANALYSES)` as a flat list in the root Makefile, `$(OUT_*)` directories, an
`env/` sub-Makefile. If your project has grown a different shape, you would
otherwise have to refuse all thirty targets to avoid those twelve.

## Adopting the layers in an existing project

Take them in order of risk. Each step is independently useful, so stop wherever
it stops paying.

**1. Make the machinery reachable.** If `lib/repro-tools` is not already a
submodule, add it. It must be a *checkout*, not just an installed package: the
`include` is resolved when `make` **parses** your Makefile, and `env/env.sh` has
to read the shared toolchain file to work out where `.venv` is. A package inside
`.venv` is unreachable at exactly the moment it is needed.

```bash
git submodule add <repro-tools-url> lib/repro-tools
```

If your `.gitignore` is allowlist-style (starts with `*`), add `!/lib/repro-tools`
first — otherwise `git submodule add` refuses with *"Use -f if you really want to
add them"*, which reads like a warning about the submodule rather than about
your ignore file.

Point the Python dependency at the same checkout, so one commit pins both:

```toml
[tool.uv.sources]
repro-tools = { path = "lib/repro-tools", editable = true }
```

**2. Include `git.mk` first.** It collides with almost nothing and it *is* the
propagation channel — `update-submodules` is how every later fix arrives.

```makefile
REPRO_LIB := lib/repro-tools/src/repro_tools/lib
include $(REPRO_LIB)/git.mk
```

**3. Then `tools.mk` and `repro.mk`.** These define `$(PYTHON)`-driven targets you
may already have. Delete your copies and adapt through **variables**, never by
redefining the recipe — `make` resolves a redefinition silently
(last-definition-wins) and its "overriding recipe" warning buries real ones.

```makefile
PYTHON          := env/scripts/runpython
TEST_PATHS      :=                      # empty => your pytest testpaths win
TEST_DEPS       := check-environment    # run before the test targets
LINT_PATHS      := src/ tests/          # default is .
TYPECHECK_PATHS := src/
CHECK_DEPS      := lint format-check type-check   # what `make check` enforces
```

**`TEST_PATHS` deserves care.** Its default is empty on purpose. An earlier
version defaulted to `tests/`, which in a project whose `testpaths` span several
directories collected *55% of the suite and still printed a tick*. If you set it,
confirm the collected count:

```bash
make -n test                      # see the exact pytest invocation
python3 -m pytest --collect-only -q | tail -1
```

**4. Keep your own `layout.mk` targets.** If your data is many files, or your
analyses are declared in sub-Makefiles, or your outputs are grouped into
subdirectories, then `verify`, `test-outputs`, `check-deps` and `clean` encode
facts about *your* project. Do not include `layout.mk`; keep yours.

## Checking that adoption worked

```bash
make -n help 2>&1 | grep -i overriding   # must be silent: a hit is a silent collision
make -n <target>                          # what each inherited target will actually run
make list-analyses-names                  # bare artifact names, one per line
make pre-submit                           # must do real work, not just print a banner
```

The last one is not rhetorical. An undefined `make` variable expands to the
empty string and is **not** an error, so a target whose command variable is
undefined prints its banner, runs nothing, and exits 0. Every command in these
layers now carries a `?=` default and a test enforces it, but the same trap is
available to any Makefile you write. When a check passes, ask what it would look
like if it were broken; if the answer is "the same", it is not a check.

## If something goes wrong

- **A target does the wrong thing after adoption** — you have two definitions.
  `make -n help 2>&1 | grep overriding` finds it; convert your version into a
  variable rather than keeping both.
- **`make pre-submit` reports artifacts missing that plainly exist** — the
  checker looks in `output/<kind>/<name>.<ext>` and one directory below it. If
  you nest deeper than one level, flatten or file an issue.
- **`include` fails on a fresh clone** — `git submodule update --init --recursive`.
  If it refuses because the path is non-empty, you copied a working tree over a
  clone; remove `lib/repro-tools` and retry. See
  [troubleshooting.md](troubleshooting.md).
