#!/usr/bin/env python3
"""Validate theory predictions about tunneling empirically.

This script tests claims from the N-Link Rule Theory and Database Inference
Graph Theory against empirical Wikipedia data.

Validations:
  1. Do high-degree hubs form more tunnels? (Theory: hub nodes should tunnel more)
  2. Does tunnel frequency correlate with semantic centrality? (Theory: central = more tunnels)
  3. Does depth predict tunnel probability? (From Phase 4: shallow nodes tunnel more)
  4. Are tunnel nodes concentrated at phase transition N values? (Theory: N=5 is critical)

Output: tunneling_validation_metrics.tsv with validation results

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
  - data/wikipedia/processed/multiplex/tunnel_frequency_ranking.tsv
  - data/wikipedia/processed/multiplex/tunnel_mechanisms.tsv
  - data/wikipedia/processed/links_prose.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def validate_hub_tunnel_correlation(
    tunnel_nodes_df: pd.DataFrame,
    con: duckdb.DuckDBPyConnection,
    sample_size: int = 10000,
) -> dict:
    """Test: Do high-degree pages form more tunnels?

    Theory prediction: Hub nodes (high out-degree) should be more likely to tunnel
    because they have more link options that can diverge across N values.
    """
    print("  Testing hub-tunnel correlation...")

    # Sample pages
    tunnel_pages = tunnel_nodes_df[tunnel_nodes_df["is_tunnel_node"] == True]["page_id"].tolist()
    non_tunnel_pages = tunnel_nodes_df[tunnel_nodes_df["is_tunnel_node"] == False]["page_id"].tolist()

    # Sample for efficiency
    if len(tunnel_pages) > sample_size:
        tunnel_sample = np.random.choice(tunnel_pages, sample_size, replace=False)
    else:
        tunnel_sample = tunnel_pages

    if len(non_tunnel_pages) > sample_size:
        non_tunnel_sample = np.random.choice(non_tunnel_pages, sample_size, replace=False)
    else:
        non_tunnel_sample = non_tunnel_pages[:sample_size]

    # Get out-degrees
    tunnel_ids = ",".join(str(int(p)) for p in tunnel_sample)
    non_tunnel_ids = ",".join(str(int(p)) for p in non_tunnel_sample)

    tunnel_degrees = con.execute(f"""
        SELECT from_id, COUNT(*) as out_degree
        FROM links_prose
        WHERE from_id IN ({tunnel_ids})
        GROUP BY from_id
    """).fetchdf()

    non_tunnel_degrees = con.execute(f"""
        SELECT from_id, COUNT(*) as out_degree
        FROM links_prose
        WHERE from_id IN ({non_tunnel_ids})
        GROUP BY from_id
    """).fetchdf()

    # Statistics
    tunnel_mean = tunnel_degrees["out_degree"].mean() if len(tunnel_degrees) > 0 else 0
    non_tunnel_mean = non_tunnel_degrees["out_degree"].mean() if len(non_tunnel_degrees) > 0 else 0

    # T-test
    if len(tunnel_degrees) > 0 and len(non_tunnel_degrees) > 0:
        t_stat, p_value = stats.ttest_ind(
            tunnel_degrees["out_degree"],
            non_tunnel_degrees["out_degree"],
            equal_var=False
        )
    else:
        t_stat, p_value = 0, 1

    result = {
        "test": "hub_tunnel_correlation",
        "hypothesis": "Tunnel nodes have higher out-degree than non-tunnel nodes",
        "tunnel_mean_degree": round(tunnel_mean, 2),
        "non_tunnel_mean_degree": round(non_tunnel_mean, 2),
        "degree_ratio": round(tunnel_mean / non_tunnel_mean, 3) if non_tunnel_mean > 0 else 0,
        "t_statistic": round(t_stat, 3),
        "p_value": round(p_value, 6),
        "validated": p_value < 0.05 and tunnel_mean > non_tunnel_mean,
        "sample_size": len(tunnel_degrees) + len(non_tunnel_degrees),
    }

    print(f"    Tunnel mean degree: {tunnel_mean:.1f}")
    print(f"    Non-tunnel mean degree: {non_tunnel_mean:.1f}")
    print(f"    Validated: {result['validated']} (p={p_value:.4f})")

    return result


def validate_depth_tunnel_correlation(
    tunnel_freq_df: pd.DataFrame,
) -> dict:
    """Test: Does depth predict tunnel probability?

    From Phase 4 discovery: Tunnel nodes have mean depth 11.1 (shallow).
    Test if there's a significant correlation between depth and tunnel score.
    """
    print("  Testing depth-tunnel correlation...")

    if "mean_depth" not in tunnel_freq_df.columns:
        return {
            "test": "depth_tunnel_correlation",
            "hypothesis": "Shallow nodes are more likely to tunnel",
            "validated": None,
            "reason": "mean_depth column not found",
        }

    # Correlation
    depths = tunnel_freq_df["mean_depth"].dropna()
    scores = tunnel_freq_df["tunnel_score"].dropna()

    if len(depths) < 10:
        return {
            "test": "depth_tunnel_correlation",
            "hypothesis": "Shallow nodes are more likely to tunnel",
            "validated": None,
            "reason": "insufficient data",
        }

    # Align indices
    common_idx = depths.index.intersection(scores.index)
    depths = depths.loc[common_idx]
    scores = scores.loc[common_idx]

    corr, p_value = stats.pearsonr(depths, scores)

    result = {
        "test": "depth_tunnel_correlation",
        "hypothesis": "Shallow nodes (low depth) have higher tunnel scores",
        "correlation": round(corr, 4),
        "p_value": round(p_value, 6),
        "mean_depth": round(depths.mean(), 2),
        "validated": p_value < 0.05 and corr < 0,  # Negative = shallow means more tunneling
        "sample_size": len(depths),
    }

    print(f"    Correlation: {corr:.3f}")
    print(f"    Mean depth of tunnel nodes: {depths.mean():.1f}")
    print(f"    Validated: {result['validated']} (p={p_value:.4f})")

    return result


def validate_transition_concentration(
    mechanisms_df: pd.DataFrame,
) -> dict:
    """Test: Are transitions concentrated at specific N values?

    Theory prediction: Phase transition at N=5 should show as concentration
    of tunnel transitions around N=5.
    """
    print("  Testing transition concentration at N=5...")

    if "transition" not in mechanisms_df.columns:
        return {
            "test": "transition_concentration",
            "hypothesis": "Tunnel transitions concentrate around N=5",
            "validated": None,
            "reason": "transition column not found",
        }

    # Count transitions by type
    trans_counts = mechanisms_df["transition"].value_counts()

    # Calculate concentration
    total = trans_counts.sum()
    n5_related = sum(
        count for trans, count in trans_counts.items()
        if "N5" in trans
    )
    n5_fraction = n5_related / total if total > 0 else 0

    # Chi-square test: is N5 overrepresented?
    # Under uniform distribution, each transition type would have equal probability
    n_transition_types = len(trans_counts)
    expected_fraction = 1 / n_transition_types if n_transition_types > 0 else 0

    result = {
        "test": "transition_concentration",
        "hypothesis": "Tunnel transitions concentrate around N=5 (phase transition)",
        "n5_related_fraction": round(n5_fraction, 4),
        "expected_if_uniform": round(expected_fraction, 4),
        "concentration_ratio": round(n5_fraction / expected_fraction, 2) if expected_fraction > 0 else 0,
        "top_transitions": dict(trans_counts.head(5)),
        "validated": n5_fraction > 0.5,  # N=5 involved in >50% of transitions
        "sample_size": int(total),
    }

    print(f"    N5-related transitions: {n5_fraction:.1%}")
    print(f"    Validated: {result['validated']}")

    return result


def validate_mechanism_predictions(
    mechanisms_df: pd.DataFrame,
) -> dict:
    """Test: Is degree_shift the dominant mechanism?

    Theory prediction: Since N-link rule directly selects different links,
    degree_shift (different Nth link) should dominate over path_divergence.
    """
    print("  Testing mechanism distribution...")

    if "mechanism" not in mechanisms_df.columns:
        return {
            "test": "mechanism_distribution",
            "hypothesis": "degree_shift dominates over path_divergence",
            "validated": None,
            "reason": "mechanism column not found",
        }

    mech_counts = mechanisms_df["mechanism"].value_counts()
    total = mech_counts.sum()

    degree_shift_frac = mech_counts.get("degree_shift", 0) / total if total > 0 else 0
    path_div_frac = mech_counts.get("path_divergence", 0) / total if total > 0 else 0

    result = {
        "test": "mechanism_distribution",
        "hypothesis": "degree_shift (different Nth link) dominates mechanisms",
        "degree_shift_fraction": round(degree_shift_frac, 4),
        "path_divergence_fraction": round(path_div_frac, 4),
        "dominance_ratio": round(degree_shift_frac / path_div_frac, 1) if path_div_frac > 0 else float("inf"),
        "mechanism_counts": dict(mech_counts),
        "validated": degree_shift_frac > 0.9,  # >90% is degree_shift
        "sample_size": int(total),
    }

    print(f"    degree_shift: {degree_shift_frac:.1%}")
    print(f"    path_divergence: {path_div_frac:.1%}")
    print(f"    Validated: {result['validated']}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate tunneling theory predictions"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunneling_validation_metrics.tsv",
        help="Output TSV file",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10000,
        help="Sample size for degree correlation test",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Validating Tunneling Theory Predictions")
    print("=" * 70)
    print()

    # Set random seed for reproducibility
    np.random.seed(42)

    # Connect to data
    print("Loading data sources...")
    con = duckdb.connect(":memory:")
    con.execute(f"""
        CREATE VIEW links_prose AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "links_prose.parquet"}')
    """)

    tunnel_nodes_df = pd.read_parquet(MULTIPLEX_DIR / "tunnel_nodes.parquet")
    print(f"  Tunnel nodes: {len(tunnel_nodes_df):,} pages")

    tunnel_freq_df = pd.read_csv(MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv", sep="\t")
    print(f"  Tunnel frequency: {len(tunnel_freq_df):,} entries")

    mechanisms_path = MULTIPLEX_DIR / "tunnel_mechanisms.tsv"
    if mechanisms_path.exists():
        mechanisms_df = pd.read_csv(mechanisms_path, sep="\t")
        print(f"  Mechanisms: {len(mechanisms_df):,} entries")
    else:
        mechanisms_df = pd.DataFrame()
        print("  Mechanisms: not found (skipping related tests)")
    print()

    # Run validations
    print("Running validation tests...")
    print()

    validations = []

    # Test 1: Hub-tunnel correlation
    result1 = validate_hub_tunnel_correlation(tunnel_nodes_df, con, args.sample_size)
    validations.append(result1)
    print()

    # Test 2: Depth-tunnel correlation
    result2 = validate_depth_tunnel_correlation(tunnel_freq_df)
    validations.append(result2)
    print()

    # Test 3: Transition concentration
    if len(mechanisms_df) > 0:
        result3 = validate_transition_concentration(mechanisms_df)
        validations.append(result3)
        print()

        # Test 4: Mechanism distribution
        result4 = validate_mechanism_predictions(mechanisms_df)
        validations.append(result4)
        print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print()

    validated_count = sum(1 for v in validations if v.get("validated") == True)
    failed_count = sum(1 for v in validations if v.get("validated") == False)
    skipped_count = sum(1 for v in validations if v.get("validated") is None)

    print(f"Tests run: {len(validations)}")
    print(f"  Validated: {validated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print()

    for v in validations:
        status = "PASS" if v.get("validated") else "FAIL" if v.get("validated") == False else "SKIP"
        print(f"  [{status}] {v['test']}: {v['hypothesis'][:50]}...")
    print()

    # Write output
    print(f"Writing to {args.output}...")

    # Flatten for TSV output
    rows = []
    for v in validations:
        row = {
            "test": v["test"],
            "hypothesis": v["hypothesis"],
            "validated": v.get("validated"),
            "sample_size": v.get("sample_size", 0),
        }
        # Add test-specific metrics
        for k, val in v.items():
            if k not in ["test", "hypothesis", "validated", "sample_size"]:
                if isinstance(val, (int, float, bool, str)):
                    row[k] = val
        rows.append(row)

    results_df = pd.DataFrame(rows)
    results_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(results_df)} tests written")
    print()

    con.close()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
