#!/usr/bin/env bash
# Check prerequisites BEFORE running 'make environment'
# This script can run without any Python/Julia environment installed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=============================================="
echo "Checking prerequisites for environment setup"
echo "=============================================="
echo ""

EXIT_CODE=0

# ---------- Check GNU Make version ----------
echo "Checking GNU Make version..."
if ! command -v make &> /dev/null; then
    echo "❌ ERROR: make not found"
    echo "   Install: apt install make (Linux) or brew install make (macOS)"
    EXIT_CODE=1
else
    MAKE_VERSION=$(make --version | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    MAKE_MAJOR=$(echo "$MAKE_VERSION" | cut -d. -f1)
    MAKE_MINOR=$(echo "$MAKE_VERSION" | cut -d. -f2)
    
    if [ "$MAKE_MAJOR" -lt 4 ] || ([ "$MAKE_MAJOR" -eq 4 ] && [ "$MAKE_MINOR" -lt 3 ]); then
        echo "❌ ERROR: GNU Make $MAKE_VERSION is too old (need 4.3+)"
        echo "   Current: $MAKE_VERSION"
        echo "   macOS: brew install make; use 'gmake' instead"
        EXIT_CODE=1
    else
        echo "✓ GNU Make $MAKE_VERSION (OK)"
    fi
fi
echo ""

# ---------- Check git ----------
echo "Checking git..."
if ! command -v git &> /dev/null; then
    echo "❌ ERROR: git not found"
    echo "   Install: apt install git (Linux) or xcode-select --install (macOS)"
    EXIT_CODE=1
else
    GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    echo "✓ git $GIT_VERSION (OK)"
fi
echo ""

# ---------- Check disk space ----------
echo "Checking disk space..."
AVAILABLE_GB=$(df -BG "$REPO_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -lt 10 ]; then
    echo "⚠️  WARNING: Only ${AVAILABLE_GB}GB free (recommend 10GB+)"
    echo "   Environment needs ~5GB, builds need more"
else
    echo "✓ ${AVAILABLE_GB}GB available (OK)"
fi
echo ""

# ---------- Check for existing installations ----------
echo "Checking for conflicting installations..."

# Check for global Julia
if command -v julia &> /dev/null; then
    JULIA_PATH=$(which julia)
    echo "⚠️  WARNING: Global Julia found at $JULIA_PATH"
    echo "   This won't conflict (we use bundled Julia) but may be confusing"
fi

# Check for conda/mamba/micromamba
CONDA_FOUND=0
if command -v conda &> /dev/null; then
    echo "✓ conda found (will be used)"
    CONDA_FOUND=1
elif command -v mamba &> /dev/null; then
    echo "✓ mamba found (will be used)"
    CONDA_FOUND=1
elif command -v micromamba &> /dev/null; then
    echo "✓ micromamba found (will be used)"
    CONDA_FOUND=1
else
    echo "ℹ️  No conda/mamba/micromamba found (will auto-install micromamba)"
fi
echo ""

# ---------- Check for stale installation artifacts ----------
echo "Checking for stale installation artifacts..."

STALE_FOUND=0

if [ -d "$REPO_ROOT/.env" ]; then
    echo "ℹ️  Found existing Python environment at .env/"
fi

if [ -d "$REPO_ROOT/.julia" ]; then
    echo "ℹ️  Found existing Julia installation at .julia/"
    
    # Check for stale compiled cache (common issue)
    if [ -d "$REPO_ROOT/.julia/compiled" ]; then
        echo "   - Found .julia/compiled/ (may need cleanup if errors occur)"
    fi
    
    # Note: .julia/Project.toml and .julia/Manifest.toml are NORMAL
    # They are created by juliacall for the shared Julia environment
    # The user's project is in env/Project.toml (separate)
fi

if [ "$STALE_FOUND" -eq 0 ]; then
    echo "✓ No problematic artifacts found"
fi
echo ""

# ---------- Check env/Project.toml for PythonCall bug ----------
echo "Checking env/Project.toml for common errors..."

if [ -f "$REPO_ROOT/env/Project.toml" ]; then
    # Check if PythonCall is listed as a dependency (not just in comments)
    if grep -E '^PythonCall\s*=' "$REPO_ROOT/env/Project.toml" > /dev/null 2>&1; then
        echo "❌ CRITICAL ERROR: PythonCall found as dependency in env/Project.toml!"
        echo "   This is the #1 cause of installation failures"
        echo "   PythonCall is managed by juliacall and should ONLY be in .julia/pyjuliapkg/"
        echo "   Remove it from env/Project.toml [deps] section"
        EXIT_CODE=1
    else
        echo "✓ env/Project.toml looks good (no PythonCall dependency)"
    fi
    
    # Check for other common mistakes
    if grep -E '^\[name\]|^name\s*=' "$REPO_ROOT/env/Project.toml" > /dev/null 2>&1; then
        echo "❌ ERROR: env/Project.toml has 'name' field"
        echo "   This is an environment, not a package - should not have name/uuid/version"
        EXIT_CODE=1
    fi
    
    # Check Julia version compat
    if ! grep -q '\[compat\]' "$REPO_ROOT/env/Project.toml"; then
        echo "⚠️  WARNING: No [compat] section in env/Project.toml"
        echo "   Consider adding version constraints for reproducibility"
    fi
else
    echo "⚠️  WARNING: env/Project.toml not found"
fi
echo ""

# ---------- Check for problematic environment variables ----------
echo "Checking for problematic environment variables..."

ENV_ISSUES=0

# Check JULIA_PROJECT (should not be set globally)
if [ -n "$JULIA_PROJECT" ]; then
    echo "⚠️  WARNING: JULIA_PROJECT is set globally: $JULIA_PROJECT"
    echo "   This may interfere with juliacall. Unset it or use env/scripts/runpython"
    ENV_ISSUES=1
fi

# Check JULIA_CONDAPKG_BACKEND
if [ -n "$JULIA_CONDAPKG_BACKEND" ] && [ "$JULIA_CONDAPKG_BACKEND" != "Null" ]; then
    echo "⚠️  WARNING: JULIA_CONDAPKG_BACKEND=$JULIA_CONDAPKG_BACKEND"
    echo "   Should be 'Null' to avoid duplicate Python installations"
    echo "   The env/scripts/runpython wrapper sets this automatically"
    ENV_ISSUES=1
fi

# Check PYTHON_JULIAPKG_PROJECT
if [ -n "$PYTHON_JULIAPKG_PROJECT" ] && [ "$PYTHON_JULIAPKG_PROJECT" != "$REPO_ROOT/.julia" ]; then
    echo "⚠️  WARNING: PYTHON_JULIAPKG_PROJECT=$PYTHON_JULIAPKG_PROJECT"
    echo "   Expected: $REPO_ROOT/.julia"
    echo "   The env/scripts/runpython wrapper sets this automatically"
    ENV_ISSUES=1
fi

if [ "$ENV_ISSUES" -eq 0 ]; then
    echo "✓ No problematic environment variables found"
    echo "  (Run scripts via env/scripts/runpython to ensure correct config)"
fi
echo ""

# ---------- Check Python environment for juliacall ----------
if [ -d "$REPO_ROOT/.env" ]; then
    echo "Checking Python environment for Julia integration..."
    
    # Check if juliacall is installed
    if [ -f "$REPO_ROOT/.env/bin/python" ]; then
        JULIACALL_VERSION=$("$REPO_ROOT/.env/bin/python" -c "import juliacall; print(juliacall.__version__)" 2>/dev/null || echo "NOT_INSTALLED")
        
        if [ "$JULIACALL_VERSION" = "NOT_INSTALLED" ]; then
            echo "⚠️  WARNING: juliacall not installed in Python environment"
            echo "   Run: make environment"
        else
            echo "✓ juliacall $JULIACALL_VERSION installed"
        fi
    fi
    echo ""
fi

# ---------- Check for CUDA if requested ----------
if [ -n "$JULIA_ENABLE_CUDA" ] && [ "$JULIA_ENABLE_CUDA" = "1" ]; then
    echo "Checking CUDA availability (JULIA_ENABLE_CUDA=1 detected)..."
    
    if command -v nvidia-smi &> /dev/null; then
        echo "✓ NVIDIA driver found (nvidia-smi available)"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1 | sed 's/^/  GPU: /'
    else
        echo "⚠️  WARNING: JULIA_ENABLE_CUDA=1 but nvidia-smi not found"
        echo "   GPU support will not work without NVIDIA drivers"
    fi
    
    if [ -d "/usr/local/cuda" ]; then
        CUDA_VERSION=$(cat /usr/local/cuda/version.txt 2>/dev/null || echo "unknown")
        echo "  CUDA: $CUDA_VERSION"
    else
        echo "⚠️  WARNING: /usr/local/cuda not found"
        echo "   CUDA toolkit may not be installed"
    fi
    echo ""
fi

# ---------- Summary ----------
echo "=============================================="
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✓ All prerequisite checks passed!"
    echo ""
    echo "Ready to run: make environment"
else
    echo "❌ Some checks failed - fix errors above first"
fi
echo "=============================================="

exit $EXIT_CODE
