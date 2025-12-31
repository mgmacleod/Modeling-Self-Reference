#!/usr/bin/env python3
"""Render a human-facing Markdown report + charts from analysis TSV artifacts.

Inputs (expected in data/wikipedia/processed/analysis/):
- branch_trunkiness_dashboard_n=5_*.tsv
- dominance_collapse_dashboard_n=5_*.tsv
- dominant_upstream_chain_n=5_from=*.tsv (optional; a few will be plotted if present)

Outputs (committed to repo):
- n-link-analysis/report/overview.md
- n-link-analysis/report/assets/*.png

Rationale: keep `data/**/analysis/**` gitignored, but publish lightweight, human-facing
summaries inside the repo.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report"
ASSETS_DIR = REPORT_DIR / "assets"


def _render_md_row(vals: list[str], cols: list[str], widths: dict[str, int]) -> str:
    return "| " + " | ".join(str(v).ljust(widths[c]) for v, c in zip(vals, cols)) + " |"


def _read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")


def _short_cycle(cycle_key: str, max_len: int = 48) -> str:
    s = str(cycle_key)
    if len(s) <= max_len:
        return s
    # Keep ends since many keys share prefixes.
    return s[: max_len - 3] + "..."


def _md_table(df: pd.DataFrame, *, max_rows: int = 20) -> str:
    """Render a simple markdown table without extra dependencies."""
    if df.empty:
        return "(no rows)"

    view = df.head(max_rows).copy()
    cols = list(view.columns)

    # Convert values to strings (avoid scientific notation surprises).
    for c in cols:
        view[c] = view[c].map(lambda x: "" if pd.isna(x) else str(x))

    widths = {c: max(len(c), *(len(v) for v in view[c].tolist())) for c in cols}

    header = _render_md_row([str(c) for c in cols], cols, widths)
    sep = "| " + " | ".join("-" * widths[c] for c in cols) + " |"

    body_lines: list[str] = []
    for _, r in view.iterrows():
        body_lines.append(_render_md_row([r[c] for c in cols], cols, widths))
    body = "\n".join(body_lines)

    return "\n".join([header, sep, body])


def _save_fig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_trunkiness(trunk_path: Path) -> list[Path]:
    df = _read_tsv(trunk_path)
    df = df.sort_values(["top1_share_total", "total_basin_nodes"], ascending=[False, False]).copy()

    labels = [_short_cycle(x) for x in df["cycle_key"].tolist()]
    y = df["top1_share_total"].astype(float).tolist()

    plt.figure(figsize=(10, 4.8))
    plt.bar(range(len(y)), y)
    plt.xticks(range(len(y)), labels, rotation=35, ha="right")
    plt.ylim(0.0, 1.0)
    plt.ylabel("Top-1 branch share (of total basin)")
    plt.title("N=5 trunkiness across basins")
    out1 = ASSETS_DIR / "trunkiness_top1_share.png"
    _save_fig(out1)

    plt.figure(figsize=(6.2, 4.8))
    plt.scatter(df["total_basin_nodes"].astype(float), df["top1_share_total"].astype(float))
    plt.xscale("log")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Total basin nodes (log)")
    plt.ylabel("Top-1 branch share")
    plt.title("Basin size vs trunkiness (N=5)")
    out2 = ASSETS_DIR / "trunkiness_scatter_size_vs_top1.png"
    _save_fig(out2)

    return [out1, out2]


def plot_collapse(collapse_path: Path) -> list[Path]:
    df = _read_tsv(collapse_path)

    # Normalize hop column (empty -> NaN)
    hop_col = "first_below_threshold_hop"
    if hop_col in df.columns:
        df[hop_col] = pd.to_numeric(df[hop_col], errors="coerce")
    else:
        df[hop_col] = float("nan")

    df = df.sort_values([hop_col, "min_share"], ascending=[True, True]).copy()

    labels = [_short_cycle(x) for x in df["seed_title"].tolist()]
    hops = df[hop_col].tolist()

    plt.figure(figsize=(10, 4.8))
    plt.bar(range(len(hops)), [(-1 if pd.isna(h) else float(h)) for h in hops])
    plt.xticks(range(len(hops)), labels, rotation=35, ha="right")
    plt.ylabel("First hop where share < threshold (or -1 if none)")
    plt.title("Dominance collapse point (N=5, threshold run)")
    out = ASSETS_DIR / "dominance_collapse_first_below_hop.png"
    _save_fig(out)

    return [out]


def plot_chase_series(chain_path: Path) -> list[Path]:
    df = _read_tsv(chain_path)

    share_col = "dominant_share_of_upstream"
    basin_col = "basin_total_including_seed"
    if share_col not in df.columns or basin_col not in df.columns:
        return []

    title = chain_path.stem.replace("dominant_upstream_chain_", "").replace("_", " ")

    plt.figure(figsize=(7.2, 4.6))
    plt.plot(df["hop"], df[share_col].astype(float), marker="o", linewidth=1)
    plt.ylim(0.0, 1.0)
    plt.xlabel("Hop")
    plt.ylabel("Dominant share")
    plt.title(f"Dominant share vs hop\n{title}")
    out1 = ASSETS_DIR / f"chase_{chain_path.stem}_share.png"
    _save_fig(out1)

    plt.figure(figsize=(7.2, 4.6))
    plt.plot(df["hop"], df[basin_col].astype(float), marker="o", linewidth=1)
    plt.yscale("log")
    plt.xlabel("Hop")
    plt.ylabel("Basin size (log)")
    plt.title(f"Basin size vs hop\n{title}")
    out2 = ASSETS_DIR / f"chase_{chain_path.stem}_basin.png"
    _save_fig(out2)

    return [out1, out2]


def plot_chase_overlay_share(chain_paths: list[Path]) -> Path | None:
    """Overlay dominant share vs hop for multiple chase outputs."""
    if not chain_paths:
        return None

    share_col = "dominant_share_of_upstream"

    plt.figure(figsize=(7.6, 4.8))
    plotted = 0
    for p in chain_paths:
        df = _read_tsv(p)
        if share_col not in df.columns or "hop" not in df.columns:
            continue
        # Legend label: prefer the first seed title.
        label = None
        if "seed_title" in df.columns and not df.empty:
            label = str(df.iloc[0]["seed_title"])
        if not label:
            label = p.stem.replace("dominant_upstream_chain_n=", "")

        plt.plot(
            df["hop"].astype(int),
            df[share_col].astype(float),
            marker="o",
            linewidth=1,
            markersize=3,
            label=label,
        )
        plotted += 1

    if plotted == 0:
        plt.close()
        return None

    plt.ylim(0.0, 1.0)
    plt.xlabel("Hop")
    plt.ylabel("Dominant share")
    plt.title("Dominant share vs hop (overlay)")
    plt.legend(loc="best", fontsize=8)

    out = ASSETS_DIR / "chase_overlay_dominant_share.png"
    _save_fig(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag",
        default="bootstrap_2025-12-30",
        help="Which dashboard tag to prefer when multiple exist.",
    )
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    trunk_candidates = sorted(ANALYSIS_DIR.glob(f"branch_trunkiness_dashboard_n=5_{args.tag}.tsv"))
    if not trunk_candidates:
        trunk_candidates = sorted(ANALYSIS_DIR.glob("branch_trunkiness_dashboard_n=5_*.tsv"))
    if not trunk_candidates:
        raise SystemExit(f"Missing trunkiness dashboard TSV in: {ANALYSIS_DIR}")
    trunk_path = trunk_candidates[-1]

    collapse_candidates = sorted(ANALYSIS_DIR.glob(f"dominance_collapse_dashboard_n=5_*{args.tag}*.tsv"))
    if not collapse_candidates:
        collapse_candidates = sorted(ANALYSIS_DIR.glob("dominance_collapse_dashboard_n=5_*.tsv"))
    collapse_path = collapse_candidates[-1] if collapse_candidates else None

    trunk_figs = plot_trunkiness(trunk_path)
    collapse_figs = plot_collapse(collapse_path) if collapse_path else []

    # Prefer a few known chains if present.
    preferred_chain_names = [
        "dominant_upstream_chain_n=5_from=Massachusetts_bootstrap_2025-12-30.tsv",
        "dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30.tsv",
        "dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30.tsv",
    ]
    chain_paths: list[Path] = []
    for name in preferred_chain_names:
        p = ANALYSIS_DIR / name
        if p.exists():
            chain_paths.append(p)

    # If none of the preferred are present, plot up to 3 arbitrary chains.
    if not chain_paths:
        chain_paths = sorted(ANALYSIS_DIR.glob("dominant_upstream_chain_n=5_from=*.tsv"))[:3]

    chase_figs: list[Path] = []
    for p in chain_paths:
        chase_figs.extend(plot_chase_series(p))

    overlay_share = plot_chase_overlay_share(chain_paths)

    # Build a compact table preview.
    trunk_df = _read_tsv(trunk_path)
    trunk_preview = trunk_df[[
        "cycle_key",
        "total_basin_nodes",
        "top1_share_total",
        "effective_branches",
        "dominant_entry_title",
        "dominant_enters_cycle_title",
    ]].copy()
    trunk_preview["top1_share_total"] = trunk_preview["top1_share_total"].map(lambda x: f"{float(x):.4f}")
    trunk_preview["effective_branches"] = trunk_preview["effective_branches"].map(lambda x: f"{float(x):.3f}")
    trunk_preview = trunk_preview.sort_values(["top1_share_total", "total_basin_nodes"], ascending=[False, False])

    collapse_section = ""
    if collapse_path:
        collapse_df = _read_tsv(collapse_path)
        # Keep it small and human readable.
        cols = ["seed_title", "first_below_threshold_hop", "min_share", "stop_reason", "stop_at_title"]
        cols = [c for c in cols if c in collapse_df.columns]
        view = collapse_df[cols].copy()
        if "min_share" in view.columns:
            view["min_share"] = pd.to_numeric(view["min_share"], errors="coerce").map(
                lambda x: "" if pd.isna(x) else f"{float(x):.3f}"
            )
        collapse_section = textwrap.dedent(
            f"""
            ## Dominance Collapse (Threshold Run)

            Collapse dashboard input:
            - `{collapse_path.relative_to(REPO_ROOT).as_posix()}`

            Preview (sorted by min share):

            {_md_table(view.sort_values(['min_share'], ascending=[True]), max_rows=20)}
            """
        ).strip()

    # Write report.
    report_path = REPORT_DIR / "overview.md"
    md = textwrap.dedent(
        f"""
        # N=5 Basin Structure — Human-Facing Summary (So Far)

        **Date**: 2025-12-30  
        **Scope**: Wikipedia fixed-$N$ rule with $N=5$ (the induced functional graph $f_5$).  
        **Goal**: Summarize what we’ve empirically learned about basin sizes, branch (“watershed”) structure, and dominant-upstream trunks.

        This report is generated from gitignored analysis artifacts under `data/wikipedia/processed/analysis/`.

        ## Key Takeaways

        - Basin sizes vary substantially in a small sample; a “giant basin” candidate exists (`Massachusetts ↔ Gulf_of_Maine`).
        - Many basins are highly *single-trunk* at depth 1: one predecessor subtree captures most upstream mass.
        - “Non-trunky” at hop 0 does not imply “non-trunky” upstream: dominant-upstream chase can quickly enter high-dominance regimes.
        - Dominance can later *collapse* (shares plunge) as the chase enters diffuse / long-tail regions.

        ## Trunkiness Dashboard

        Dashboard input:
        - `{trunk_path.relative_to(REPO_ROOT).as_posix()}`

        **Charts**:
        - ![Top-1 share](assets/{trunk_figs[0].name})
        - ![Size vs share](assets/{trunk_figs[1].name})

        **Preview table**:

        {_md_table(trunk_preview, max_rows=20)}

        {collapse_section}

        ## Example Chases (Dominant Share vs Hop)

        These are pulled from any available `dominant_upstream_chain_n=5_from=*.tsv` artifacts.

        {"\n".join([f"- {p.name}" for p in chain_paths])}

        **Charts** (share + basin size per chase):

        {"\n".join([f"- ![chart](assets/{p.name})" for p in chase_figs])}

        **Overlay comparison**:

        {(f"- ![overlay](assets/{overlay_share.name})" if overlay_share else "(overlay not available)")}

        ## How to Regenerate

        From repo root:
        - `python n-link-analysis/scripts/render-human-report.py --tag {args.tag}`

        This rewrites:
        - `n-link-analysis/report/overview.md`
        - `n-link-analysis/report/assets/*.png`
        """
    ).strip() + "\n"

    report_path.write_text(md, encoding="utf-8")
    print(f"Wrote report: {report_path}")
    print(f"Wrote assets: {ASSETS_DIR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
