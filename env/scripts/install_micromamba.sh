#!/usr/bin/env bash
# Auto-install micromamba if conda/mamba/micromamba not found
# This ensures the environment can be set up on any Linux/macOS machine

set -euo pipefail

echo "=========================================================================="
echo "Checking for conda/mamba/micromamba..."
echo "=========================================================================="
echo ""

# Check if any conda-like tool is available
if command -v conda &>/dev/null; then
    echo "✓ Found conda: $(command -v conda)"
    exit 0
elif command -v mamba &>/dev/null; then
    echo "✓ Found mamba: $(command -v mamba)"
    exit 0
elif command -v micromamba &>/dev/null; then
    echo "✓ Found micromamba: $(command -v micromamba)"
    exit 0
fi

echo "No conda/mamba/micromamba found."
echo ""
echo "Installing micromamba (lightweight conda alternative)..."
echo "  - ~15 MB download"
echo "  - Installs to: ~/.local/bin/micromamba"
echo "  - No admin privileges required"
echo ""

# Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

# Set download URL
case "${OS}-${ARCH}" in
    Linux-x86_64)
        URL="https://micro.mamba.pm/api/micromamba/linux-64/latest"
        ;;
    Linux-aarch64)
        URL="https://micro.mamba.pm/api/micromamba/linux-aarch64/latest"
        ;;
    Darwin-x86_64)
        URL="https://micro.mamba.pm/api/micromamba/osx-64/latest"
        ;;
    Darwin-arm64)
        URL="https://micro.mamba.pm/api/micromamba/osx-arm64/latest"
        ;;
    *)
        echo "❌ Unsupported platform: ${OS}-${ARCH}"
        echo ""
        echo "Please install conda manually:"
        echo "  https://docs.conda.io/en/latest/miniconda.html"
        exit 1
        ;;
esac

# Create installation directory
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "${INSTALL_DIR}"

# Download and install
echo "Downloading from ${URL}..."
TEMP_FILE=$(mktemp)
if command -v curl &>/dev/null; then
    curl -L "${URL}" -o "${TEMP_FILE}"
elif command -v wget &>/dev/null; then
    wget "${URL}" -O "${TEMP_FILE}"
else
    echo "❌ Neither curl nor wget found. Cannot download micromamba."
    exit 1
fi

# Extract and install
tar -xj -C "${INSTALL_DIR}" -f "${TEMP_FILE}" bin/micromamba
rm "${TEMP_FILE}"

# Make executable (micromamba is now at ${INSTALL_DIR}/bin/micromamba)
# Move it to ${INSTALL_DIR}/micromamba for consistency
mv "${INSTALL_DIR}/bin/micromamba" "${INSTALL_DIR}/micromamba"
rmdir "${INSTALL_DIR}/bin" 2>/dev/null || true
chmod +x "${INSTALL_DIR}/micromamba"

echo ""
echo "✓ micromamba installed to: ${INSTALL_DIR}/micromamba"
echo ""
echo "Adding to PATH..."

# Add to PATH if not already there
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    export PATH="${INSTALL_DIR}:${PATH}"
    
    # Add to shell rc files
    for RC in ~/.bashrc ~/.zshrc ~/.profile; do
        if [[ -f "$RC" ]]; then
            if ! grep -q "export PATH=\"${INSTALL_DIR}:\$PATH\"" "$RC"; then
                echo "" >> "$RC"
                echo "# Added by project_template environment setup" >> "$RC"
                echo "export PATH=\"${INSTALL_DIR}:\$PATH\"" >> "$RC"
                echo "  ✓ Added to $RC"
            fi
        fi
    done
fi

echo ""
echo "=========================================================================="
echo "micromamba installation complete!"
echo "=========================================================================="
echo ""
echo "To use immediately in this shell:"
echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
echo ""
echo "For new shells, it's already added to your rc files."
echo ""
echo "Continuing with environment setup..."
echo ""
