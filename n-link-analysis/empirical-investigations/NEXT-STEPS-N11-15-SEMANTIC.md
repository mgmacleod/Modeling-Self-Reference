# Next Steps Plan: N-Range Extension + Semantic Analysis

**Document Type**: Implementation Plan
**Created**: 2026-01-02
**Status**: Approved, ready to execute
**Scope**: Medium project (3-4 sessions)

---

## Overview

Two sequential phases:
1. **Phase A**: Extend N-link analysis from N=3-10 to N=3-15 (full pipeline)
2. **Phase B**: Semantic analysis of tunnel nodes with Wikipedia categories

**Order**: N-range first, then semantic analysis (so semantic analysis benefits from expanded tunnel node set)

---

## Phase A: Extend N-Link Analysis to N=11-15

### A.1 Pre-Extension Validation (~15 min)

Verify data exists for N=11-15 in `nlink_sequences.parquet`:

```bash
python -c "
import pyarrow.parquet as pq
df = pq.ParquetFile('data/wikipedia/processed/nlink_sequences.parquet').read().to_pandas()
for n in range(11, 16):
    coverage = (df['link_sequence'].apply(len) >= n).sum()
    print(f'N={n}: {coverage:,} pages ({100*coverage/len(df):.1f}%)')
"
```

**Expected**: N=15 has ~3.2M pages (17.8%)

**Validation Checkpoint**: If any N value has <10% coverage, reassess scope.

---

### A.2 Run Basin Analysis for N=11-15 (~20-60 min)

```bash
for N in 11 12 13 14 15; do
  python n-link-analysis/scripts/run-analysis-harness.py --n $N --quick --max-cycles 6 &
done
wait
```

**Outputs per N**:
- `basin_n={N}_cycle=*_layers.tsv` — Depth layer counts
- `branches_n={N}_cycle=*_assignments.parquet` — Basin assignments
- `branch_trunkiness_dashboard_n={N}_*.tsv` — Trunk concentration

**Validation Checkpoint**: 6 basin files exist per N value (11-15)

---

### A.3 Update Hardcoded N Ranges (~30 min)

| File | Line(s) | Change |
|------|---------|--------|
| `scripts/validate-hf-dataset.py` | 321, 608 | `range(3, 11)` → `range(3, 16)` |
| `scripts/compare-across-n.py` | 186 | default `[3,5,7]` → `[3,5,7,10,15]` |
| `viz/tunneling/tunneling-explorer.py` | 415, 500, 520, 576, 1421 | `range(3, 11)` → `range(3, 16)` |
| `viz/multiplex-analyzer.py` | 127, 228 | `range(3, 11)` → `range(3, 16)` |
| `scripts/tunneling/build-multiplex-table.py` | 58-63 | `n-max=10` → `n-max=15` |
| `scripts/tunneling/run-tunneling-pipeline.py` | 205-210 | `n-max=7` → `n-max=15` |

---

### A.4 Rebuild Tunneling Pipeline (~30-45 min)

```bash
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py --n-min 3 --n-max 15
```

**Outputs Updated**:
- `multiplex_basin_assignments.parquet` — Now includes N=11-15 rows
- `tunnel_nodes.parquet` — Adds `basin_at_N11` through `basin_at_N15` columns
- `tunnel_frequency_ranking.tsv` — Recalculated with 13 N values

**Validation Checkpoint**: `tunnel_nodes.parquet` has `basin_at_N11` through `basin_at_N15` columns

---

### A.5 Update Phase Transition Charts (~15 min)

- Rename/update `analyze-phase-transition-n3-n10.py` for N=3-15
- Regenerate `phase_transition_n3_to_n15_comprehensive.png`
- Regenerate `universal_cycles_heatmap_n3_to_n15.png`

---

### A.6 Documentation (~20 min)

- Update `TUNNELING-ROADMAP.md`: "N=3-10" → "N=3-15"
- Update `MULTI-N-PHASE-MAP.md`: Add N=11-15 data rows
- Add timeline entry in `project-timeline.md`

---

## Phase B: Semantic Analysis of Tunnel Nodes

### B.1 Fetch Categories for All Tunnel Nodes (~2-4 hours API time)

**Create**: `n-link-analysis/scripts/semantic/fetch-tunnel-categories-full.py`

Features:
- Batch Wikipedia API calls (50 pages/batch, 0.2s delay)
- Checkpoint/resume capability for large runs
- Rate limiting to respect API guidelines

