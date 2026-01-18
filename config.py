"""
config.py
Centralized configuration for all build artifacts.
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "output"
PAPER_DIR = REPO_ROOT / "paper"

# ═══════════════════════════════════════════════════════════════════════════
# DATA FILES
# ═══════════════════════════════════════════════════════════════════════════

DATA_FILES = {
    "housing": DATA_DIR / "housing_panel.csv",
}

# ═══════════════════════════════════════════════════════════════════════════
# ARTIFACT CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════

ARTIFACTS = {
    "price_base": {
        "script": "build_price_base.py",
        "inputs": [DATA_FILES["housing"]],
        "outputs": {
            "figure": OUTPUT_DIR / "figures" / "price_base.pdf",
            "table": OUTPUT_DIR / "tables" / "price_base.tex",
            "provenance": OUTPUT_DIR / "provenance" / "price_base.yml",
        },
    },
    "remodel_base": {
        "script": "build_remodel_base.py",
        "inputs": [DATA_FILES["housing"]],
        "outputs": {
            "figure": OUTPUT_DIR / "figures" / "remodel_base.pdf",
            "table": OUTPUT_DIR / "tables" / "remodel_base.tex",
            "provenance": OUTPUT_DIR / "provenance" / "remodel_base.yml",
        },
    },
}
