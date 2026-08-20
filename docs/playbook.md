# Playbook: what to do, by situation

Look up the situation, run the command. Each entry links onward for the *why*.

Two audiences, and the split matters — see [Which am I?](#which-am-i) if unsure:

- **[In a project](#in-a-project)** — you are doing research in a project made from this template.
- **[On the template](#on-the-template)** — you are changing the template itself, or the shared machinery.
- **[Propagating changes](#propagating-changes)** — you fixed something in the template and want it in projects that already exist.

---

## Which am I?

```bash
test -f template-origin.toml && echo "a generated project" || echo "the template itself"
```

<!-- template-only:start -->
`bootstrap.py` writes `template-origin.toml` into every project it creates; the template has none. Several commands and tests branch on exactly this.
<!-- template-only:end -->

Your project has `template-origin.toml`, recording the template commit it was generated from. Several commands and tests branch on exactly this.

---

## In a project

### Starting and setting up

<!-- template-only:start -->
**Starting a new project.** "Use this template" on GitHub, then:

```bash
git clone --recursive <your new repo>
cd <your project>
python3 bootstrap.py --interactive     # choose languages, rename
```

Run bootstrap **before** `make environment` — it edits `pyproject.toml` and the
Makefiles, and doing it afterwards means rebuilding a multi-gigabyte environment.
See [bootstrap_and_markers.md](bootstrap_and_markers.md).
<!-- template-only:end -->

| Situation | Do this |
|---|---|
| Cloned without `--recursive`; `lib/repro-tools` is empty | `git submodule update --init --recursive` |
| Set up the environment | `make environment` (~10–15 min), then `make verify` |
| Set up on a second machine | Same two commands. The environment is never committed; it is rebuilt from `uv.lock` |
| Check what I am running | `make info` (versions, layout), `make system-info` (OS, Make, interpreters, GPU) |

### Generating and checking figures and tables

| Situation | Do this |
|---|---|
| Build everything | `make all` → figures, tables and a `provenance.yml` per artifact in `output/` |
| Build one analysis | `make <name>` — list them with `make list-analyses` |
| See what a build *would* do, without doing it | `make dryrun` |
| Inspect one analysis's inputs, outputs and runner | `make show-analysis-<name>` |
| Confirm every expected output exists | `make test-outputs` |
| **Check the numbers did not change** | `make check-baseline` — compares against a committed reference. This is the check that matters |
| Compare current output against what was published | `make diff-outputs` |
| A figure looks wrong | Rebuild that one analysis, then open the PDF. Check `output/logs/<name>.log` and `output/provenance/<name>.yml` for the exact command and inputs |
| A build is slow | `make -j4 all`. Only helps for independent targets |
| Force a rebuild | `touch` the input, or delete the artifact. Do not edit `output/` by hand |

### Publishing and submitting

| Situation | Do this |
|---|---|
| Copy artifacts into the paper | `make publish` — the only sanctioned route from `output/` to `paper/`. Enforces a clean tree, not-behind-upstream, and artifacts built from the current HEAD. See [publishing.md](publishing.md) |
| Publish while the tree is dirty | `make publish ALLOW_DIRTY=1` — and know that the provenance then records a dirty build |
| **Build the replication package** | `make journal-package` → a self-contained directory; then `make journal-package-zip` or `-tarball`. It vendors every submodule, deletes `.gitmodules`, and asserts the result contains no submodules, no symlinks and no instruction to run git |
| Check I am ready to submit | `make pre-submit` — environment, data checksums, artifacts built, provenance current, git state |
| Regenerate the pip requirements a package ships | `make -C env python-export`. `journal-package` refuses a stale export, comparing a recorded `uv.lock` hash rather than mtimes |

### Adding to and changing the project

| Situation | Do this |
|---|---|
| Add an analysis | Add its entry in `Makefile` (`ANALYSES` + the per-analysis variables) and its study in `shared/config.py`. See [TEMPLATE_USAGE.md](../TEMPLATE_USAGE.md) |
| Remove an analysis | `make remove-analysis NAME=<name>` — drops the Makefile entry, the config entry, the script and its artifacts |
| Add a Python dependency | Edit `pyproject.toml`, then `make -C env python-relock`, then re-run `make check-baseline` |
| Change the version | `make bump-version VERSION=X.Y.Z` — updates every place at once and refuses a version not ahead of your release tags |
| Run the checks CI runs | `make check` (lint, format-check, type-check, test). **Run this before pushing**, not after |
| Just the fast tests | `make test-fast` |

### When something is wrong

| Situation | Do this |
|---|---|
| Anything at all | `make verify` first, then [troubleshooting.md](troubleshooting.md), which is organized by symptom |
| An error mentions a submodule and a github.com URL | Read the line *above* it. Usually the path exists and is non-empty (a working tree copied over a clone), not an auth problem |
| Tests fail on `AGENTS.md`/`CLAUDE.md` with a pathlib error | Dangling symlinks into the gitignored `private/` overlay. `make private-init`, or delete the links |
| A wrapper "works" but CI disagrees | Test it with the environment stripped — direnv may be handing it an environment it never sets. See troubleshooting |
| A path became two paths | `CDPATH`. See troubleshooting; it is the first thing to check after touching any wrapper |
| `make` behaves oddly on macOS | You are on Make 3.81. `brew install make`, then use `gmake` |

---

## On the template

| Situation | Do this |
|---|---|
| I changed anything | `make check` **and** `make test-variants` before pushing. The first is what CI runs; the second builds each pruned variant, which is where template-only assumptions break |
| I edited documentation | Same two. If you documented a Julia- or Stata-specific command, wrap it in `<!-- julia:start -->` / `<!-- julia:end -->` markers — see [bootstrap_and_markers.md](bootstrap_and_markers.md). Markers cannot go inside a code fence |
| I want a real generated project to poke at | `make instance VARIANT=python-only` → a disposable tree in a sibling directory. `make instance-list`, `make instance-clean` |
| I added a make target | Add it to `make help`. If it is generic, it probably belongs in the shared machinery instead — see below |
| I changed the shared machinery | Edit under `lib/repro-tools/src/repro_tools/lib/`, commit **and push** in that submodule, then commit the new pointer in the parent. Both repos that vendor it must be bumped |
| Which layer does a target belong in? | `tools.mk` if it needs only `$(PYTHON)`; `repro.mk` if it needs the `repro_tools` package; `git.mk` if only git; `layout.mk` if it assumes `$(DATA)`/`$(ANALYSES)`/`$(OUT_*)`. See [shared_machinery.md](shared_machinery.md) |
| CI is red and local is green | Check that CI calls the make targets rather than restating commands, and that the tool versions are pinned in one place |
| I want to cut a release | `make bump-version VERSION=X.Y.Z`, review `git diff`, commit, then tag `vX.Y.Z`. The bump refuses a version not ahead of existing tags |

---

## Propagating changes

**You fixed something in the template. Getting it into projects that already exist depends on which half it lives in.**

### The two halves

| Half | What it is | Does a fix travel? |
|---|---|---|
| **Referenced** — `lib/repro-tools` | the `repro_tools` package and the shared `*.mk` / `env.sh` | **Yes.** `make update-submodules` |
| **Copied** — `Makefile`, `env/`, `scripts/`, docs, tests | everything bootstrap copied at generation | **No.** Diff and port by hand |

So the first question for any fix is *which half does this belong in* — and if it is generic, moving it into `lib/repro-tools` is what makes this problem go away permanently for every future fix.

### The procedure

```bash
# In the project that should receive the fix:
make template-diff            # what changed in the template since this project was generated
make template-diff ARGS=--verbose   # every differing file, not just a summary

make update-submodules        # pull the referenced half
make update-environment       # the same, and reinstall the environment

make check                    # then verify nothing broke
make check-baseline           # and that no number moved
```

`template-diff` reads `template-origin.toml` to learn which template commit the project came from, clones the template, and reports what has changed since. It **shows** you the drift; it does not merge — a generated project has diverged on purpose, and an automatic merge would overwrite deliberate local choices.

### Keeping track of which projects exist

**There is no registry, and nothing discovers them.** This is a real gap, stated plainly rather than papered over. What exists today:

- Each project records where it came from, in its own `template-origin.toml`.
- Nothing records, anywhere central, that the project exists.

Until that changes, the practical options are:

```bash
# Find them on this machine:
find ~ -name template-origin.toml -not -path '*/.*' 2>/dev/null

# Ask each what it is missing:
for p in $(find ~ -name template-origin.toml -not -path '*/.*' 2>/dev/null); do
    d="$(dirname "$p")"; echo "== $d"; (cd "$d" && make template-diff 2>&1 | tail -3)
done
```

If you keep a list by hand, keep it somewhere that is not the template — the template does not know its children, and pretending otherwise in a file here would rot.

### Where a fix should live — decide once, not per incident

Ask: **would this fix need to reach projects that already exist?**

- **Yes, and it is generic** → `lib/repro-tools`. Every project gets it with one command.
- **Yes, but it is project-shaped** (assumes `$(DATA)`, `$(ANALYSES)`, an output layout) → the template's copied half, and accept that existing projects need `template-diff` and a manual port.
- **No** → wherever is convenient.

Every environment bug found in this template so far has been in the generic half, which is why that half was moved into the submodule.

---

## See also

- [shared_machinery.md](shared_machinery.md) — the four make layers, and adopting them in an existing project
- [bootstrap_and_markers.md](bootstrap_and_markers.md) — what bootstrap does, and the doc-marker convention *(deleted in generated projects)*
- [troubleshooting.md](troubleshooting.md) — by symptom, plus problems caused by how you obtained the project
- [publishing.md](publishing.md) · [provenance.md](provenance.md) — the build → publish chain
- [README.md](README.md) — every document, listed by topic
