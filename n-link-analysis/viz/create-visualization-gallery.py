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

        {tunneling_section}

        <h2 style="font-size: 1.8rem; margin: 2rem 0 1rem; color: #2c3e50;">N=5 Basin Geometries</h2>
        <div class="gallery">
            {''.join(items_html)}
        </div>

        {grid_section}
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
