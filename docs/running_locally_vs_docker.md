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

## How the two paths relate

- **They share specs, not built binaries.** Both build from `pyproject.toml`/`uv.lock`/`env/Project.toml`. They do **not** share `.venv/` or `.julia/` — those contain OS/architecture‑specific binaries and are rebuilt independently in each environment (which is why they're git‑ignored). The container can't reuse your host's `.venv`, and vice‑versa.
- **The Julia version is consistent.** Under uv, the Python interpreter links OpenSSL 3.0 on both a typical Linux/macOS host *and* in the Debian image, so juliapkg selects **Julia 1.11** in both — results match across local and Docker.
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

## Caveats & notes

- **macOS performance:** Docker runs a Linux VM, so bind‑mount I/O and the build are slower than native. Apple Silicon prefers `linux/arm64`; `linux/amd64` is emulated.
- **Reproducibility granularity:** the `.tex` tables reproduce byte‑for‑byte; the matplotlib **PDFs are not byte‑identical** because matplotlib embeds a creation timestamp (the underlying numbers are identical). Provenance records SHA256 of every output either way.
- **The image isn't published to a registry** by default — build it from the committed `Dockerfile`. Publishing to a registry (e.g. GHCR) is an optional extra step.
- **Multiple repro layers:** the project also ships a Nix dev shell (`flake.nix`). Pick the layer that fits — uv alone for most work, Docker for shipping/isolation, Nix if you already use it. You don't need all three.

See also: [environment.md](environment.md), [platform_compatibility.md](platform_compatibility.md), [publishing.md](publishing.md).
