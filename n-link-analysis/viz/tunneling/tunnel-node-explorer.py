#!/usr/bin/env python3
"""Generate interactive tunnel node explorer as standalone HTML.

This script creates a searchable, sortable HTML table of all tunnel nodes
using DataTables.js for client-side interactivity. No server required.

Output:
  - report/assets/tunnel_node_explorer.html

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_frequency_ranking.tsv
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def load_tunnel_nodes(path: Path) -> pd.DataFrame:
    """Load tunnel frequency ranking data."""
    if not path.exists():
        raise FileNotFoundError(f"Tunnel ranking file not found: {path}")
    return pd.read_csv(path, sep="\t")


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if pd.isna(text):
        return ""
    return html.escape(str(text))


def truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if pd.isna(text):
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def generate_html(df: pd.DataFrame) -> str:
    """Generate complete HTML page with embedded data."""

    # Prepare data for JavaScript
    table_data = []
    for idx, row in df.iterrows():
        page_title = row.get("page_title", "")
        if pd.isna(page_title) or page_title == "":
            page_title = f"page_{row['page_id']}"

        # Create Wikipedia link
        wiki_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

        table_data.append({
            "rank": idx + 1,
            "page_id": int(row["page_id"]),
            "page_title": escape_html(page_title),
            "wiki_url": wiki_url,
            "tunnel_score": round(float(row["tunnel_score"]), 2),
            "n_basins": int(row["n_basins_bridged"]),
            "n_transitions": int(row["n_transitions"]),
            "mean_depth": round(float(row["mean_depth"]), 1),
            "tunnel_type": row.get("tunnel_type", ""),
            "basin_list": truncate(row.get("basin_list", ""), 60),
            "stable_ranges": row.get("stable_ranges", ""),
        })

    # Convert to JSON for embedding
    data_json = json.dumps(table_data)

    # Statistics
    total_nodes = len(df)
    progressive_count = len(df[df["tunnel_type"] == "progressive"])
    alternating_count = len(df[df["tunnel_type"] == "alternating"])
    mean_score = df["tunnel_score"].mean()
    max_score = df["tunnel_score"].max()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tunnel Node Explorer - Wikipedia N-Link Analysis</title>

    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.dataTables.min.css">

    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #1a1a2e;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 20px;
        }}
        .stats-row {{
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 6px;
            border-left: 4px solid #1f77b4;
        }}
        .stat-card.progressive {{ border-left-color: #2ca02c; }}
        .stat-card.alternating {{ border-left-color: #ff7f0e; }}
        .stat-card.score {{ border-left-color: #9467bd; }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1a1a2e;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .description {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        table.dataTable {{
            width: 100% !important;
            font-size: 13px;
        }}
        table.dataTable thead th {{
            background: #1a1a2e;
            color: white;
            font-weight: 500;
        }}
        table.dataTable tbody tr:hover {{
            background: #f0f7ff !important;
        }}
        .wiki-link {{
            color: #1f77b4;
            text-decoration: none;
        }}
        .wiki-link:hover {{
            text-decoration: underline;
        }}
        .type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        .type-progressive {{
            background: #d4edda;
            color: #155724;
        }}
        .type-alternating {{
            background: #fff3cd;
            color: #856404;
        }}
        .basin-list {{
            font-size: 11px;
            color: #666;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .dt-buttons {{
            margin-bottom: 15px;
        }}
        .dataTables_filter input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Tunnel Node Explorer</h1>
        <p class="subtitle">Wikipedia N-Link Rule Analysis - {total_nodes:,} Tunnel Nodes</p>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">{total_nodes:,}</div>
                <div class="stat-label">Total Tunnel Nodes</div>
            </div>
            <div class="stat-card progressive">
                <div class="stat-value">{progressive_count:,}</div>
                <div class="stat-label">Progressive</div>
            </div>
            <div class="stat-card alternating">
                <div class="stat-value">{alternating_count:,}</div>
                <div class="stat-label">Alternating</div>
            </div>
            <div class="stat-card score">
                <div class="stat-value">{mean_score:.1f}</div>
                <div class="stat-label">Mean Score</div>
            </div>
        </div>

        <div class="description">
            <strong>What are tunnel nodes?</strong> Tunnel nodes are Wikipedia pages that belong to
            <em>different</em> basins under different N-link rules. A <strong>progressive</strong>
            tunnel makes a single switch (e.g., Basin A at N=5, Basin B at N=6), while an
            <strong>alternating</strong> tunnel switches multiple times. Higher tunnel scores
            indicate more semantically central pages.
        </div>

        <table id="tunnelTable" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Page Title</th>
                    <th>Score</th>
                    <th>Basins</th>
                    <th>Transitions</th>
                    <th>Mean Depth</th>
                    <th>Type</th>
                    <th>Basin List</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>

        <div class="footer">
            <p>Data source: Wikipedia English (enwiki-20251220) | N-Link Rule Analysis</p>
            <p>Generated by tunnel-node-explorer.py</p>
        </div>
    </div>

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <!-- DataTables Buttons -->
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

    <script>
        // Embedded data
        const tunnelData = {data_json};

        $(document).ready(function() {{
            $('#tunnelTable').DataTable({{
                data: tunnelData,
                columns: [
                    {{ data: 'rank', className: 'dt-center' }},
                    {{
                        data: null,
                        render: function(data, type, row) {{
                            return '<a href="' + row.wiki_url + '" target="_blank" class="wiki-link">' + row.page_title + '</a>';
                        }}
                    }},
                    {{ data: 'tunnel_score', className: 'dt-center' }},
                    {{ data: 'n_basins', className: 'dt-center' }},
                    {{ data: 'n_transitions', className: 'dt-center' }},
                    {{ data: 'mean_depth', className: 'dt-center' }},
                    {{
                        data: 'tunnel_type',
                        className: 'dt-center',
                        render: function(data) {{
                            const cls = data === 'progressive' ? 'type-progressive' : 'type-alternating';
                            return '<span class="type-badge ' + cls + '">' + data + '</span>';
                        }}
                    }},
                    {{
                        data: 'basin_list',
                        render: function(data) {{
                            return '<div class="basin-list" title="' + data + '">' + data + '</div>';
                        }}
                    }}
                ],
                pageLength: 50,
                order: [[2, 'desc']],  // Sort by score descending
                dom: 'Bfrtip',
                buttons: [
                    {{
                        extend: 'csv',
                        text: 'Export CSV',
                        filename: 'tunnel_nodes_export',
                        exportOptions: {{
                            columns: [0, 1, 2, 3, 4, 5, 6, 7]
                        }}
                    }}
                ],
                language: {{
                    search: "Search pages:",
                    lengthMenu: "Show _MENU_ nodes per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ tunnel nodes",
                    paginate: {{
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    return html_content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate tunnel node explorer HTML"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv",
        help="Tunnel frequency ranking TSV file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORT_DIR / "tunnel_node_explorer.html",
        help="Output HTML file",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Generating Tunnel Node Explorer")
    print("=" * 70)
    print()

    # Load data
    print(f"Loading tunnel nodes from {args.input}...")
    df = load_tunnel_nodes(args.input)
    print(f"  Found {len(df):,} tunnel nodes")
    print()

    # Show top 5
    print("Top 5 tunnel nodes by score:")
    for i, row in df.head(5).iterrows():
        title = row.get("page_title", f"page_{row['page_id']}")
        print(f"  {i+1}. {title} (score: {row['tunnel_score']:.2f})")
    print()

    # Generate HTML
    print("Generating HTML...")
    html_content = generate_html(df)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  Saved to {args.output}")
    print(f"  File size: {args.output.stat().st_size / 1024:.1f} KB")
    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
