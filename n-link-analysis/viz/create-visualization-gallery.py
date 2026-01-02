#!/usr/bin/env python3
"""Generate an HTML gallery page to browse all basin visualizations.

This creates a responsive gallery with thumbnails, metadata, and links to
both static PNGs and interactive HTML viewers.

Run (repo root)
--------------
  python n-link-analysis/viz/create-visualization-gallery.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"


BASIN_METADATA = {
    "Massachusetts": {
        "nodes": 121_291,
        "depth": 8,
        "type": "Explosive Wide",
        "description": "Largest basin (25% of Wikipedia), massive width with shallow depth",
    },
    "Kingdom_(biology)": {
        "nodes": 54_589,
        "depth": 9,
        "type": "Hub-Driven",
        "description": "Early peak then taper, strong hub connectivity",
    },
    "Autumn": {
        "nodes": 54_537,
        "depth": 7,
        "type": "Balanced",
        "description": "Mid-range peak, stable convergence pattern",
    },
    "Sea_salt": {
        "nodes": 104_711,
        "depth": 14,
        "type": "Tall Trunk",
        "description": "Late exponential growth, peaks at depth 14",
    },
    "Mountain": {
        "nodes": 74_325,
        "depth": 20,
        "type": "Tall Trunk",
        "description": "Extended depth with late growth phase",
    },
    "Latvia": {
        "nodes": 52_491,
        "depth": 12,
        "type": "Balanced",
        "description": "Moderate depth and width, steady convergence",
    },
    "Precedent": {
        "nodes": 56_034,
        "depth": 23,
        "type": "Hub-Driven",
        "description": "Deep exploration driven by hub connectivity",
    },
    "American_Revolutionary_War": {
        "nodes": 46_159,
        "depth": 10,
        "type": "Balanced",
        "description": "Classic balanced profile with moderate dimensions",
    },
    "Thermosetting_polymer": {
        "nodes": 61_109,
        "depth": 48,
        "type": "Skyscraper Trunk",
        "description": "Extraordinarily deep (48 steps, 2× any other), narrow funnel",
    },
}

# Extended cross-N analysis figures (beyond the core 4)
CROSS_N_EXTENDED = [
    ("cross_n_basin_sizes.png", "Basin Sizes Across N", "Total basin sizes at each N value"),
    ("cross_n_collapse.png", "Basin Collapse", "Collapse patterns across N values"),
    ("cross_n_comprehensive.png", "Comprehensive View", "Full multi-panel cross-N analysis"),
    ("cross_n_sampling.png", "Sampling Analysis", "Sampling methodology and coverage"),
    ("cross_n_trunkiness.png", "Trunkiness Analysis", "Trunk structure patterns across N"),
    ("cross_n_universal_cycles.png", "Universal Cycles", "Cycles appearing across multiple N values"),
    ("universal_cycles_heatmap_n3_to_n10.png", "Universal Cycles Heatmap", "Heatmap of cycle persistence across N=3-10"),
    ("bottleneck_analysis_n3_to_n7.png", "Bottleneck Analysis", "Bottleneck identification N=3-7"),
    ("mechanism_comparison_n3_to_n7.png", "Mechanism Comparison", "Traversal mechanism comparison N=3-7"),
    ("phase_transition_n3_to_n7.png", "Phase Transition (N=3-7)", "Phase transition curve for N=3-7 range"),
    ("phase_transition_n3_to_n10_comprehensive.png", "Comprehensive Phase Transition", "Full phase transition with all metrics"),
]

# Coverage and evolution analysis
COVERAGE_EVOLUTION = [
    ("coverage_vs_basin_mass.png", "Coverage vs Basin Mass", "Relationship between coverage and basin size"),
    ("coverage_zones_analysis.png", "Coverage Zones", "Analysis of coverage zone boundaries"),
    ("cycle_dominance_evolution.png", "Cycle Dominance Evolution", "How cycle dominance changes across N"),
    ("cycle_evolution_basin_sizes.png", "Basin Size Evolution", "Evolution of basin sizes across N values"),
    ("massachusetts_deep_dive.png", "Massachusetts Deep Dive", "Detailed analysis of the largest basin"),
    ("massachusetts_evolution_n3_to_n10.png", "Massachusetts Evolution", "Massachusetts basin across N=3-10"),
]

# Additional analysis figures
ADDITIONAL_ANALYSIS = [
    ("dominance_collapse_first_below_hop.png", "Dominance Collapse", "First-hop dominance collapse analysis"),
    ("multiplex_layer_connectivity.png", "Multiplex Connectivity", "Layer connectivity in the multiplex structure"),
    ("trunkiness_scatter_size_vs_top1.png", "Trunkiness Scatter", "Scatter plot: basin size vs top-1 share"),
    ("trunkiness_top1_share.png", "Top-1 Share Distribution", "Distribution of top-1 contributor shares"),
    ("tunnel_summary_chart.png", "Tunnel Summary", "Summary chart of tunneling statistics"),
]

# Wrap-up analysis (from 2026-01-02 comprehensive analysis)
WRAPUP_ANALYSIS = [
    # Semantic Model
    ("semantic_model_central_entities.html", "Central Tunnel Entities", "Top 30 tunnel nodes by score - interactive"),
    ("subsystem_stability_comparison.html", "Basin Stability Analysis", "Persistence scores and stability classes"),
    ("hidden_relationships_flow.html", "Cross-Basin Flows", "Sankey diagram of hidden relationships"),
    ("tunnel_type_breakdown.html", "Tunnel Type Distribution", "Alternating vs progressive tunnel types"),
    ("depth_vs_tunnel_score.html", "Depth vs Tunnel Score", "Scatter plot of depth vs tunnel score"),
    # Edit-Stability Correlation
    ("edit_vs_stability_correlation.html", "Edit-Stability Correlation", "Edit frequency vs basin stability"),
    # Universal Cycle Analysis
    ("universal_cycle_n_evolution.html", "Universal Cycle Evolution", "Basin size evolution N=3-10 for universal cycles"),
    ("universal_cycle_properties.html", "Universal Cycle Properties", "Comparison of the 6 universal cycles"),
    ("universal_cycle_domains.html", "Semantic Domain Breakdown", "Universal cycles by semantic domain"),
    # Basin Statistics
    ("universal_attractors_chart.html", "Universal Attractors", "Attractors by total page count"),
    ("basin_stats_summary.html", "Basin Statistics Summary", "Per-N basin statistics overview"),
]


def generate_gallery_html() -> str:
    """Generate responsive HTML gallery with thumbnails and metadata."""

    # Find all basin PNG files
    basin_pngs = sorted(ASSETS_DIR.glob("basin_3d_n=5_cycle=*.png"))

    # Find multi-N analysis figures
    multi_n_pngs = [
        ("phase_transition_n3_n10.png", "Phase Transition (N=3-10)", "Basin size across N values, showing N=5 peak"),
        ("basin_collapse_n5_vs_n10.png", "Basin Collapse", "Size comparison N=5 vs N=10 with collapse factors"),
        ("tunnel_node_distribution.png", "Tunnel Distribution", "Distribution of tunnel nodes by basins bridged"),
        ("depth_distribution_by_n.png", "Depth by N", "Mean, median, and max depth across N values"),
    ]

    if not basin_pngs:
        return "<p>No basin visualizations found. Run batch-render-basin-images.py first.</p>"

    # Build gallery items
    items_html = []

    for png_path in basin_pngs:
        # Extract cycle name from filename
        match = re.search(r"cycle=(.+)\.png$", png_path.name)
        if not match:
            continue

        cycle_slug = match.group(1)
        cycle_name = cycle_slug.replace("_", " ")

        # Get metadata
        meta = BASIN_METADATA.get(cycle_slug, {})
        nodes = meta.get("nodes", "Unknown")
        depth = meta.get("depth", "Unknown")
        basin_type = meta.get("type", "Unknown")
        description = meta.get("description", "")

        # Check for interactive HTML version
        html_path = ASSETS_DIR / f"basin_pointcloud_3d_n=5_cycle={cycle_slug}.html"
        has_interactive = html_path.exists()

        # Format file size
        size_mb = png_path.stat().st_size / (1024 * 1024)

        # Build card HTML
        item = f"""
        <div class="gallery-item">
            <div class="thumbnail">
                <img src="{png_path.name}" alt="{cycle_name}" loading="lazy">
            </div>
            <div class="info">
                <h3>{cycle_name}</h3>
                <div class="metadata">
                    <span class="badge type">{basin_type}</span>
                    <span class="badge">Nodes: {nodes:,}</span>
                    <span class="badge">Depth: {depth}</span>
                </div>
                <p class="description">{description}</p>
                <div class="links">
                    <a href="{png_path.name}" class="btn" download>Download PNG ({size_mb:.1f} MB)</a>
                    {f'<a href="basin_pointcloud_3d_n=5_cycle={cycle_slug}.html" class="btn interactive" target="_blank">Interactive 3D</a>' if has_interactive else ''}
                </div>
            </div>
        </div>
        """
        items_html.append(item.strip())

    # Check for comparison grid
    grid_path = ASSETS_DIR / "basin_comparison_grid_n=5.png"
    grid_section = ""
    if grid_path.exists():
        grid_size_mb = grid_path.stat().st_size / (1024 * 1024)
        grid_section = f"""
        <section class="comparison-section">
            <h2>Comparison Grid</h2>
            <div class="comparison-grid">
                <img src="basin_comparison_grid_n=5.png" alt="Basin Comparison Grid">
                <div class="info">
                    <p>Side-by-side comparison of all 9 N=5 terminal cycles, showing the diversity of basin geometries.</p>
                    <a href="basin_comparison_grid_n=5.png" class="btn" download>Download Grid ({grid_size_mb:.1f} MB)</a>
                </div>
            </div>
        </section>
        """

    # Build multi-N analysis section
    multi_n_items = []
    for filename, title, description in multi_n_pngs:
        png_path = ASSETS_DIR / filename
        if png_path.exists():
            size_kb = png_path.stat().st_size / 1024
            # Check for interactive HTML version
            html_name = filename.replace(".png", ".html")
            html_path = ASSETS_DIR / html_name
            interactive_link = f'<a href="{html_name}" class="btn interactive" target="_blank">Interactive</a>' if html_path.exists() else ""
            multi_n_items.append(f"""
            <div class="analysis-card">
                <img src="{filename}" alt="{title}" loading="lazy">
                <div class="card-info">
                    <h4>{title}</h4>
                    <p>{description}</p>
                    <div class="links">
                        <a href="{filename}" class="btn" download>PNG ({size_kb:.0f} KB)</a>
                        {interactive_link}
                    </div>
                </div>
            </div>
            """)

    multi_n_section = ""
    if multi_n_items:
        multi_n_section = f"""
        <section class="analysis-section">
            <h2>Multi-N Analysis (N=3-10)</h2>
            <p class="section-intro">Cross-N analysis revealing phase transitions, basin collapse, and tunneling behavior.</p>
            <div class="analysis-grid">
                {''.join(multi_n_items)}
            </div>
        </section>
        """

    # Check for tunneling visualizations
    tunneling_htmls = [
        ("tunneling_sankey.html", "Tunneling Sankey", "Interactive flow diagram of cross-basin page transitions"),
        ("tunnel_node_explorer.html", "Tunnel Explorer", "Searchable table of 41,732 tunnel nodes"),
        ("multi_n_summary_table.html", "Summary Table", "Key statistics across all N values"),
        ("multiplex_visualization.html", "Multiplex Visualization", "Interactive multiplex layer visualization"),
    ]
    tunneling_items = []
    for filename, title, description in tunneling_htmls:
        html_path = ASSETS_DIR / filename
        if html_path.exists():
            size_kb = html_path.stat().st_size / 1024
            tunneling_items.append(f"""
            <div class="tool-card">
                <h4>{title}</h4>
                <p>{description}</p>
                <a href="{filename}" class="btn interactive" target="_blank">Open ({size_kb:.0f} KB)</a>
            </div>
            """)

    tunneling_section = ""
    if tunneling_items:
        tunneling_section = f"""
        <section class="tools-section">
            <h2>Interactive Tools</h2>
            <div class="tools-grid">
                {''.join(tunneling_items)}
            </div>
        </section>
        """

    # Build extended cross-N analysis section
    cross_n_extended_items = []
    for filename, title, description in CROSS_N_EXTENDED:
        png_path = ASSETS_DIR / filename
        if png_path.exists():
            size_kb = png_path.stat().st_size / 1024
            cross_n_extended_items.append(f"""
            <div class="analysis-card">
                <img src="{filename}" alt="{title}" loading="lazy">
                <div class="card-info">
                    <h4>{title}</h4>
                    <p>{description}</p>
                    <div class="links">
                        <a href="{filename}" class="btn" download>PNG ({size_kb:.0f} KB)</a>
                    </div>
                </div>
            </div>
            """)

    cross_n_extended_section = ""
    if cross_n_extended_items:
        cross_n_extended_section = f"""
        <section class="analysis-section">
            <h2>Cross-N Analysis Extended</h2>
            <p class="section-intro">Additional cross-N analysis figures showing phase transitions, trunkiness patterns, and universal cycles.</p>
            <div class="analysis-grid">
                {''.join(cross_n_extended_items)}
            </div>
        </section>
        """

    # Build upstream dominance analysis section
    upstream_items = []
    # Find all chase_dominant files and group by basin
    chase_files = sorted(ASSETS_DIR.glob("chase_dominant_upstream_chain_*.png"))
    basins_seen: dict[str, dict[str, Path]] = {}
    overlay_path = None

    for f in chase_files:
        if "overlay" in f.name:
            overlay_path = f
            continue
        # Extract basin name: chase_dominant_upstream_chain_n=5_from=Massachusetts_basin.png
        match = re.search(r"from=(.+)_(basin|share)\.png$", f.name)
        if match:
            basin_name = match.group(1)
            file_type = match.group(2)
            if basin_name not in basins_seen:
                basins_seen[basin_name] = {}
            basins_seen[basin_name][file_type] = f

    for basin_name in sorted(basins_seen.keys()):
        files = basins_seen[basin_name]
        display_name = basin_name.replace("_", " ")
        links_html = []
        for ftype, fpath in sorted(files.items()):
            size_kb = fpath.stat().st_size / 1024
            links_html.append(f'<a href="{fpath.name}" class="btn" download>{ftype.title()} ({size_kb:.0f} KB)</a>')

        upstream_items.append(f"""
        <div class="analysis-card">
            <img src="{files.get('basin', files.get('share', list(files.values())[0])).name}" alt="{display_name}" loading="lazy">
            <div class="card-info">
                <h4>{display_name}</h4>
                <p>Dominant upstream chain analysis</p>
                <div class="links">
                    {''.join(links_html)}
                </div>
            </div>
        </div>
        """)

    # Add overlay if exists
    if overlay_path and overlay_path.exists():
        size_kb = overlay_path.stat().st_size / 1024
        upstream_items.insert(0, f"""
        <div class="analysis-card" style="grid-column: span 2;">
            <img src="{overlay_path.name}" alt="Dominant Share Overlay" loading="lazy">
            <div class="card-info">
                <h4>Dominant Share Overlay</h4>
                <p>Composite view of dominant upstream shares across all basins</p>
                <div class="links">
                    <a href="{overlay_path.name}" class="btn" download>PNG ({size_kb:.0f} KB)</a>
                </div>
            </div>
        </div>
        """)

    upstream_section = ""
    if upstream_items:
        upstream_section = f"""
        <section class="analysis-section">
            <h2>Upstream Dominance Analysis</h2>
            <p class="section-intro">Analysis of dominant upstream chains showing how pages flow toward basin attractors at N=5.</p>
            <div class="analysis-grid">
                {''.join(upstream_items)}
            </div>
        </section>
        """

    # Build coverage & evolution section
    coverage_items = []
    for filename, title, description in COVERAGE_EVOLUTION:
        png_path = ASSETS_DIR / filename
        if png_path.exists():
            size_kb = png_path.stat().st_size / 1024
            coverage_items.append(f"""
            <div class="analysis-card">
                <img src="{filename}" alt="{title}" loading="lazy">
                <div class="card-info">
                    <h4>{title}</h4>
                    <p>{description}</p>
                    <div class="links">
                        <a href="{filename}" class="btn" download>PNG ({size_kb:.0f} KB)</a>
                    </div>
                </div>
            </div>
            """)

    coverage_section = ""
    if coverage_items:
        coverage_section = f"""
        <section class="analysis-section">
            <h2>Coverage & Evolution</h2>
            <p class="section-intro">Analysis of coverage patterns and how basin structures evolve across N values.</p>
            <div class="analysis-grid">
                {''.join(coverage_items)}
            </div>
        </section>
        """

    # Build additional analysis section
    additional_items = []
    for filename, title, description in ADDITIONAL_ANALYSIS:
        png_path = ASSETS_DIR / filename
        if png_path.exists():
            size_kb = png_path.stat().st_size / 1024
            additional_items.append(f"""
            <div class="analysis-card">
                <img src="{filename}" alt="{title}" loading="lazy">
                <div class="card-info">
                    <h4>{title}</h4>
                    <p>{description}</p>
                    <div class="links">
                        <a href="{filename}" class="btn" download>PNG ({size_kb:.0f} KB)</a>
                    </div>
                </div>
            </div>
            """)

    additional_section = ""
    if additional_items:
        additional_section = f"""
        <section class="analysis-section">
            <h2>Additional Analysis</h2>
            <p class="section-intro">Supplementary analysis figures covering trunkiness, tunneling, and multiplex connectivity.</p>
            <div class="analysis-grid">
                {''.join(additional_items)}
            </div>
        </section>
        """

    # Build wrap-up analysis section (2026-01-02 comprehensive wrap-up)
    wrapup_items = []
    for filename, title, description in WRAPUP_ANALYSIS:
        file_path = ASSETS_DIR / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            is_html = filename.endswith('.html')
            btn_class = "btn interactive" if is_html else "btn"
            btn_text = "Interactive" if is_html else "PNG"
            wrapup_items.append(f"""
            <div class="tool-card">
                <h4>{title}</h4>
                <p>{description}</p>
                <a href="{filename}" class="{btn_class}" target="_blank">{btn_text} ({size_kb:.0f} KB)</a>
            </div>
            """)

    wrapup_section = ""
    if wrapup_items:
        wrapup_section = f"""
        <section class="tools-section">
            <h2>Wrap-Up Analysis</h2>
            <p class="section-intro">Comprehensive analysis of underutilized data: semantic model visualization, edit-stability correlation, universal cycle analysis, and basin statistics.</p>
            <div class="tools-grid">
                {''.join(wrapup_items)}
            </div>
        </section>
        """

    # Build variants section (color scale alternatives)
    variants_dir = ASSETS_DIR / "variants"
    variants_items = []
    if variants_dir.exists():
        for variant_png in sorted(variants_dir.glob("*.png")):
            size_mb = variant_png.stat().st_size / (1024 * 1024)
            # Extract basin and variant type from filename
            display_name = variant_png.stem.replace("_", " ").replace("basin 3d n=5 cycle=", "").title()
            variants_items.append(f"""
            <div class="analysis-card">
                <img src="variants/{variant_png.name}" alt="{display_name}" loading="lazy">
                <div class="card-info">
                    <h4>{display_name}</h4>
                    <p>Alternative color scale rendering</p>
                    <div class="links">
                        <a href="variants/{variant_png.name}" class="btn" download>PNG ({size_mb:.1f} MB)</a>
                    </div>
                </div>
            </div>
            """)

    variants_section = ""
    if variants_items:
        variants_section = f"""
        <section class="analysis-section">
            <h2>Basin Visualization Variants</h2>
            <p class="section-intro">Alternative color scale renderings of selected basins (plasma, standard colorscales).</p>
            <div class="analysis-grid">
                {''.join(variants_items)}
            </div>
        </section>
        """

    # Build tributary trees section
    tributary_htmls = sorted(ASSETS_DIR.glob("tributary_tree_3d_*.html"))
    tributary_items = []

    # Group by N value
    tributary_by_n: dict[int, list[tuple[str, str, Path]]] = {}
    for html_path in tributary_htmls:
        # Parse: tributary_tree_3d_n=5_cycle=Massachusetts__Gulf_of_Maine_k=4_levels=4_depth=10.html
        # Cycle names can contain underscores, so use __ as the separator between cycle pair
        match = re.search(r"n=(\d+)_cycle=(.+)__(.+)_k=(\d+)", html_path.name)
        if match:
            n_val = int(match.group(1))
            cycle_a = match.group(2).replace("_", " ")
            cycle_b = match.group(3).replace("_", " ")
            cycle_name = f"{cycle_a} ↔ {cycle_b}"
            if n_val not in tributary_by_n:
                tributary_by_n[n_val] = []
            tributary_by_n[n_val].append((html_path.name, cycle_name, html_path))

    # Build cards grouped by N
    tributary_section = ""
    if tributary_by_n:
        tributary_cards = []
        for n_val in sorted(tributary_by_n.keys()):
            items = tributary_by_n[n_val]
            # Create a sub-section for this N value
            links_html = []
            for filename, cycle_name, path in sorted(items, key=lambda x: x[1]):
                size_mb = path.stat().st_size / (1024 * 1024)
                links_html.append(
                    f'<a href="{filename}" class="btn interactive" target="_blank" title="{cycle_name}">'
                    f'{cycle_name} ({size_mb:.1f}MB)</a>'
                )

            cycle_word = "cycle" if len(items) == 1 else "cycles"
            tributary_cards.append(f"""
            <div class="tool-card" style="grid-column: span 1;">
                <h4>N={n_val} Trees ({len(items)} {cycle_word})</h4>
                <p>3D tributary tree visualizations showing page flow toward attractors</p>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                    {''.join(links_html)}
                </div>
            </div>
            """)

        tributary_section = f"""
        <section class="tools-section">
            <h2>Tributary Trees (3D)</h2>
            <p class="section-intro">Interactive 3D visualizations showing how pages flow toward basin attractors. Each tree shows k nearest predecessors at multiple depth levels.</p>
            <div class="tools-grid" style="grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));">
                {''.join(tributary_cards)}
            </div>
        </section>
        """

    # Build written reports section
    reports_data = [
        # Core Findings
        ("overview.html", "Basin Overview", "N=5 basin structure summary with trunkiness and dominance analysis", "core"),
        ("multi-n-analysis.html", "Multi-N Analysis", "Cross-N comparative analysis (N=3-10) with phase transition findings", "core"),
        ("tunneling-findings.html", "Tunneling Findings", "Analysis of cross-basin tunneling mechanisms and theory validation", "core"),
        ("edit-history.html", "Edit History", "Wikipedia edit activity analysis for cycle page stability assessment", "core"),
        # Reference
        ("annotated-bibliography.html", "Annotated Bibliography", "Academic literature on multiplex networks, schema theory, and functional graphs", "reference"),
        # Dataset Docs
        ("dataset-card.html", "Dataset Card", "HuggingFace dataset metadata and usage information", "dataset"),
        ("huggingface-readme.html", "Dataset README", "Comprehensive HuggingFace dataset documentation with examples", "dataset"),
        ("huggingface-manifest.html", "Upload Manifest", "HuggingFace upload configurations and file manifest", "dataset"),
    ]

    reports_by_category: dict[str, list[tuple[str, str, str]]] = {"core": [], "reference": [], "dataset": []}
    for filename, title, desc, category in reports_data:
        if (ASSETS_DIR / filename).exists():
            reports_by_category[category].append((filename, title, desc))

    written_reports_section = ""
    if any(reports_by_category.values()):
        def make_report_cards(items: list[tuple[str, str, str]]) -> str:
            cards = []
            for filename, title, desc in items:
                cards.append(f"""
                <div class="tool-card">
                    <h4>{title}</h4>
                    <p>{desc}</p>
                    <a href="{filename}" class="btn" target="_blank">Read Report</a>
                </div>
                """)
            return ''.join(cards)

        sections = []
        if reports_by_category["core"]:
            sections.append(f"""
            <h3 style="margin-top: 1.5rem; color: #2c3e50;">Core Findings</h3>
            <div class="tools-grid">{make_report_cards(reports_by_category["core"])}</div>
            """)
        if reports_by_category["reference"]:
            sections.append(f"""
            <h3 style="margin-top: 1.5rem; color: #2c3e50;">Reference</h3>
            <div class="tools-grid">{make_report_cards(reports_by_category["reference"])}</div>
            """)
        if reports_by_category["dataset"]:
            sections.append(f"""
            <h3 style="margin-top: 1.5rem; color: #2c3e50;">Dataset Documentation</h3>
            <div class="tools-grid">{make_report_cards(reports_by_category["dataset"])}</div>
            """)

        written_reports_section = f"""
        <section class="tools-section">
            <h2>Written Reports</h2>
            <p class="section-intro">Detailed analysis documents with findings, methodology, and conclusions.</p>
            {''.join(sections)}
        </section>
        """

    # Full HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N-Link Basin Analysis Gallery</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}

        .gallery-item {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .gallery-item:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}

        .thumbnail {{
            width: 100%;
            height: 250px;
            overflow: hidden;
            background: #f0f0f0;
        }}

        .thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .info {{
            padding: 1.5rem;
        }}

        .info h3 {{
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            color: #2c3e50;
        }}

        .metadata {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .badge {{
            background: #e8f4f8;
            color: #2980b9;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        .badge.type {{
            background: #667eea;
            color: white;
        }}

        .description {{
            color: #666;
            font-size: 0.95rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}

        .links {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .btn {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}

        .btn:hover {{
            background: #2980b9;
        }}

        .btn.interactive {{
            background: #9b59b6;
        }}

        .btn.interactive:hover {{
            background: #8e44ad;
        }}

        .comparison-section {{
            margin-top: 3rem;
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .comparison-section h2 {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: #2c3e50;
        }}

        .comparison-grid img {{
            width: 100%;
            border-radius: 4px;
            margin-bottom: 1rem;
        }}

        .analysis-section, .tools-section {{
            margin-top: 3rem;
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .analysis-section h2, .tools-section h2 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }}

        .section-intro {{
            color: #666;
            margin-bottom: 1.5rem;
        }}

        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}

        .analysis-card {{
            background: #f9f9f9;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #eee;
        }}

        .analysis-card img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
        }}

        .card-info {{
            padding: 1rem;
        }}

        .card-info h4 {{
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }}

        .card-info p {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.75rem;
        }}

        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }}

        .tool-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
        }}

        .tool-card h4 {{
            margin-bottom: 0.5rem;
        }}

        .tool-card p {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 1rem;
        }}

        .tool-card .btn {{
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
        }}

        .tool-card .btn:hover {{
            background: rgba(255,255,255,0.3);
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            .gallery {{
                grid-template-columns: 1fr;
            }}

            header h1 {{
                font-size: 1.8rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>N-Link Basin Analysis Gallery</h1>
        <p>Visualizations of Wikipedia's link graph structure under N-link rules (N=3-10)</p>
    </header>

    <div class="container">
        <section class="intro">
            <p style="font-size: 1.1rem; color: #555; margin-bottom: 2rem;">
                These visualizations show the three-dimensional structure of attraction basins in Wikipedia's link graph.
                Each basin represents the set of articles that converge to a specific 2-cycle when following the 5th link iteratively.
                The N=5 rule exhibits a dramatic phase transition with basins 20-60× larger than other N values.
            </p>
        </section>

        {multi_n_section}

        {cross_n_extended_section}

        {tunneling_section}

        {tributary_section}

        <h2 style="font-size: 1.8rem; margin: 2rem 0 1rem; color: #2c3e50;">N=5 Basin Geometries</h2>
        <div class="gallery">
            {''.join(items_html)}
        </div>

        {grid_section}

        {variants_section}

        {upstream_section}

        {coverage_section}

        {additional_section}

        {wrapup_section}

        {written_reports_section}
    </div>

    <footer>
        <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Part of the Self-Reference Modeling Project</p>
    </footer>
</body>
</html>
"""

    return html


def main() -> int:
    """Generate visualization gallery HTML."""
    print("Generating visualization gallery...")

    html = generate_gallery_html()

    output_path = ASSETS_DIR / "gallery.html"
    output_path.write_text(html, encoding="utf-8")

    print(f"✓ Gallery created: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
