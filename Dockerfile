# syntax=docker/dockerfile:1
#
# Digest-pinned image: builds the full Python (uv) + Julia environment and
# reproduces every figure, table, and provenance record.
#
#   docker build -t project-template-repro .
#   docker run --rm -v "$PWD/output:/project/output" project-template-repro
#
# WHY THIS LAYOUT (full rationale in docs/running_locally_vs_docker.md):
#  - The environment (.venv, .julia) is built INTO image layers, which live on the
#    Docker VM's disk — NOT bind-mounted from the host. At run time the heavy env is
#    read VM-native; only ./output crosses the macOS<->Linux-VM boundary. Mounting the
#    repo/env from the host instead would make every package import cross that (slow)
#    boundary.
#  - Layers are ordered so the cheap one busts last: Python deps and the Julia depot
#    each get their own layer keyed only on their inputs, so editing analysis source
#    rebuilds only the final COPY — fast enough to iterate (develop) under Docker.
#
# Notes:
#  - Stata is omitted (commercial license); no shipped artifact needs it.
#  - On Debian, uv's CPython links OpenSSL 3.5, so juliapkg installs Julia 1.12.
#    (Python 3.12's CPython links OpenSSL 3.5 on macOS too, so local hosts also get
#    Julia 1.12 -- local and image now run the identical Julia version.)
#  - linux/amd64 on Apple Silicon: add --platform linux/amd64 (emulated, slower).
FROM debian:bookworm-slim@sha256:0104b334637a5f19aa9c983a91b54c89887c0984081f2068983107a6f6c21eeb

ENV DEBIAN_FRONTEND=noninteractive \
    UV_FROZEN=1

# System prerequisites: GNU Make 4.3+ (bookworm ships 4.3), git, curl, ca-certificates.
RUN apt-get update && apt-get install -y --no-install-recommends \
        make \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv (pinned by digest) manages the Python environment from pyproject.toml + uv.lock.
COPY --from=ghcr.io/astral-sh/uv@sha256:e49fde5daf002023f0a2e2643861ce9ca8a8da5b73d0e6db83ef82ff99969baf /uv /uvx /usr/local/bin/

WORKDIR /project

# --- Layer 1: Python env -> .venv (rebuilds only when deps change) -------------
# `uv sync` needs only the lock/spec and the editable repro-tools source, so copy
# just those: editing analysis code below won't invalidate this (expensive) layer.
COPY pyproject.toml uv.lock ./
COPY lib/repro-tools ./lib/repro-tools
RUN uv sync

# --- Layer 2: Julia depot -> .julia (rebuilds only when env/ changes) ----------
# juliacall downloads Julia (1.12 on Debian's OpenSSL 3.5) and precompiles
# PythonCall/DataFrames/FixedEffectModels into the image.
COPY env ./env
RUN make -C env julia-install-via-python

# --- Layer 3: analysis source (editing these rebuilds only from here down) -----
COPY . .

# Default: reproduce all artifacts, then verify they exist.
CMD ["sh", "-c", "make all && make test-outputs"]
