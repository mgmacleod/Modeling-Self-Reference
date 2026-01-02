#!/usr/bin/env python3
"""Automated smoke tests for consolidated visualization dashboards.

This script tests:
1. Shared module imports and functions
2. Data loaders return expected data volumes
3. Dashboard startup (HTTP 200 response)
4. API client functionality (if API server is running)

Usage:
    python n-link-analysis/viz/tests/test_dashboards.py

Exit codes:
    0: All tests passed
    1: Some tests failed
"""

import subprocess
import sys
import time
from pathlib import Path

# Add viz directory to path
VIZ_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(VIZ_DIR))


def test_shared_imports():
    """Test shared module imports."""
    print("Testing shared module imports...")

    from shared import BASIN_COLORS, BASIN_SHORT_NAMES, get_basin_color, get_short_name
    assert len(BASIN_COLORS) > 0, "BASIN_COLORS is empty"
    assert len(BASIN_SHORT_NAMES) > 0, "BASIN_SHORT_NAMES is empty"

    # Test color functions
    color = get_basin_color("Gulf_of_Maine__Massachusetts")
    assert color == "#1f77b4", f"Expected #1f77b4, got {color}"

    unknown_color = get_basin_color("Unknown_Basin")
    assert unknown_color == "#7f7f7f", f"Expected gray fallback, got {unknown_color}"

    short_name = get_short_name("Gulf_of_Maine__Massachusetts")
    assert short_name == "Gulf of Maine", f"Expected 'Gulf of Maine', got {short_name}"

    from shared import load_basin_assignments, load_basin_flows, load_tunnel_ranking, REPO_ROOT
    assert REPO_ROOT.exists(), f"REPO_ROOT does not exist: {REPO_ROOT}"

    from shared import metric_card, filter_row, badge, info_card, hex_to_rgba
    # Just verify they're callable
    assert callable(metric_card)
    assert callable(hex_to_rgba)

    print("  ✓ All shared imports successful")
    return True


def test_data_loaders():
    """Test data loaders return expected data volumes."""
    print("Testing data loaders...")

    from shared import load_basin_assignments, load_basin_flows, load_tunnel_ranking

    df = load_basin_assignments()
    assert len(df) > 2_000_000, f"Basin assignments: expected >2M rows, got {len(df):,}"
    print(f"  ✓ Basin assignments: {len(df):,} rows")

    flows = load_basin_flows()
    assert len(flows) > 50, f"Basin flows: expected >50 rows, got {len(flows)}"
    print(f"  ✓ Basin flows: {len(flows)} rows")

    ranking = load_tunnel_ranking()
    assert len(ranking) > 40_000, f"Tunnel ranking: expected >40K rows, got {len(ranking):,}"
    print(f"  ✓ Tunnel ranking: {len(ranking):,} rows")

    return True


def test_dashboard_starts(name: str, command: str, port: int, timeout: int = 20) -> bool:
    """Test that a dashboard starts and responds with HTTP 200."""
    import requests

    print(f"Testing {name} (port {port})...")

    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        # Wait for startup
        for i in range(timeout):
            try:
                resp = requests.get(f"http://localhost:{port}", timeout=2)
                if resp.status_code == 200:
                    print(f"  ✓ {name} responds with HTTP 200")
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)

        print(f"  ✗ {name} did not respond within {timeout}s")
        return False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_api_client():
    """Test API client module."""
    print("Testing API client...")

    from api_client import NLinkAPIClient, check_api_available

    api_url = "http://localhost:8000"

    # Client instantiation should always work
    client = NLinkAPIClient(api_url)
    assert hasattr(client, "health_check")
    assert hasattr(client, "search_pages")
    assert hasattr(client, "trace_single")
    print("  ✓ API client instantiation works")

    # Live tests only if API is running
    if check_api_available(api_url):
        print(f"  API server detected at {api_url}")

        # Health check
        health = client.health_check()
        assert health is True, f"Health check failed: {health}"
        print("  ✓ health_check() returns True")

        # Search
        results = client.search_pages("Massachusetts", limit=3)
        assert len(results) > 0, "Search returned no results"
        print(f"  ✓ search_pages() returns {len(results)} results")

        # Trace
        trace = client.trace_single(n=1, start_title="Massachusetts")
        assert trace is not None, "Trace returned None"
        print(f"  ✓ trace_single() returns trace data")
    else:
        print(f"  (API server not running - skipping live tests)")

    return True


def run_all_tests():
    """Run all dashboard smoke tests."""
    print("=" * 60)
    print("Visualization Dashboard Smoke Tests")
    print("=" * 60)
    print()

    results = {}

    # Module tests
    try:
        results["shared_imports"] = test_shared_imports()
    except Exception as e:
        print(f"  ✗ Shared imports failed: {e}")
        results["shared_imports"] = False
    print()

    try:
        results["data_loaders"] = test_data_loaders()
    except Exception as e:
        print(f"  ✗ Data loaders failed: {e}")
        results["data_loaders"] = False
    print()

    try:
        results["api_client"] = test_api_client()
    except Exception as e:
        print(f"  ✗ API client failed: {e}")
        results["api_client"] = False
    print()

    # Dashboard startup tests (use non-standard ports to avoid conflicts)
    dashboards = [
        ("Basin Geometry Viewer", f"python {VIZ_DIR}/dash-basin-geometry-viewer.py --port 8555", 8555),
        ("Multiplex Analyzer", f"python {VIZ_DIR}/multiplex-analyzer.py --port 8556", 8556),
        ("Tunneling Explorer", f"python {VIZ_DIR}/tunneling/tunneling-explorer.py --port 8560", 8560),
    ]

    for name, cmd, port in dashboards:
        try:
            results[name] = test_dashboard_starts(name, cmd, port, timeout=20)
        except Exception as e:
            print(f"  ✗ {name} test failed: {e}")
            results[name] = False

    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    return all(results.values())


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted")
        sys.exit(1)
