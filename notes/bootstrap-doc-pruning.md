# bootstrap.py prunes code but not documentation

**Found 2026-08-19** by porting fire's documented-command sweep here: the test
passes on this repository and fails on every pruned variant in CI.

## What happens

`bootstrap.py --python-only` (and `--remove-julia`, `--remove-stata`) removes
the language's scripts, its Makefile targets, its environment files and its
tests. It does not touch `docs/`.

So a generated python-only project ships documentation instructing the reader to
run commands that no longer exist there:

```
make sample-julia
make -C env julia-check
make sample-stata
```

Five files at least: QUICKSTART.md, docs/julia_python_integration.md,
docs/notebook_interactive_workflow.md, docs/platform_compatibility.md,
docs/troubleshooting.md.

## Why it is not fixed here

Deleting a Makefile target is a line. Pruning prose is not: most of these files
discuss all three languages in the same paragraph, and several explain how the
Python/Julia bridge works as a way of explaining the environment as a whole. A
mechanical strip would leave dangling references and half-sentences, which is
worse than a command that does not exist.

Options, roughly in order of effort:

1. **Mark language-specific sections**, e.g. `<!-- julia:start -->` /
   `<!-- julia:end -->`, and have bootstrap drop them. Explicit, reviewable, and
   the marks document what a section is about even when nothing is pruned.
2. **Split the docs by language** — `docs/julia/...` — and delete directories.
   Simplest to implement, worst to read: the three-language story fragments.
3. **Add a note at the top of each affected file** saying it describes the full
   template and that some commands will not exist in a pruned project. Cheap,
   honest, and does not fix the reader's actual problem.

## Meanwhile

`tests/test_documented_commands_exist.py` skips in pruned variants and enforces
in the full one, so no NEW broken command can be introduced. The gap is bounded
to language sections that bootstrap should have removed.
