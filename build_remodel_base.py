from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from repro_tools import enable_auto_provenance

# Enable automatic provenance recording at script exit
enable_auto_provenance(__file__)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build remodel_base: one figure + one table + per-artifact provenance"
    )
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out-fig", type=Path, required=True)
    ap.add_argument("--out-table", type=Path, required=True)
    args = ap.parse_args()

    args.out_fig.parent.mkdir(parents=True, exist_ok=True)
    args.out_table.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)

    # Table: remodel rate summary by region
    tbl = (
        df.groupby("region", as_index=False)["remodel_rate"]
        .agg(["mean", "min", "max"])
        .reset_index()
    )
    # pandas creates multi-index cols for agg on series; flatten them
    tbl.columns = [
        "index",
        "region",
        "mean_remodel_rate",
        "min_remodel_rate",
        "max_remodel_rate",
    ]
    tbl = tbl.drop(columns=["index"])  # Remove the extra index column

    tex = tbl.to_latex(index=False, float_format="%.3f")
    args.out_table.write_text(tex, encoding="utf-8")

    # Figure: remodel rate by year (mean across regions)
    g = df.groupby("year", as_index=False)["remodel_rate"].mean().sort_values("year")
    fig, ax = plt.subplots()
    ax.plot(g["year"], g["remodel_rate"], marker="o")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean remodel rate")
    ax.set_title("Mean remodel rate over time")
    fig.tight_layout()
    fig.savefig(args.out_fig)
    plt.close(fig)


if __name__ == "__main__":
    main()
