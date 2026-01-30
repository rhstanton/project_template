#!/usr/bin/env python
"""Difference-in-Differences Analysis - Template Demonstration

A streamlined DiD analysis demonstrating Julia/Python backend interoperability.
Based on fire/housing-analysis/run_did.py but simplified for template use.

Features:
  - DiD event study regression
  - Backend selection: Julia (FixedEffectModels.jl) or Python (pyfixest)
  - Event study plot generation
  - Diagnostic output

Usage:
  run_did.py [options]
  run_did.py --help

Options:
  --data=<path>         Input CSV file [default: data/housing_panel.csv]
  --yvar=<name>         Outcome variable [default: outcome]
  --time-var=<name>     Event time variable [default: relative_year]
  --treat-var=<name>    Treatment indicator [default: treated]
  --id-var=<name>       Unit identifier [default: property_id]
  --ref-year=<int>      Reference period (omitted) [default: -1]
  --fe-spec=<spec>      Fixed effects spec [default: property_id & year]
  --cluster=<var>       Clustering variable [default: property_id]
  
  --use-julia=<0|1>     Use Julia backend [default: 1]
  --use-gpu=<0|1>       Enable GPU (Julia only) [default: 0]
  --pyfixest-backend=<name>  pyfixest backend (rust|cupy|jax) [default: rust]
  
  --figure=<path>       Output figure path [default: output/figures/did_example.pdf]
  --table=<path>        Output table path [default: output/tables/did_example.tex]
  --out-meta=<path>     Provenance file [default: output/provenance/did_example.yml]
  
  --help                Show this help
"""

import os
import sys
from pathlib import Path

# Set Julia configuration before any Julia-related imports
os.environ.setdefault("PYTHON_JULIACALL_HANDLE_SIGNALS", "yes")

# Get script directory and repo root
_script_dir = Path(__file__).resolve().parent

# Point juliapkg to use env/ directly
if "PYTHON_JULIAPKG_PROJECT" not in os.environ:
    os.environ["PYTHON_JULIAPKG_PROJECT"] = str(_script_dir / ".julia")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from repro_tools import auto_build_record, friendly_docopt, setup_environment


