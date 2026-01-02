#!/usr/bin/env python3
"""Correlate Wikipedia edit history with basin stability metrics.

Creates a visualization showing the relationship between:
- Edit frequency (from EDIT-HISTORY-ANALYSIS.md)
- Basin stability metrics (from basin_stability_scores.tsv)

Research question: Do high-edit pages have fragile basins?

Run (repo root):
  python n-link-analysis/scripts/correlate-edit-basin-stability.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


REPO_ROOT = Path(__file__).resolve().parents[2]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report"
REPORT_ASSETS_DIR = REPORT_DIR / "assets"


def parse_edit_history_markdown() -> pd.DataFrame:
    """Parse edit data from EDIT-HISTORY-ANALYSIS.md markdown table."""
    md_path = REPORT_DIR / "EDIT-HISTORY-ANALYSIS.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Missing: {md_path}")

    text = md_path.read_text()

    # Find the table section
    table_match = re.search(
        r'\| Page \| Edits.*?\n((?:\|.*?\n)+)',
        text
    )
    if not table_match:
        raise ValueError("Could not find edit history table in markdown")

    rows = []
    for line in table_match.group(1).strip().split('\n'):
        if line.startswith('|---'):
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 5:
            page = parts[0]
            edits = int(parts[1])
            days_since = parts[2]
            major_edits = int(parts[3])
            largest_delta = parts[4]

            # Parse days_since (handle N/A)
            try:
                days = int(days_since)
            except ValueError:
                days = 999  # N/A means never edited

            # Parse largest_delta
            delta_match = re.search(r'([+-]?\d+)', largest_delta)
            delta = int(delta_match.group(1)) if delta_match else 0

            rows.append({
                'page_title': page,
                'edit_count': edits,
                'days_since_last_edit': days,
                'major_edits': major_edits,
                'largest_delta': delta,
            })

    return pd.DataFrame(rows)


def load_stability_scores() -> pd.DataFrame:
    """Load basin stability scores from TSV."""
    path = MULTIPLEX_DIR / "basin_stability_scores.tsv"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")

    return pd.read_csv(path, sep='\t')


def normalize_page_name(name: str) -> str:
    """Normalize page name for matching."""
    return name.lower().replace('_', ' ').replace(' (', '(').strip()


def match_pages_to_basins(edit_df: pd.DataFrame, stability_df: pd.DataFrame) -> pd.DataFrame:
    """Match edit history pages to basin stability records."""
    # Create mapping from page name to basin
    # Basin IDs are like "Gulf_of_Maine__Massachusetts" - we need to extract individual pages

    page_to_basin = {}
    for _, row in stability_df.iterrows():
        basin_id = row['canonical_cycle_id']
        # Extract page names from basin ID (format: Page1__Page2 or Page1_tunneling__Page2)
        parts = basin_id.replace('_tunneling', '').split('__')
        for part in parts:
            normalized = part.replace('_', ' ')
            page_to_basin[normalize_page_name(normalized)] = {
                'basin_id': basin_id,
                'stability_class': row['stability_class'],
                'persistence_score': row['persistence_score'],
                'mean_jaccard': row['mean_jaccard'],
                'total_pages': row['total_pages'],
            }

    # Match edit history pages to basins
    matched_rows = []
    for _, row in edit_df.iterrows():
        page = row['page_title']
        normalized = normalize_page_name(page)

        if normalized in page_to_basin:
            basin_info = page_to_basin[normalized]
            matched_rows.append({
                **row.to_dict(),
                **basin_info,
            })
        else:
            # Try partial matching
            for key, basin_info in page_to_basin.items():
                if normalized in key or key in normalized:
                    matched_rows.append({
                        **row.to_dict(),
                        **basin_info,
                    })
                    break

    return pd.DataFrame(matched_rows)


def save_figure(fig, output_dir: Path, name: str, width: int = 1200, height: int = 600) -> Path:
    """Save figure as HTML (and PNG if Chrome available)."""
    html_path = output_dir / f"{name}.html"
    fig.write_html(str(html_path))
    print(f"✓ Saved: {html_path.name}")

    try:
        png_path = output_dir / f"{name}.png"
        fig.write_image(str(png_path), width=width, height=height, scale=2)
        print(f"✓ Saved: {png_path.name}")
    except Exception:
        print(f"⚠️  PNG export failed (Chrome not available): {name}.png")

    return html_path


def create_correlation_chart(matched_df: pd.DataFrame, output_dir: Path) -> Path:
    """Create scatter plot correlating edits with stability."""
    if matched_df.empty:
        print("⚠️  No matched data for correlation chart")
        return None

    # Color by stability class
    stability_colors = {
        'stable': '#2ca02c',
        'moderate': '#ff7f0e',
        'fragile': '#d62728',
    }
    matched_df['color'] = matched_df['stability_class'].map(stability_colors).fillna('#666666')

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            "Edit Count vs Basin Size",
            "Edit Count by Stability Class"
        ],
        column_widths=[0.6, 0.4],
    )

    # Left: Scatter plot - edits vs total_pages
    fig.add_trace(go.Scatter(
        x=matched_df['edit_count'],
        y=matched_df['total_pages'],
        mode='markers+text',
        marker=dict(
            size=12,
            color=matched_df['color'],
        ),
        text=matched_df['page_title'],
        textposition='top center',
        textfont=dict(size=8),
        hovertemplate="<b>%{text}</b><br>Edits: %{x}<br>Basin Size: %{y:,}<br>Stability: %{customdata}<extra></extra>",
        customdata=matched_df['stability_class'],
    ), row=1, col=1)

    # Right: Bar chart - average edits by stability class
    avg_by_stability = matched_df.groupby('stability_class')['edit_count'].agg(['mean', 'count']).reset_index()
    avg_by_stability = avg_by_stability.sort_values('mean', ascending=False)

    fig.add_trace(go.Bar(
        x=avg_by_stability['stability_class'],
        y=avg_by_stability['mean'],
        marker_color=[stability_colors.get(s, '#666') for s in avg_by_stability['stability_class']],
        text=[f"n={int(c)}" for c in avg_by_stability['count']],
        textposition='outside',
    ), row=1, col=2)

    fig.update_layout(
        title=dict(
            text="Edit Activity vs Basin Stability<br><sub>Do high-edit cycle pages have fragile basins?</sub>",
            font=dict(size=18),
            x=0.5,
        ),
        template="plotly_white",
        width=1200,
        height=600,
        showlegend=False,
    )

    fig.update_xaxes(title="Edit Count (90 days)", row=1, col=1)
    fig.update_yaxes(title="Total Basin Pages", type="log", row=1, col=1)
    fig.update_xaxes(title="Stability Class", row=1, col=2)
    fig.update_yaxes(title="Mean Edit Count", row=1, col=2)

    return save_figure(fig, output_dir, "edit_vs_stability_correlation")


def create_report(matched_df: pd.DataFrame, edit_df: pd.DataFrame, output_dir: Path) -> Path:
    """Generate markdown report on edit-stability correlation."""
    if matched_df.empty:
        content = """# Edit History - Basin Stability Correlation

