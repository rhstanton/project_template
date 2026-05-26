# Running Locally vs. with Docker

There are two supported ways to build this project's artifacts:

1. **Locally (native)** — uv builds a virtualenv directly on your machine. Fastest; best for day‑to‑day work.
2. **In Docker** — a digest‑pinned Linux image builds the *same* environment inside a container. Isolated and OS‑pinned; best for replication packages, sandboxing, and eliminating "works on my machine" drift.

Both build from the **same sources** — `pyproject.toml` + `uv.lock` (Python), `env/Project.toml` (Julia), and the `Makefile`. Docker is deliberately a thin wrapper that runs the same `make environment` / `make all` you'd run locally, so there is **one source of truth** and the two paths can't drift apart.

---

## TL;DR

| | Local (native) | Docker |
|---|---|---|
| Setup | `make environment` | `docker build -t project-template-repro .` |
| Run all artifacts | `make all` | `docker run --rm -v "$PWD/output:/project/output" project-template-repro` |
| Speed | Fast (native) | Slower on macOS (Linux VM) |
| Isolation | Runs on your host | Fully isolated container |
| Reproducibility | High (uv.lock) | Highest (OS + libs pinned by digest) |
| Stata | ✅ if installed | ❌ omitted (commercial license) |
| Best for | Developing & iterating | Replication, sandboxing, CI parity |

---

## Running locally (native)

**Prerequisites** (only one is truly required up front):

- **GNU Make 4.3+** — *required*. macOS ships 3.81; install a modern Make with `brew install make` and use `gmake`. Most Linux distros already have ≥4.3.
- **git** — for cloning and provenance.
- **uv**, **Julia**, and all packages are **auto‑installed** by `make environment` (uv via `env/scripts/install_uv.sh`; Julia via juliacall).
- **Stata** (optional) — only if you use the Stata example; it's commercial and not auto‑installed.

**Commands:**

```bash
make environment    # uv sync (.venv) + Julia via juliacall + Stata packages (if Stata present)
make verify         # quick smoke test (~1 min)
make all            # build all figures/tables/provenance into output/
make check          # lint + format + type-check + tests
make publish        # copy output/ -> paper/ with provenance (see publishing.md)
```

**Where things live:** the Python env is `.venv/`, the Julia depot is `.julia/`, and build outputs go to `output/` — all inside the repo, none global. (All are git‑ignored and rebuilt per machine.)

Use the wrappers (`env/scripts/runpython`, `runjulia`, `runnotebook`) — not bare `python`/`julia` — so the Julia bridge and `PYTHONPATH` are set correctly. See [environment.md](environment.md).

---

## Running with Docker

The repo ships a **digest‑pinned `Dockerfile`** at its root.

```bash
# Build the image (one time; installs the whole environment inside it)
docker build -t project-template-repro .

# Reproduce all artifacts; outputs are written to ./output on your host
docker run --rm -v "$PWD/output:/project/output" project-template-repro
```

What happens:

- The image is based on `debian:bookworm-slim` **pinned by SHA256 digest**, with `make`, `git`, `curl` and a **pinned uv** added.
- At **build time** it runs `make environment` — `uv sync` from `uv.lock` (so the Python env is exact) plus Julia via juliacall — and precompiles, so reproduction is fast and offline.
- The default command (`CMD`) runs `make all && make test-outputs`, producing the five artifacts and verifying them.
- Mounting `-v "$PWD/output:/project/output"` makes the generated figures/tables/provenance appear in your host's `output/` directory.

**Architecture:** building on Apple Silicon produces a native `linux/arm64` image. For a reviewer‑standard `linux/amd64` image, add `--platform linux/amd64` (emulated, slower to build).

**Stata** is intentionally omitted from the image (license); no shipped artifact needs it. If you require Stata in a container you must mount a licensed installation yourself.

---

## Developing under Docker

The section above *reproduces* artifacts (build once, run, collect `output/`). This section is for the other case: actually **iterating** inside the container — running tests, rebuilding artifacts, editing source. You'd want this for **sandboxing** (e.g. letting a coding agent run without host access), when you're **on Linux** (no VM penalty), or to **debug a Docker-only issue**.

