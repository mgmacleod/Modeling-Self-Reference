#!/usr/bin/env python3
"""Unified launcher for tunneling visualization tools.

This script provides a single entry point to:
1. Generate static HTML visualizations (Sankey, Explorer)
2. Start interactive Dash servers (Dashboard, Path Tracer)
3. Launch all tools at once

Usage:
    # Generate all static visualizations
    python launch-tunneling-viz.py --static

    # Start dashboard server only
    python launch-tunneling-viz.py --dashboard

    # Start all servers
    python launch-tunneling-viz.py --all

    # Generate static and start dashboard
    python launch-tunneling-viz.py --static --dashboard
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
REPORT_ASSETS = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def run_static_generators() -> List[Path]:
    """Run static HTML generators and return output paths."""
    outputs = []

    print("=" * 70)
    print("Generating Static Visualizations")
    print("=" * 70)
    print()

    # Sankey diagram
    print("[1/2] Generating Sankey diagram...")
    sankey_script = SCRIPT_DIR / "sankey-basin-flows.py"
    result = subprocess.run(
        [sys.executable, str(sankey_script)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    else:
        output_path = REPORT_ASSETS / "tunneling_sankey.html"
        if output_path.exists():
            outputs.append(output_path)
            print(f"  Created: {output_path}")
    print()

    # Tunnel node explorer
    print("[2/2] Generating Tunnel Node Explorer...")
    explorer_script = SCRIPT_DIR / "tunnel-node-explorer.py"
    result = subprocess.run(
        [sys.executable, str(explorer_script)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    else:
        output_path = REPORT_ASSETS / "tunnel_node_explorer.html"
        if output_path.exists():
            outputs.append(output_path)
            print(f"  Created: {output_path}")
    print()

    return outputs


def start_dashboard(port: int = 8060) -> subprocess.Popen:
    """Start the dashboard server."""
    dashboard_script = SCRIPT_DIR / "tunneling-dashboard.py"
    process = subprocess.Popen(
        [sys.executable, str(dashboard_script), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return process


def start_path_tracer(port: int = 8061) -> subprocess.Popen:
    """Start the path tracer server."""
    tracer_script = SCRIPT_DIR / "path-tracer-tool.py"
    process = subprocess.Popen(
        [sys.executable, str(tracer_script), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return process


def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for a server to become available."""
    import socket

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                return True
        except socket.error:
            pass
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Launch tunneling visualization tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch-tunneling-viz.py --static           Generate static HTML files
  python launch-tunneling-viz.py --dashboard        Start dashboard server
  python launch-tunneling-viz.py --tracer           Start path tracer server
  python launch-tunneling-viz.py --all              Start all servers
  python launch-tunneling-viz.py --static --all     Generate static + start servers
        """,
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Generate static HTML visualizations",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Start the main dashboard server",
    )
    parser.add_argument(
        "--tracer",
        action="store_true",
        help="Start the path tracer server",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Start all servers (dashboard + tracer)",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8060,
        help="Port for dashboard (default: 8060)",
    )
    parser.add_argument(
        "--tracer-port",
        type=int,
        default=8061,
        help="Port for path tracer (default: 8061)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open browser after starting servers",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available visualizations and exit",
    )
    args = parser.parse_args()

    # Handle --list
    if args.list:
        print("Available Tunneling Visualizations:")
        print("=" * 50)
        print()
        print("Static HTML (no server required):")
        print("  - Sankey Diagram: report/assets/tunneling_sankey.html")
        print("  - Node Explorer: report/assets/tunnel_node_explorer.html")
        print()
        print("Interactive Servers:")
        print("  - Dashboard: http://localhost:8060 (5-tab exploration)")
        print("  - Path Tracer: http://localhost:8061 (per-page tracing)")
        print()
        return

    # Default to showing help if no options
    if not any([args.static, args.dashboard, args.tracer, args.all]):
        parser.print_help()
        return

    # Run static generators
    static_outputs = []
    if args.static:
        static_outputs = run_static_generators()

    # Start servers
    processes: List[subprocess.Popen] = []
    server_urls = []

    if args.all:
        args.dashboard = True
        args.tracer = True

    if args.dashboard:
        print("=" * 70)
        print("Starting Dashboard Server")
        print("=" * 70)
        print()
        proc = start_dashboard(args.dashboard_port)
        processes.append(proc)
        url = f"http://localhost:{args.dashboard_port}"
        server_urls.append(("Dashboard", url))
        print(f"  Starting on {url}...")

        if wait_for_server(args.dashboard_port):
            print(f"  Dashboard ready at {url}")
        else:
            print("  Warning: Server may not be ready yet")
        print()

    if args.tracer:
        print("=" * 70)
        print("Starting Path Tracer Server")
        print("=" * 70)
        print()
        proc = start_path_tracer(args.tracer_port)
        processes.append(proc)
        url = f"http://localhost:{args.tracer_port}"
        server_urls.append(("Path Tracer", url))
        print(f"  Starting on {url}...")

        if wait_for_server(args.tracer_port):
            print(f"  Path Tracer ready at {url}")
        else:
            print("  Warning: Server may not be ready yet")
        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()

    if static_outputs:
        print("Static files created:")
        for path in static_outputs:
            print(f"  - {path}")
        print()

    if server_urls:
        print("Servers running:")
        for name, url in server_urls:
            print(f"  - {name}: {url}")
        print()

        if args.open_browser and server_urls:
            time.sleep(1)  # Give servers a moment
            webbrowser.open(server_urls[0][1])

        print("Press Ctrl+C to stop all servers")
        print()

        try:
            # Wait for processes
            while True:
                for proc in processes:
                    if proc.poll() is not None:
                        print(f"Server process exited with code {proc.returncode}")
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            print("Shutting down servers...")
            for proc in processes:
                proc.terminate()
            for proc in processes:
                proc.wait(timeout=5)
            print("All servers stopped")
    else:
        if static_outputs:
            print("Open the HTML files in a browser to view:")
            for path in static_outputs:
                print(f"  file://{path}")
        print()
        print("Done!")


if __name__ == "__main__":
    main()