**Output**: `data/wikipedia/processed/semantic/tunnel_node_categories_full.json`

**Validation Checkpoint**: JSON file >10MB

---

### B.2 Analyze Category Patterns (~30 min)

**Create**: `n-link-analysis/scripts/semantic/analyze-tunnel-categories.py`

Features:
- Classify categories into domains (geography, biology, history, politics, science, culture, people, sports)
- Compare tunnel node distribution vs baseline
- Identify overrepresented categories

**Output**: `data/wikipedia/processed/semantic/tunnel_category_analysis.json`

**Prior Finding to Validate**: 22.5% of tunnel nodes from New England (vs ~1% expected)

---

### B.3 Domain Intersection Analysis (~20 min)

**Create**: `n-link-analysis/scripts/semantic/compute-domain-basin-flows.py`

Features:
- Map which semantic domains tunnel to which basins
- Track (domain, from_basin, to_basin) triples
- Identify strongest domain-basin associations

**Output**: `data/wikipedia/processed/semantic/domain_basin_flows.json`

---

### B.4 Top Tunnel Node Deep-Dive (~30 min)

**Create**: `n-link-analysis/scripts/semantic/generate-tunnel-deep-dive.py`

Features:
- Profile top 50 tunnel nodes by score
- Include: categories, basin trajectory (N=3-15), mechanism interpretation
- Qualitative analysis of bridging roles

**Output**: `n-link-analysis/empirical-investigations/TUNNEL-NODE-DEEP-DIVE.md`

**Validation Checkpoint**: Deep-dive markdown has 50 profiles

---

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/semantic/fetch-tunnel-categories-full.py` | Batch category fetching with checkpoints |
| `scripts/semantic/analyze-tunnel-categories.py` | Domain classification and statistics |
| `scripts/semantic/compute-domain-basin-flows.py` | Domain-to-basin flow mapping |
| `scripts/semantic/generate-tunnel-deep-dive.py` | Top tunnel node profiles |

---

## Files to Modify

| File | Changes |
|------|---------|
| `scripts/validate-hf-dataset.py` | N range 3-10 → 3-15 |
| `scripts/compare-across-n.py` | Default N values |
| `viz/tunneling/tunneling-explorer.py` | N range in 5 locations |
| `viz/multiplex-analyzer.py` | N range in 2 locations |
| `scripts/tunneling/build-multiplex-table.py` | Default n-max |
| `scripts/tunneling/run-tunneling-pipeline.py` | Default n-max |
| `scripts/analyze-phase-transition-n3-n10.py` | Extend to N=15 |

---

## Documentation Outputs

- `n-link-analysis/empirical-investigations/N11-15-EXTENSION.md` — Phase transition findings for N=11-15
- `n-link-analysis/empirical-investigations/TUNNEL-NODE-DEEP-DIVE.md` — Top 50 tunnel node profiles
- Updated `MULTI-N-PHASE-MAP.md` with N=11-15 data
- Timeline entry in `project-timeline.md`

---

## Session Breakdown

| Session | Tasks | Duration |
|---------|-------|----------|
| 1 | A.1-A.3: Validation, basin analysis, code updates | 2-3 hours |
| 2 | A.4-A.6: Multiplex rebuild, charts, docs | 1.5-2 hours |
| 3 | B.1-B.2: Category fetching, pattern analysis | 3-4 hours |
| 4 | B.3-B.5: Domain flows, deep-dive, final docs | 1-2 hours |

---

## Theoretical Predictions for N=11-15

Based on current findings:

1. **Basin mass continuation**: Expected to follow declining curve from N=5 peak
   - N=10: ~20K-150K nodes per cycle
   - N=11-15: Further 40-60% decline expected

2. **Phase transition behavior**: No new peaks predicted (N=5 is unique)

3. **HALT probability**: Likely increases further (N=10 ~20%, N=15 ~25-30% estimated)

4. **Cycle persistence**: Main 6 universal cycles likely continue at N=11-15 but with smaller basins

---

## Key Insight from Exploration

The infrastructure is already N-agnostic — core scripts accept `--n` parameter. Most work is:
1. Updating default N ranges in visualization/validation scripts
2. Running the existing pipeline with higher N values
3. Creating new semantic analysis scripts

**Estimated effort**: 5-10 hours total across 3-4 sessions

---

**Last Updated**: 2026-01-02
