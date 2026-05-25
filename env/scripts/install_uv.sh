#!/usr/bin/env bash
# Install uv (Astral) if not already available.
# uv manages this project's Python environment (.venv) from pyproject.toml + uv.lock.
# Installs to ~/.local/bin (user-space, no admin required).
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  echo ">> uv already installed: $(uv --version)"
  exit 0
fi

echo ">> Installing uv (Astral)..."
# Pin the installer channel; the standalone installer drops uv in ~/.local/bin.
if command -v curl >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
elif command -v wget >/dev/null 2>&1; then
  wget -qO- https://astral.sh/uv/install.sh | sh
else
  echo "ERROR: need curl or wget to install uv." >&2
  echo "       See https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

# Make uv discoverable in this shell; callers should ensure ~/.local/bin is on PATH.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv installed but not on PATH. Add \$HOME/.local/bin to your PATH." >&2
  exit 1
fi
echo ">> uv installed: $(uv --version)"
