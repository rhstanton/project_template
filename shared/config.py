"""
config.py
Centralized configuration for shared constants and study parameters.

This file defines study configurations for the unified run_analysis.py script.
Each study in the STUDIES dictionary specifies:
- Data source
- Plot parameters (xlabel, ylabel, title)
- Variables (xvar, yvar, groupby)
- Table aggregation function
- Output paths (figure, table)

Adding a new study:
    1. Add entry to STUDIES dict below
    2. Add study name to ANALYSES in Makefile
    3. Add pattern definition in Makefile (script, runner, inputs, outputs, args)
    4. Build with: make <study_name>

Example:
    from config import STUDIES, DATA_FILES
    study = STUDIES["price_base"]
    data_file = study["data"]
"""

from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════

# config.py is in shared/, so go up one level to get project root
REPO_ROOT = Path(__file__).resolve().parent.parent
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
# GLOBAL DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════
# Default values applied to all studies unless overridden.
# Priority: DEFAULTS (lowest) < STUDIES[study] (medium) < command-line args (highest)

DEFAULTS = {
    "data": DATA_FILES["housing"],  # Default data source
    "xlabel": "Year",  # Default x-axis label
    "ylabel": "Value",  # Default y-axis label
    "title": "Analysis",  # Default plot title
    "groupby": "region",  # Default grouping variable
    "xvar": "year",  # Default x-axis variable
    "table_agg": "mean",  # Default table aggregation function
}

# ═══════════════════════════════════════════════════════════════════════════
# STUDY CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Each study defines parameters for a single run of run_analysis.py.
# Only specify values that differ from DEFAULTS.
# This follows the pattern from fire/housing-analysis where a single executable
# handles multiple study configurations via command-line arguments.

STUDIES = {
    "price_base": {
        # Only specify what differs from DEFAULTS
        "ylabel": "Price index",  # Override default ylabel
        "title": "Price index over time",  # Override default title
        "yvar": "price_index",  # Study-specific outcome variable (required)
        "figure": OUTPUT_DIR / "figures" / "price_base.pdf",  # Output paths (required)
        "table": OUTPUT_DIR / "tables" / "price_base.tex",
        # Inherits: data, xlabel, groupby, xvar, table_agg from DEFAULTS
    },
    "remodel_base": {
        # Only specify what differs from DEFAULTS
        "ylabel": "Remodel rate",
        "title": "Remodeling activity over time",
        "yvar": "remodel_rate",  # Study-specific outcome variable (required)
        "figure": OUTPUT_DIR / "figures" / "remodel_base.pdf",
        "table": OUTPUT_DIR / "tables" / "remodel_base.tex",
        # Inherits: data, xlabel, groupby, xvar, table_agg from DEFAULTS
    },
}