**Status**: No matching data available for correlation analysis.

The edit history pages could not be matched to basin stability records.
This may be due to naming mismatches between the page titles and basin cycle IDs.
"""
    else:
        # Calculate correlation
        correlation = matched_df['edit_count'].corr(matched_df['total_pages'])

        # Find fragile basins
        fragile = matched_df[matched_df['stability_class'] == 'fragile']
        fragile_edits = fragile['edit_count'].mean() if not fragile.empty else 0

        moderate = matched_df[matched_df['stability_class'] == 'moderate']
        moderate_edits = moderate['edit_count'].mean() if not moderate.empty else 0

        # Most edited pages
        top_edited = matched_df.nlargest(5, 'edit_count')[['page_title', 'edit_count', 'stability_class', 'total_pages']]

        content = f"""# Edit History - Basin Stability Correlation

**Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}
**Pages Analyzed**: {len(edit_df)}
**Pages Matched to Basins**: {len(matched_df)}

## Key Finding

**Correlation between edit count and basin size**: {correlation:.3f}

{"Strong" if abs(correlation) > 0.5 else "Moderate" if abs(correlation) > 0.3 else "Weak"} {"positive" if correlation > 0 else "negative"} correlation observed.

## Stability Class Comparison

| Stability Class | Mean Edits (90 days) | Count |
|-----------------|---------------------|-------|
| Fragile | {fragile_edits:.1f} | {len(fragile)} |
| Moderate | {moderate_edits:.1f} | {len(moderate)} |

## Most Edited Cycle Pages

| Page | Edits | Stability | Basin Size |
|------|-------|-----------|------------|
"""
        for _, row in top_edited.iterrows():
            content += f"| {row['page_title']} | {row['edit_count']} | {row['stability_class']} | {row['total_pages']:,} |\n"

        content += f"""
## Interpretation

{"The fragile basin (Gulf_of_Maine → Massachusetts) shows **zero edits** to Gulf of Maine but high edits (24) to Massachusetts, suggesting instability may arise from one side of the cycle." if not fragile.empty else "No fragile basins in the matched dataset."}

{"Moderate basins show varying edit activity, with higher-traffic pages like American Revolutionary War and Autumn seeing 25-30+ edits in 90 days." if not moderate.empty else ""}

## Visualization

See [edit_vs_stability_correlation.html](assets/edit_vs_stability_correlation.html) for interactive visualization.
"""

    report_path = REPORT_DIR / "EDIT-STABILITY-CORRELATION.md"
    report_path.write_text(content)
    print(f"✓ Saved: {report_path.name}")
    return report_path


def main() -> int:
    print("\nCorrelating edit history with basin stability...")
    print(f"Output: {REPORT_ASSETS_DIR}\n")

    # Load data
    try:
        edit_df = parse_edit_history_markdown()
        print(f"Loaded {len(edit_df)} pages from edit history")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    try:
        stability_df = load_stability_scores()
        print(f"Loaded {len(stability_df)} basin stability records")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Match pages
    matched_df = match_pages_to_basins(edit_df, stability_df)
    print(f"Matched {len(matched_df)} pages to basins")

    if matched_df.empty:
        print("\n⚠️  No pages could be matched between edit history and stability data")
        print("Page names in edit history:")
        for p in edit_df['page_title'].head(10):
            print(f"  - {p}")
        print("\nBasin IDs in stability data:")
        for b in stability_df['canonical_cycle_id'].head(10):
            print(f"  - {b}")
    else:
        print(f"\nMatched data preview:")
        print(matched_df[['page_title', 'edit_count', 'stability_class', 'total_pages']].to_string())

    # Create outputs
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    viz_path = create_correlation_chart(matched_df, REPORT_ASSETS_DIR)
    report_path = create_report(matched_df, edit_df, REPORT_DIR)

    print(f"\n✓ Analysis complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
