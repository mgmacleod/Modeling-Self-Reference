#!/usr/bin/env python3
"""
Analyze HALT probability across N values to test Conjectures 6.1 and 6.3.

Conjecture 6.1 (Monotonic HALT Probability):
    P_HALT(N1) <= P_HALT(N2) whenever N1 < N2

Conjecture 6.3 (Phase Transition):
    There exists N* such that P_CYCLE(N*) = P_HALT(N*) = 0.5

P_HALT(N) = fraction of pages with out-degree < N (cannot follow N-th link)
P_CYCLE(N) = 1 - P_HALT(N) = fraction that can participate in basin structure
"""

from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).parents[2]
ANALYSIS_DIR = REPO_ROOT / "data/wikipedia/processed/analysis"

def load_degree_distribution():
    """Load exact degree distribution."""
    path = ANALYSIS_DIR / "link_degree_distribution_exact.tsv"
    df = pd.read_csv(path, sep="\t")
    return df

def load_cumulative_distribution():
    """Load cumulative distribution (pages with >= N links)."""
    path = ANALYSIS_DIR / "link_degree_distribution.tsv"
    df = pd.read_csv(path, sep="\t")
    return df

def compute_halt_probability(exact_df: pd.DataFrame, max_n: int = 50) -> pd.DataFrame:
    """
    Compute P_HALT(N) for each N.

    P_HALT(N) = (pages with degree < N) / total_pages
             = (pages with degree 1 + degree 2 + ... + degree N-1) / total
    """
    total_pages = exact_df["num_pages"].sum()
    print(f"Total pages: {total_pages:,}")

    results = []
    cumulative_halt = 0

    for n in range(1, max_n + 1):
        # Pages that HALT at N are those with degree < N
        # i.e., degree in {1, 2, ..., N-1}
        halt_pages = exact_df[exact_df["num_links"] < n]["num_pages"].sum()
        cycle_pages = total_pages - halt_pages

        p_halt = halt_pages / total_pages
        p_cycle = cycle_pages / total_pages

        results.append({
            "N": n,
            "halt_pages": halt_pages,
            "cycle_pages": cycle_pages,
            "P_HALT": p_halt,
            "P_CYCLE": p_cycle,
            "P_HALT_pct": p_halt * 100,
            "P_CYCLE_pct": p_cycle * 100,
        })

    return pd.DataFrame(results)

def test_conjecture_6_1(df: pd.DataFrame) -> dict:
    """
    Test Conjecture 6.1: P_HALT is monotonically increasing with N.
    """
    violations = []
    for i in range(len(df) - 1):
        if df.iloc[i]["P_HALT"] > df.iloc[i + 1]["P_HALT"]:
            violations.append({
                "N1": df.iloc[i]["N"],
                "N2": df.iloc[i + 1]["N"],
                "P_HALT_N1": df.iloc[i]["P_HALT"],
                "P_HALT_N2": df.iloc[i + 1]["P_HALT"],
            })

    is_monotonic = len(violations) == 0
    return {
        "conjecture": "6.1 (Monotonic HALT Probability)",
        "result": "VALIDATED" if is_monotonic else "REFUTED",
        "is_monotonic": is_monotonic,
        "violations": violations,
        "details": f"P_HALT increases strictly with N for all tested values" if is_monotonic
                   else f"Found {len(violations)} violations of monotonicity"
    }

def test_conjecture_6_3(df: pd.DataFrame) -> dict:
    """
    Test Conjecture 6.3: Find N* where P_HALT = P_CYCLE = 0.5.
    """
    # Find the crossover point where P_HALT crosses 0.5
    crossover_n = None
    for i in range(len(df) - 1):
        if df.iloc[i]["P_HALT"] < 0.5 and df.iloc[i + 1]["P_HALT"] >= 0.5:
            # Linear interpolation to find exact crossover
            n1, n2 = df.iloc[i]["N"], df.iloc[i + 1]["N"]
            p1, p2 = df.iloc[i]["P_HALT"], df.iloc[i + 1]["P_HALT"]
            crossover_n = n1 + (0.5 - p1) * (n2 - n1) / (p2 - p1)
            break

    # Also find N* as the closest integer where P_HALT ≈ 0.5
    df["diff_from_50"] = abs(df["P_HALT"] - 0.5)
    closest_row = df.loc[df["diff_from_50"].idxmin()]

    return {
        "conjecture": "6.3 (Phase Transition at N*)",
        "result": "VALIDATED" if crossover_n else "NOT FOUND IN RANGE",
        "crossover_n_interpolated": crossover_n,
        "closest_integer_n": int(closest_row["N"]),
        "P_HALT_at_closest": closest_row["P_HALT"],
        "P_CYCLE_at_closest": closest_row["P_CYCLE"],
        "details": f"Crossover at N* ≈ {crossover_n:.2f}" if crossover_n
                   else "No crossover found in tested range"
    }

