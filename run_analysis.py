#!/usr/bin/env python
"""run_analysis.py - Unified analysis script for generating figures and tables.

This script handles multiple studies via configuration.
Study parameters are defined in config.py in the STUDIES dictionary.

Defaults are resolved in this priority order:
  1. Docopt defaults (lowest priority, shown below)
  2. config.DEFAULTS (medium priority, global defaults)
  3. config.STUDIES[study] (higher priority, study-specific config)
  4. Command-line arguments (highest priority, overrides all)

Usage:
  run_analysis.py <study> [options]
  run_analysis.py --list
  run_analysis.py -h | --help
  run_analysis.py --version

Arguments:
  <study>             Study name from config.STUDIES (e.g., price_base, remodel_base)

Options:
  --list              List all available studies and exit
  -h --help           Show this help message
  --version           Show version information
  
  Study overrides:
    --data=<path>      Override input data file
    --yvar=<name>      Override outcome variable
    --xvar=<name>      Override x-axis variable
    --groupby=<name>   Override grouping variable
    --xlabel=<text>    Override x-axis label
    --ylabel=<text>    Override y-axis label
    --title=<text>     Override plot title
    --table-agg=<fn>   Override table aggregation (mean|sum|median|count|std|min|max) [default: mean]
    --figure=<path>    Override figure output path
    --table=<path>     Override table output path

"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from repro_tools import (
    auto_build_record,
    friendly_docopt,
    print_config,
    print_validation_errors,
    setup_environment,
)

from shared import config
from shared.config_validator import validate_config


def list_studies() -> None:
    """Print available studies and exit."""
    print("\nAvailable studies:")
    for study_name in config.STUDIES:
        print(f"  - {study_name}")
    print()
    sys.exit(0)


def build_config(study_name: str, args: dict) -> dict:
    """
    Build configuration with 3-level priority:
      1. config.DEFAULTS (lowest)
      2. config.STUDIES[study_name] (medium)
      3. Command-line args (highest)
    """
    # Start with global defaults
    cfg = config.DEFAULTS.copy()
    
    # Override with study-specific config
    if study_name in config.STUDIES:
        cfg.update(config.STUDIES[study_name])
    
    # Override with command-line arguments (if provided)
    # Convert docopt arg names to config keys
    override_map = {
        "--data": "data",
        "--yvar": "yvar",
        "--xvar": "xvar",
        "--groupby": "groupby",
        "--xlabel": "xlabel",
        "--ylabel": "ylabel",
        "--title": "title",
        "--table-agg": "table_agg",
        "--figure": "figure",
        "--table": "table",
    }
    
    for arg_name, cfg_key in override_map.items():
        if args.get(arg_name):
            cfg[cfg_key] = args[arg_name]
    
    return cfg


def main() -> None:
    # Setup environment (detects Jupyter, IPython, terminal, etc.)
    setup_environment()
    
    # Parse arguments with enhanced error messages
    args = friendly_docopt(__doc__, version="run_analysis 1.0")
    
    if args["--list"]:
        list_studies()
    
    study_name = args["<study>"]
    
    # Check study exists
    if study_name not in config.STUDIES:
        print(f"\n❌ Error: Unknown study '{study_name}'")
        print("\nAvailable studies:")
        for name in config.STUDIES.keys():
            print(f"  - {name}")
        print("\nRun with --list to see all available studies\n")
        sys.exit(1)
    
    # Build final configuration (3-level merge: DEFAULTS → STUDIES → args)
    study = build_config(study_name, args)
    
    # Validate configuration before proceeding
    validation_errors = validate_config(study, study_name)
    if validation_errors:
        print_validation_errors(validation_errors)
        sys.exit(1)
    
    # Print configuration for transparency
    print_config(
        {
            "Study": study_name,
            "Data": study["data"],
            "Y Variable": study["yvar"],
            "X Variable": study["xvar"],
            "Group By": study.get("groupby", "None"),
            "Figure Output": study["figure"],
            "Table Output": study["table"],
        },
        title=f"RUNNING STUDY: {study_name.upper()}",
    )
    
    # Extract paths from study config
    data_file = Path(study["data"])
    out_fig = Path(study["figure"])
    out_table = Path(study["table"])
    
    # Create output directories
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    out_table.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(data_file)
    
    # Extract parameters from study config
    xvar = study["xvar"]
    yvar = study["yvar"]
    groupby = study["groupby"]
    xlabel = study["xlabel"]
    ylabel = study["ylabel"]
    title = study["title"]
    table_agg = study["table_agg"]
    
    # Generate table: aggregate yvar by xvar
    tbl = (
        df.groupby(xvar, as_index=False)[yvar]
        .agg(table_agg)
        .rename(columns={yvar: f"{table_agg}_{yvar}"})
    )
    
    tex = tbl.to_latex(index=False, float_format="%.2f")
    out_table.write_text(tex, encoding="utf-8")
    
    # Generate figure: lines by group
    fig, ax = plt.subplots()
    for group_val, g in df.groupby(groupby):
        g2 = g.sort_values(xvar)
        ax.plot(g2[xvar], g2[yvar], label=f"{groupby.capitalize()} {group_val}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_fig)
    plt.close(fig)
    
    # Auto-generate provenance
    prov_file = out_fig.parent.parent / "provenance" / f"{study_name}.yml"
    prov_file.parent.mkdir(parents=True, exist_ok=True)
    auto_build_record(
        artifact_name=study_name,  # Explicitly set artifact name
        out_meta=prov_file,
        inputs=[data_file],
        outputs=[out_fig, out_table],
    )
    
    print(f"✓ {study_name} complete")


if __name__ == "__main__":
    main()
