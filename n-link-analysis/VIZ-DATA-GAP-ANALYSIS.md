# Visualization & Reporting Data Gap Analysis

**Date**: 2026-01-01 (Updated)
**Purpose**: Track gaps and fixes for N=3-10 data support

---

## Status: RESOLVED

All identified gaps have been fixed. The visualization and reporting tools now fully support N=3-10.

---

## Fixes Applied

### Data Updates

| Data Source | Before | After | Action |
|------------|--------|-------|--------|
| `tunnel_nodes.parquet` | N=3-7 columns | N=3-10 columns | Regenerated with `--n-max 10` |
| `tunnel_classification.tsv` | 9,018 tunnel nodes | 41,732 tunnel nodes | Auto-regenerated |
| `tunnel_frequency_ranking.tsv` | 9,018 nodes | 41,732 nodes | Auto-regenerated |
| `basin_stability_scores.tsv` | 9 basins | 15 basins | Regenerated with `--n-max 10` |
| `basin_flows.tsv` | 16 flows | 58 flows | Auto-regenerated |

### Script Updates

| Script | Change | Status |
|--------|--------|--------|
| `path-tracer-tool.py` | `range(3, 8)` → `range(3, 11)` in 5 locations | FIXED |
| `dash-multiplex-explorer.py` | Badge: `N=3-7` → `N=3-10` | FIXED |
| `generate-tunneling-report.py` | N Range metadata: `3-7` → `3-10` | FIXED |

---

## Key Discovery: Tunnel Node Explosion

Extending to N=3-10 revealed a **4.6× increase** in tunnel nodes:

| Metric | N=3-7 | N=3-10 | Change |
|--------|-------|--------|--------|
| Total tunnel nodes | 9,018 | 41,732 | +363% |
| 2-basin nodes | 8,909 | 41,372 | +364% |
| 3-basin nodes | 108 | 359 | +232% |
| 4-basin nodes | 1 | 1 | — |

**Interpretation**: Most additional tunneling occurs at N=8-10 transitions, where pages that were stable at N=5-7 finally diverge to different basins.

---

## Scripts NOT Needing Updates

These scripts dynamically load data and work correctly without changes:

| Script | Reason |
|--------|--------|
| `tunneling-dashboard.py` | Loads from dynamic TSV files |
| `sankey-basin-flows.py` | Reads from `basin_flows.tsv` |
| `tunnel-node-explorer.py` | Reads from `tunnel_frequency_ranking.tsv` |
| `batch-render-basin-images.py` | Takes N as parameter |
| `render-full-basin-geometry.py` | Takes N as parameter |
| `dash-basin-geometry-viewer.py` | Takes N as parameter |

---

## Validation Commands

```bash
# 1. Verify tunnel_nodes has N8-10 columns
python -c "import pandas as pd; print(pd.read_parquet('data/wikipedia/processed/multiplex/tunnel_nodes.parquet').columns.tolist())"
# Expected: [..., 'basin_at_N8', 'basin_at_N9', 'basin_at_N10', ...]

# 2. Start path tracer and verify N=8-10 appear
python n-link-analysis/viz/tunneling/path-tracer-tool.py --port 8061

# 3. Verify dashboard shows updated data
python n-link-analysis/viz/tunneling/tunneling-dashboard.py --port 8060
```

---

## Remaining Work (Optional)

- **Mechanism analysis**: `analyze-tunnel-mechanisms.py` runs very slowly (~10+ minutes). The existing mechanism data covers N=3-7 transitions only. A full re-run would analyze all 41,732 tunnel nodes.

---

**Last Updated**: 2026-01-01
