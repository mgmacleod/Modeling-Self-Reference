"""Report generation engine for N-Link analysis.

This module provides the core logic for generating human-facing Markdown
reports and PNG charts from analysis TSV artifacts.

Extracted from render-human-report.py for reuse in API layer.
"""

from __future__ import annotations

import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd


ProgressCallback = Callable[[float, str], None] | None


@dataclass
class FigureInfo:
    """Information about a generated figure."""

    name: str
    path: str
    description: str


@dataclass
class ReportResult:
    """Result of report generation."""

    tag: str
    report_path: str
    assets_dir: str
    figures: list[FigureInfo]
    trunk_data_path: str | None = None
    collapse_data_path: str | None = None
    chain_data_paths: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0


def _render_md_row(vals: list[str], cols: list[str], widths: dict[str, int]) -> str:
    """Render a markdown table row."""
    return "| " + " | ".join(str(v).ljust(widths[c]) for v, c in zip(vals, cols)) + " |"


def _read_tsv(path: Path) -> pd.DataFrame:
    """Read a TSV file into a DataFrame."""
    return pd.read_csv(path, sep="\t")


def _short_cycle(cycle_key: str, max_len: int = 48) -> str:
    """Truncate a cycle key for display."""
    s = str(cycle_key)
    if len(s) <= max_len:
        return s
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
    """Save current figure to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _plot_trunkiness(trunk_path: Path, assets_dir: Path) -> list[FigureInfo]:
    """Generate trunkiness bar chart and scatter plot."""
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
    out1 = assets_dir / "trunkiness_top1_share.png"
    _save_fig(out1)

    plt.figure(figsize=(6.2, 4.8))
    plt.scatter(df["total_basin_nodes"].astype(float), df["top1_share_total"].astype(float))
    plt.xscale("log")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Total basin nodes (log)")
    plt.ylabel("Top-1 branch share")
    plt.title("Basin size vs trunkiness (N=5)")
    out2 = assets_dir / "trunkiness_scatter_size_vs_top1.png"
    _save_fig(out2)

    return [
        FigureInfo(
            name=out1.name,
            path=str(out1),
            description="Top-1 branch share bar chart",
        ),
        FigureInfo(
            name=out2.name,
            path=str(out2),
            description="Basin size vs trunkiness scatter plot",
        ),
    ]


def _plot_collapse(collapse_path: Path, assets_dir: Path) -> list[FigureInfo]:
    """Generate dominance collapse chart."""
    df = _read_tsv(collapse_path)

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
    out = assets_dir / "dominance_collapse_first_below_hop.png"
    _save_fig(out)

    return [
        FigureInfo(
            name=out.name,
            path=str(out),
            description="Dominance collapse first-below-threshold hop",
        ),
    ]


def _plot_chase_series(chain_path: Path, assets_dir: Path) -> list[FigureInfo]:
    """Generate chase series charts for a single chain."""
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
    out1 = assets_dir / f"chase_{chain_path.stem}_share.png"
    _save_fig(out1)

    plt.figure(figsize=(7.2, 4.6))
    plt.plot(df["hop"], df[basin_col].astype(float), marker="o", linewidth=1)
    plt.yscale("log")
    plt.xlabel("Hop")
    plt.ylabel("Basin size (log)")
    plt.title(f"Basin size vs hop\n{title}")
    out2 = assets_dir / f"chase_{chain_path.stem}_basin.png"
    _save_fig(out2)

    return [
        FigureInfo(
            name=out1.name,
            path=str(out1),
            description=f"Dominant share vs hop for {chain_path.stem}",
        ),
        FigureInfo(
            name=out2.name,
            path=str(out2),
            description=f"Basin size vs hop for {chain_path.stem}",
        ),
    ]


def _plot_chase_overlay(chain_paths: list[Path], assets_dir: Path) -> FigureInfo | None:
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

    out = assets_dir / "chase_overlay_dominant_share.png"
    _save_fig(out)
    return FigureInfo(
        name=out.name,
        path=str(out),
        description="Overlay of dominant share vs hop across basins",
    )


def generate_report(
    analysis_dir: Path,
    report_dir: Path,
    tag: str,
    *,
    repo_root: Path | None = None,
    progress_callback: ProgressCallback = None,
    verbose: bool = True,
) -> ReportResult:
    """Generate a human-facing Markdown report with charts.

    Args:
        analysis_dir: Directory containing analysis TSV artifacts.
        report_dir: Directory to write report and assets.
        tag: Tag to match for dashboard files.
        repo_root: Repository root for relative paths in report.
        progress_callback: Optional callback for progress updates.
        verbose: Whether to print progress.

    Returns:
        ReportResult with paths to generated files.
    """
    t0 = time.time()
    analysis_dir = Path(analysis_dir)
    report_dir = Path(report_dir)
    assets_dir = report_dir / "assets"

    report_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    if repo_root is None:
        # Try to infer repo root from common patterns
        repo_root = analysis_dir.parents[2]  # data/wikipedia/processed/analysis -> repo

    if progress_callback:
        progress_callback(0.1, "Finding data files")

    # Find trunkiness dashboard
    trunk_candidates = sorted(analysis_dir.glob(f"branch_trunkiness_dashboard_n=5_{tag}.tsv"))
    if not trunk_candidates:
        trunk_candidates = sorted(analysis_dir.glob("branch_trunkiness_dashboard_n=5_*.tsv"))
    if not trunk_candidates:
        raise FileNotFoundError(f"Missing trunkiness dashboard TSV in: {analysis_dir}")
    trunk_path = trunk_candidates[-1]

    # Find collapse dashboard
    collapse_candidates = sorted(analysis_dir.glob(f"dominance_collapse_dashboard_n=5_*{tag}*.tsv"))
    if not collapse_candidates:
        collapse_candidates = sorted(analysis_dir.glob("dominance_collapse_dashboard_n=5_*.tsv"))
    collapse_path = collapse_candidates[-1] if collapse_candidates else None

    if progress_callback:
        progress_callback(0.2, "Generating trunkiness charts")

    figures: list[FigureInfo] = []
    trunk_figs = _plot_trunkiness(trunk_path, assets_dir)
    figures.extend(trunk_figs)

    if progress_callback:
        progress_callback(0.4, "Generating collapse charts")

    collapse_figs: list[FigureInfo] = []
    if collapse_path:
        collapse_figs = _plot_collapse(collapse_path, assets_dir)
        figures.extend(collapse_figs)

    if progress_callback:
        progress_callback(0.5, "Finding chain data")

    # Find chain data for chase plots
    preferred_chain_names = [
        "dominant_upstream_chain_n=5_from=Massachusetts_bootstrap_2025-12-30.tsv",
        "dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30.tsv",
        "dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30.tsv",
    ]
    chain_paths: list[Path] = []
    for name in preferred_chain_names:
        p = analysis_dir / name
        if p.exists():
            chain_paths.append(p)

    if not chain_paths:
        chain_paths = sorted(analysis_dir.glob("dominant_upstream_chain_n=5_from=*.tsv"))[:3]

    if progress_callback:
        progress_callback(0.6, "Generating chase charts")

    chase_figs: list[FigureInfo] = []
    for p in chain_paths:
        chase_figs.extend(_plot_chase_series(p, assets_dir))
    figures.extend(chase_figs)

    overlay_fig = _plot_chase_overlay(chain_paths, assets_dir)
    if overlay_fig:
        figures.append(overlay_fig)

    if progress_callback:
        progress_callback(0.8, "Writing report markdown")

    # Build table previews
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
        cols = ["seed_title", "first_below_threshold_hop", "min_share", "stop_reason", "stop_at_title"]
        cols = [c for c in cols if c in collapse_df.columns]
        view = collapse_df[cols].copy()
        if "min_share" in view.columns:
            view["min_share"] = pd.to_numeric(view["min_share"], errors="coerce").map(
                lambda x: "" if pd.isna(x) else f"{float(x):.3f}"
            )

        try:
            collapse_rel = collapse_path.relative_to(repo_root).as_posix()
        except ValueError:
            collapse_rel = str(collapse_path)

        collapse_section = textwrap.dedent(
            f"""
            ## Dominance Collapse (Threshold Run)

            Collapse dashboard input:
            - `{collapse_rel}`

            Preview (sorted by min share):

            {_md_table(view.sort_values(['min_share'], ascending=[True]), max_rows=20)}
            """
        ).strip()

    try:
        trunk_rel = trunk_path.relative_to(repo_root).as_posix()
    except ValueError:
        trunk_rel = str(trunk_path)

    # Write report
    report_path = report_dir / "overview.md"
    md = textwrap.dedent(
        f"""
        # N=5 Basin Structure - Human-Facing Summary (So Far)

        **Date**: 2025-12-30
        **Scope**: Wikipedia fixed-$N$ rule with $N=5$ (the induced functional graph $f_5$).
        **Goal**: Summarize what we've empirically learned about basin sizes, branch ("watershed") structure, and dominant-upstream trunks.

        This report is generated from gitignored analysis artifacts under `data/wikipedia/processed/analysis/`.

        ## Key Takeaways

        - Basin sizes vary substantially in a small sample; a "giant basin" candidate exists (`Massachusetts <-> Gulf_of_Maine`).
        - Many basins are highly *single-trunk* at depth 1: one predecessor subtree captures most upstream mass.
        - "Non-trunky" at hop 0 does not imply "non-trunky" upstream: dominant-upstream chase can quickly enter high-dominance regimes.
        - Dominance can later *collapse* (shares plunge) as the chase enters diffuse / long-tail regions.

        ## Trunkiness Dashboard

        Dashboard input:
        - `{trunk_rel}`

        **Charts**:
        - ![Top-1 share](assets/{trunk_figs[0].name})
        - ![Size vs share](assets/{trunk_figs[1].name})

        **Preview table**:

        {_md_table(trunk_preview, max_rows=20)}

        {collapse_section}

        ## Example Chases (Dominant Share vs Hop)

        These are pulled from any available `dominant_upstream_chain_n=5_from=*.tsv` artifacts.

        {chr(10).join([f"- {p.name}" for p in chain_paths])}

        **Charts** (share + basin size per chase):

        {chr(10).join([f"- ![chart](assets/{f.name})" for f in chase_figs])}

        **Overlay comparison**:

        {(f"- ![overlay](assets/{overlay_fig.name})" if overlay_fig else "(overlay not available)")}

        ## How to Regenerate

        From repo root:
        - `python n-link-analysis/scripts/render-human-report.py --tag {tag}`

        This rewrites:
        - `n-link-analysis/report/overview.md`
        - `n-link-analysis/report/assets/*.png`
        """
    ).strip() + "\n"

    report_path.write_text(md, encoding="utf-8")

    if verbose:
        print(f"Wrote report: {report_path}")
        print(f"Wrote assets: {assets_dir}")

    if progress_callback:
        progress_callback(1.0, "Complete")

    elapsed = time.time() - t0

    return ReportResult(
        tag=tag,
        report_path=str(report_path),
        assets_dir=str(assets_dir),
        figures=figures,
        trunk_data_path=str(trunk_path),
        collapse_data_path=str(collapse_path) if collapse_path else None,
        chain_data_paths=[str(p) for p in chain_paths],
        elapsed_seconds=elapsed,
    )
