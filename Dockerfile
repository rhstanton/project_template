# syntax=docker/dockerfile:1
#
# Digest-pinned replication image: builds the full Python (uv) + Julia environment
# and reproduces every figure, table, and provenance record.
#
#   docker build -t project-template-repro .
#   docker run --rm -v "$PWD/output:/project/output" project-template-repro
#
# Notes:
#   * Stata is omitted (commercial license); no shipped artifact requires it.
#   * On Debian (its Python links OpenSSL 3.0), juliapkg installs Julia 1.11
#     automatically — the OpenSSL-compatible Julia for this interpreter.
#   * For a reviewer-standard linux/amd64 image on Apple Silicon:
#       docker build --platform linux/amd64 -t project-template-repro .
#     (emulated, slower; native arm64 builds are faster).
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
COPY . .

# Build the environment once at image-build time (uv sync from the lockfile + Julia
# via juliacall + precompile) so reproduction at run time is fast and offline.
# UV_FROZEN=1 makes `uv sync` use the committed uv.lock exactly.
RUN make environment

# Default: reproduce all artifacts, then verify they exist.
CMD ["sh", "-c", "make all && make test-outputs"]