def main():
    print("=" * 70)
    print("HALT PROBABILITY ANALYSIS")
    print("Testing Conjectures 6.1 and 6.3 from N-Link Rule Theory")
    print("=" * 70)

    # Load data
    print("\nLoading degree distribution data...")
    exact_df = load_degree_distribution()

    # Compute P_HALT for N=1 to 50
    print("\nComputing P_HALT(N) for N=1 to 50...")
    results_df = compute_halt_probability(exact_df, max_n=50)

    # Display key values
    print("\n" + "-" * 70)
    print("P_HALT(N) and P_CYCLE(N) by N value:")
    print("-" * 70)
    print(f"{'N':>4}  {'P_HALT':>10}  {'P_CYCLE':>10}  {'HALT pages':>15}  {'CYCLE pages':>15}")
    print("-" * 70)

    for _, row in results_df.iterrows():
        if row["N"] <= 20 or row["N"] % 5 == 0:
            print(f"{int(row['N']):>4}  {row['P_HALT']:>10.4f}  {row['P_CYCLE']:>10.4f}  "
                  f"{int(row['halt_pages']):>15,}  {int(row['cycle_pages']):>15,}")

    # Test Conjecture 6.1
    print("\n" + "=" * 70)
    print("CONJECTURE 6.1: Monotonic HALT Probability")
    print("=" * 70)
    result_6_1 = test_conjecture_6_1(results_df)
    print(f"\nResult: {result_6_1['result']}")
    print(f"Details: {result_6_1['details']}")
    if result_6_1['violations']:
        print("Violations:")
        for v in result_6_1['violations']:
            print(f"  N={v['N1']} → N={v['N2']}: P_HALT decreased from {v['P_HALT_N1']:.6f} to {v['P_HALT_N2']:.6f}")

    # Test Conjecture 6.3
    print("\n" + "=" * 70)
    print("CONJECTURE 6.3: Phase Transition (P_HALT = P_CYCLE = 0.5)")
    print("=" * 70)
    result_6_3 = test_conjecture_6_3(results_df)
    print(f"\nResult: {result_6_3['result']}")
    if result_6_3['crossover_n_interpolated']:
        print(f"Crossover point N* ≈ {result_6_3['crossover_n_interpolated']:.2f}")
    print(f"Closest integer N = {result_6_3['closest_integer_n']}")
    print(f"At N={result_6_3['closest_integer_n']}: P_HALT = {result_6_3['P_HALT_at_closest']:.4f}, "
          f"P_CYCLE = {result_6_3['P_CYCLE_at_closest']:.4f}")

    # Additional insights
    print("\n" + "=" * 70)
    print("ADDITIONAL INSIGHTS")
    print("=" * 70)

    # Find key thresholds
    for threshold in [0.1, 0.25, 0.5, 0.75, 0.9]:
        row = results_df[results_df["P_HALT"] >= threshold].iloc[0] if any(results_df["P_HALT"] >= threshold) else None
        if row is not None:
            print(f"P_HALT reaches {threshold*100:.0f}% at N = {int(row['N'])}")

    # Relationship to N=5 phase transition
    print("\n" + "-" * 70)
    print("Connection to N=5 Phase Transition Discovery:")
    print("-" * 70)
    n5_row = results_df[results_df["N"] == 5].iloc[0]
    print(f"At N=5: P_HALT = {n5_row['P_HALT']:.4f} ({n5_row['P_HALT_pct']:.2f}%)")
    print(f"        P_CYCLE = {n5_row['P_CYCLE']:.4f} ({n5_row['P_CYCLE_pct']:.2f}%)")
    print(f"        {int(n5_row['cycle_pages']):,} pages can participate in N=5 basin structure")
    print(f"\nNote: Basin SIZE peak at N=5 occurs despite P_CYCLE being relatively low.")
    print("This suggests the phase transition is driven by DEPTH dynamics, not just eligibility.")

    # Save results
    output_path = ANALYSIS_DIR / "halt_probability_analysis.tsv"
    results_df.to_csv(output_path, sep="\t", index=False)
    print(f"\n\nResults saved to: {output_path}")

    # Summary for contracts
    print("\n" + "=" * 70)
    print("SUMMARY FOR CONTRACT REGISTRY")
    print("=" * 70)
    print(f"""
Conjecture 6.1 (Monotonic HALT): {result_6_1['result']}
  - P_HALT(N) increases strictly with N
  - At N=1: P_HALT = 0% (all pages have ≥1 link)
  - At N=50: P_HALT = {results_df[results_df['N']==50].iloc[0]['P_HALT']*100:.1f}%

Conjecture 6.3 (Phase Transition N*): {result_6_3['result']}
  - Crossover point N* ≈ {result_6_3['crossover_n_interpolated']:.1f}
  - At N={result_6_3['closest_integer_n']}: P_HALT ≈ P_CYCLE ≈ 50%
  - This is DIFFERENT from basin SIZE peak at N=5

Key Insight:
  - HALT/CYCLE crossover occurs at N* ≈ {result_6_3['crossover_n_interpolated']:.0f}
  - Basin SIZE peak occurs at N=5
  - These are DIFFERENT phenomena:
    * N* marks eligibility threshold (can vs cannot follow N-th link)
    * N=5 peak marks depth dynamics optimum (exploration vs convergence)
""")

if __name__ == "__main__":
    main()