There are three loops, from simplest to most seamless. **Loop A is the recommended default.** All of them start from the image you built with `docker build -t project-template-repro .`.

> **The one rule that makes Docker dev confusing if you miss it:** the Python env (`/project/.venv`) and Julia depot (`/project/.julia`) are **baked into the image as Linux binaries**. Never bind-mount your host repo over `/project` — your host's `.venv`/`.julia` (macOS, or absent) would shadow them and nothing would import. The loops below are exactly the ways to get live source edits *without* shadowing those two paths.

### Loop A — edit → rebuild → run (recommended)

No live mounts; you rebuild between change sets. The rebuild is fast because only the final source layer is rebuilt (the Python and Julia layers stay cached — see [layer ordering](#layer-ordering-for-fast-rebuilds-the-decision) below).

```bash
# 1. Build once.
docker build -t project-template-repro .

# 2. Edit run_analysis.py / shared/config.py / a notebook on your host, then:
docker build -t project-template-repro .                                  # seconds: only the COPY . . layer rebuilds
docker run --rm -v "$PWD/output:/project/output" project-template-repro   # re-runs `make all`, writes ./output

# Repeat step 2 for each change set.
```

To run something other than the default `make all && make test-outputs`, append a command — it overrides the image's `CMD`:

```bash
docker run --rm -v "$PWD/output:/project/output" project-template-repro make verify
docker run --rm -v "$PWD/output:/project/output" project-template-repro make test
docker run --rm -v "$PWD/output:/project/output" project-template-repro make price_base
```

Or drop into an interactive shell and work there (the whole toolchain is present):

```bash
docker run --rm -it -v "$PWD/output:/project/output" project-template-repro bash
# inside the container — note these see the source as of the last `docker build`:
make verify                                              # smoke test
make all                                                 # build all artifacts -> /project/output (= host ./output)
make test                                                # full pytest suite
env/scripts/runpython -m pytest tests/test_defaults.py -v
exit                                                     # --rm deletes the container; the image is unchanged
```

### Loop B — live source mount (no rebuild between edits)

For a tight inner loop: edit on the host, immediately re-run inside the container, **no rebuild**. The trick is to bind-mount **only the specific source files/dirs you edit** — never the whole repo (that would shadow `.venv`/`.julia`; see the rule above).

```bash
docker run --rm -it \
  -v "$PWD/output:/project/output" \
  -v "$PWD/run_analysis.py:/project/run_analysis.py" \
  -v "$PWD/run_did.py:/project/run_did.py" \
  -v "$PWD/shared:/project/shared" \
  -v "$PWD/notebooks:/project/notebooks" \
  -v "$PWD/tests:/project/tests" \
  project-template-repro bash
# now host edits to any of those paths are visible immediately inside the container:
make all          # picks up your edits — no rebuild
make test
```

Add a `-v "$PWD/<path>:/project/<path>"` line for any other top-level file or dir you actively edit (e.g. `Makefile`). **Do not** add a `-v` for `.venv`, `.julia`, `env/`, or the whole repo — those must stay the image's Linux builds.

### Loop C — full live dev (whole repo mounted, env in named volumes)

The most seamless option: the **entire repo is live** (no enumerating mounts), yet `.venv`/`.julia` are protected because two **named volumes** sit on top of exactly those paths and are seeded from the image. This is the model a VS Code Dev Container uses.

```bash
docker run --rm -it \
  -v "$PWD:/project" \
  -v project-template-venv:/project/.venv \
  -v project-template-julia:/project/.julia \
  project-template-repro bash
# every file under /project is now live AND .venv/.julia are the image's Linux builds:
make all
make test
```

Why this works (and why it's safe):

- `-v "$PWD:/project"` makes every file live — including `output/`, so results land on the host with no separate mount.
- The two named volumes target **more specific paths** (`/project/.venv`, `/project/.julia`), so they win over the repo bind mount at exactly those subpaths. On first use Docker **seeds each empty named volume from the image's content** at that path — i.e. the baked Linux env — then persists it across runs.

**Gotcha — named volumes are sticky.** Once seeded they persist. If you later rebuild the image with new Python/Julia deps, the volumes keep the *old* env. Re-seed by deleting them:

```bash
docker volume rm project-template-venv project-template-julia   # next run re-seeds from the new image
```

**Turning Loop C into a VS Code Dev Container.** Create `.devcontainer/devcontainer.json` (not shipped — this is the exact recipe):

```json
{
  "name": "project-template",
  "build": { "dockerfile": "../Dockerfile" },
  "workspaceFolder": "/project",
  "workspaceMount": "source=${localWorkspaceFolder},target=/project,type=bind",
  "mounts": [
    "source=project-template-venv,target=/project/.venv,type=volume",
    "source=project-template-julia,target=/project/.julia,type=volume"
  ],
  "overrideCommand": true
}
```

Then in VS Code: **Dev Containers: Reopen in Container**. `overrideCommand: true` keeps the container idling on a shell instead of running the image's `make all` `CMD`, so you can work interactively. (The same named-volume re-seed gotcha applies: `docker volume rm …` after a dependency change.)

### Which loop?

| | Live edits without rebuild? | Mounts to manage | Best for |
|---|---|---|---|
| **A** edit → rebuild → run | No (rebuild ~seconds) | `output/` only | Most work; simplest, nothing to get wrong |
| **B** selective source mount | Yes, for mounted paths | One `-v` per edited path | A tight loop on a known set of files |
| **C** whole repo + named volumes | Yes, everything | repo + 2 named volumes | Full in-container dev / VS Code Dev Container |

All three keep the slow env build cached or baked, so your feedback loop is the analysis run itself, not an environment rebuild.

---

## How the two paths relate

- **They share specs, not built binaries.** Both build from `pyproject.toml`/`uv.lock`/`env/Project.toml`. They do **not** share `.venv/` or `.julia/` — those contain OS/architecture‑specific binaries and are rebuilt independently in each environment (which is why they're git‑ignored). The container can't reuse your host's `.venv`, and vice‑versa.
- **Both paths run Julia 1.12.** juliapkg derives the allowed Julia version from the Python interpreter's OpenSSL; on Python 3.12 uv's CPython links OpenSSL 3.5 on **both macOS and Linux**, so both install **Julia 1.12**. A macOS host and the Debian image therefore run the *identical* Julia version, and the produced figures/tables match to display precision (verified). The Docker image remains the canonical reproducible artifact (always Linux + Julia 1.12). *(Under the old Python 3.11, macOS was capped at Julia 1.11 while Linux got 1.12 — bumping to 3.12 unified them; see [docs/julia_python_integration.md](julia_python_integration.md).)*
- **You can use both, interchangeably.** They don't conflict: `.dockerignore` excludes your local `.venv/`, `.julia/`, and `output/`, so the image always builds a clean environment regardless of your working tree.

---

## Why pick one over the other

**Use local (native) when you are:**

- Developing and iterating — far faster feedback (no container build, native I/O).
- Debugging (breakpoints, REPL, editor integration).
- Using **Stata** (only available on the host).
- On a machine you trust and where toolchain footprint isn't a concern.

**Use Docker when you want:**

- **A replication artifact** — a reviewer runs two commands and reproduces your results on a known‑good OS, no local toolchain required. This is the strongest "it will still run in N years / on someone else's machine" guarantee.
- **Sandboxing** — run untrusted or autonomous code (e.g. coding agents) without giving it access to the rest of your machine. (For true isolation, also avoid passing host credentials and restrict network — the container boundary alone doesn't do that.)
- **To eliminate OS drift** — the image pins the OS, system libraries, and toolchain, ruling out "works on my machine" problems that pinned Python/Julia versions alone can't.
- **CI parity** — the container mirrors what CI builds.

Rule of thumb: **develop locally, ship/verify with Docker.**

---

## How the Docker image is built — storage, the macOS boundary, and layer caching

This section records *why* the `Dockerfile` is structured the way it is — both the file-storage/performance reasoning and the layer ordering — so the choices are clear a year from now.

### Docker on macOS runs a Linux VM

Containers are Linux, so on macOS Docker (Docker Desktop / colima) runs a lightweight **Linux VM**. All images and containers live on **the VM's virtual disk**, not directly on your Mac. "The boundary" is the macOS ↔ VM line; crossing it (via the file-sharing layer, VirtioFS / gRPC-FUSE) is **slow for many small files** — exactly the access pattern of importing thousands of Python/Julia files.

### Where each thing is stored, and whether it crosses the boundary

| What | Stored in | Crosses the boundary at run time? |
|---|---|---|
| `.venv` (Python env, multi-GB) | **image layer** (VM disk) | **No** — read VM-native |
| `.julia` (Julia depot + precompiled cache) | **image layer** (VM disk) | **No** — read VM-native |
| analysis source (`run_analysis.py`, …) | image layer (VM disk) | No |
| `output/` (figures / tables / provenance) | **bind mount** → your Mac | Yes — but only ~15 small files |

The environment is **baked into the image** during `docker build`, so at run time it's read at full VM speed. The only bind mount is `-v "$PWD/output:/project/output"`, so only the handful of small result files cross the boundary. `.dockerignore` keeps the build context lean (it excludes `.venv/`, `.julia/`, `output/`, …), so the host→VM transfer at build is small and one-time.

**The anti-pattern we avoid:** `docker run -v "$PWD:/project"` (mounting the whole repo) and building `.venv` on that mount — then every `import` would `stat`/`open` files **across the boundary** (often 5–20× slower on macOS), and a host `.venv` (macOS binaries) wouldn't even run in the Linux container. We deliberately copy source into the image and build the env in the image instead.

### Layer ordering for fast rebuilds (the decision)

**Decision (2026-05):** order the `Dockerfile` so the expensive, slow-changing steps are their own layers *before* the analysis source is copied.

**Why:** Docker caches each layer by a key that includes its inputs; for `COPY . .` that key is a hash of the **entire** source tree. So a flat `COPY . . && make environment` re-runs the ~15–25 min `uv sync` + Julia precompile whenever **any** file changes — painful if you develop under Docker. The split keeps the env layers cached across source edits.

The three layers and what invalidates each:

1. **Python env** — `COPY pyproject.toml uv.lock` + `lib/repro-tools`, then `uv sync`. Rebuilds only when **dependencies** change.
2. **Julia depot** — `COPY env`, then `make -C env julia-install-via-python`. Rebuilds only when **`env/`** changes (e.g. `env/Project.toml`).
3. **Analysis source** — `COPY . .`. Editing `run_analysis.py`, `shared/config.py`, a notebook, etc. rebuilds **only this** layer (seconds), reusing the cached env.

**Trade-off:** a slightly longer Dockerfile vs. a flat one — worth it because we may iterate under Docker. For a strictly build-once replication image, a flat `COPY . . && make environment` would also have been fine.

This caching split is what makes iterating under Docker practical: editing analysis source rebuilds only layer 3 (seconds), reusing the baked env. For the concrete edit/run loops that build on this — including live source mounts and a VS Code Dev Container recipe — see **[Developing under Docker](#developing-under-docker)** above.

## Caveats & notes

- **macOS performance:** Docker runs a Linux VM, so bind‑mount I/O and the build are slower than native. Apple Silicon prefers `linux/arm64`; `linux/amd64` is emulated.
- **Reproducibility granularity:** the `.tex` tables reproduce byte‑for‑byte; the matplotlib **PDFs are not byte‑identical** because matplotlib embeds a creation timestamp (the underlying numbers are identical). Provenance records SHA256 of every output either way.
- **The image isn't published to a registry** by default — build it from the committed `Dockerfile`. Publishing to a registry (e.g. GHCR) is an optional extra step.
- **Multiple repro layers:** the project also ships a Nix dev shell (`flake.nix`). Pick the layer that fits — uv alone for most work, Docker for shipping/isolation, Nix if you already use it. You don't need all three.

See also: [environment.md](environment.md), [platform_compatibility.md](platform_compatibility.md), [publishing.md](publishing.md).
