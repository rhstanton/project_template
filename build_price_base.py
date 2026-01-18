from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from scripts.provenance import write_build_record


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build price_base: one figure + one table + per-artifact provenance"
    )
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out-fig", type=Path, required=True)
    ap.add_argument("--out-table", type=Path, required=True)
    ap.add_argument("--out-meta", type=Path, required=True)
    args = ap.parse_args()

    args.out_fig.parent.mkdir(parents=True, exist_ok=True)
    args.out_table.parent.mkdir(parents=True, exist_ok=True)
    args.out_meta.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)

    # Table: mean price index by year
    tbl = (
        df.groupby("year", as_index=False)["price_index"]
        .mean()
        .rename(columns={"price_index": "mean_price_index"})
    )

    tex = tbl.to_latex(index=False, float_format="%.2f")
    args.out_table.write_text(tex, encoding="utf-8")

    # Figure: lines by region
    fig, ax = plt.subplots()
    for region, g in df.groupby("region"):
        g2 = g.sort_values("year")
        ax.plot(g2["year"], g2["price_index"], label=f"Region {region}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Price index")
    ax.set_title("Price index over time")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out_fig)
    plt.close(fig)

    repo_root = Path(__file__).resolve().parent
    write_build_record(
        out_meta=args.out_meta,
        artifact_name="price_base",
        command=["python", str(Path(__file__).name), "--data", str(args.data)],
        repo_root=repo_root,
        inputs=[args.data],
        outputs=[args.out_fig, args.out_table],
    )


if __name__ == "__main__":
    main()