def run_julia_did(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Run DiD regression using Julia FixedEffectModels.jl"""
    try:
        from juliacall import Main as jl
    except ImportError as e:
        print(f"❌ Julia import failed: {e}")
        print("Falling back to pyfixest backend")
        return run_pyfixest_did(df, config)
    
    # Load Julia packages
    try:
        jl.seval("using FixedEffectModels, DataFrames")
        
        # Get version
        fem_version = str(jl.seval("string(pkgversion(FixedEffectModels))"))
        print(f"Using Julia FixedEffectModels v{fem_version}")
        
        # GPU check
        if config["use_gpu"] == 1:
            try:
                jl.seval("using CUDA")
                if jl.seval("CUDA.functional()"):
                    print("Using GPU acceleration")
                else:
                    print("GPU requested but unavailable; using CPU")
            except:
                print("GPU requested but CUDA unavailable; using CPU")
        else:
            print("Using CPU (set --use-gpu=1 to enable GPU acceleration)")
            
    except Exception as e:
        print(f"❌ Julia setup error: {e}")
        print("Falling back to pyfixest backend")
        return run_pyfixest_did(df, config)
    
    # Convert to Julia DataFrame
    jl_df = jl.DataFrame(df)
    
    # Build formula
    time_var = config["time_var"]
    treat_var = config["treat_var"]
    yvar = config["yvar"]
    fe_spec = config["fe_spec"]
    cluster = config["cluster"]
    ref_year = config["ref_year"]
    
    # Create interaction dummies manually (Julia approach)
    times = sorted(df[time_var].unique())
    times = [t for t in times if t != ref_year]  # Exclude reference
    
    # Create dummy columns
    for t in times:
        col_name = f"_time_{int(t) if t >= 0 else f'm{abs(int(t))}'}"
        df[col_name] = ((df[time_var] == t) & (df[treat_var] == 1)).astype(int)
    
    # Convert to Julia DataFrame after creating all dummies
    jl_df = jl.DataFrame(df)
    
    # Build formula
    interaction_terms = [f"_time_{int(t) if t >= 0 else f'm{abs(int(t))}'}" for t in times]
    # For FixedEffectModels.jl, we need separate fe() calls for each fixed effect
    fe_vars = [v.strip() for v in fe_spec.replace('&', '+').split('+')]
    fe_formula = ' + '.join([f'fe({v})' for v in fe_vars])
    formula_str = f"{yvar} ~ {' + '.join(interaction_terms)} + {fe_formula}"
    
    print(f"Regression formula = {formula_str}")
    
    # Run regression
    # reg() signature: reg(df, formula, vcov)
    result = jl.reg(jl_df, jl.seval(f"@formula({formula_str})"), 
                   jl.seval(f"Vcov.cluster(:{cluster})"))
    
    # Extract coefficients
    coef_df = pd.DataFrame({
        'relative_year': times,
        'estimate': [jl.coef(result)[i] for i in range(len(times))],
        'std_error': [jl.stderror(result)[i] for i in range(len(times))],
    })
    
    return coef_df


def run_pyfixest_did(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Run DiD regression using pyfixest"""
    try:
        import pyfixest as pf
    except ImportError as e:
        print(f"❌ pyfixest not installed: {e}")
        sys.exit(1)
    
    print(f"Using pyfixest v{pf.__version__}")
    print(f"Backend: {config['pyfixest_backend']}")
    
    # Build formula
    time_var = config["time_var"]
    treat_var = config["treat_var"]
    yvar = config["yvar"]
    fe_spec = config["fe_spec"]
    cluster = config["cluster"]
    ref_year = config["ref_year"]
    
    # pyfixest formula: i(time_var, treat_var, ref=ref_year)
    formula = f"{yvar} ~ i({time_var}, {treat_var}, ref={ref_year}) | {fe_spec}"
    
    print(f"Regression formula = {formula}")
    
    # Run regression
    result = pf.feols(formula, data=df, vcov={"CRV1": cluster})
    
    # Extract event study coefficients
    coef_names = result.coef().index
    event_coefs = [c for c in coef_names if time_var in c]
    
    coef_df = pd.DataFrame({
        'relative_year': [int(c.split('[T.')[1].split(']')[0]) 
                          for c in event_coefs],
        'estimate': [result.coef()[c] for c in event_coefs],
        'std_error': [result.se()[c] for c in event_coefs],
    })
    
    return coef_df.sort_values('relative_year')


def plot_event_study(coef_df: pd.DataFrame, config: dict) -> None:
    """Generate event study plot"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculate confidence intervals
    coef_df['ci_lower'] = coef_df['estimate'] - 1.96 * coef_df['std_error']
    coef_df['ci_upper'] = coef_df['estimate'] + 1.96 * coef_df['std_error']
    
    # Plot
    ax.plot(coef_df['relative_year'], coef_df['estimate'], 
            'o-', color='steelblue', linewidth=2, markersize=8)
    ax.fill_between(coef_df['relative_year'], 
                     coef_df['ci_lower'], coef_df['ci_upper'],
                     alpha=0.2, color='steelblue')
    
    # Reference lines
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    # Labels
    ax.set_xlabel('Event Time (years relative to treatment)', fontsize=12)
    ax.set_ylabel('Treatment Effect', fontsize=12)
    ax.set_title('Difference-in-Differences Event Study', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Save
    output_path = Path(config["figure"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    print(f"\n✓ Figure saved: {output_path}")


def save_table(coef_df: pd.DataFrame, config: dict) -> None:
    """Save regression table as LaTeX"""
    output_path = Path(config["table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format table
    table_df = coef_df.copy()
    table_df['conf_int'] = table_df.apply(
        lambda row: f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]", axis=1
    )
    
    latex_str = table_df[['relative_year', 'estimate', 'std_error', 'conf_int']].to_latex(
        index=False,
        float_format='%.3f',
        column_format='rccc',
        caption='DiD Event Study Coefficients',
        label='tab:did_results'
    )
    
    output_path.write_text(latex_str)
    print(f"✓ Table saved: {output_path}")


def main():
    """Main entry point"""
    args = friendly_docopt(__doc__, version='1.0.0')
    setup_environment()
    
    # Build configuration
    config = {
        "data": Path(args["--data"]),
        "yvar": args["--yvar"],
        "time_var": args["--time-var"],
        "treat_var": args["--treat-var"],
        "id_var": args["--id-var"],
        "ref_year": int(args["--ref-year"]),
        "fe_spec": args["--fe-spec"],
        "cluster": args["--cluster"],
        "use_julia": int(args["--use-julia"]),
        "use_gpu": int(args["--use-gpu"]),
        "pyfixest_backend": args["--pyfixest-backend"],
        "figure": Path(args["--figure"]),
        "table": Path(args["--table"]),
        "out_meta": Path(args["--out-meta"]),
    }
    
    print("\n" + "=" * 70)
    print("DIFFERENCE-IN-DIFFERENCES ANALYSIS")
    print("=" * 70)
    print(f"Data: {config['data']}")
    print(f"Outcome: {config['yvar']}")
    print(f"Backend: {'Julia (FixedEffectModels)' if config['use_julia'] else 'Python (pyfixest)'}")
    print("=" * 70 + "\n")
    
    # Load data
    df = pd.read_csv(config["data"])
    print(f"Loaded {len(df):,} observations\n")
    
    # Run regression
    if config["use_julia"] == 1:
        coef_df = run_julia_did(df, config)
    else:
        coef_df = run_pyfixest_did(df, config)
    
    # Generate outputs
    plot_event_study(coef_df, config)
    save_table(coef_df, config)
    
    # Write provenance
    auto_build_record(
        artifact_name="did_example",
        out_meta=config["out_meta"],
        inputs=[config["data"]],
        outputs=[config["figure"], config["table"]],
    )
    
    print("\n✓ Analysis complete!\n")


if __name__ == "__main__":
    main()
