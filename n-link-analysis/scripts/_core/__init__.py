"""Core analysis engines for N-Link Basin Analysis.

This package contains reusable logic extracted from the analysis scripts.
These engines can be used by both CLI scripts and the API service layer.

Modules:
    trace_engine: Trace sampling and path following
    basin_engine: Basin mapping via reverse BFS
    branch_engine: Branch structure analysis
    dashboard_engine: Trunkiness dashboard computation
    report_engine: Report and figure generation
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

from _core.dashboard_engine import (
    TrunkinessCycleStats,
    TrunkinessDashboardResult,
    compute_trunkiness_dashboard,
    gini_coefficient,
)

from _core.report_engine import (
    FigureInfo,
    ReportResult,
    generate_report,
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
    # dashboard_engine
    "TrunkinessCycleStats",
    "TrunkinessDashboardResult",
    "compute_trunkiness_dashboard",
    "gini_coefficient",
    # report_engine
    "FigureInfo",
    "ReportResult",
    "generate_report",
]
