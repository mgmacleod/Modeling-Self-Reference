"""Core analysis engines for N-Link Basin Analysis.

This package contains reusable logic extracted from the analysis scripts.
These engines can be used by both CLI scripts and the API service layer.

Modules:
    trace_engine: Trace sampling and path following
    basin_engine: Basin mapping via reverse BFS
    branch_engine: Branch structure analysis
    report_engine: Report and figure generation (to be added)
"""

from _core.trace_engine import (
    SampleRow,
    TraceSampleResult,
    load_successor_arrays,
    sample_traces,
    trace_once,
)

from _core.basin_engine import (
    BasinMapResult,
    LayerInfo,
    ensure_edges_table,
    get_edges_db_path,
    map_basin,
    resolve_ids_to_titles,
    resolve_titles_to_ids,
)

from _core.branch_engine import (
    BranchAnalysisResult,
    BranchInfo,
    analyze_branches,
)

__all__ = [
    # trace_engine
    "SampleRow",
    "TraceSampleResult",
    "load_successor_arrays",
    "sample_traces",
    "trace_once",
    # basin_engine
    "BasinMapResult",
    "LayerInfo",
    "ensure_edges_table",
    "get_edges_db_path",
    "map_basin",
    "resolve_ids_to_titles",
    "resolve_titles_to_ids",
    # branch_engine
    "BranchAnalysisResult",
    "BranchInfo",
    "analyze_branches",
]
