# Tunneling Analysis Scripts

Scripts for cross-N multiplex analysis and tunneling node identification.

## Quick Start

```bash
# Run complete pipeline (all 5 phases)
python run-tunneling-pipeline.py

# Run specific phases
python run-tunneling-pipeline.py --phase 1 2

# Dry run
python run-tunneling-pipeline.py --dry-run
```

## Pipeline Phases

| Phase | Scripts | Purpose |
|-------|---------|---------|
| **1** | `build-multiplex-table.py`, `normalize-cycle-identity.py`, `compute-intersection-matrix.py` | Multiplex Data Layer |
| **2** | `find-tunnel-nodes.py`, `classify-tunnel-types.py`, `compute-tunnel-frequency.py` | Tunnel Node Identification |
| **3** | `build-multiplex-graph.py`, `compute-multiplex-reachability.py`, `visualize-multiplex-slice.py` | Multiplex Connectivity |
| **4** | `analyze-tunnel-mechanisms.py`, `trace-tunneling-paths.py`, `quantify-basin-stability.py` | Mechanism Classification |
| **5** | `compute-semantic-model.py`, `validate-tunneling-predictions.py`, `generate-tunneling-report.py` | Applications & Validation |

## Output Directory

All outputs go to `data/wikipedia/processed/multiplex/`.

## Documentation

- [TUNNELING-ROADMAP.md](../../TUNNELING-ROADMAP.md) - Full implementation roadmap
- [TUNNELING-FINDINGS.md](../../report/TUNNELING-FINDINGS.md) - Results summary
