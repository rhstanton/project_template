"""
config.py
Centralized configuration for all analyses.

Think of each entry as an "analysis" or "run" that produces multiple artifacts.
For example, "price_base" is an analysis that generates:
  - A figure (price_base.pdf)
  - A table (price_base.tex)  
  - Provenance metadata (price_base.yml)
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
# ANALYSIS CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Each analysis is a "run" that generates multiple output artifacts.
# Don't think of these as single artifacts - they're analytical workflows.

ANALYSES = {
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
